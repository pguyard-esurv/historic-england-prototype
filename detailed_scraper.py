#!/usr/bin/env python3
"""
Detailed Scraper for Historic England Building Pages
Scrapes detailed information including architectural descriptions from all tabs
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

def get_random_building() -> Optional[Dict[str, Any]]:
    """Get a random building from the API"""
    print(f"🎲 Getting random building from API...")
    
    try:
        layer_url = f"{NHLE_BASE_URL}/0/query"
        params = {
            'where': '1=1',
            'outFields': 'Name,Grade,ListEntry,ListDate,hyperlink,NGR,Easting,Northing',
            'returnGeometry': 'false',
            'f': 'json',
            'resultRecordCount': 5
        }
        
        response = requests.get(layer_url, params=params)
        response.raise_for_status()
        data = response.json()
        
        if 'features' in data and data['features']:
            selected = random.choice(data['features'])
            attrs = selected.get('attributes', {})
            
            building = {
                'name': attrs.get('Name', 'Unnamed'),
                'grade': attrs.get('Grade', 'N/A'),
                'list_entry': attrs.get('ListEntry', 'N/A'),
                'list_date': attrs.get('ListDate', 'N/A'),
                'hyperlink': attrs.get('hyperlink', ''),
                'ngr': attrs.get('NGR', 'N/A'),
                'easting': attrs.get('Easting', 'N/A'),
                'northing': attrs.get('Northing', 'N/A')
            }
            
            print(f"✅ Selected: {building['name']}")
            return building
        else:
            print("❌ No buildings found")
            return None
            
    except Exception as e:
        print(f"❌ Error getting building: {e}")
        return None

def scrape_building_details(url: str) -> Optional[Dict[str, Any]]:
    """Scrape detailed building information from all tabs"""
    print(f"  🔍 Scraping detailed content from: {url}")
    
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
                print(f"    🍪 Handling cookie consent...")
                cookie_buttons[0].click()
                time.sleep(2)
        except:
            pass
        
        # Wait for page to load
        try:
            wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        except:
            pass
        
        time.sleep(3)
        
        # Collect content from all tabs
        all_content = {
            'overview': {},
            'official_list_entry': {},
            'comments_photos': {},
            'tabs_found': [],
            'tabs_clicked': []
        }
        
        # First, get the initial content (Overview tab)
        print(f"    📋 Getting initial content (Overview tab)...")
        initial_html = driver.page_source
        initial_soup = BeautifulSoup(initial_html, 'html.parser')
        all_content['overview'] = extract_tab_content(initial_soup, 'Overview')
        
        # Look for specific tab buttons
        print(f"    🔍 Looking for tabs...")
        
        tab_texts = ['Overview', 'Official List Entry', 'Comments', 'Photos']
        found_tabs = []
        
        for text in tab_texts:
            try:
                xpath_patterns = [
                    f"//button[contains(text(), '{text}')]",
                    f"//div[contains(text(), '{text}')]",
                    f"//a[contains(text(), '{text}')]",
                    f"//span[contains(text(), '{text}')]",
                    f"//*[contains(text(), '{text}')]"
                ]
                
                for xpath in xpath_patterns:
                    elements = driver.find_elements(By.XPATH, xpath)
                    for elem in elements:
                        if elem.is_displayed() and elem.is_enabled():
                            found_tabs.append({
                                'element': elem,
                                'text': text,
                                'tag': elem.tag_name
                            })
                            break
                    if found_tabs and any(tab['text'] == text for tab in found_tabs):
                        break
            except:
                continue
        
        print(f"    📋 Found {len(found_tabs)} tab elements:")
        for i, tab in enumerate(found_tabs, 1):
            print(f"      {i}. '{tab['text']}' ({tab['tag']})")
        
        all_content['tabs_found'] = [tab['text'] for tab in found_tabs]
        
        # Click on each tab and collect content
        for tab in found_tabs:
            try:
                print(f"    🔄 Clicking tab: '{tab['text']}'")
                
                driver.execute_script("arguments[0].scrollIntoView(true);", tab['element'])
                time.sleep(1)
                
                try:
                    tab['element'].click()
                except:
                    driver.execute_script("arguments[0].click();", tab['element'])
                
                time.sleep(3)
                
                html = driver.page_source
                soup = BeautifulSoup(html, 'html.parser')
                
                tab_content = extract_tab_content(soup, tab['text'])
                all_content['tabs_clicked'].append(tab['text'])
                
                # Store content by tab type
                if 'overview' in tab['text'].lower():
                    all_content['overview'] = tab_content
                elif 'official' in tab['text'].lower() or 'list entry' in tab['text'].lower():
                    all_content['official_list_entry'] = tab_content
                elif 'comment' in tab['text'].lower() or 'photo' in tab['text'].lower():
                    all_content['comments_photos'] = tab_content
                
                print(f"      ✅ Extracted content from '{tab['text']}'")
                
            except Exception as e:
                print(f"      ❌ Error clicking tab '{tab['text']}': {e}")
                continue
        
        # Get final page state
        final_html = driver.page_source
        driver.quit()
        
        print(f"    ✅ Tab navigation complete!")
        return {
            'url': url,
            'scraped_at': datetime.now().isoformat(),
            'tabs_processed': len(all_content['tabs_clicked']),
            'final_html': final_html,
            'tab_content': all_content
        }
        
    except Exception as e:
        print(f"    ❌ Scraping error: {e}")
        return None

def extract_tab_content(soup: BeautifulSoup, tab_name: str) -> Dict[str, Any]:
    """Extract content from a specific tab"""
    content = {
        'tab_name': tab_name,
        'headings': [],
        'paragraphs': [],
        'images': [],
        'links': [],
        'text_content': '',
        'specific_data': {}
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
    
    # Get main text content
    main_content = soup.find('main') or soup.find('body')
    if main_content:
        content['text_content'] = main_content.get_text().strip()
    
    # Extract specific data for official list entry
    if 'official' in tab_name.lower() or 'list entry' in tab_name.lower():
        content['specific_data'] = extract_building_specific_data(soup)
    
    return content

def extract_building_specific_data(soup: BeautifulSoup) -> Dict[str, Any]:
    """Extract specific building data from the official list entry tab"""
    data = {
        'grade': '',
        'list_entry': '',
        'list_date': '',
        'description': '',
        'history': '',
        'architectural_details': '',
        'reasons_for_listing': '',
        'location': '',
        'coordinates': '',
        'address': ''
    }
    
    # Look for grade
    grade_patterns = [
        r'Grade\s+([I2*]+)',
        r'Grade\s*:\s*([I2*]+)',
        r'([I2*]+)\s*Grade'
    ]
    
    for pattern in grade_patterns:
        grade_match = soup.find(string=re.compile(pattern, re.I))
        if grade_match:
            match = re.search(pattern, grade_match, re.I)
            if match:
                data['grade'] = match.group(1)
                break
    
    # Look for list entry
    entry_patterns = [
        r'List Entry\s*[:\s]*(\d+)',
        r'Entry\s*[:\s]*(\d+)',
        r'(\d{6,})'
    ]
    
    for pattern in entry_patterns:
        entry_match = soup.find(string=re.compile(pattern, re.I))
        if entry_match:
            match = re.search(pattern, entry_match, re.I)
            if match:
                data['list_entry'] = match.group(1)
                break
    
    # Look for coordinates
    coord_patterns = [
        r'National Grid Reference[:\s]*([A-Z]{2}\s?\d{4,6}\s?\d{4,6})',
        r'NGR[:\s]*([A-Z]{2}\s?\d{4,6}\s?\d{4,6})',
        r'Grid Reference[:\s]*([A-Z]{2}\s?\d{4,6}\s?\d{4,6})'
    ]
    
    for pattern in coord_patterns:
        coord_match = soup.find(string=re.compile(pattern, re.I))
        if coord_match:
            match = re.search(pattern, coord_match, re.I)
            if match:
                data['coordinates'] = match.group(1)
                break
    
    # Look for architectural description in paragraphs
    architectural_keywords = [
        'semi-detached', 'cottages', 'coursed rubble', 'stone', 'tiled',
        'brick stacks', 'mullioned', 'casements', 'chamfered', 'beams',
        'planked doors', 'recessed', 'diagonally-set', 'axial position'
    ]
    
    for para in soup.find_all('p'):
        text = para.get_text().strip()
        if len(text) > 100:
            keyword_count = sum(1 for keyword in architectural_keywords if keyword.lower() in text.lower())
            if keyword_count >= 3:
                data['architectural_details'] = text
                break
    
    return data

def main():
    """Main function"""
    print("🏛️  Detailed Historic England Building Scraper")
    print("=" * 60)
    
    # Get a random building
    building = get_random_building()
    
    if not building:
        print("❌ No building to scrape")
        return
    
    print(f"\n🏛️  Building: {building['name']}")
    print(f"   Grade: {building['grade']}, Entry: {building['list_entry']}")
    print(f"   URL: {building['hyperlink']}")
    
    # Scrape detailed content
    result = scrape_building_details(building['hyperlink'])
    
    if result:
        print(f"\n✅ SUCCESS! Detailed scraping completed")
        print(f"   Tabs found: {len(result['tab_content']['tabs_found'])}")
        print(f"   Tabs clicked: {len(result['tab_content']['tabs_clicked'])}")
        print(f"   Tabs processed: {result['tabs_processed']}")
        
        # Save results
        with open('detailed_scraping_results.json', 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        print(f"\n📁 Results saved to detailed_scraping_results.json")
        
        # Show what we found
        for tab_name, tab_data in result['tab_content'].items():
            if isinstance(tab_data, dict) and 'tab_name' in tab_data:
                print(f"\n📋 Tab: {tab_data['tab_name']}")
                print(f"   Headings: {len(tab_data['headings'])}")
                print(f"   Paragraphs: {len(tab_data['paragraphs'])}")
                print(f"   Images: {len(tab_data['images'])}")
                print(f"   Links: {len(tab_data['links'])}")
                
                if tab_data['specific_data']:
                    print(f"   Specific data: {list(tab_data['specific_data'].keys())}")
                    if tab_data['specific_data'].get('architectural_details'):
                        print(f"   Architectural details: {tab_data['specific_data']['architectural_details'][:200]}...")
        
    else:
        print(f"\n❌ Failed to scrape detailed content")

if __name__ == "__main__":
    main()
