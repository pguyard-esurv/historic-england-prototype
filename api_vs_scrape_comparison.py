#!/usr/bin/env python3
"""
Compare API data vs Scraped data from Historic England pages
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

def get_building_from_api() -> Optional[Dict[str, Any]]:
    """Get a random building from the API"""
    print("🎲 Getting random building from API...")
    
    try:
        layer_url = f"{NHLE_BASE_URL}/0/query"
        params = {
            'where': '1=1',
            'outFields': 'Name,Grade,ListEntry,ListDate,hyperlink,NGR,Easting,Northing,AmendDate,CaptureScale',
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
                'amend_date': attrs.get('AmendDate', 'N/A'),
                'capture_scale': attrs.get('CaptureScale', 'N/A'),
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
    """Scrape detailed building information"""
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
        
        # Get content from all tabs
        all_content = {
            'overview': {},
            'official_list_entry': {},
            'comments_photos': {},
            'tabs_found': [],
            'tabs_clicked': []
        }
        
        # Get initial content (Overview tab)
        print(f"    📋 Getting Overview tab content...")
        initial_html = driver.page_source
        initial_soup = BeautifulSoup(initial_html, 'html.parser')
        all_content['overview'] = extract_tab_content(initial_soup, 'Overview')
        
        # Look for and click other tabs
        print(f"    🔍 Looking for additional tabs...")
        
        tab_texts = ['Official List Entry', 'Comments', 'Photos']
        found_tabs = []
        
        for text in tab_texts:
            try:
                xpath_patterns = [
                    f"//button[contains(text(), '{text}')]",
                    f"//div[contains(text(), '{text}')]",
                    f"//a[contains(text(), '{text}')]",
                    f"//span[contains(text(), '{text}')]"
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
        
        print(f"    📋 Found {len(found_tabs)} additional tabs")
        
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
                if 'official' in tab['text'].lower() or 'list entry' in tab['text'].lower():
                    all_content['official_list_entry'] = tab_content
                elif 'comment' in tab['text'].lower() or 'photo' in tab['text'].lower():
                    all_content['comments_photos'] = tab_content
                
                print(f"      ✅ Extracted content from '{tab['text']}'")
                
            except Exception as e:
                print(f"      ❌ Error clicking tab '{tab['text']}': {e}")
                continue
        
        driver.quit()
        
        print(f"    ✅ Scraping complete!")
        return {
            'url': url,
            'scraped_at': datetime.now().isoformat(),
            'tabs_processed': len(all_content['tabs_clicked']),
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
        'address': '',
        'materials': '',
        'construction_period': '',
        'architectural_style': '',
        'interior_features': '',
        'exterior_features': ''
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
        'planked doors', 'recessed', 'diagonally-set', 'axial position',
        'timber', 'slate', 'thatch', 'gable', 'dormer', 'bay window'
    ]
    
    for para in soup.find_all('p'):
        text = para.get_text().strip()
        if len(text) > 100:
            keyword_count = sum(1 for keyword in architectural_keywords if keyword.lower() in text.lower())
            if keyword_count >= 3:
                data['architectural_details'] = text
                
                # Extract specific details
                if 'coursed rubble' in text.lower():
                    data['materials'] += 'coursed rubble stone, '
                if 'tiled' in text.lower():
                    data['materials'] += 'tiled roof, '
                if 'brick' in text.lower():
                    data['materials'] += 'brick, '
                if 'timber' in text.lower():
                    data['materials'] += 'timber, '
                
                # Extract construction period
                period_patterns = [
                    r'Mid C(\d+)',
                    r'Early C(\d+)',
                    r'Late C(\d+)',
                    r'(\d+)th century',
                    r'(\d+)th-century'
                ]
                
                for pattern in period_patterns:
                    match = re.search(pattern, text, re.I)
                    if match:
                        data['construction_period'] = match.group(1)
                        break
                
                break
    
    return data

def compare_data(api_data: Dict[str, Any], scraped_data: Optional[Dict[str, Any]]):
    """Compare API data vs scraped data"""
    print(f"\n📊 DATA COMPARISON")
    print("=" * 60)
    
    print(f"\n🏛️  Building: {api_data['name']}")
    print(f"   List Entry: {api_data['list_entry']}")
    print(f"   Grade: {api_data['grade']}")
    
    print(f"\n📋 API DATA:")
    print("-" * 30)
    for key, value in api_data.items():
        if value and value != 'N/A':
            print(f"  {key}: {value}")
    
    if scraped_data:
        print(f"\n🕷️  SCRAPED DATA:")
        print("-" * 30)
        
        # Overview tab
        if 'overview' in scraped_data['tab_content']:
            overview = scraped_data['tab_content']['overview']
            print(f"  Overview Tab:")
            print(f"    Headings: {len(overview['headings'])}")
            print(f"    Paragraphs: {len(overview['paragraphs'])}")
            print(f"    Images: {len(overview['images'])}")
            print(f"    Links: {len(overview['links'])}")
        
        # Official List Entry tab
        if 'official_list_entry' in scraped_data['tab_content']:
            official = scraped_data['tab_content']['official_list_entry']
            print(f"  Official List Entry Tab:")
            if 'headings' in official:
                print(f"    Headings: {len(official['headings'])}")
            if 'paragraphs' in official:
                print(f"    Paragraphs: {len(official['paragraphs'])}")
            if 'images' in official:
                print(f"    Images: {len(official['images'])}")
            if 'links' in official:
                print(f"    Links: {len(official['links'])}")
            
            if 'specific_data' in official and official['specific_data']:
                print(f"    Specific Data:")
                for key, value in official['specific_data'].items():
                    if value:
                        print(f"      {key}: {value}")
        
        # Comments/Photos tab
        if 'comments_photos' in scraped_data['tab_content']:
            comments = scraped_data['tab_content']['comments_photos']
            print(f"  Comments/Photos Tab:")
            if 'headings' in comments:
                print(f"    Headings: {len(comments['headings'])}")
            if 'paragraphs' in comments:
                print(f"    Paragraphs: {len(comments['paragraphs'])}")
            if 'images' in comments:
                print(f"    Images: {len(comments['images'])}")
            if 'links' in comments:
                print(f"    Links: {len(comments['links'])}")
        
        print(f"\n📈 DATA ENRICHMENT:")
        print("-" * 30)
        
        # Compare what we get from each source
        api_fields = set(api_data.keys())
        scraped_fields = set()
        
        if 'official_list_entry' in scraped_data['tab_content']:
            scraped_fields = set(scraped_data['tab_content']['official_list_entry']['specific_data'].keys())
        
        common_fields = api_fields.intersection(scraped_fields)
        api_only = api_fields - scraped_fields
        scraped_only = scraped_fields - api_fields
        
        print(f"  Common fields: {len(common_fields)}")
        for field in sorted(common_fields):
            print(f"    - {field}")
        
        print(f"  API only: {len(api_only)}")
        for field in sorted(api_only):
            print(f"    - {field}")
        
        print(f"  Scraped only: {len(scraped_only)}")
        for field in sorted(scraped_only):
            print(f"    - {field}")
        
        # Show additional content from scraping
        print(f"\n🎯 ADDITIONAL CONTENT FROM SCRAPING:")
        print("-" * 30)
        
        total_headings = 0
        total_paragraphs = 0
        total_images = 0
        total_links = 0
        
        for tab_name, tab_data in scraped_data['tab_content'].items():
            if isinstance(tab_data, dict) and 'tab_name' in tab_data:
                total_headings += len(tab_data['headings'])
                total_paragraphs += len(tab_data['paragraphs'])
                total_images += len(tab_data['images'])
                total_links += len(tab_data['links'])
        
        print(f"  Total headings: {total_headings}")
        print(f"  Total paragraphs: {total_paragraphs}")
        print(f"  Total images: {total_images}")
        print(f"  Total links: {total_links}")
        print(f"  Tabs processed: {scraped_data['tabs_processed']}")
        
    else:
        print(f"\n❌ No scraped data available for comparison")
    
    print(f"\n💡 SUMMARY:")
    print("-" * 30)
    print(f"  API provides: Basic building information, coordinates, grades")
    print(f"  Scraping provides: Detailed descriptions, architectural details, images, full content")
    print(f"  Combined: Complete building profile with both structured and detailed information")

def main():
    """Main function"""
    print("🏛️  API vs Scrape Data Comparison")
    print("=" * 60)
    
    # Get building from API
    api_data = get_building_from_api()
    
    if not api_data:
        print("❌ No building to compare")
        return
    
    print(f"\n🏛️  Building: {api_data['name']}")
    print(f"   Grade: {api_data['grade']}, Entry: {api_data['list_entry']}")
    print(f"   URL: {api_data['hyperlink']}")
    
    # Scrape detailed content
    scraped_data = scrape_building_details(api_data['hyperlink'])
    
    # Compare the data
    compare_data(api_data, scraped_data)
    
    # Save comparison results
    comparison_result = {
        'building_name': api_data['name'],
        'list_entry': api_data['list_entry'],
        'comparison_date': datetime.now().isoformat(),
        'api_data': api_data,
        'scraped_data': scraped_data
    }
    
    with open('api_vs_scrape_comparison.json', 'w', encoding='utf-8') as f:
        json.dump(comparison_result, f, indent=2, ensure_ascii=False)
    
    print(f"\n📁 Comparison results saved to api_vs_scrape_comparison.json")

if __name__ == "__main__":
    main()
