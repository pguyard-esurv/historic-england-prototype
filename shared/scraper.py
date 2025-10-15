#!/usr/bin/env python3
"""
Shared web scraper for Historic England pages
"""

import re
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from bs4 import BeautifulSoup


class HistoricEnglandScraper:
    """Scraper for Historic England building pages"""
    
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.driver = None
    
    def _setup_driver(self):
        """Set up Chrome WebDriver"""
        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support import expected_conditions as EC
            from selenium.webdriver.support.ui import WebDriverWait
            
            options = Options()
            if self.headless:
                options.add_argument('--headless')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)
            options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
            
            self.driver = webdriver.Chrome(options=options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            return True
        except Exception as e:
            print(f"❌ Error setting up driver: {e}")
            return False
    
    def _handle_cookie_consent(self):
        """Handle cookie consent banner"""
        try:
            from selenium.webdriver.common.by import By
            
            cookie_buttons = self.driver.find_elements(By.XPATH, "//button[contains(text(), 'Accept') or contains(text(), 'Accept All')]")
            if cookie_buttons:
                cookie_buttons[0].click()
                time.sleep(1)
                return True
        except:
            pass
        return False
    
    def scrape_building(self, url: str, building_name: str = "") -> Tuple[Optional[Dict[str, Any]], Dict[str, float]]:
        """Scrape a single building page"""
        timing = {
            'start_time': time.time(),
            'setup_time': 0,
            'page_load_time': 0,
            'cookie_time': 0,
            'scraping_time': 0,
            'total_time': 0
        }
        
        try:
            # Setup driver
            setup_start = time.time()
            if not self._setup_driver():
                return None, timing
            
            timing['setup_time'] = time.time() - setup_start
            
            # Load page
            page_start = time.time()
            self.driver.get(url)
            
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support import expected_conditions as EC
            from selenium.webdriver.support.ui import WebDriverWait
            
            wait = WebDriverWait(self.driver, 15)
            try:
                wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            except:
                pass
            
            timing['page_load_time'] = time.time() - page_start
            
            # Handle cookies
            cookie_start = time.time()
            self._handle_cookie_consent()
            timing['cookie_time'] = time.time() - cookie_start
            
            time.sleep(2)
            
            # Scrape content
            scrape_start = time.time()
            html = self.driver.page_source
            soup = BeautifulSoup(html, 'html.parser')
            
            content = self._extract_content(soup, building_name)
            content['url'] = url
            content['scraped_at'] = datetime.now().isoformat()
            
            timing['scraping_time'] = time.time() - scrape_start
            timing['total_time'] = time.time() - timing['start_time']
            
            return content, timing
            
        except Exception as e:
            print(f"❌ Scraping error: {e}")
            timing['total_time'] = time.time() - timing['start_time']
            return None, timing
        finally:
            if self.driver:
                self.driver.quit()
    
    def scrape_with_tabs(self, url: str, building_name: str = "") -> Tuple[Optional[Dict[str, Any]], Dict[str, float]]:
        """Scrape building page with tab navigation"""
        timing = {
            'start_time': time.time(),
            'setup_time': 0,
            'page_load_time': 0,
            'cookie_time': 0,
            'tab_navigation_time': 0,
            'content_extraction_time': 0,
            'total_time': 0,
            'tab_timings': {}
        }
        
        try:
            # Setup driver
            setup_start = time.time()
            if not self._setup_driver():
                return None, timing
            
            timing['setup_time'] = time.time() - setup_start
            
            # Load page
            page_start = time.time()
            self.driver.get(url)
            
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support import expected_conditions as EC
            from selenium.webdriver.support.ui import WebDriverWait
            
            wait = WebDriverWait(self.driver, 15)
            try:
                wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            except:
                pass
            
            timing['page_load_time'] = time.time() - page_start
            
            # Handle cookies
            cookie_start = time.time()
            self._handle_cookie_consent()
            timing['cookie_time'] = time.time() - cookie_start
            
            time.sleep(2)
            
            # Get initial content (Overview tab)
            all_content = {
                'overview': {},
                'official_list_entry': {},
                'comments_photos': {},
                'tabs_found': [],
                'tabs_clicked': []
            }
            
            initial_html = self.driver.page_source
            initial_soup = BeautifulSoup(initial_html, 'html.parser')
            all_content['overview'] = self._extract_tab_content(initial_soup, 'Overview')
            
            # Look for and click other tabs
            tab_start = time.time()
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
                        elements = self.driver.find_elements(By.XPATH, xpath)
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
            
            # Click on each tab and collect content
            for tab in found_tabs:
                try:
                    tab_click_start = time.time()
                    
                    self.driver.execute_script("arguments[0].scrollIntoView(true);", tab['element'])
                    time.sleep(1)
                    
                    try:
                        tab['element'].click()
                    except:
                        self.driver.execute_script("arguments[0].click();", tab['element'])
                    
                    time.sleep(3)
                    
                    html = self.driver.page_source
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    tab_content = self._extract_tab_content(soup, tab['text'])
                    all_content['tabs_clicked'].append(tab['text'])
                    
                    # Store content by tab type
                    if 'official' in tab['text'].lower() or 'list entry' in tab['text'].lower():
                        all_content['official_list_entry'] = tab_content
                    elif 'comment' in tab['text'].lower() or 'photo' in tab['text'].lower():
                        all_content['comments_photos'] = tab_content
                    
                    tab_click_end = time.time()
                    timing['tab_timings'][tab['text'].lower().replace(' ', '_')] = tab_click_end - tab_click_start
                    
                except Exception as e:
                    print(f"      ❌ Error clicking tab '{tab['text']}': {e}")
                    continue
            
            timing['tab_navigation_time'] = time.time() - tab_start
            
            # Final content extraction
            extract_start = time.time()
            final_html = self.driver.page_source
            timing['content_extraction_time'] = time.time() - extract_start
            timing['total_time'] = time.time() - timing['start_time']
            
            content = {
                'url': url,
                'scraped_at': datetime.now().isoformat(),
                'tabs_processed': len(all_content['tabs_clicked']),
                'final_html': final_html,
                'tab_content': all_content
            }
            
            return content, timing
            
        except Exception as e:
            print(f"❌ Scraping error: {e}")
            timing['total_time'] = time.time() - timing['start_time']
            return None, timing
        finally:
            if self.driver:
                self.driver.quit()
    
    def _extract_content(self, soup: BeautifulSoup, building_name: str = "") -> Dict[str, Any]:
        """Extract content from a page"""
        content = {
            'building_name': building_name,
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
        
        # Extract specific building data
        content['specific_data'] = self._extract_building_specific_data(soup)
        
        return content
    
    def _extract_tab_content(self, soup: BeautifulSoup, tab_name: str) -> Dict[str, Any]:
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
            content['specific_data'] = self._extract_building_specific_data(soup)
        
        return content
    
    def _extract_building_specific_data(self, soup: BeautifulSoup) -> Dict[str, Any]:
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
    
    def search_for_uprn_patterns(self, text: str) -> List[str]:
        """Search for UPRN patterns in text"""
        patterns = [
            r'UPRN[:\s]*(\d{12})',  # UPRN: 123456789012
            r'Unique Property Reference Number[:\s]*(\d{12})',
            r'Property Reference[:\s]*(\d{12})',
            r'(\d{12})',  # Any 12-digit number
            r'UPRN[:\s]*(\d+)',  # UPRN with any number of digits
            r'Property ID[:\s]*(\d+)',
            r'Address ID[:\s]*(\d+)',
            r'Building ID[:\s]*(\d+)',
            r'Reference[:\s]*(\d{8,12})',  # 8-12 digit reference
        ]
        
        found = []
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                if len(match) >= 8:  # UPRN should be at least 8 digits
                    found.append(match)
        
        return list(set(found))  # Remove duplicates
