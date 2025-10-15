#!/usr/bin/env python3
"""
NHLE API Explorer - Simple script to explore the National Heritage List for England API
"""

import json
from datetime import datetime

import requests

# NHLE API endpoint
NHLE_BASE_URL = "https://services-eu1.arcgis.com/ZOdPfBS3aqqDYPUQ/arcgis/rest/services/National_Heritage_List_for_England_NHLE_v02_VIEW/FeatureServer"

def get_api_info():
    """Get basic information about the API"""
    print("🔍 Exploring NHLE API...")
    print(f"Base URL: {NHLE_BASE_URL}")
    print("-" * 50)
    
    try:
        response = requests.get(NHLE_BASE_URL, params={'f': 'json'})
        response.raise_for_status()
        
        data = response.json()
        print("📋 API Information:")
        print(f"Service Name: {data.get('serviceName', 'N/A')}")
        print(f"Max Record Count: {data.get('maxRecordCount', 'N/A')}")
        print(f"Supported Query Formats: {data.get('supportedQueryFormats', 'N/A')}")
        print(f"Supported Export Formats: {', '.join(data.get('supportedExportFormats', []))}")
        
        # List available layers
        if 'layers' in data:
            print(f"\n🗂️  Available Layers ({len(data['layers'])}):")
            for i, layer in enumerate(data['layers']):
                print(f"  {i}. ID: {layer.get('id')} - {layer.get('name', 'Unnamed')}")
                print(f"     Type: {layer.get('type', 'N/A')}")
                print(f"     Geometry Type: {layer.get('geometryType', 'N/A')}")
                print()
        
        return data
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Error connecting to API: {e}")
        return None

def count_listed_buildings():
    """Count total listed buildings"""
    print("🏛️  Counting Listed Buildings...")
    
    try:
        layer_url = f"{NHLE_BASE_URL}/0/query"
        params = {
            'where': '1=1',
            'returnCountOnly': 'true',
            'f': 'json'
        }
        
        response = requests.get(layer_url, params=params)
        response.raise_for_status()
        data = response.json()
        
        if 'count' in data:
            total_count = data['count']
            print(f"✅ Total listed buildings: {total_count:,}")
            
            # Get count by grade
            grades = ['I', 'II*', 'II']
            grade_counts = {}
            
            for grade in grades:
                params = {
                    'where': f"Grade = '{grade}'",
                    'returnCountOnly': 'true',
                    'f': 'json'
                }
                
                response = requests.get(layer_url, params=params)
                response.raise_for_status()
                data = response.json()
                
                if 'count' in data:
                    grade_counts[grade] = data['count']
                    print(f"  Grade {grade}: {data['count']:,}")
            
            print(f"\n📊 Summary:")
            print(f"Total Listed Buildings: {total_count:,}")
            for grade, count in grade_counts.items():
                percentage = (count / total_count) * 100 if total_count > 0 else 0
                print(f"Grade {grade}: {count:,} ({percentage:.1f}%)")
            
            return total_count, grade_counts
        else:
            print("❌ Count not found in response")
            return None, None
            
    except Exception as e:
        print(f"❌ Error counting buildings: {e}")
        return None, None

def get_sample_buildings(limit=5):
    """Get sample buildings from the API"""
    print(f"\n📦 Getting {limit} sample buildings...")
    
    try:
        layer_url = f"{NHLE_BASE_URL}/0/query"
        params = {
            'where': '1=1',
            'outFields': 'Name,Grade,ListEntry,ListDate,hyperlink,NGR',
            'returnGeometry': 'false',
            'f': 'json',
            'resultRecordCount': limit
        }
        
        response = requests.get(layer_url, params=params)
        response.raise_for_status()
        data = response.json()
        
        if 'features' in data and data['features']:
            print(f"✅ Found {len(data['features'])} sample buildings:")
            
            for i, feature in enumerate(data['features'], 1):
                attrs = feature.get('attributes', {})
                name = attrs.get('Name', 'Unnamed')
                grade = attrs.get('Grade', 'N/A')
                list_entry = attrs.get('ListEntry', 'N/A')
                hyperlink = attrs.get('hyperlink', 'N/A')
                
                print(f"\n  {i}. {name}")
                print(f"     Grade: {grade}")
                print(f"     List Entry: {list_entry}")
                print(f"     NHLE Link: {hyperlink}")
            
            return data['features']
        else:
            print("❌ No buildings found")
            return []
            
    except Exception as e:
        print(f"❌ Error getting sample buildings: {e}")
        return []

def search_buildings(search_term, limit=5):
    """Search for buildings by name"""
    print(f"\n🔍 Searching for '{search_term}'...")
    
    try:
        layer_url = f"{NHLE_BASE_URL}/0/query"
        params = {
            'where': f"UPPER(Name) LIKE UPPER('%{search_term}%')",
            'outFields': 'Name,Grade,ListEntry,hyperlink',
            'returnGeometry': 'false',
            'f': 'json',
            'resultRecordCount': limit
        }
        
        response = requests.get(layer_url, params=params)
        response.raise_for_status()
        data = response.json()
        
        if 'features' in data and data['features']:
            print(f"✅ Found {len(data['features'])} results:")
            
            for i, feature in enumerate(data['features'], 1):
                attrs = feature.get('attributes', {})
                name = attrs.get('Name', 'Unnamed')
                grade = attrs.get('Grade', 'N/A')
                list_entry = attrs.get('ListEntry', 'N/A')
                hyperlink = attrs.get('hyperlink', 'N/A')
                
                print(f"\n  {i}. {name}")
                print(f"     Grade: {grade}")
                print(f"     List Entry: {list_entry}")
                print(f"     NHLE Link: {hyperlink}")
            
            return data['features']
        else:
            print("❌ No results found")
            return []
            
    except Exception as e:
        print(f"❌ Error searching buildings: {e}")
        return []

def main():
    """Main function"""
    print("🏛️  National Heritage List for England (NHLE) API Explorer")
    print("=" * 60)
    
    # Get API info
    api_info = get_api_info()
    if not api_info:
        return
    
    # Count buildings
    total_count, grade_counts = count_listed_buildings()
    
    # Get sample buildings
    sample_buildings = get_sample_buildings(5)
    
    # Search for some examples
    search_buildings("castle", 3)
    search_buildings("church", 3)
    
    print(f"\n" + "=" * 60)
    print("✅ API exploration complete!")
    print(f"\nKey findings:")
    print(f"• {total_count:,} listed buildings available")
    print(f"• 11 different data layers")
    print(f"• Rich search capabilities")
    print(f"• Direct links to detailed pages")

if __name__ == "__main__":
    main()
