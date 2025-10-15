#!/usr/bin/env python3
"""
Batch processor for multiple buildings - Refactored
"""

import json
import time
from datetime import datetime

from shared.api_client import NHLEAPIClient
from shared.scraper import HistoricEnglandScraper


def process_batch(count: int = 5, look_for_uprn: bool = False):
    """Process a batch of buildings"""
    print(f"🏛️  Batch Processing {count} Buildings")
    print("=" * 50)
    
    # Initialize clients
    api_client = NHLEAPIClient()
    scraper = HistoricEnglandScraper(headless=True)
    
    # Get buildings from API
    print(f"🎲 Getting {count} buildings from API...")
    buildings = api_client.get_buildings(count)
    
    if not buildings:
        print("❌ No buildings to process")
        return
    
    print(f"✅ Selected {len(buildings)} buildings")
    
    # Process each building
    results = []
    start_time = time.time()
    
    for i, building in enumerate(buildings, 1):
        print(f"\n[{i}/{len(buildings)}] {building['name']}")
        print(f"   Grade: {building['grade']}, Entry: {building['list_entry']}")
        
        # Scrape building
        scraped_data, timing = scraper.scrape_building(building['hyperlink'], building['name'])
        
        # Look for UPRN if requested
        uprn_found = []
        if look_for_uprn and scraped_data:
            uprn_found = scraper.search_for_uprn_patterns(scraped_data.get('text_content', ''))
        
        result = {
            'building': building,
            'scraped_data': scraped_data,
            'timing': timing,
            'uprn_found': uprn_found,
            'processed_at': datetime.now().isoformat()
        }
        
        results.append(result)
        
        print(f"   ✅ Scraped in {timing['total_time']:.2f}s")
        if look_for_uprn:
            print(f"   🎯 UPRN found: {len(uprn_found)} - {uprn_found}")
        
        # Small delay to be respectful
        time.sleep(1)
    
    total_time = time.time() - start_time
    
    # Analyze results
    print(f"\n📊 BATCH ANALYSIS")
    print("=" * 50)
    
    successful_scrapes = len([r for r in results if r['scraped_data'] is not None])
    total_uprn_found = sum(len(r['uprn_found']) for r in results)
    buildings_with_uprn = len([r for r in results if r['uprn_found']])
    
    print(f"Total buildings processed: {len(buildings)}")
    print(f"Successful scrapes: {successful_scrapes}")
    print(f"Success rate: {(successful_scrapes/len(buildings))*100:.1f}%")
    
    if look_for_uprn:
        print(f"Buildings with UPRN: {buildings_with_uprn}")
        print(f"Total UPRNs found: {total_uprn_found}")
        print(f"UPRN discovery rate: {(buildings_with_uprn/successful_scrapes)*100:.1f}%" if successful_scrapes > 0 else "N/A")
    
    # Timing analysis
    timings = [r['timing']['total_time'] for r in results if r['timing']]
    if timings:
        avg_time = sum(timings) / len(timings)
        min_time = min(timings)
        max_time = max(timings)
        print(f"\n⏱️  TIMING ANALYSIS:")
        print(f"Average scraping time: {avg_time:.2f}s")
        print(f"Fastest scrape: {min_time:.2f}s")
        print(f"Slowest scrape: {max_time:.2f}s")
        print(f"Total processing time: {total_time:.2f}s")
        print(f"Average time per building: {total_time/len(buildings):.2f}s")
    
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
    
    # Save results
    batch_results = {
        'metadata': {
            'total_buildings': len(buildings),
            'processing_date': datetime.now().isoformat(),
            'total_processing_time': total_time,
            'average_time_per_building': total_time/len(buildings),
            'look_for_uprn': look_for_uprn
        },
        'summary': {
            'successful_scrapes': successful_scrapes,
            'buildings_with_uprn': buildings_with_uprn,
            'total_uprn_found': total_uprn_found,
            'success_rate': (successful_scrapes/len(buildings))*100,
            'uprn_discovery_rate': (buildings_with_uprn/successful_scrapes)*100 if successful_scrapes > 0 else 0
        },
        'timing': {
            'average_time': sum(timings) / len(timings) if timings else 0,
            'min_time': min(timings) if timings else 0,
            'max_time': max(timings) if timings else 0,
            'total_time': total_time
        },
        'content': {
            'total_headings': total_headings,
            'total_paragraphs': total_paragraphs,
            'total_images': total_images,
            'total_links': total_links
        },
        'detailed_results': results
    }
    
    filename = f'batch_results_{count}_buildings.json'
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(batch_results, f, indent=2, ensure_ascii=False)
    
    print(f"\n📁 Results saved to {filename}")
    
    # Show buildings with UPRN if looking for them
    if look_for_uprn and buildings_with_uprn > 0:
        print(f"\n🎯 BUILDINGS WITH UPRN FOUND:")
        for result in results:
            if result['uprn_found']:
                building = result['building']
                print(f"  • {building['name']} (Entry: {building['list_entry']})")
                print(f"    UPRNs: {result['uprn_found']}")
    elif look_for_uprn:
        print(f"\n❌ No UPRNs found in any of the scraped buildings")

def main():
    """Main function"""
    import sys
    
    count = 5
    look_for_uprn = False
    
    if len(sys.argv) > 1:
        try:
            count = int(sys.argv[1])
        except ValueError:
            print("❌ Invalid count argument. Using default of 5.")
    
    if len(sys.argv) > 2 and sys.argv[2].lower() == 'uprn':
        look_for_uprn = True
    
    process_batch(count, look_for_uprn)

if __name__ == "__main__":
    main()
