/**
 * Cuts the butterfly out of the brand artwork in src/assets/brand and renders
 * every icon the panel ships from it, so favicon, PWA icons and the header mark
 * are all the same artwork rather than a redrawn approximation. Run `npm run
 * brand:icons` after replacing the artwork.
 */
import { mkdir, writeFile } from 'node:fs/promises'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'

import sharp from 'sharp'

const root = join(dirname(fileURLToPath(import.meta.url)), '..')
const source = join(root, 'src/assets/brand/logo-source.png')
const brandDir = join(root, 'public/brand')
const publicDir = join(root, 'public')

const crop = { left: 56, top: 32, width: 336, height: 336 }
const plate = { r: 8, g: 7, b: 5 }

const master = await sharp(source)
  .extract(crop)
  .resize(1024, 1024, { kernel: 'lanczos3' })
  .png()
  .toBuffer()

function featherMask(size) {
  return Buffer.from(
    `<svg xmlns="http://www.w3.org/2000/svg" width="${size}" height="${size}">
       <defs><radialGradient id="m" cx="0.5" cy="0.5" r="0.5">
         <stop offset="0.74" stop-color="#fff" stop-opacity="1"/>
         <stop offset="1" stop-color="#fff" stop-opacity="0"/>
       </radialGradient></defs>
       <rect width="${size}" height="${size}" fill="url(#m)"/>
     </svg>`,
  )
}

function roundedMask(size, radius) {
  return Buffer.from(
    `<svg xmlns="http://www.w3.org/2000/svg" width="${size}" height="${size}">
       <rect width="${size}" height="${size}" rx="${radius}" ry="${radius}" fill="#fff"/>
     </svg>`,
  )
}

const encode = { compressionLevel: 9, effort: 10, palette: true, quality: 92 }

async function feathered(size) {
  const art = await sharp(master).resize(size, size, { kernel: 'lanczos3' }).png().toBuffer()
  return sharp(art)
    .composite([{ input: featherMask(size), blend: 'dest-in' }])
    .png(encode)
    .toBuffer()
}

async function plated(size, { scale = 0.94, radius = 0 } = {}) {
  const artSize = Math.round(size * scale)
  const art = await feathered(artSize)
  const composed = await sharp({
    create: { width: size, height: size, channels: 4, background: { ...plate, alpha: 1 } },
  })
    .composite([{ input: art, gravity: 'center' }])
    .png()
    .toBuffer()

  if (!radius) return sharp(composed).png(encode).toBuffer()
  return sharp(composed)
    .composite([{ input: roundedMask(size, radius), blend: 'dest-in' }])
    .png(encode)
    .toBuffer()
}

function buildIco(images) {
  const header = Buffer.alloc(6)
  header.writeUInt16LE(0, 0)
  header.writeUInt16LE(1, 2)
  header.writeUInt16LE(images.length, 4)

  let offset = 6 + images.length * 16
  const entries = []
  for (const { size, data } of images) {
    const entry = Buffer.alloc(16)
    entry.writeUInt8(size >= 256 ? 0 : size, 0)
    entry.writeUInt8(size >= 256 ? 0 : size, 1)
    entry.writeUInt16LE(1, 4)
    entry.writeUInt16LE(32, 6)
    entry.writeUInt32LE(data.length, 8)
    entry.writeUInt32LE(offset, 12)
    entries.push(entry)
    offset += data.length
  }

  return Buffer.concat([header, ...entries, ...images.map((image) => image.data)])
}

await mkdir(brandDir, { recursive: true })

const written = []
async function emit(file, data) {
  const target = join(file.startsWith('favicon') ? publicDir : brandDir, file)
  await writeFile(target, data)
  written.push(`${file} — ${(data.length / 1024).toFixed(1)} kB`)
}

await emit('logo-mark-512.png', await feathered(512))
await emit('logo-tile-64.png', await plated(64, { radius: 14 }))
await emit('logo-tile-128.png', await plated(128, { radius: 28 }))
await emit('icon-16.png', await plated(16, { radius: 3 }))
await emit('icon-32.png', await plated(32, { radius: 6 }))
await emit('icon-48.png', await plated(48, { radius: 9 }))
await emit('apple-touch-icon.png', await plated(180, { scale: 0.82 }))
await emit('pwa-192.png', await plated(192, { radius: 42 }))
await emit('pwa-512.png', await plated(512, { radius: 112 }))
await emit('pwa-maskable-512.png', await plated(512, { scale: 0.6 }))

await emit(
  'favicon.ico',
  buildIco([
    { size: 16, data: await plated(16, { radius: 3 }) },
    { size: 32, data: await plated(32, { radius: 6 }) },
    { size: 48, data: await plated(48, { radius: 9 }) },
  ]),
)

console.log(written.join('\n'))
