import frappe
from frappe.model.document import Document


class FLOWPushDevice(Document):
	def before_validate(self):
		if frappe.session.user == "Guest":
			frappe.throw(frappe._("Please sign in before enabling push notifications"))
		self.user = frappe.session.user

