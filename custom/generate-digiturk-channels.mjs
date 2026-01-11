import fs from 'node:fs'
import path from 'node:path'

const repoRoot = path.resolve(path.dirname(new URL(import.meta.url).pathname), '..')

const inputPaths = [
  path.join(repoRoot, 'sites', 'digiturk.com.tr', 'digiturk.com.tr.channels.xml'),
  path.join(repoRoot, 'sites', 'tvplus.com.tr', 'tvplus.com.tr.channels.xml')
]
const outputPath = path.join(repoRoot, 'custom', 'tr.channels.xml')

/** @type {{site: string, site_id: string, lang?: string, xmltv_id: string, name: string}[]} */
const channels = []
const seenXmltvIds = new Set()

for (const inputPath of inputPaths) {
  if (!fs.existsSync(inputPath)) continue

  const xml = fs.readFileSync(inputPath, 'utf8')
  const isDigiturk = inputPath.includes('digiturk.com.tr')

  // Very small, purpose-built parser for our simple channels XML format.
  // Extract <channel ...>NAME</channel>
  const re = /<channel\s+([^>]+)>([\s\S]*?)<\/channel>/g

  for (const match of xml.matchAll(re)) {
    const attrsRaw = match[1]
    const nameRaw = match[2]

    const getAttr = (key) => {
      const m = attrsRaw.match(new RegExp(`${key}="([^"]*)"`))
      return m ? m[1] : ''
    }

    const site = getAttr('site')
    const site_id = getAttr('site_id')
    const lang = getAttr('lang') || ''
    const xmltv_id_in = getAttr('xmltv_id')

    if (!site || !site_id) continue

    const xmltv_id = xmltv_id_in && xmltv_id_in.trim() ? xmltv_id_in.trim() : `${site.replace(/\./g, '_')}_${site_id}`
    const name = nameRaw.replace(/\s+/g, ' ').trim()

    // Eğer xmltv_id daha önce (Digiturk tarafından) eklendiyse, TV+'tan geleni atla
    if (seenXmltvIds.has(xmltv_id)) continue

    channels.push({ site, site_id, lang: lang || undefined, xmltv_id, name })
    seenXmltvIds.add(xmltv_id)
  }
}

channels.sort((a, b) => {
  // Keep stable order: by (name, site_id)
  const na = a.name.toLocaleLowerCase('tr')
  const nb = b.name.toLocaleLowerCase('tr')
  if (na < nb) return -1
  if (na > nb) return 1
  return a.site_id.localeCompare(b.site_id)
})

const outLines = []
outLines.push('<?xml version="1.0" encoding="UTF-8"?>')
outLines.push('<channels>')
outLines.push('  <!-- Auto-generated from multiple sources (Digiturk & TV+) -->')
outLines.push('  <!-- NOTE: display-name is prefixed with "TR: " to match playlist naming style. -->')
outLines.push('')

for (const ch of channels) {
  const langAttr = ch.lang ? ` lang="${ch.lang}"` : ''
  // Escape XML special chars in display name
  const displayName = `TR: ${ch.name}`
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')

  outLines.push(
    `  <channel site="${ch.site}" site_id="${ch.site_id}"${langAttr} xmltv_id="${ch.xmltv_id}">${displayName}</channel>`
  )
}

outLines.push('</channels>')
outLines.push('')

fs.mkdirSync(path.dirname(outputPath), { recursive: true })
fs.writeFileSync(outputPath, outLines.join('\n'), 'utf8')

console.log(`[ok] wrote ${outputPath} (${channels.length} channels)`)
