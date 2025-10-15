#!/usr/bin/env python3
"""
Export API vs Scraped data differences as structured JSON
"""

import json
from datetime import datetime
from typing import Any, Dict, List, Optional


def export_differences_as_json():
    """Export the differences between API and scraped data as structured JSON"""
    print("📊 Exporting API vs Scraped Data Differences as JSON")
    print("=" * 60)
    
    try:
        # Load the comparison data
        with open('api_vs_scrape_comparison.json', 'r', encoding='utf-8') as f:
            comparison_data = json.load(f)
        
        api_data = comparison_data['api_data']
        scraped_data = comparison_data['scraped_data']
        
        # Create structured difference analysis
        differences = {
            'metadata': {
                'building_name': comparison_data['building_name'],
                'list_entry': comparison_data['list_entry'],
                'export_date': datetime.now().isoformat(),
                'analysis_type': 'API vs Scraped Data Differences'
            },
            'data_sources': {
                'api': {
                    'name': 'National Heritage List for England API',
                    'endpoint': 'https://services-eu1.arcgis.com/ZOdPfBS3aqqDYPUQ/arcgis/rest/services/National_Heritage_List_for_England_NHLE_v02_VIEW/FeatureServer',
                    'data_type': 'Structured JSON',
                    'update_frequency': 'Real-time',
                    'total_buildings': 379604
                },
                'scraping': {
                    'name': 'Historic England Website Scraping',
                    'base_url': 'https://historicengland.org.uk/listing/the-list/',
                    'data_type': 'HTML Content + Structured Extraction',
                    'update_frequency': 'On-demand',
                    'content_depth': 'Detailed'
                }
            },
            'field_analysis': {
                'common_fields': [],
                'api_only_fields': [],
                'scraped_only_fields': [],
                'field_comparison': {}
            },
            'content_analysis': {
                'api_content': {},
                'scraped_content': {},
                'content_enrichment': {}
            },
            'data_quality': {
                'api': {
                    'completeness': 0,
                    'accuracy': 'High',
                    'consistency': 'High',
                    'availability': 'High'
                },
                'scraping': {
                    'completeness': 0,
                    'accuracy': 'Medium',
                    'consistency': 'Medium',
                    'availability': 'Medium'
                }
            },
            'use_cases': {
                'api_recommended': [],
                'scraping_recommended': [],
                'combined_recommended': []
            },
            'technical_specifications': {
                'api': {
                    'response_time': 'Milliseconds',
                    'rate_limits': '1000 records per query',
                    'maintenance': 'None (managed by Historic England)',
                    'cost': 'Free',
                    'reliability': '99.9%+'
                },
                'scraping': {
                    'response_time': 'Seconds per building',
                    'rate_limits': 'Respectful delays required',
                    'maintenance': 'Regular updates needed',
                    'cost': 'Server resources + ChromeDriver',
                    'reliability': 'Depends on website changes'
                }
            }
        }
        
        # Analyze field differences
        api_fields = set(api_data.keys())
        scraped_fields = set()
        
        if scraped_data and 'official_list_entry' in scraped_data['tab_content']:
            official = scraped_data['tab_content']['official_list_entry']
            if 'specific_data' in official:
                scraped_fields = set(official['specific_data'].keys())
        
        common_fields = api_fields.intersection(scraped_fields)
        api_only = api_fields - scraped_fields
        scraped_only = scraped_fields - api_fields
        
        # Populate field analysis
        differences['field_analysis']['common_fields'] = list(common_fields)
        differences['field_analysis']['api_only_fields'] = list(api_only)
        differences['field_analysis']['scraped_only_fields'] = list(scraped_only)
        
        # Create field comparison
        for field in common_fields:
            api_value = api_data.get(field, 'N/A')
            scraped_value = 'N/A'
            
            if scraped_data and 'official_list_entry' in scraped_data['tab_content']:
                official = scraped_data['tab_content']['official_list_entry']
                if 'specific_data' in official:
                    scraped_value = official['specific_data'].get(field, 'N/A')
            
            differences['field_analysis']['field_comparison'][field] = {
                'api_value': api_value,
                'scraped_value': scraped_value,
                'values_match': str(api_value) == str(scraped_value),
                'data_source_preference': 'api' if api_value != 'N/A' else 'scraped'
            }
        
        # Populate API content
        differences['content_analysis']['api_content'] = {
            'total_fields': len(api_data),
            'populated_fields': len([v for v in api_data.values() if v and v != 'N/A']),
            'data_types': {
                'string': len([v for v in api_data.values() if isinstance(v, str)]),
                'numeric': len([v for v in api_data.values() if isinstance(v, (int, float))]),
                'url': len([v for v in api_data.values() if isinstance(v, str) and v.startswith('http')])
            },
            'sample_data': api_data
        }
        
        # Populate scraped content
        if scraped_data:
            total_headings = 0
            total_paragraphs = 0
            total_images = 0
            total_links = 0
            
            for tab_name, tab_data in scraped_data['tab_content'].items():
                if isinstance(tab_data, dict) and 'tab_name' in tab_data:
                    total_headings += len(tab_data.get('headings', []))
                    total_paragraphs += len(tab_data.get('paragraphs', []))
                    total_images += len(tab_data.get('images', []))
                    total_links += len(tab_data.get('links', []))
            
            differences['content_analysis']['scraped_content'] = {
                'tabs_processed': scraped_data.get('tabs_processed', 0),
                'content_counts': {
                    'headings': total_headings,
                    'paragraphs': total_paragraphs,
                    'images': total_images,
                    'links': total_links
                },
                'tabs_available': list(scraped_data['tab_content'].keys()),
                'architectural_details': {}
            }
            
            # Add architectural details if available
            if 'official_list_entry' in scraped_data['tab_content']:
                official = scraped_data['tab_content']['official_list_entry']
                if 'specific_data' in official and official['specific_data']:
                    differences['content_analysis']['scraped_content']['architectural_details'] = official['specific_data']
        
        # Calculate data quality metrics
        api_completeness = len([v for v in api_data.values() if v and v != 'N/A']) / len(api_data) * 100
        differences['data_quality']['api']['completeness'] = round(api_completeness, 1)
        
        if scraped_data:
            scraped_completeness = len([v for v in scraped_fields if scraped_data.get('tab_content', {}).get('official_list_entry', {}).get('specific_data', {}).get(v)]) / len(scraped_fields) * 100 if scraped_fields else 0
            differences['data_quality']['scraping']['completeness'] = round(scraped_completeness, 1)
        
        # Populate use cases
        differences['use_cases']['api_recommended'] = [
            "Building counts and statistics",
            "Geographic analysis and mapping",
            "Bulk data processing",
            "Building identification and basic info",
            "Fast, reliable data access",
            "Real-time building queries",
            "Large-scale heritage analysis"
        ]
        
        differences['use_cases']['scraping_recommended'] = [
            "Detailed architectural research",
            "Historical context and significance",
            "Visual content and images",
            "Complete building descriptions",
            "User-generated content analysis",
            "Heritage documentation",
            "Educational content creation"
        ]
        
        differences['use_cases']['combined_recommended'] = [
            "Comprehensive building databases",
            "Research and analysis platforms",
            "Heritage management systems",
            "Educational and cultural applications",
            "Complete building profiles",
            "Heritage tourism applications",
            "Academic research projects"
        ]
        
        # Add content enrichment analysis
        differences['content_analysis']['content_enrichment'] = {
            'api_contributes': {
                'structured_data': True,
                'geographic_precision': True,
                'bulk_access': True,
                'reliability': True,
                'real_time_updates': True
            },
            'scraping_contributes': {
                'detailed_descriptions': True,
                'visual_content': True,
                'historical_context': True,
                'architectural_details': True,
                'user_content': True
            },
            'combined_benefits': {
                'complete_profiles': True,
                'scalable_solution': True,
                'research_ready': True,
                'heritage_comprehensive': True
            }
        }
        
        # Save the structured differences
        output_file = 'api_vs_scrape_differences.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(differences, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Differences exported to {output_file}")
        print(f"📊 Analysis Summary:")
        print(f"   Common fields: {len(common_fields)}")
        print(f"   API only fields: {len(api_only)}")
        print(f"   Scraped only fields: {len(scraped_only)}")
        print(f"   API completeness: {differences['data_quality']['api']['completeness']}%")
        if scraped_data:
            print(f"   Scraped completeness: {differences['data_quality']['scraping']['completeness']}%")
        
        # Also create a simplified version
        simplified_differences = {
            'building': {
                'name': comparison_data['building_name'],
                'list_entry': comparison_data['list_entry']
            },
            'data_sources': {
                'api_fields': list(api_fields),
                'scraped_fields': list(scraped_fields),
                'common_fields': list(common_fields),
                'api_only': list(api_only),
                'scraped_only': list(scraped_only)
            },
            'content_summary': {
                'api_data': api_data,
                'scraped_architectural_details': scraped_data.get('tab_content', {}).get('official_list_entry', {}).get('specific_data', {}) if scraped_data else {}
            },
            'recommendations': {
                'use_api_for': differences['use_cases']['api_recommended'],
                'use_scraping_for': differences['use_cases']['scraping_recommended'],
                'use_combined_for': differences['use_cases']['combined_recommended']
            }
        }
        
        simplified_file = 'differences_summary.json'
        with open(simplified_file, 'w', encoding='utf-8') as f:
            json.dump(simplified_differences, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Simplified differences exported to {simplified_file}")
        
        return differences
        
    except FileNotFoundError:
        print("❌ Comparison file not found. Run api_vs_scrape_comparison.py first.")
        return None
    except Exception as e:
        print(f"❌ Error exporting differences: {e}")
        return None

if __name__ == "__main__":
    export_differences_as_json()
