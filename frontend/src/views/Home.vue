<template>
	<BaseLayout>
		<template #body>
			<div class="flex flex-col items-center px-4 pt-5 pb-24 gap-5 bg-gray-50 min-h-full">
				<CheckInPanel />
				<QuickLinks :items="quickLinks" :title="__('Your workspace')" />
				<RequestPanel />
			</div>
		</template>
	</BaseLayout>
</template>

<script setup>
import { inject, markRaw } from "vue"

import CheckInPanel from "@/components/CheckInPanel.vue"
import QuickLinks from "@/components/QuickLinks.vue"
import BaseLayout from "@/components/BaseLayout.vue"
import RequestPanel from "@/components/RequestPanel.vue"
import AttendanceIcon from "@/components/icons/AttendanceIcon.vue"
import ShiftIcon from "@/components/icons/ShiftIcon.vue"
import LeaveIcon from "@/components/icons/LeaveIcon.vue"
import ExpenseIcon from "@/components/icons/ExpenseIcon.vue"
import SalaryIcon from "@/components/icons/SalaryIcon.vue"

const __ = inject("$translate")

const quickLinks = [
	{
		icon: markRaw(AttendanceIcon),
		title: __("Attendance"),
		description: __("Calendar and requests"),
		route: "AttendanceDashboard",
	},
	{
		icon: markRaw(ShiftIcon),
		title: __("My Check-ins"),
		description: __("View check-in history"),
		route: "EmployeeCheckinListView",
	},
	{
		icon: markRaw(LeaveIcon),
		title: __("Leave"),
		description: __("Balance and requests"),
		route: "LeavesDashboard",
	},
	{
		icon: markRaw(ExpenseIcon),
		title: __("Expenses"),
		description: __("Claims and status"),
		route: "ExpenseClaimsDashboard",
	},
	{
		icon: markRaw(SalaryIcon),
		title: __("Salary Slips"),
		description: __("View payslips"),
		route: "SalarySlipsDashboard",
	},
	{
		featherIcon: "briefcase",
		title: __("Projects"),
		description: __("Your assigned projects"),
		href: "/app/project",
	},
	{
		featherIcon: "message-circle",
		title: __("FlowConnect"),
		description: __("Messages and channels"),
		href: "/raven",
	},
	{
		featherIcon: "plus-circle",
		title: __("Quick Request"),
		description: __("Submit a leave request"),
		route: "LeaveApplicationFormView",
	},
]
</script>
