#!/usr/bin/env python3
"""
Detailed Scraper for Historic England Building Pages - Refactored
"""

import json

from shared.api_client import NHLEAPIClient
from shared.scraper import HistoricEnglandScraper


def main():
    """Main function"""
    print("🏛️  Detailed Historic England Building Scraper")
    print("=" * 60)
    
    # Initialize clients
    api_client = NHLEAPIClient()
    scraper = HistoricEnglandScraper(headless=True)
    
    # Get a random building
    print("🎲 Getting random building from API...")
    building = api_client.get_random_building()
    
    if not building:
        print("❌ No building to scrape")
        return
    
    print(f"✅ Selected: {building['name']}")
    print(f"\n🏛️  Building: {building['name']}")
    print(f"   Grade: {building['grade']}, Entry: {building['list_entry']}")
    print(f"   URL: {building['hyperlink']}")
    
    # Scrape detailed content
    print(f"\n🔍 Scraping detailed content...")
    result, timing = scraper.scrape_with_tabs(building['hyperlink'], building['name'])
    
    if result:
        print(f"\n✅ SUCCESS! Detailed scraping completed")
        print(f"   Tabs found: {len(result.get('tab_content', {}).get('tabs_found', []))}")
        print(f"   Tabs clicked: {len(result.get('tab_content', {}).get('tabs_clicked', []))}")
        print(f"   Tabs processed: {result.get('tabs_processed', 0)}")
        print(f"   Total time: {timing['total_time']:.2f}s")
        
        # Save results
        with open('detailed_scraping_results.json', 'w', encoding='utf-8') as f:
            json.dump({
                'building': building,
                'scraped_data': result,
                'timing': timing
            }, f, indent=2, ensure_ascii=False)
        
        print(f"\n📁 Results saved to detailed_scraping_results.json")
        
        # Show what we found
        for tab_name, tab_data in result.get('tab_content', {}).items():
            if isinstance(tab_data, dict) and 'tab_name' in tab_data:
                print(f"\n📋 Tab: {tab_data['tab_name']}")
                print(f"   Headings: {len(tab_data.get('headings', []))}")
                print(f"   Paragraphs: {len(tab_data.get('paragraphs', []))}")
                print(f"   Images: {len(tab_data.get('images', []))}")
                print(f"   Links: {len(tab_data.get('links', []))}")
                
                if tab_data.get('specific_data'):
                    print(f"   Specific data: {list(tab_data['specific_data'].keys())}")
                    if tab_data['specific_data'].get('architectural_details'):
                        print(f"   Architectural details: {tab_data['specific_data']['architectural_details'][:200]}...")
        
    else:
        print(f"\n❌ Failed to scrape detailed content")

if __name__ == "__main__":
    main()
