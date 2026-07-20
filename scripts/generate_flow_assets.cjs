const fs = require("node:fs")
const path = require("node:path")
const sharp = require("sharp")

const root = path.resolve(__dirname, "..")
const frameworkLogo = path.join(root, "hrms/public/images/framework_logo.png")
const hrLogo = path.join(root, "hrms/public/images/flow_hr_logo.png")
const connectLogo = path.join(root, "hrms/public/images/flow_connect_logo.png")

const existingFiles = (directory, extension) =>
  fs.existsSync(directory)
    ? fs
        .readdirSync(directory)
        .filter((name) => name.toLowerCase().endsWith(extension))
        .map((name) => path.join(directory, name))
    : []

async function renderLike(source, target, options = {}) {
  const current = await sharp(target).metadata()
  const width = options.width || current.width
  const height = options.height || current.height
  const format = options.format || path.extname(target).slice(1)
  let pipeline = sharp(source, { density: 256 }).resize(width, height, { fit: "cover" })
  if (format === "jpg" || format === "jpeg") pipeline = pipeline.jpeg({ quality: 92 })
  else pipeline = pipeline.png({ compressionLevel: 9 })
  await pipeline.toFile(`${target}.flow-tmp`)
  fs.renameSync(`${target}.flow-tmp`, target)
}

async function renderSplash(source, target) {
  const current = await sharp(target).metadata()
  const width = current.width
  const height = current.height
  const logoSize = Math.max(128, Math.round(Math.min(width, height) * 0.26))
  const logo = await sharp(source, { density: 256 })
    .resize(logoSize, logoSize, { fit: "contain" })
    .png()
    .toBuffer()
  const canvas = sharp({
    create: { width, height, channels: 4, background: "#ffffff" },
  }).composite([{ input: logo, gravity: "centre" }])
  const ext = path.extname(target).toLowerCase()
  const pipeline = ext === ".jpg" || ext === ".jpeg"
    ? canvas.jpeg({ quality: 92 })
    : canvas.png({ compressionLevel: 9 })
  await pipeline.toFile(`${target}.flow-tmp`)
  fs.renameSync(`${target}.flow-tmp`, target)
}

async function main() {
  const frameworkIconTargets = [
    "hrms/public/manifest/manifest-icon-512.maskable.png",
    "hrms/public/manifest/manifest-icon-192.maskable.png",
    "hrms/public/manifest/favicon-196.png",
    "hrms/public/manifest/apple-icon-180.png",
  ]
  const hrIconTargets = [
    "hrms/public/images/frappe-hr-logo.png",
    "hrms/hrms.png",
    "frontend/public/favicon.png",
    "roster/public/favicon.png",
  ]
  const connectIconTargets = [
    "raven/raven_logo.png",
    "raven/raven/public/raven-logo.png",
    "raven/raven/public/manifest/mstile-150x150.png",
    "raven/raven/public/manifest/favicon-96x96.png",
    "raven/raven/public/manifest/favicon-32x32.png",
    "raven/raven/public/manifest/favicon-16x16.png",
    "raven/raven/public/manifest/apple-touch-icon.png",
    "raven/raven/public/manifest/android-chrome-512x512.png",
    "raven/raven/public/manifest/android-chrome-192x192.png",
    "raven/apps/mobile/assets/icon.png",
    "raven/apps/mobile/assets/favicon.png",
    "raven/apps/mobile/assets/adaptive-icon.png",
  ]

  for (const [source, targets] of [
    [frameworkLogo, frameworkIconTargets],
    [hrLogo, hrIconTargets],
    [connectLogo, connectIconTargets],
  ]) {
    for (const relative of targets) {
      const target = path.join(root, relative)
      if (fs.existsSync(target)) await renderLike(source, target)
    }
  }

  const splashTargets = [
    ...existingFiles(path.join(root, "hrms/public/manifest"), ".jpg"),
    ...existingFiles(path.join(root, "raven/frontend/public/splash_screens"), ".png"),
  ]
  for (const target of splashTargets) {
    await renderSplash(target.includes(`${path.sep}raven${path.sep}`) ? connectLogo : hrLogo, target)
  }

  const mobileSplash = path.join(root, "raven/apps/mobile/assets/splash.png")
  if (fs.existsSync(mobileSplash)) await renderSplash(connectLogo, mobileSplash)

  const iconCount = frameworkIconTargets.length + hrIconTargets.length + connectIconTargets.length
  console.log(`FLOW assets generated: ${iconCount} icons, ${splashTargets.length + 1} splashes`)
}

main().catch((error) => {
  console.error(error)
  process.exitCode = 1
})
