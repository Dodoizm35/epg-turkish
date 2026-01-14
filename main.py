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

# Constants
EMPTY_EPG_DATA = {"channels": [], "programmes": []}


def xml_time(dt: datetime, tz: str) -> str:
    """Format datetime for XMLTV with timezone"""
    if not isinstance(dt, datetime):
        raise ValueError(f"Expected datetime object, got {type(dt)}")
    if not tz:
        raise ValueError("Timezone cannot be empty")
    return dt.strftime("%Y%m%d%H%M%S") + f" {tz}"


def escape_xml(text: str) -> str:
    """Escape special characters for XML"""
    if not text:
        return ""
    return escape(text)


def generate_xml(channels: List[Dict], programmes: List[Dict], channel_aliases: Dict[str, List[str]]) -> str:
    """Generate XMLTV format XML with multiple channel IDs for compatibility"""
    if not isinstance(channels, list):
        raise ValueError(f"channels must be a list, got {type(channels)}")
    if not isinstance(programmes, list):
        raise ValueError(f"programmes must be a list, got {type(programmes)}")
    if not isinstance(channel_aliases, dict):
        raise ValueError(f"channel_aliases must be a dict, got {type(channel_aliases)}")
    
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<!DOCTYPE tv SYSTEM "xmltv.dtd">',
        '<tv generator-info-name="Turkey EPG" generator-info-url="https://github.com/dogukandogan/epg">',
    ]

    # Channel definitions - create entry for each alias
    for ch in channels:
        if not isinstance(ch, dict):
            logger.warning(f"Skipping invalid channel entry: {ch}")
            continue
        
        primary_id = ch.get("id")
        ch_name = ch.get("name", "")
        
        if not primary_id:
            logger.warning(f"Skipping channel with missing id: {ch}")
            continue
        
        ch_name = escape_xml(ch_name)
        logo = ch.get("logo", "")

        # Get all aliases for this channel
        all_ids = channel_aliases.get(primary_id, [primary_id])

        for ch_id in all_ids:
            if not ch_id:
                continue
            line = f'  <channel id="{escape_xml(ch_id)}">'
            line += f'<display-name>{ch_name}</display-name>'
            if logo:
                line += f'<icon src="{escape_xml(logo)}" />'
            line += '</channel>'
            lines.append(line)

    # Programme entries - create entry for each alias
    for prog in programmes:
        if not isinstance(prog, dict):
            logger.warning(f"Skipping invalid programme entry: {prog}")
            continue
        
        primary_id = prog.get("channel")
        if not primary_id:
            logger.warning(f"Skipping programme with missing channel: {prog}")
            continue
        
        tz = prog.get("tz", config.TZ_UTC)
        start_dt = prog.get("start")
        stop_dt = prog.get("stop")
        title = prog.get("title", "")
        
        if not start_dt or not stop_dt:
            logger.warning(f"Skipping programme with missing times: {prog}")
            continue
        
        if not title:
            logger.debug(f"Programme with empty title on channel {primary_id}")
            title = "Unknown"
        
        try:
            start = xml_time(start_dt, tz)
            stop = xml_time(stop_dt, tz)
        except (ValueError, AttributeError) as e:
            logger.warning(f"Skipping programme with invalid datetime: {e}")
            continue
        
        title = escape_xml(title)

        # Get all aliases for this channel
        all_ids = channel_aliases.get(primary_id, [primary_id])

        for ch_id in all_ids:
            if not ch_id:
                continue
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
        if not isinstance(source, dict):
            logger.warning(f"Skipping invalid source: {type(source)}")
            continue
        
        for ch in source.get("channels", []):
            if not isinstance(ch, dict):
                logger.warning(f"Skipping invalid channel: {ch}")
                continue
            
            ch_id = ch.get("id")
            if not ch_id:
                logger.warning(f"Skipping channel with missing id: {ch}")
                continue
            
            if ch_id not in all_channels:
                all_channels[ch_id] = ch

        programmes = source.get("programmes", [])
        if isinstance(programmes, list):
            all_programmes.extend(programmes)
        else:
            logger.warning(f"Invalid programmes list in source: {type(programmes)}")

    # Sort programmes by start time
    try:
        all_programmes.sort(key=lambda x: (x.get("channel", ""), x.get("start", datetime.min)))
    except (TypeError, AttributeError) as e:
        logger.warning(f"Error sorting programmes: {e}")

    return {
        "channels": list(all_channels.values()),
        "programmes": all_programmes,
    }


def main():
    """Main entry point"""
    try:
        logger.info("Starting EPG generation...")

        # Fetch from all sources
        logger.info("Fetching D-Smart EPG...")
        try:
            dsmart_data = dsmart.fetch_all()
        except Exception as e:
            logger.error(f"Failed to fetch D-Smart data: {e}", exc_info=True)
            dsmart_data = EMPTY_EPG_DATA

        logger.info("Fetching beIN Sports EPG...")
        try:
            beinsports_data = beinsports.fetch_all()
        except Exception as e:
            logger.error(f"Failed to fetch beIN Sports data: {e}", exc_info=True)
            beinsports_data = EMPTY_EPG_DATA

        # Merge all sources
        merged = merge_data(dsmart_data, beinsports_data)

        logger.info(f"Total: {len(merged['channels'])} channels, {len(merged['programmes'])} programmes")

        if len(merged['channels']) == 0:
            logger.warning("No channels found! Generated EPG will be empty.")

        # Generate channel aliases for universal IPTV compatibility
        logger.info("Generating channel aliases for IPTV compatibility...")
        channel_aliases = {}
        total_aliases = 0
        for ch in merged["channels"]:
            try:
                aliases = generate_channel_ids(ch.get("name", ""), ch.get("id", ""))
                ch_id = ch.get("id")
                if ch_id:
                    channel_aliases[ch_id] = aliases
                    total_aliases += len(aliases)
            except Exception as e:
                logger.error(f"Error generating aliases for channel {ch}: {e}")

        logger.info(f"Generated {total_aliases} channel aliases for {len(merged['channels'])} channels")

        # Generate XML
        try:
            xml_content = generate_xml(merged["channels"], merged["programmes"], channel_aliases)
        except Exception as e:
            logger.error(f"Failed to generate XML: {e}", exc_info=True)
            return 1

        # Ensure output directory exists
        os.makedirs(config.OUTPUT_DIR, exist_ok=True)

        # Write output
        try:
            with open(config.OUTPUT_FILE, "w", encoding="utf-8") as f:
                f.write(xml_content)
            logger.info(f"EPG written to {config.OUTPUT_FILE}")
        except IOError as e:
            logger.error(f"Failed to write output file: {e}", exc_info=True)
            return 1

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
    
    except Exception as e:
        logger.error(f"Unexpected error in main: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
