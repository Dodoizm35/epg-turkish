#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Turkey EPG Generator
Generates XMLTV format EPG for Turkish TV channels.

Sources:
- D-Smart: ~150 channels (general TV)
- beIN Sports: 5 channels (sports)
"""

import os
import sys
import logging
from datetime import datetime
from html import escape
from typing import Dict, Any, List

import config
from scrapers import dsmart, beinsports
from channel_mapping import generate_channel_ids

# Setup logging
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def xml_time(dt: datetime, tz: str) -> str:
    """Format datetime for XMLTV with timezone"""
    return dt.strftime("%Y%m%d%H%M%S") + f" {tz}"


def escape_xml(text: str) -> str:
    """Escape special characters for XML"""
    if not text:
        return ""
    return escape(text)


def generate_xml(channels: List[Dict], programmes: List[Dict], channel_aliases: Dict[str, List[str]]) -> str:
    """Generate XMLTV format XML with multiple channel IDs for compatibility"""
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<!DOCTYPE tv SYSTEM "xmltv.dtd">',
        '<tv generator-info-name="Turkey EPG" generator-info-url="https://github.com/dogukandogan/epg">',
    ]

    # Channel definitions - create entry for each alias
    for ch in channels:
        primary_id = ch["id"]
        ch_name = escape_xml(ch["name"])
        logo = ch.get("logo", "")

        # Get all aliases for this channel
        all_ids = channel_aliases.get(primary_id, [primary_id])

        for ch_id in all_ids:
            line = f'  <channel id="{escape_xml(ch_id)}">'
            line += f'<display-name>{ch_name}</display-name>'
            if logo:
                line += f'<icon src="{escape_xml(logo)}" />'
            line += '</channel>'
            lines.append(line)

    # Programme entries - create entry for each alias
    for prog in programmes:
        primary_id = prog["channel"]
        tz = prog.get("tz", config.TZ_UTC)
        start = xml_time(prog["start"], tz)
        stop = xml_time(prog["stop"], tz)
        title = escape_xml(prog["title"])

        # Get all aliases for this channel
        all_ids = channel_aliases.get(primary_id, [primary_id])

        for ch_id in all_ids:
            line = f'  <programme start="{start}" stop="{stop}" channel="{escape_xml(ch_id)}">'
            line += f'<title lang="tr">{title}</title>'

            if prog.get("desc"):
                line += f'<desc lang="tr">{escape_xml(prog["desc"])}</desc>'

            if prog.get("category"):
                line += f'<category lang="tr">{escape_xml(prog["category"])}</category>'

            line += '</programme>'
            lines.append(line)

    lines.append('</tv>')

    return '\n'.join(lines)


def merge_data(*sources: Dict[str, Any]) -> Dict[str, Any]:
    """Merge data from multiple sources"""
    all_channels = {}
    all_programmes = []

    for source in sources:
        for ch in source.get("channels", []):
            ch_id = ch["id"]
            if ch_id not in all_channels:
                all_channels[ch_id] = ch

        all_programmes.extend(source.get("programmes", []))

    # Sort programmes by start time
    all_programmes.sort(key=lambda x: (x["channel"], x["start"]))

    return {
        "channels": list(all_channels.values()),
        "programmes": all_programmes,
    }


def main():
    """Main entry point"""
    logger.info("Starting EPG generation...")

    # Fetch from all sources
    logger.info("Fetching D-Smart EPG...")
    dsmart_data = dsmart.fetch_all()

    logger.info("Fetching beIN Sports EPG...")
    beinsports_data = beinsports.fetch_all()

    # Merge all sources
    merged = merge_data(dsmart_data, beinsports_data)

    logger.info(f"Total: {len(merged['channels'])} channels, {len(merged['programmes'])} programmes")

    # Generate channel aliases for universal IPTV compatibility
    logger.info("Generating channel aliases for IPTV compatibility...")
    channel_aliases = {}
    total_aliases = 0
    for ch in merged["channels"]:
        aliases = generate_channel_ids(ch["name"], ch["id"])
        channel_aliases[ch["id"]] = aliases
        total_aliases += len(aliases)

    logger.info(f"Generated {total_aliases} channel aliases for {len(merged['channels'])} channels")

    # Generate XML
    xml_content = generate_xml(merged["channels"], merged["programmes"], channel_aliases)

    # Ensure output directory exists
    os.makedirs(config.OUTPUT_DIR, exist_ok=True)

    # Write output
    with open(config.OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(xml_content)

    logger.info(f"EPG written to {config.OUTPUT_FILE}")

    # Print summary
    print(f"\n{'='*50}")
    print(f"EPG Generation Complete!")
    print(f"{'='*50}")
    print(f"Channels: {len(merged['channels'])}")
    print(f"Channel IDs (with aliases): {total_aliases}")
    print(f"Programmes: {len(merged['programmes'])}")
    print(f"Output: {config.OUTPUT_FILE}")
    print(f"{'='*50}\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
