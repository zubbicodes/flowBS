<template>
	<div class="flex flex-col gap-3 w-full">
		<div class="flex items-center justify-between px-0.5">
			<div class="text-base font-semibold text-gray-900">{{ title || __("Quick Links") }}</div>
			<span class="text-xs font-medium text-gray-500">{{ __("Quick access") }}</span>
		</div>
		<div class="grid grid-cols-2 gap-3">
			<router-link
				v-for="link in internalLinks"
				:key="link.title"
				:to="{ name: link.route }"
				class="flex min-h-32 flex-col justify-between rounded-xl border border-gray-200 bg-white p-4 shadow-sm transition active:scale-95"
			>
				<div class="flex h-10 w-10 items-center justify-center rounded-lg bg-gray-100 text-gray-700">
					<component v-if="link.icon" :is="link.icon" class="h-5 w-5" />
					<FeatherIcon v-else :name="link.featherIcon" class="h-5 w-5" />
				</div>
				<div>
					<div class="text-sm font-semibold text-gray-900">{{ link.title }}</div>
					<div class="mt-1 text-xs leading-4 text-gray-500">{{ link.description }}</div>
				</div>
			</router-link>
			<a
				v-for="link in externalLinks"
				:key="link.title"
				:href="link.href"
				class="flex min-h-32 flex-col justify-between rounded-xl border border-gray-200 bg-white p-4 shadow-sm transition active:scale-95"
			>
				<div class="flex items-start justify-between">
					<div class="flex h-10 w-10 items-center justify-center rounded-lg bg-gray-100 text-gray-700">
						<component v-if="link.icon" :is="link.icon" class="h-5 w-5" />
						<FeatherIcon v-else :name="link.featherIcon" class="h-5 w-5" />
					</div>
					<FeatherIcon name="arrow-up-right" class="h-4 w-4 text-gray-400" />
				</div>
				<div>
					<div class="text-sm font-semibold text-gray-900">{{ link.title }}</div>
					<div class="mt-1 text-xs leading-4 text-gray-500">{{ link.description }}</div>
				</div>
			</a>
		</div>
	</div>
</template>

<script setup>
import { FeatherIcon } from "frappe-ui"
import { computed } from "vue"

const props = defineProps({
	title: {
		type: String,
		required: false,
		default: "",
	},
	items: {
		type: Array,
		required: true,
	},
})

const internalLinks = computed(() => props.items.filter((link) => link.route))
const externalLinks = computed(() => props.items.filter((link) => link.href))
</script>
