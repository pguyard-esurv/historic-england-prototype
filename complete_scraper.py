#!/usr/bin/env python3
"""
Complete Historic England Scraper

Combines both:
1. NHLE API data (quick, structured data)
2. Web scraping of official list entry (detailed descriptions)

This gives you the most complete dataset possible.

Usage:
    python complete_scraper.py 1380908
"""

import asyncio
import json
import os
import re
import sys
import time
from datetime import datetime
from typing import Any, Dict, Optional

import requests

try:
    from playwright.async_api import async_playwright
except ImportError:
    print("❌ Install playwright: pip install playwright")
    print("   Then: playwright install chromium")
    sys.exit(1)


# NHLE API Configuration
NHLE_API_BASE = "https://services-eu1.arcgis.com/ZOdPfBS3aqqDYPUQ/arcgis/rest/services/National_Heritage_List_for_England_NHLE_v02_VIEW/FeatureServer/0/query"


def get_api_data(list_entry_number: str) -> tuple[Optional[Dict[str, Any]], float]:
    """
    Fetch data from the NHLE API.

    Returns tuple of (structured data, elapsed time in seconds)
    """
    print(f"🔍 Fetching API data for {list_entry_number}...")
    start_time = time.time()

    def convert_timestamp(timestamp_ms: Optional[int]) -> Optional[str]:
        """Convert Unix timestamp in milliseconds to readable date format (DD-MMM-YYYY)"""
        if timestamp_ms is None:
            return None
        try:
            dt = datetime.fromtimestamp(timestamp_ms / 1000)
            return dt.strftime('%d-%b-%Y')
        except:
            return None

    try:
        params = {
            'where': f"ListEntry = '{list_entry_number}'",
            'outFields': '*',
            'returnGeometry': 'true',
            'f': 'json'
        }

        response = requests.get(NHLE_API_BASE, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()

        if 'features' not in data or not data['features']:
            elapsed = time.time() - start_time
            print(f"   ⚠️  No API data found ({elapsed:.2f}s)")
            return None, elapsed

        feature = data['features'][0]
        attrs = feature.get('attributes', {})
        geometry = feature.get('geometry', {})

        api_data = {
            'name': attrs.get('Name'),
            'grade': attrs.get('Grade'),
            'list_entry': attrs.get('ListEntry'),
            'list_date': convert_timestamp(attrs.get('ListDate')),
            'amend_date': convert_timestamp(attrs.get('AmendDate')),
            'category': attrs.get('Category'),
            'location': {
                'ngr': attrs.get('NGR'),
                'easting': attrs.get('Easting'),
                'northing': attrs.get('Northing'),
                'capturescale': attrs.get('CaptureScale'),
                'longitude': geometry.get('x') if geometry else None,
                'latitude': geometry.get('y') if geometry else None
            },
            'hyperlink': attrs.get('hyperlink')
        }

        elapsed = time.time() - start_time
        print(f"   ✅ API: {api_data['name']} (Grade {api_data['grade']}) ({elapsed:.2f}s)")
        return api_data, elapsed

    except Exception as e:
        elapsed = time.time() - start_time
        print(f"   ❌ API error: {e} ({elapsed:.2f}s)")
        return None, elapsed


async def scrape_web_data(list_entry_number: str, headless: bool = True) -> tuple[Optional[Dict[str, Any]], float]:
    """
    Scrape detailed data from the official list entry web page.

    Returns tuple of (comprehensive description and detailed metadata, elapsed time in seconds)
    """
    print(f"📋 Scraping web page for {list_entry_number}...")
    start_time = time.time()

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=headless)
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        )
        page = await context.new_page()

        try:
            url = f"https://historicengland.org.uk/listing/the-list/list-entry/{list_entry_number}?section=official-list-entry"

            await page.goto(url, wait_until='domcontentloaded', timeout=30000)

            # Handle cookies
            await asyncio.sleep(2)
            try:
                cookie_btn = page.locator('button:has-text("Accept all")').first
                if await cookie_btn.is_visible(timeout=3000):
                    await cookie_btn.click()
                    await asyncio.sleep(2)
            except:
                pass

            await page.wait_for_selector('h1', timeout=10000)
            await asyncio.sleep(1)

            web_data = {}

            # Title
            title_elem = page.locator('h1').first
            if await title_elem.count() > 0:
                web_data['title'] = (await title_elem.text_content()).strip()

            # Address
            address_elem = page.locator('main p').first
            if await address_elem.count() > 0:
                addr_text = await address_elem.text_content()
                if addr_text and len(addr_text) < 200:
                    web_data['address'] = addr_text.strip()

            # Key info
            web_data['key_info'] = {}
            key_info_dl = page.locator('dl.key-info').first
            if await key_info_dl.count() > 0:
                dts = await key_info_dl.locator('dt').all_text_contents()
                dds = await key_info_dl.locator('dd').all_text_contents()
                for dt, dd in zip(dts, dds):
                    web_data['key_info'][dt.strip().rstrip(':')] = dd.strip()

            # Extract major amendment date from key_info
            major_amendment_date = web_data['key_info'].get('Date of most recent amendment')
            web_data['major_amendment_date'] = major_amendment_date if major_amendment_date else None

            # Location
            web_data['location'] = {}
            statutory_dt = page.locator('dt:has-text("Statutory Address")').first
            if await statutory_dt.count() > 0:
                dd = statutory_dt.locator('xpath=following-sibling::dd[1]')
                if await dd.count() > 0:
                    web_data['location']['statutory_address'] = (await dd.text_content()).strip()

            location_dl = page.locator('dl.nhle__location-info').first
            if await location_dl.count() > 0:
                dts = await location_dl.locator('dt').all_text_contents()
                dds = await location_dl.locator('dd').all_text_contents()
                for dt, dd in zip(dts, dds):
                    key = dt.strip().rstrip(':').lower().replace(' ', '_')
                    web_data['location'][key] = dd.strip()

            # Architectural description (THE MOST IMPORTANT PART!)
            details_heading = page.locator('h3:has-text("Details")').first
            if await details_heading.count() > 0:
                desc_p = details_heading.locator('xpath=following-sibling::p[1]')
                if await desc_p.count() > 0:
                    description_text = (await desc_p.text_content()).strip()
                    web_data['description'] = description_text

                    # Extract minor amendment date from description
                    # Pattern: "This list entry was subject to a Minor Amendment on [DATE]"
                    minor_amendment_match = re.search(
                        r'This list entry was subject to a Minor Amendment.*?on\s+(\d{1,2}[/-]\d{1,2}[/-]\d{4}|\d{1,2}\s+\w+\s+\d{4})',
                        description_text,
                        re.IGNORECASE
                    )
                    if minor_amendment_match:
                        web_data['minor_amendment_date'] = minor_amendment_match.group(1)
                    else:
                        web_data['minor_amendment_date'] = None

            # Legacy
            web_data['legacy'] = {}
            legacy_dl = page.locator('dl.nhle-legacy').first
            if await legacy_dl.count() > 0:
                dts = await legacy_dl.locator('dt').all_text_contents()
                dds = await legacy_dl.locator('dd').all_text_contents()
                for dt, dd in zip(dts, dds):
                    key = dt.strip().rstrip(':').lower().replace(' ', '_')
                    web_data['legacy'][key] = dd.strip()

            # Sources
            sources_heading = page.locator('h3:has-text("Sources")').first
            if await sources_heading.count() > 0:
                sources_p = sources_heading.locator('xpath=following-sibling::p[1]')
                if await sources_p.count() > 0:
                    web_data['sources'] = (await sources_p.text_content()).strip()

            # Legal
            legal_heading = page.locator('h3:has-text("Legal")').first
            if await legal_heading.count() > 0:
                legal_p = legal_heading.locator('xpath=following-sibling::p[1]')
                if await legal_p.count() > 0:
                    web_data['legal'] = (await legal_p.text_content()).strip()

            # Map PDF
            map_link = page.locator('a:has-text("Download a full scale map")').first
            if await map_link.count() > 0:
                web_data['map_pdf_url'] = await map_link.get_attribute('href')

            elapsed = time.time() - start_time
            print(f"   ✅ Web: {web_data.get('title', 'N/A')} ({elapsed:.2f}s)")
            return web_data, elapsed

        except Exception as e:
            elapsed = time.time() - start_time
            print(f"   ❌ Web scraping error: {e} ({elapsed:.2f}s)")
            return None, elapsed

        finally:
            await browser.close()


async def scrape_complete(list_entry_number: str, headless: bool = True) -> Dict[str, Any]:
    """
    Get complete data by combining API and web scraping.

    Args:
        list_entry_number: The NHLE list entry number
        headless: Run browser in headless mode

    Returns:
        Complete dataset with both API and scraped data
    """
    total_start = time.time()

    result = {
        'list_entry_number': list_entry_number,
        'scraped_at': datetime.now().isoformat(),
        'urls': {
            'official_list_entry': f'https://historicengland.org.uk/listing/the-list/list-entry/{list_entry_number}?section=official-list-entry',
            'comments_and_photos': f'https://historicengland.org.uk/listing/the-list/list-entry/{list_entry_number}?section=comments-and-photos'
        },
        'timing': {
            'api_seconds': 0,
            'web_scraping_seconds': 0,
            'total_seconds': 0
        },
        'api_data': None,
        'web_data': None,
        'success': False
    }

    # Get API data (fast)
    api_data, api_time = get_api_data(list_entry_number)
    result['timing']['api_seconds'] = round(api_time, 2)
    if api_data:
        result['api_data'] = api_data

    # Get web data (detailed)
    web_data, web_time = await scrape_web_data(list_entry_number, headless=headless)
    result['timing']['web_scraping_seconds'] = round(web_time, 2)
    if web_data:
        result['web_data'] = web_data

    # Calculate total time
    total_time = time.time() - total_start
    result['timing']['total_seconds'] = round(total_time, 2)

    # Mark as success if we got at least one source
    result['success'] = bool(api_data or web_data)

    return result


async def main():
    """Example usage"""
    print("🏛️  Complete Historic England Scraper")
    print("   (API + Web Scraping)\n")

    # Get list entry number from command line or use default
    list_entry_number = sys.argv[1] if len(sys.argv) > 1 else '1380908'

    # Scrape complete data
    result = await scrape_complete(list_entry_number, headless=True)

    # Create results directory if it doesn't exist
    os.makedirs('results', exist_ok=True)

    # Save to file in results folder
    output_file = f'results/complete_{list_entry_number}.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    # Print summary
    print(f"\n{'='*70}")
    print(f"📊 SUMMARY for {list_entry_number}")
    print(f"{'='*70}")

    if result['api_data']:
        api = result['api_data']
        print(f"\n✅ API DATA:")
        print(f"   Name: {api.get('name')}")
        print(f"   Grade: {api.get('grade')}")
        print(f"   Listed: {api.get('list_date')}")
        print(f"   Category: {api.get('category')}")
        print(f"   NGR: {api['location'].get('ngr')}")
        print(f"   Coordinates: {api['location'].get('latitude')}, {api['location'].get('longitude')}")

    if result['web_data']:
        web = result['web_data']
        print(f"\n✅ WEB DATA:")
        print(f"   Title: {web.get('title')}")
        print(f"   Address: {web.get('address')}")
        print(f"   Key Info: {len(web.get('key_info', {}))} fields")
        print(f"   Location: {len(web.get('location', {}))} fields")
        if web.get('description'):
            print(f"   Description: {len(web['description'])} characters")
        print(f"   Legacy ID: {web.get('legacy', {}).get('legacy_system_number')}")

    print(f"\n💾 Complete data saved to: {output_file}")

    if not result['success']:
        print(f"\n⚠️  Warning: No data retrieved")
        return 1

    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
