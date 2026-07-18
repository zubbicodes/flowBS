(() => {
  const BRAND = Object.freeze({
    master: "FLOW",
    erp: "FlowERP",
    hr: "FlowHR",
    connect: "FlowConnect",
    drive: "FlowDrive",
  })

  const PRODUCT_LOGOS = Object.freeze({
    erp: "/assets/hrms/images/flow_erp_logo.png",
    hr: "/assets/hrms/images/flow_hr_logo.png",
    connect: "/assets/hrms/images/flow_conncet_logo.png",
    drive: "/assets/hrms/images/flow_drive_logo.png",
  })

  const substitutions = [
    [/Telegram Drive/g, BRAND.drive],
    [/Frappe HR/g, BRAND.hr],
    [/ERPNext/g, BRAND.erp],
    [/Raven/g, BRAND.connect],
    [/Frappe/g, BRAND.master],
  ]

  const replaceVisibleText = (root) => {
    if (!root?.querySelectorAll) return
    const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT)
    const nodes = []
    while (walker.nextNode()) nodes.push(walker.currentNode)
    for (const node of nodes) {
		if (node.parentElement?.closest("script, style, code, pre, input, textarea, [contenteditable='true']")) continue
		let value = node.nodeValue || ""
		for (const [pattern, replacement] of substitutions) value = value.replace(pattern, replacement)
		if (value !== node.nodeValue) node.nodeValue = value
    }
  }

  const applyBrand = () => {
    document.documentElement.dataset.brand = "flow"
	let title = document.title
	for (const [pattern, replacement] of substitutions) title = title.replace(pattern, replacement)
	document.title = title
	replaceVisibleText(document.body)

    document.querySelectorAll("img").forEach((image) => {
      const source = image.getAttribute("src") || ""
      const alt = image.getAttribute("alt") || ""
      const identity = `${source} ${alt}`
      if (/erpnext-logo|flowerp/i.test(identity)) {
        image.src = PRODUCT_LOGOS.erp
        image.alt = BRAND.erp
      } else if (/frappe-hr-logo|flowhr/i.test(identity)) {
        image.src = PRODUCT_LOGOS.hr
        image.alt = BRAND.hr
      } else if (/raven-logo|flowconnect/i.test(identity)) {
        image.src = PRODUCT_LOGOS.connect
        image.alt = BRAND.connect
      } else if (/telegram-drive|telegram_drive|flowdrive/i.test(identity)) {
        image.src = PRODUCT_LOGOS.drive
        image.alt = BRAND.drive
      }
    })

    document.querySelectorAll('link[rel~="icon"]:not([rel="apple-touch-startup-image"])').forEach((icon) => {
      icon.href = "/assets/hrms/images/flow-logo.png"
      icon.type = "image/png"
    })
  }

  const configureGlobalPWA = async () => {
    if (!location.pathname.startsWith("/app")) return

    if (!document.querySelector('link[rel="manifest"]')) {
      const manifest = document.createElement("link")
      manifest.rel = "manifest"
      manifest.href = "/assets/hrms/flow.webmanifest"
      document.head.appendChild(manifest)
    }

    if (!document.querySelector('link[rel="apple-touch-icon"]')) {
      const icon = document.createElement("link")
      icon.rel = "apple-touch-icon"
      icon.href = "/assets/hrms/manifest/apple-icon-180.png"
      document.head.appendChild(icon)
    }

    if (!("serviceWorker" in navigator)) return

    let workerURL = "/assets/hrms/frontend/sw.js"
    try {
      const response = await fetch("/api/method/hrms.api.push.get_web_config")
      if (response.ok) {
        const payload = await response.json()
        const config = payload?.message?.config
        if (config) workerURL += `?config=${encodeURIComponent(JSON.stringify(config))}`
      }
    } catch (error) {
      console.info("FLOW PWA registered without push configuration", error)
    }

    try {
      await navigator.serviceWorker.register(workerURL, { scope: "/" })
    } catch (error) {
      console.error("Unable to register the FLOW application service worker", error)
    }
  }

  const observer = new MutationObserver(applyBrand)
  const start = () => {
    applyBrand()
    configureGlobalPWA()
    observer.observe(document.body, { childList: true, subtree: true })
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", start, { once: true })
  } else {
    start()
  }
})()
