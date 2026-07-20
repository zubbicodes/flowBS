import os

import frappe


BRAND = {
	"master": "FLOW",
	"erp": "FlowERP",
	"hr": "FlowHR",
	"connect": "FlowConnect",
	"drive": "FlowDrive",
	"roster": "FlowRoster",
	"careers": "FlowCareers",
	"logo": "/assets/hrms/images/framework_logo.png",
	"framework_logo": "/assets/hrms/images/framework_logo.png",
	"erp_logo": "/assets/hrms/images/flow_erp_logo.png",
	"hr_logo": "/assets/hrms/images/flow_hr_logo.png",
	"connect_logo": "/assets/hrms/images/flow_connect_logo.png",
	"drive_logo": "/assets/hrms/images/flow_drive_logo.png",
}


def get_brand():
	brand = dict(BRAND)
	brand["support_email"] = (
		frappe.conf.get("flow_support_email")
		or os.environ.get("FLOW_SUPPORT_EMAIL")
		or "support@flow.local"
	)
	brand["site_url"] = (
		frappe.conf.get("flow_site_url")
		or os.environ.get("FLOW_SITE_URL")
		or ""
	)
	return brand


def extend_bootinfo(bootinfo):
	brand = frappe._dict(get_brand())
	bootinfo.flow_brand = brand

	# Frappe builds the launcher before this extension runs. Apply the dedicated
	# product logo to each FLOW app, including the framework shell itself.
	for app in bootinfo.get("app_data") or []:
		identity = " ".join(
			str(app.get(key) or "")
			for key in ("app_name", "name", "title", "app_title", "route")
		).lower()
		if "erpnext" in identity or "flowerp" in identity:
			app["app_logo_url"] = brand.erp_logo
		elif "hrms" in identity or "flowhr" in identity:
			app["app_logo_url"] = brand.hr_logo
		elif "raven" in identity or "flowconnect" in identity:
			app["app_logo_url"] = brand.connect_logo
		elif "telegram_drive" in identity or "telegram-drive" in identity or "flowdrive" in identity:
			app["app_logo_url"] = brand.drive_logo
		elif "frappe" in identity or "framework" in identity:
			app["app_logo_url"] = brand.framework_logo


def update_website_context(context):
	brand = get_brand()
	context.update(
		{
			"app_name": brand["master"],
			"favicon": brand["logo"],
			"splash_image": brand["logo"],
			"flow_brand": frappe._dict(brand),
		}
	)


def _set_single_values(doctype, values):
	if not frappe.db.exists("DocType", doctype):
		return

	meta = frappe.get_meta(doctype)
	for fieldname, value in values.items():
		if meta.has_field(fieldname):
			frappe.db.set_single_value(doctype, fieldname, value, update_modified=False)


def apply_site_branding():
	"""Synchronize FLOW identity after migrations without touching business data."""
	brand = get_brand()
	_set_single_values(
		"Website Settings",
		{
			"app_name": brand["master"],
			"favicon": brand["logo"],
			"app_logo": brand["logo"],
			"brand_html": (
				'<span class="flow-brand"><img src="{logo}" alt="FLOW">FLOW</span>'
			).format(logo=brand["logo"]),
		},
	)
	_set_single_values("System Settings", {"app_name": brand["master"]})
	_set_single_values("Navbar Settings", {"app_logo": brand["logo"]})

	if frappe.db.exists("DocType", "Desktop Icon"):
		if frappe.db.exists("Desktop Icon", "Frappe HR") and not frappe.db.exists(
			"Desktop Icon", brand["hr"]
		):
			frappe.rename_doc("Desktop Icon", "Frappe HR", brand["hr"], force=True)
		frappe.db.set_value(
			"Desktop Icon",
			{"parent_icon": "Frappe HR"},
			"parent_icon",
			brand["hr"],
			update_modified=False,
		)

	frappe.clear_cache()


def apply_site_branding_and_commit():
	"""Apply branding immediately outside the migrate/install transaction."""
	apply_site_branding()
	frappe.db.commit()


def get_applied_branding():
	"""Return persisted brand values for deployment health checks."""
	return {
		"website_app_name": frappe.db.get_single_value("Website Settings", "app_name"),
		"website_favicon": frappe.db.get_single_value("Website Settings", "favicon"),
		"navbar_logo": frappe.db.get_single_value("Navbar Settings", "app_logo"),
		"runtime": get_brand(),
	}
