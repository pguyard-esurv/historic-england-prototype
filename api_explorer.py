#!/usr/bin/env python3
"""
NHLE API Explorer - Refactored to use shared modules
"""

from shared.api_client import NHLEAPIClient


def main():
    """Main function"""
    print("🏛️  National Heritage List for England (NHLE) API Explorer")
    print("=" * 60)
    
    # Initialize API client
    api_client = NHLEAPIClient()
    
    # Get API info
    print("🔍 Exploring NHLE API...")
    api_info = api_client.get_api_info()
    
    if api_info:
        print("📋 API Information:")
        print(f"Service Name: {api_info.get('serviceName', 'N/A')}")
        print(f"Max Record Count: {api_info.get('maxRecordCount', 'N/A')}")
        print(f"Supported Query Formats: {api_info.get('supportedQueryFormats', 'N/A')}")
        print(f"Supported Export Formats: {', '.join(api_info.get('supportedExportFormats', []))}")
        
        # List available layers
        if 'layers' in api_info:
            print(f"\n🗂️  Available Layers ({len(api_info['layers'])}):")
            for i, layer in enumerate(api_info['layers']):
                print(f"  {i}. ID: {layer.get('id')} - {layer.get('name', 'Unnamed')}")
                print(f"     Type: {layer.get('type', 'N/A')}")
                print(f"     Geometry Type: {layer.get('geometryType', 'N/A')}")
                print()
    
    # Count buildings
    print("🏛️  Counting Listed Buildings...")
    total_count, grade_counts = api_client.count_buildings()
    
    if total_count is not None:
        print(f"✅ Total listed buildings: {total_count:,}")
        
        if grade_counts:
            for grade, count in grade_counts.items():
                print(f"  Grade {grade}: {count:,}")
            
            print(f"\n📊 Summary:")
            print(f"Total Listed Buildings: {total_count:,}")
            for grade, count in grade_counts.items():
                percentage = (count / total_count) * 100 if total_count > 0 else 0
                print(f"Grade {grade}: {count:,} ({percentage:.1f}%)")
    
    # Get sample buildings
    print(f"\n📦 Getting sample buildings...")
    sample_buildings = api_client.get_buildings(5)
    
    if sample_buildings:
        print(f"✅ Found {len(sample_buildings)} sample buildings:")
        
        for i, building in enumerate(sample_buildings, 1):
            print(f"\n  {i}. {building['name']}")
            print(f"     Grade: {building['grade']}")
            print(f"     List Entry: {building['list_entry']}")
            print(f"     NHLE Link: {building['hyperlink']}")
    
    # Search for some examples
    print(f"\n🔍 Searching for 'castle'...")
    castle_results = api_client.search_buildings("castle", 3)
    
    if castle_results:
        print(f"✅ Found {len(castle_results)} results:")
        for i, building in enumerate(castle_results, 1):
            print(f"\n  {i}. {building['name']}")
            print(f"     Grade: {building['grade']}")
            print(f"     List Entry: {building['list_entry']}")
            print(f"     NHLE Link: {building['hyperlink']}")
    
    print(f"\n🔍 Searching for 'church'...")
    church_results = api_client.search_buildings("church", 3)
    
    if church_results:
        print(f"✅ Found {len(church_results)} results:")
        for i, building in enumerate(church_results, 1):
            print(f"\n  {i}. {building['name']}")
            print(f"     Grade: {building['grade']}")
            print(f"     List Entry: {building['list_entry']}")
            print(f"     NHLE Link: {building['hyperlink']}")
    
    print(f"\n" + "=" * 60)
    print("✅ API exploration complete!")
    print(f"\nKey findings:")
    print(f"• {total_count:,} listed buildings available")
    print(f"• 11 different data layers")
    print(f"• Rich search capabilities")
    print(f"• Direct links to detailed pages")

if __name__ == "__main__":
    main()
