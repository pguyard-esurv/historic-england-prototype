#!/usr/bin/env python3
"""
API vs Scraped Data Comparison - Refactored
"""

import json
from datetime import datetime

from shared.api_client import NHLEAPIClient
from shared.scraper import HistoricEnglandScraper


def compare_data_with_timing(api_data, api_timing, scraped_data, scraped_timing):
    """Compare API data vs scraped data with timing analysis"""
    print(f"\n📊 DATA COMPARISON WITH TIMING")
    print("=" * 60)
    
    print(f"\n🏛️  Building: {api_data['name']}")
    print(f"   List Entry: {api_data['list_entry']}")
    print(f"   Grade: {api_data['grade']}")
    
    print(f"\n⏱️  TIMING ANALYSIS:")
    print("-" * 30)
    print(f"  API Total Time: {api_timing:.3f}s")
    print(f"  Scraping Total Time: {scraped_timing['total_time']:.3f}s")
    print(f"    - Setup: {scraped_timing['setup_time']:.3f}s")
    print(f"    - Page Load: {scraped_timing['page_load_time']:.3f}s")
    print(f"    - Cookie Handling: {scraped_timing['cookie_time']:.3f}s")
    print(f"    - Tab Navigation: {scraped_timing['tab_navigation_time']:.3f}s")
    print(f"    - Content Extraction: {scraped_timing['content_extraction_time']:.3f}s")
    
    if scraped_timing.get('tab_timings'):
        print(f"    - Individual Tab Times:")
        for tab_name, tab_time in scraped_timing['tab_timings'].items():
            print(f"      * {tab_name}: {tab_time:.3f}s")
    
    print(f"\n📈 PERFORMANCE COMPARISON:")
    print("-" * 30)
    speed_ratio = scraped_timing['total_time'] / api_timing
    print(f"  API vs Scraping Speed: 1:{speed_ratio:.1f}")
    print(f"  API is {speed_ratio:.1f}x faster than scraping")
    
    print(f"\n📋 API DATA:")
    print("-" * 30)
    for key, value in api_data.items():
        if value and value != 'N/A':
            print(f"  {key}: {value}")
    
    if scraped_data:
        print(f"\n🕷️  SCRAPED DATA:")
        print("-" * 30)
        
        # Overview tab
        if 'overview' in scraped_data.get('tab_content', {}):
            overview = scraped_data['tab_content']['overview']
            print(f"  Overview Tab:")
            print(f"    Headings: {len(overview.get('headings', []))}")
            print(f"    Paragraphs: {len(overview.get('paragraphs', []))}")
            print(f"    Images: {len(overview.get('images', []))}")
            print(f"    Links: {len(overview.get('links', []))}")
        
        # Official List Entry tab
        if 'official_list_entry' in scraped_data.get('tab_content', {}):
            official = scraped_data['tab_content']['official_list_entry']
            print(f"  Official List Entry Tab:")
            print(f"    Headings: {len(official.get('headings', []))}")
            print(f"    Paragraphs: {len(official.get('paragraphs', []))}")
            print(f"    Images: {len(official.get('images', []))}")
            print(f"    Links: {len(official.get('links', []))}")
            
            if official.get('specific_data'):
                print(f"    Specific Data:")
                for key, value in official['specific_data'].items():
                    if value:
                        print(f"      {key}: {value}")
        
        print(f"\n💡 TIMING INSIGHTS:")
        print("-" * 30)
        print(f"  • API provides instant access to structured data")
        print(f"  • Scraping takes {scraped_timing['total_time']:.1f}s but provides rich content")
        print(f"  • Selenium setup overhead: {scraped_timing['setup_time']:.3f}s")
        print(f"  • Page load time: {scraped_timing['page_load_time']:.3f}s")
        print(f"  • Tab navigation: {scraped_timing['tab_navigation_time']:.3f}s")
        
        if scraped_timing.get('tab_timings'):
            fastest_tab = min(scraped_timing['tab_timings'].items(), key=lambda x: x[1])
            slowest_tab = max(scraped_timing['tab_timings'].items(), key=lambda x: x[1])
            print(f"  • Fastest tab: {fastest_tab[0]} ({fastest_tab[1]:.3f}s)")
            print(f"  • Slowest tab: {slowest_tab[0]} ({slowest_tab[1]:.3f}s)")
    
    else:
        print(f"\n❌ No scraped data available for comparison")
    
    print(f"\n🎯 RECOMMENDATIONS:")
    print("-" * 30)
    print(f"  • Use API for: Fast queries, bulk operations, real-time data")
    print(f"  • Use Scraping for: Detailed analysis, rich content, research")
    print(f"  • Combined approach: API for discovery, scraping for details")

def main():
    """Main function"""
    print("🏛️  API vs Scraped Data Comparison with Timing")
    print("=" * 60)
    
    # Initialize clients
    api_client = NHLEAPIClient()
    scraper = HistoricEnglandScraper(headless=True)
    
    # Get building from API with timing
    print("🎲 Getting random building from API...")
    import time
    api_start = time.time()
    building = api_client.get_random_building()
    api_timing = time.time() - api_start
    
    if not building:
        print("❌ No building to compare")
        return
    
    print(f"✅ Selected: {building['name']}")
    print(f"   API timing: {api_timing:.3f}s")
    
    print(f"\n🏛️  Building: {building['name']}")
    print(f"   Grade: {building['grade']}, Entry: {building['list_entry']}")
    print(f"   URL: {building['hyperlink']}")
    
    # Scrape detailed content with timing
    print(f"\n🔍 Scraping detailed content...")
    scraped_data, scraped_timing = scraper.scrape_with_tabs(building['hyperlink'], building['name'])
    
    # Compare the data with timing analysis
    compare_data_with_timing(building, api_timing, scraped_data, scraped_timing)
    
    # Save comparison results
    comparison_result = {
        'building_name': building['name'],
        'list_entry': building['list_entry'],
        'comparison_date': datetime.now().isoformat(),
        'api_data': building,
        'api_timing': api_timing,
        'scraped_data': scraped_data,
        'scraped_timing': scraped_timing,
        'performance_summary': {
            'api_total_time': api_timing,
            'scraping_total_time': scraped_timing['total_time'],
            'speed_ratio': scraped_timing['total_time'] / api_timing if api_timing > 0 else 0,
            'api_faster_by': scraped_timing['total_time'] / api_timing if api_timing > 0 else 0
        }
    }
    
    with open('comparison_results.json', 'w', encoding='utf-8') as f:
        json.dump(comparison_result, f, indent=2, ensure_ascii=False)
    
    print(f"\n📁 Results saved to comparison_results.json")

if __name__ == "__main__":
    main()
