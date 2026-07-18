import base64
import json
import os
from functools import lru_cache

from google.auth.transport.requests import AuthorizedSession
from google.oauth2 import service_account

import frappe
from frappe import _
from frappe.utils import add_months, now_datetime, strip_html

PRODUCTS = {
	"flow": "FLOW",
	"hrms": "FlowHR",
	"flowhr": "FlowHR",
	"raven": "FlowConnect",
	"flowconnect": "FlowConnect",
}
FCM_SCOPE = "https://www.googleapis.com/auth/firebase.messaging"
MAX_DATA_VALUE_LENGTH = 1000


def _setting(name: str):
	return os.environ.get(name) or frappe.conf.get(name.lower())


def _load_json_setting(name: str) -> dict:
	value = _setting(name)
	if isinstance(value, dict):
		return value
	if not value:
		return {}
	try:
		return json.loads(value)
	except (TypeError, json.JSONDecodeError) as exc:
		raise frappe.ValidationError(_("{0} must contain valid JSON").format(name)) from exc


def get_firebase_web_config() -> dict:
	config = _load_json_setting("FLOW_FIREBASE_WEB_CONFIG")
	required = {"apiKey", "appId", "messagingSenderId", "projectId"}
	if not required.issubset(config):
		return {}
	return config


def get_vapid_public_key() -> str:
	return _setting("FLOW_FIREBASE_VAPID_PUBLIC_KEY") or ""


def is_enabled(require_sender: bool = False) -> bool:
	if not get_firebase_web_config() or not get_vapid_public_key():
		return False
	return not require_sender or bool(_setting("FLOW_FIREBASE_SERVICE_ACCOUNT_B64"))


@frappe.whitelist()
def get_web_config() -> dict:
	if frappe.session.user == "Guest":
		frappe.throw(_("Authentication required"), frappe.PermissionError)
	if not is_enabled():
		frappe.throw(_("FLOW web push notifications are not configured"), frappe.ValidationError)
	return {"config": get_firebase_web_config(), "vapid_public_key": get_vapid_public_key()}


def _normalise_product(product: str) -> str:
	value = PRODUCTS.get((product or "").lower())
	if not value:
		frappe.throw(_("Unsupported notification product"))
	return value


@frappe.whitelist(methods=["POST"])
def subscribe(
	fcm_token: str,
	product: str,
	device_information: str | None = None,
	device_id: str | None = None,
):
	if frappe.session.user == "Guest":
		frappe.throw(_("Authentication required"), frappe.PermissionError)
	if not is_enabled():
		frappe.throw(_("FLOW web push notifications are not configured"), frappe.ValidationError)
	if not fcm_token or len(fcm_token) > 512:
		frappe.throw(_("Invalid Firebase registration token"))

	product = _normalise_product(product)
	name = frappe.db.exists("FLOW Push Device", {"token": fcm_token, "product": product})
	if name:
		doc = frappe.get_doc("FLOW Push Device", name)
		doc.user = frappe.session.user
		doc.product = product
		doc.device_id = (device_id or "")[:140]
		doc.device_information = (device_information or "")[:1000]
		doc.save(ignore_permissions=True)
	else:
		frappe.get_doc(
			{
				"doctype": "FLOW Push Device",
				"user": frappe.session.user,
				"product": product,
				"device_id": (device_id or "")[:140],
				"token": fcm_token,
				"device_information": (device_information or "")[:1000],
			}
		).insert(ignore_permissions=True)
	return "Subscribed"


@frappe.whitelist(methods=["POST"])
def unsubscribe(fcm_token: str, product: str):
	if frappe.session.user == "Guest":
		frappe.throw(_("Authentication required"), frappe.PermissionError)
	name = frappe.db.exists(
		"FLOW Push Device",
		{"token": fcm_token, "user": frappe.session.user, "product": _normalise_product(product)},
	)
	if name:
		frappe.delete_doc("FLOW Push Device", name, ignore_permissions=True)
	return "Unsubscribed"


@frappe.whitelist(methods=["POST"])
def send_test_notification(product: str = "FlowConnect"):
	if frappe.session.user == "Guest":
		frappe.throw(_("Authentication required"), frappe.PermissionError)
	product = _normalise_product(product)
	link = frappe.utils.get_url("/raven" if product == "FlowConnect" else "/hrms")
	enqueue_notification_to_user(
		user=frappe.session.user,
		title="FLOW notifications are ready",
		body=f"Your {product} browser notifications are configured correctly.",
		link=link,
		product=product,
		data={"type": "Test notification"},
	)
	return "Queued"


def enqueue_notification_to_user(user: str, title: str, body: str, link: str, product: str, data=None, icon=None):
	enqueue_notification_to_users([user], title, body, link, product, data=data, icon=icon)


def enqueue_notification_to_users(users, title: str, body: str, link: str, product: str, data=None, icon=None):
	users = list(dict.fromkeys(user for user in users if user and user != "Guest"))
	if not users or not is_enabled(require_sender=True):
		return
	frappe.enqueue(
		"hrms.api.push.send_notification_to_users",
		queue="short",
		users=users,
		title=title,
		body=body,
		link=link,
		product=_normalise_product(product),
		data=data or {},
		icon=icon,
	)


def send_notification_to_users(users, title: str, body: str, link: str, product: str, data=None, icon=None):
	if not is_enabled(require_sender=True):
		return
	product = _normalise_product(product)
	filters = {"user": ("in", users)}
	if product != "FLOW":
		filters["product"] = product
	devices = frappe.get_all(
		"FLOW Push Device",
		filters=filters,
		fields=["token", "device_id", "modified"],
		order_by="modified desc",
	)
	tokens = []
	seen_installations = set()
	for device in devices:
		installation = device.device_id or device.token
		if installation in seen_installations:
			continue
		seen_installations.add(installation)
		tokens.append(device.token)
	for token in tokens:
		_send_to_token(token, title, body, link, data=data, icon=icon)


def notify_from_notification_log(doc, method=None):
	"""Deliver standard Desk/ERP notifications to every enabled FLOW browser."""
	if not is_enabled(require_sender=True):
		return
	user = getattr(doc, "for_user", None)
	if not user or user in {"Guest", getattr(doc, "from_user", None)}:
		return
	document_type = getattr(doc, "document_type", None) or ""
	document_name = getattr(doc, "document_name", None) or ""
	# FlowHR creates richer PWA notifications for these documents.
	if document_type in {"Leave Application", "Expense Claim", "Shift Request"}:
		return
	link = getattr(doc, "link", None)
	if not link and document_type and document_name:
		link = f"{frappe.utils.get_url()}/app/{frappe.scrub(document_type).replace('_', '-')}/{document_name}"
	elif link and link.startswith("/"):
		link = frappe.utils.get_url() + link
	link = link or frappe.utils.get_url("/app")
	enqueue_notification_to_user(
		user=user,
		title=document_type or "FLOW",
		body=getattr(doc, "subject", None) or getattr(doc, "email_content", None) or "You have a new notification",
		link=link,
		product="FLOW",
		data={"reference_doctype": document_type, "reference_name": document_name},
	)


def prune_stale_devices():
	"""Remove browser registrations not refreshed for two months."""
	frappe.db.delete("FLOW Push Device", {"modified": ("<", add_months(now_datetime(), -2))})


def _string_data(data: dict) -> dict:
	result = {}
	for key, value in (data or {}).items():
		if value is None:
			continue
		if isinstance(value, (dict, list)):
			value = json.dumps(value, separators=(",", ":"))
		elif isinstance(value, bool):
			value = "1" if value else "0"
		else:
			value = str(value)
		result[str(key)] = value[:MAX_DATA_VALUE_LENGTH]
	return result


def _send_to_token(token: str, title: str, body: str, link: str, data=None, icon=None):
	project_id = get_firebase_web_config()["projectId"]
	payload_data = _string_data(data or {})
	payload_data.update(
		{
			"title": strip_html(title or "FLOW")[:200],
			"body": strip_html(body or "")[:MAX_DATA_VALUE_LENGTH],
			"click_action": link or frappe.utils.get_url(),
			"notification_icon": icon or f"{frappe.utils.get_url()}/assets/hrms/images/flow-logo.svg",
		}
	)
	payload = {
		"message": {
			"token": token,
			"data": payload_data,
			"webpush": {"headers": {"Urgency": "high"}},
		}
	}
	response = _authorized_session().post(
		f"https://fcm.googleapis.com/v1/projects/{project_id}/messages:send",
		json=payload,
		timeout=15,
	)
	if response.ok:
		return
	if response.status_code in {400, 404} and ("UNREGISTERED" in response.text or "registration-token-not-registered" in response.text):
		frappe.db.delete("FLOW Push Device", {"token": token})
		return
	frappe.log_error(
		title="FLOW push notification delivery failed",
		message=f"FCM returned HTTP {response.status_code}: {response.text[:2000]}",
	)


@lru_cache(maxsize=1)
def _authorized_session() -> AuthorizedSession:
	raw = _setting("FLOW_FIREBASE_SERVICE_ACCOUNT_B64")
	try:
		service_account_info = json.loads(base64.b64decode(raw).decode("utf-8"))
	except Exception as exc:
		raise frappe.ValidationError(_("FLOW_FIREBASE_SERVICE_ACCOUNT_B64 is invalid")) from exc
	credentials = service_account.Credentials.from_service_account_info(
		service_account_info,
		scopes=[FCM_SCOPE],
	)
	return AuthorizedSession(credentials)
