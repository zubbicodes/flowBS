(() => {
  const BRAND = Object.freeze({
    master: "FLOW",
    erp: "FlowERP",
    hr: "FlowHR",
    connect: "FlowConnect",
  })

  const substitutions = [
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
      if (/frappe(?:-framework|-hr)?-logo|erpnext-logo|raven-logo/i.test(`${source} ${alt}`)) {
        image.src = "/assets/hrms/images/flow-logo.svg"
        image.alt = BRAND.master
      }
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
