import click

from hrms.setup import after_install as setup

from hrms.flow_brand import apply_site_branding


def after_install():
	try:
		print("Setting up FlowHR...")
		setup()
		apply_site_branding()

		click.secho("Thank you for installing FlowHR!", fg="green")

	except Exception as e:
		BUG_REPORT_URL = "https://github.com/frappe/hrms/issues/new"
		click.secho(
			"Installation for FlowHR app failed due to an error."
			" Please try re-installing the app or"
			f" report the issue on {BUG_REPORT_URL} if not resolved.",
			fg="bright_red",
		)
		raise e
