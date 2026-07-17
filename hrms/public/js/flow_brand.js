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

  const observer = new MutationObserver(applyBrand)
  const start = () => {
    applyBrand()
    observer.observe(document.body, { childList: true, subtree: true })
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", start, { once: true })
  } else {
    start()
  }
})()
