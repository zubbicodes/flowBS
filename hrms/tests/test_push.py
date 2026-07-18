import json
import os
from unittest.mock import patch

from frappe.tests import UnitTestCase

from hrms.api import push


class TestFLOWPush(UnitTestCase):
	def test_payload_data_is_converted_to_fcm_strings(self):
		self.assertEqual(
			push._string_data({"count": 2, "enabled": True, "details": {"name": "FLOW"}, "none": None}),
			{"count": "2", "enabled": "1", "details": '{"name":"FLOW"}'},
		)

	@patch.dict(
		os.environ,
		{
			"FLOW_FIREBASE_WEB_CONFIG": json.dumps(
				{
					"apiKey": "test",
					"appId": "test-app",
					"messagingSenderId": "123",
					"projectId": "flow-test",
				}
			),
			"FLOW_FIREBASE_VAPID_PUBLIC_KEY": "test-vapid-key",
		},
		clear=False,
	)
	def test_web_configuration_enables_browser_registration(self):
		self.assertTrue(push.is_enabled())
		self.assertEqual(push.get_firebase_web_config()["projectId"], "flow-test")

