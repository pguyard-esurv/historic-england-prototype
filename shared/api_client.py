#!/usr/bin/env python3
"""
Shared API client for Historic England NHLE API
"""

import random
import time
from typing import Any, Dict, List, Optional, Tuple

import requests

# NHLE API endpoint
NHLE_BASE_URL = "https://services-eu1.arcgis.com/ZOdPfBS3aqqDYPUQ/arcgis/rest/services/National_Heritage_List_for_England_NHLE_v02_VIEW/FeatureServer"

class NHLEAPIClient:
    """Client for interacting with the Historic England NHLE API"""
    
    def __init__(self):
        self.base_url = NHLE_BASE_URL
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
    
    def get_api_info(self) -> Optional[Dict[str, Any]]:
        """Get basic information about the API"""
        try:
            response = self.session.get(self.base_url, params={'f': 'json'})
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"❌ Error getting API info: {e}")
            return None
    
    def count_buildings(self) -> Tuple[Optional[int], Optional[Dict[str, int]]]:
        """Count total listed buildings and by grade"""
        try:
            layer_url = f"{self.base_url}/0/query"
            params = {
                'where': '1=1',
                'returnCountOnly': 'true',
                'f': 'json'
            }
            
            response = self.session.get(layer_url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if 'count' not in data:
                return None, None
            
            total_count = data['count']
            
            # Get count by grade
            grades = ['I', 'II*', 'II']
            grade_counts = {}
            
            for grade in grades:
                params = {
                    'where': f"Grade = '{grade}'",
                    'returnCountOnly': 'true',
                    'f': 'json'
                }
                
                response = self.session.get(layer_url, params=params)
                response.raise_for_status()
                data = response.json()
                
                if 'count' in data:
                    grade_counts[grade] = data['count']
            
            return total_count, grade_counts
            
        except Exception as e:
            print(f"❌ Error counting buildings: {e}")
            return None, None
    
    def get_buildings(self, count: int = 5, fields: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Get buildings from the API"""
        if fields is None:
            fields = ['Name', 'Grade', 'ListEntry', 'ListDate', 'hyperlink', 'NGR', 'Easting', 'Northing', 'AmendDate', 'CaptureScale']
        
        try:
            layer_url = f"{self.base_url}/0/query"
            params = {
                'where': '1=1',
                'outFields': ','.join(fields),
                'returnGeometry': 'false',
                'f': 'json',
                'resultRecordCount': count
            }
            
            response = self.session.get(layer_url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if 'features' not in data or not data['features']:
                return []
            
            buildings = []
            for feature in data['features']:
                attrs = feature.get('attributes', {})
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
                buildings.append(building)
            
            return buildings
            
        except Exception as e:
            print(f"❌ Error getting buildings: {e}")
            return []
    
    def get_random_building(self, fields: Optional[List[str]] = None) -> Optional[Dict[str, Any]]:
        """Get a random building from the API"""
        buildings = self.get_buildings(5, fields)
        return random.choice(buildings) if buildings else None
    
    def search_buildings(self, search_term: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Search for buildings by name"""
        try:
            layer_url = f"{self.base_url}/0/query"
            params = {
                'where': f"UPPER(Name) LIKE UPPER('%{search_term}%')",
                'outFields': 'Name,Grade,ListEntry,hyperlink',
                'returnGeometry': 'false',
                'f': 'json',
                'resultRecordCount': limit
            }
            
            response = self.session.get(layer_url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if 'features' not in data or not data['features']:
                return []
            
            buildings = []
            for feature in data['features']:
                attrs = feature.get('attributes', {})
                building = {
                    'name': attrs.get('Name', 'Unnamed'),
                    'grade': attrs.get('Grade', 'N/A'),
                    'list_entry': attrs.get('ListEntry', 'N/A'),
                    'hyperlink': attrs.get('hyperlink', '')
                }
                buildings.append(building)
            
            return buildings
            
        except Exception as e:
            print(f"❌ Error searching buildings: {e}")
            return []
    
    def get_all_fields(self) -> List[str]:
        """Get all available fields from the API"""
        try:
            layer_url = f"{self.base_url}/0/query"
            params = {
                'where': '1=1',
                'outFields': '*',
                'returnGeometry': 'false',
                'f': 'json',
                'resultRecordCount': 1
            }
            
            response = self.session.get(layer_url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if 'features' in data and data['features']:
                return list(data['features'][0].get('attributes', {}).keys())
            
            return []
            
        except Exception as e:
            print(f"❌ Error getting fields: {e}")
            return []
