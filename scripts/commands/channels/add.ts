import { program } from 'commander'
import { Storage } from '@freearhey/storage-js'

program
    .requiredOption('--site <site>', 'Site domain (e.g. tvplus.com.tr)')
    .requiredOption('--siteId <siteId>', 'Source-specific channel id/slug used by the site')
    .requiredOption('--name <name>', 'Channel display name')
    .requiredOption('--lang <lang>', 'Language code (ISO 639-1, e.g. tr, en)')
    .option('--xmltvId <xmltvId>', 'Optional xmltv_id (e.g. BBCOne.uk@East). Empty is allowed.')
    .option('--logo <logo>', 'Optional logo URL')
    .option('--lcn <lcn>', 'Optional LCN')
    .option('--file <file>', 'Target *.channels.xml file (optional)')
    .parse(process.argv)

interface Options {
    site: string
    siteId: string
    name: string
    lang: string
    xmltvId?: string
    logo?: string
    lcn?: string
    file?: string
}

const options = program.opts<Options>()

function escapeXmlText(value: string): string {
    return String(value)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
}

function escapeXmlAttr(value: string): string {
    // Attribute value is delimited by double quotes in this repo.
    return escapeXmlText(value)
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&apos;')
}

function escapeRegExp(value: string): string {
    return value.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
}

async function resolveTargetFile(storage: Storage): Promise<string> {
    if (options.file) return options.file

    const preferred = `sites/${options.site}/${options.site}.channels.xml`
    if (await storage.exists(preferred)) return preferred

    const candidates = await storage.list(`sites/${options.site}/*.channels.xml`)
    if (candidates.length === 1) return candidates[0]

    if (candidates.length === 0) {
        throw new Error(`No *.channels.xml files found for site "${options.site}"`)
    }

    throw new Error(
        `Multiple *.channels.xml files found for site "${options.site}". ` +
        `Pass --file to select one. Candidates: ${candidates.join(', ')}`
    )
}

async function main() {
    const storage = new Storage()

    const targetFile = await resolveTargetFile(storage)
    const xml = await storage.load(targetFile)

    // Use the file's existing line endings.
    const eol = xml.includes('\r\n') ? '\r\n' : '\n'

    // Make the selected file discoverable by GitHub Actions steps.
    console.log(`TARGET_FILE=${targetFile}`)

    const siteIdRe = new RegExp(`site_id="${escapeRegExp(options.siteId)}"`)
    if (siteIdRe.test(xml)) {
        console.log(`No-op: channel with site_id="${options.siteId}" already exists in ${targetFile}`)
        return
    }

    const attrs: string[] = [
        `site="${escapeXmlAttr(options.site)}"`,
        `site_id="${escapeXmlAttr(options.siteId)}"`,
        `lang="${escapeXmlAttr(options.lang)}"`,
        `xmltv_id="${escapeXmlAttr(options.xmltvId || '')}"`
    ]

    if (options.logo) attrs.push(`logo="${escapeXmlAttr(options.logo)}"`)
    if (options.lcn) attrs.push(`lcn="${escapeXmlAttr(options.lcn)}"`)

    const line = `  <channel ${attrs.join(' ')}>${escapeXmlText(options.name)}</channel>`

    const closingIndex = xml.lastIndexOf('</channels>')
    if (closingIndex === -1) {
        throw new Error(`Invalid XML: missing </channels> in ${targetFile}`)
    }

    let before = xml.slice(0, closingIndex)
    const after = xml.slice(closingIndex)

    if (!before.endsWith('\n') && !before.endsWith('\r\n')) {
        before += eol
    }

    // Insert right before the closing tag to minimize diffs.
    const nextXml = before + line + eol + after

    await storage.save(targetFile, nextXml)

    console.log(`Added channel: site=${options.site}, site_id=${options.siteId}, name=${options.name}`)
}

main()
