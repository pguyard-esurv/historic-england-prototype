#!/usr/bin/env python3
"""
Batch comparison of multiple random listings with UPRN detection
"""

import json
import random
import re
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

import requests
from bs4 import BeautifulSoup

# NHLE API endpoint
NHLE_BASE_URL = "https://services-eu1.arcgis.com/ZOdPfBS3aqqDYPUQ/arcgis/rest/services/National_Heritage_List_for_England_NHLE_v02_VIEW/FeatureServer"

def get_multiple_buildings(count: int = 20) -> List[Dict[str, Any]]:
    """Get multiple random buildings from the API"""
    print(f"🎲 Getting {count} random buildings from API...")
    
    try:
        layer_url = f"{NHLE_BASE_URL}/0/query"
        params = {
            'where': '1=1',
            'outFields': 'Name,Grade,ListEntry,ListDate,hyperlink,NGR,Easting,Northing,AmendDate,CaptureScale',
            'returnGeometry': 'false',
            'f': 'json',
            'resultRecordCount': count * 2  # Get more to ensure we have enough variety
        }
        
        response = requests.get(layer_url, params=params)
        response.raise_for_status()
        data = response.json()
        
        if 'features' in data and data['features']:
            # Randomly select the requested number
            selected = random.sample(data['features'], min(count, len(data['features'])))
            
            buildings = []
            for feature in selected:
                attrs = feature.get('attributes', {})
                building = {
                    'name': attrs.get('Name', 'Unnamed'),
                    'grade': attrs.get('Grade', 'N/A'),
                    'list_entry': attrs.get('ListEntry', 'N/A'),
                    'list_date': attrs.get('ListDate', 'N/A'),
                    'amend_date': attrs.get('AmendDate', 'N/A'),
                    'capture_scale': attrs.get('CaptureScale', 'N/A'),
                    'hyperlink': attrs.get('hyperlink', ''),
                    'ngr': attrs.get('NGR', 'N/A'),
                    'easting': attrs.get('Easting', 'N/A'),
                    'northing': attrs.get('Northing', 'N/A')
                }
                buildings.append(building)
            
            print(f"✅ Selected {len(buildings)} buildings")
            return buildings
        else:
            print("❌ No buildings found")
            return []
            
    except Exception as e:
        print(f"❌ Error getting buildings: {e}")
        return []

def scrape_building_for_uprn(url: str, building_name: str) -> tuple[Optional[Dict[str, Any]], Dict[str, Any]]:
    """Scrape building details and look for UPRN"""
    print(f"  🔍 Scraping: {building_name}")
    
    timing = {
        'start_time': time.time(),
        'end_time': 0,
        'duration': 0
    }
    
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support import expected_conditions as EC
        from selenium.webdriver.support.ui import WebDriverWait

        # Set up Chrome options
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        driver = webdriver.Chrome(options=options)
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        driver.get(url)
        wait = WebDriverWait(driver, 15)
        
        # Handle cookie consent
        try:
            cookie_buttons = driver.find_elements(By.XPATH, "//button[contains(text(), 'Accept') or contains(text(), 'Accept All')]")
            if cookie_buttons:
                cookie_buttons[0].click()
                time.sleep(1)
        except:
            pass
        
        # Wait for page to load
        try:
            wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        except:
            pass
        
        time.sleep(2)
        
        # Get page content
        html = driver.page_source
        soup = BeautifulSoup(html, 'html.parser')
        
        # Look for UPRN patterns
        uprn_patterns = [
            r'UPRN[:\s]*(\d{12})',  # UPRN: 123456789012
            r'Unique Property Reference Number[:\s]*(\d{12})',
            r'Property Reference[:\s]*(\d{12})',
            r'(\d{12})',  # Any 12-digit number
            r'UPRN[:\s]*(\d+)',  # UPRN with any number of digits
        ]
        
        uprn_found = []
        page_text = soup.get_text()
        
        for pattern in uprn_patterns:
            matches = re.findall(pattern, page_text, re.IGNORECASE)
            for match in matches:
                if len(match) >= 8:  # UPRN should be at least 8 digits
                    uprn_found.append(match)
        
        # Also look in specific elements
        uprn_elements = soup.find_all(string=re.compile(r'UPRN|Unique Property Reference', re.I))
        for element in uprn_elements:
            parent = element.parent
            if parent:
                parent_text = parent.get_text()
                for pattern in uprn_patterns:
                    matches = re.findall(pattern, parent_text, re.IGNORECASE)
                    for match in matches:
                        if len(match) >= 8:
                            uprn_found.append(match)
        
        # Remove duplicates and sort
        uprn_found = list(set(uprn_found))
        uprn_found.sort()
        
        # Extract other useful data
        content = {
            'url': url,
            'building_name': building_name,
            'scraped_at': datetime.now().isoformat(),
            'uprn_found': uprn_found,
            'uprn_count': len(uprn_found),
            'page_text_length': len(page_text),
            'headings': [],
            'paragraphs': [],
            'links': [],
            'images': []
        }
        
        # Extract headings
        headings = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
        for heading in headings:
            text = heading.get_text().strip()
            if text and 'cookie' not in text.lower():
                content['headings'].append({
                    'level': heading.name,
                    'text': text
                })
        
        # Extract paragraphs
        paragraphs = soup.find_all('p')
        for p in paragraphs:
            text = p.get_text().strip()
            if text and len(text) > 20 and 'cookie' not in text.lower():
                content['paragraphs'].append({
                    'text': text,
                    'length': len(text)
                })
        
        # Extract links
        links = soup.find_all('a', href=True)
        for link in links:
            href = link.get('href', '')
            text = link.get_text().strip()
            if href and text:
                if href.startswith('/'):
                    href = 'https://historicengland.org.uk' + href
                content['links'].append({
                    'href': href,
                    'text': text
                })
        
        # Extract images
        images = soup.find_all('img')
        for img in images:
            src = img.get('src', '')
            alt = img.get('alt', '')
            if src:
                if src.startswith('/'):
                    src = 'https://historicengland.org.uk' + src
                content['images'].append({
                    'src': src,
                    'alt': alt
                })
        
        driver.quit()
        
        timing['end_time'] = time.time()
        timing['duration'] = timing['end_time'] - timing['start_time']
        
        print(f"    ✅ Scraped in {timing['duration']:.2f}s - UPRN found: {len(uprn_found)}")
        if uprn_found:
            print(f"    🎯 UPRNs: {uprn_found}")
        
        return content, timing
        
    except Exception as e:
        timing['end_time'] = time.time()
        timing['duration'] = timing['end_time'] - timing['start_time']
        print(f"    ❌ Scraping error: {e}")
        return None, timing

def analyze_batch_results(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze the batch scraping results"""
    print(f"\n📊 BATCH ANALYSIS")
    print("=" * 50)
    
    total_buildings = len(results)
    successful_scrapes = len([r for r in results if r['scraped_data'] is not None])
    total_uprn_found = sum(r['scraped_data']['uprn_count'] for r in results if r['scraped_data'])
    buildings_with_uprn = len([r for r in results if r['scraped_data'] and r['scraped_data']['uprn_count'] > 0])
    
    print(f"Total buildings processed: {total_buildings}")
    print(f"Successful scrapes: {successful_scrapes}")
    print(f"Buildings with UPRN: {buildings_with_uprn}")
    print(f"Total UPRNs found: {total_uprn_found}")
    print(f"Success rate: {(successful_scrapes/total_buildings)*100:.1f}%")
    print(f"UPRN discovery rate: {(buildings_with_uprn/successful_scrapes)*100:.1f}%" if successful_scrapes > 0 else "N/A")
    
    # Timing analysis
    timings = [r['scraping_timing']['duration'] for r in results if r['scraping_timing']]
    if timings:
        avg_time = sum(timings) / len(timings)
        min_time = min(timings)
        max_time = max(timings)
        print(f"\n⏱️  TIMING ANALYSIS:")
        print(f"Average scraping time: {avg_time:.2f}s")
        print(f"Fastest scrape: {min_time:.2f}s")
        print(f"Slowest scrape: {max_time:.2f}s")
    
    # UPRN analysis
    all_uprns = []
    for result in results:
        if result['scraped_data'] and result['scraped_data']['uprn_found']:
            all_uprns.extend(result['scraped_data']['uprn_found'])
    
    unique_uprns = list(set(all_uprns))
    print(f"\n🎯 UPRN ANALYSIS:")
    print(f"Total UPRNs found: {len(all_uprns)}")
    print(f"Unique UPRNs: {len(unique_uprns)}")
    if unique_uprns:
        print(f"Sample UPRNs: {unique_uprns[:5]}")
    
    # Content analysis
    total_headings = sum(len(r['scraped_data']['headings']) for r in results if r['scraped_data'])
    total_paragraphs = sum(len(r['scraped_data']['paragraphs']) for r in results if r['scraped_data'])
    total_images = sum(len(r['scraped_data']['images']) for r in results if r['scraped_data'])
    total_links = sum(len(r['scraped_data']['links']) for r in results if r['scraped_data'])
    
    print(f"\n📄 CONTENT ANALYSIS:")
    print(f"Total headings: {total_headings}")
    print(f"Total paragraphs: {total_paragraphs}")
    print(f"Total images: {total_images}")
    print(f"Total links: {total_links}")
    
    return {
        'summary': {
            'total_buildings': total_buildings,
            'successful_scrapes': successful_scrapes,
            'buildings_with_uprn': buildings_with_uprn,
            'total_uprn_found': total_uprn_found,
            'success_rate': (successful_scrapes/total_buildings)*100,
            'uprn_discovery_rate': (buildings_with_uprn/successful_scrapes)*100 if successful_scrapes > 0 else 0
        },
        'timing': {
            'average_time': sum(timings) / len(timings) if timings else 0,
            'min_time': min(timings) if timings else 0,
            'max_time': max(timings) if timings else 0
        },
        'uprn_data': {
            'total_found': len(all_uprns),
            'unique_count': len(unique_uprns),
            'all_uprns': all_uprns,
            'unique_uprns': unique_uprns
        },
        'content': {
            'total_headings': total_headings,
            'total_paragraphs': total_paragraphs,
            'total_images': total_images,
            'total_links': total_links
        }
    }

def main():
    """Main function"""
    print("🏛️  Batch Historic England Building Analysis")
    print("=" * 60)
    print("Looking for UPRN (Unique Property Reference Number) data...")
    
    # Get multiple buildings
    buildings = get_multiple_buildings(20)
    
    if not buildings:
        print("❌ No buildings to process")
        return
    
    print(f"\n📋 Processing {len(buildings)} buildings...")
    
    results = []
    start_time = time.time()
    
    for i, building in enumerate(buildings, 1):
        print(f"\n[{i}/{len(buildings)}] {building['name']}")
        print(f"   Grade: {building['grade']}, Entry: {building['list_entry']}")
        
        # Scrape for UPRN
        scraped_data, scraping_timing = scrape_building_for_uprn(
            building['hyperlink'], 
            building['name']
        )
        
        result = {
            'building': building,
            'scraped_data': scraped_data,
            'scraping_timing': scraping_timing,
            'processed_at': datetime.now().isoformat()
        }
        
        results.append(result)
        
        # Small delay to be respectful
        time.sleep(1)
    
    total_time = time.time() - start_time
    print(f"\n⏱️  Total processing time: {total_time:.2f}s")
    print(f"Average time per building: {total_time/len(buildings):.2f}s")
    
    # Analyze results
    analysis = analyze_batch_results(results)
    
    # Save results
    batch_results = {
        'metadata': {
            'total_buildings': len(buildings),
            'processing_date': datetime.now().isoformat(),
            'total_processing_time': total_time,
            'average_time_per_building': total_time/len(buildings)
        },
        'analysis': analysis,
        'detailed_results': results
    }
    
    with open('batch_comparison_results.json', 'w', encoding='utf-8') as f:
        json.dump(batch_results, f, indent=2, ensure_ascii=False)
    
    print(f"\n📁 Results saved to batch_comparison_results.json")
    
    # Show buildings with UPRN
    buildings_with_uprn = [r for r in results if r['scraped_data'] and r['scraped_data']['uprn_count'] > 0]
    if buildings_with_uprn:
        print(f"\n🎯 BUILDINGS WITH UPRN FOUND:")
        for result in buildings_with_uprn:
            building = result['building']
            scraped = result['scraped_data']
            print(f"  • {building['name']} (Entry: {building['list_entry']})")
            print(f"    UPRNs: {scraped['uprn_found']}")
    else:
        print(f"\n❌ No UPRNs found in any of the scraped buildings")

if __name__ == "__main__":
    main()
