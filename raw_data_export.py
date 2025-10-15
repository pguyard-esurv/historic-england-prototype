#!/usr/bin/env python3
"""
Export raw API and scraped data as clean JSON (no analysis)
"""

import json
from datetime import datetime
from typing import Any, Dict, Optional


def export_raw_data():
    """Export raw API and scraped data without analysis"""
    print("📊 Exporting Raw API and Scraped Data")
    print("=" * 50)
    
    try:
        # Load the comparison data
        with open('api_vs_scrape_comparison.json', 'r', encoding='utf-8') as f:
            comparison_data = json.load(f)
        
        api_data = comparison_data['api_data']
        scraped_data = comparison_data['scraped_data']
        
        # Create clean data structure
        raw_data = {
            'building': {
                'name': comparison_data['building_name'],
                'list_entry': comparison_data['list_entry'],
                'export_date': datetime.now().isoformat()
            },
            'api_data': api_data,
            'scraped_data': {}
        }
        
        # Add scraped data if available
        if scraped_data:
            raw_data['scraped_data'] = {
                'url': scraped_data.get('url', ''),
                'scraped_at': scraped_data.get('scraped_at', ''),
                'tabs_processed': scraped_data.get('tabs_processed', 0),
                'tabs_found': scraped_data.get('tab_content', {}).get('tabs_found', []),
                'tabs_clicked': scraped_data.get('tab_content', {}).get('tabs_clicked', []),
                'content': {}
            }
            
            # Add content from each tab
            for tab_name, tab_content in scraped_data.get('tab_content', {}).items():
                if isinstance(tab_content, dict) and 'tab_name' in tab_content:
                    raw_data['scraped_data']['content'][tab_name] = {
                        'tab_name': tab_content.get('tab_name', ''),
                        'headings': tab_content.get('headings', []),
                        'paragraphs': tab_content.get('paragraphs', []),
                        'images': tab_content.get('images', []),
                        'links': tab_content.get('links', []),
                        'text_content': tab_content.get('text_content', ''),
                        'specific_data': tab_content.get('specific_data', {})
                    }
        
        # Save the raw data
        output_file = 'raw_api_and_scraped_data.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(raw_data, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Raw data exported to {output_file}")
        
        # Show summary
        print(f"📊 Data Summary:")
        print(f"   Building: {raw_data['building']['name']}")
        print(f"   List Entry: {raw_data['building']['list_entry']}")
        print(f"   API fields: {len(api_data)}")
        
        if scraped_data:
            total_headings = 0
            total_paragraphs = 0
            total_images = 0
            total_links = 0
            
            for tab_name, tab_content in raw_data['scraped_data']['content'].items():
                total_headings += len(tab_content.get('headings', []))
                total_paragraphs += len(tab_content.get('paragraphs', []))
                total_images += len(tab_content.get('images', []))
                total_links += len(tab_content.get('links', []))
            
            print(f"   Scraped tabs: {len(raw_data['scraped_data']['content'])}")
            print(f"   Total headings: {total_headings}")
            print(f"   Total paragraphs: {total_paragraphs}")
            print(f"   Total images: {total_images}")
            print(f"   Total links: {total_links}")
        else:
            print(f"   Scraped data: Not available")
        
        return raw_data
        
    except FileNotFoundError:
        print("❌ Comparison file not found. Run api_vs_scrape_comparison.py first.")
        return None
    except Exception as e:
        print(f"❌ Error exporting raw data: {e}")
        return None

if __name__ == "__main__":
    export_raw_data()
