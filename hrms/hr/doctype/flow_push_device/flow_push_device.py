import frappe
from frappe.model.document import Document


class FLOWPushDevice(Document):
	# begin: auto-generated types
	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		device_id: DF.Data | None
		device_information: DF.SmallText | None
		product: DF.Literal["FLOW", "FlowHR", "FlowConnect"]
		token: DF.Data
		user: DF.Link
	# end: auto-generated types

	def before_validate(self):
		if frappe.session.user == "Guest":
			frappe.throw(frappe._("Please sign in before enabling push notifications"))
		self.user = frappe.session.user
