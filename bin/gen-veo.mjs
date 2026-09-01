#!/usr/bin/env node
// gen-veo.mjs --prompt "..." --out clip.mp4 [--ref img ...] [--dur 8] [--aspect 16:9]
// Standalone Veo 3.1 fast generation with ASSET reference images (identity lock).
// Uses amplify's @google/genai + GEMINI_API_KEY from ~/Code/amplify/.env.
// Cost: ~2.5c/second (veo-3.1-fast) => 8s ~= $0.20.
import fs from 'fs'
import path from 'path'
import os from 'os'

const AMPLIFY = path.join(os.homedir(), 'Code/amplify')
const { GoogleGenAI, VideoGenerationReferenceType } = await import(
  'file://' + path.join(AMPLIFY, 'node_modules/@google/genai/dist/node/index.mjs')
)
const env = fs.readFileSync(path.join(AMPLIFY, '.env'), 'utf8')
const apiKey = env.match(/^GEMINI_API_KEY=(.+)$/m)?.[1]?.trim()
if (!apiKey) { console.error('no GEMINI_API_KEY'); process.exit(1) }

const args = process.argv.slice(2)
const get = (f, d) => { const i = args.indexOf(f); return i >= 0 ? args[i + 1] : d }
const refs = []
for (let i = 0; i < args.length; i++) if (args[i] === '--ref') refs.push(args[i + 1])
const prompt = get('--prompt'); const out = get('--out', 'gen.mp4')
const dur = Number(get('--dur', '8')); const aspect = get('--aspect', '16:9')
if (!prompt) { console.error('need --prompt'); process.exit(1) }

const referenceImages = refs.map((p) => ({
  image: { imageBytes: fs.readFileSync(p).toString('base64'), mimeType: 'image/jpeg' },
  referenceType: VideoGenerationReferenceType.ASSET,
}))
console.log(`[gen-veo] ${refs.length} ref(s), ${dur}s ${aspect} (~$${(dur * 0.025).toFixed(2)})`)

const ai = new GoogleGenAI({ apiKey })
let op = await ai.models.generateVideos({
  model: 'veo-3.1-fast-generate-preview',
  prompt,
  config: { numberOfVideos: 1, durationSeconds: dur, aspectRatio: aspect,
    ...(referenceImages.length && { referenceImages }) },
})
console.log('[gen-veo] operation:', op.name)
const t0 = Date.now()
while (!op.done) {
  if (Date.now() - t0 > 600_000) { console.error('timeout'); process.exit(1) }
  await new Promise((r) => setTimeout(r, 10_000))
  op = await ai.operations.getVideosOperation({ operation: op })
  process.stdout.write('.')
}
console.log()
const vid = op.response?.generatedVideos?.[0]
if (!vid?.video) { console.error('no video:', JSON.stringify(op.response ?? op.error ?? {}).slice(0, 500)); process.exit(1) }
await ai.files.download({ file: vid.video, downloadPath: out })
console.log('[gen-veo] →', out)
