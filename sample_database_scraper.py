#!/usr/bin/env python3
"""
Historic England Sample Database Scraper

Fetches a small sample of API data from the Historic England NHLE API and saves it to a SQLite database.
This is perfect for testing and demonstration purposes.

Usage:
    python sample_database_scraper.py [--count 100] [--database sample_historic_england.db]
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import requests
from sqlalchemy import create_engine, text
from tqdm import tqdm

# Import our existing API client
from shared.api_client import NHLEAPIClient


class SampleHistoricEnglandDatabase:
    """Simple database manager for sample Historic England data"""
    
    def __init__(self, db_path: str = "sample_historic_england.db"):
        self.db_path = db_path
        self.engine = create_engine(f"sqlite:///{db_path}")
        self._create_tables()
    
    def _create_tables(self):
        """Create database tables if they don't exist"""
        with self.engine.connect() as conn:
            # Main buildings table
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS buildings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT,
                    grade TEXT,
                    list_entry INTEGER UNIQUE,
                    list_date TEXT,
                    amend_date TEXT,
                    category TEXT,
                    ngr TEXT,
                    easting INTEGER,
                    northing INTEGER,
                    capture_scale TEXT,
                    longitude REAL,
                    latitude REAL,
                    hyperlink TEXT,
                    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            
            # Sample metadata table
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS sample_metadata (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sample_size INTEGER,
                    total_available INTEGER,
                    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            
            conn.commit()
    
    def insert_building(self, building_data: Dict[str, Any]) -> bool:
        """Insert a single building record"""
        try:
            with self.engine.connect() as conn:
                conn.execute(text("""
                    INSERT OR REPLACE INTO buildings 
                    (name, grade, list_entry, list_date, amend_date, category, ngr, 
                     easting, northing, capture_scale, longitude, latitude, hyperlink, scraped_at)
                    VALUES (:name, :grade, :list_entry, :list_date, :amend_date, :category, :ngr, 
                            :easting, :northing, :capture_scale, :longitude, :latitude, :hyperlink, :scraped_at)
                """), {
                    "name": building_data.get('name'),
                    "grade": building_data.get('grade'),
                    "list_entry": building_data.get('list_entry'),
                    "list_date": building_data.get('list_date'),
                    "amend_date": building_data.get('amend_date'),
                    "category": building_data.get('category'),
                    "ngr": building_data.get('ngr'),
                    "easting": building_data.get('easting'),
                    "northing": building_data.get('northing'),
                    "capture_scale": building_data.get('capture_scale'),
                    "longitude": building_data.get('longitude'),
                    "latitude": building_data.get('latitude'),
                    "hyperlink": building_data.get('hyperlink'),
                    "scraped_at": datetime.now().isoformat()
                })
                conn.commit()
                return True
        except Exception as e:
            print(f"❌ Error inserting building {building_data.get('list_entry')}: {e}")
            return False
    
    def save_sample_metadata(self, sample_size: int, total_available: int):
        """Save sample metadata"""
        with self.engine.connect() as conn:
            conn.execute(text("""
                INSERT INTO sample_metadata (sample_size, total_available)
                VALUES (:sample_size, :total_available)
            """), {"sample_size": sample_size, "total_available": total_available})
            conn.commit()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        with self.engine.connect() as conn:
            # Total buildings
            total_buildings = conn.execute(text("SELECT COUNT(*) FROM buildings")).fetchone()[0]
            
            # By grade
            grade_stats = conn.execute(text("""
                SELECT grade, COUNT(*) as count 
                FROM buildings 
                GROUP BY grade 
                ORDER BY count DESC
            """)).fetchall()
            
            # Sample info
            sample_info = conn.execute(text("""
                SELECT sample_size, total_available, scraped_at 
                FROM sample_metadata 
                ORDER BY scraped_at DESC LIMIT 1
            """)).fetchone()
            
            return {
                'total_buildings': total_buildings,
                'grade_distribution': dict(grade_stats),
                'sample_info': sample_info
            }


class SampleDatabaseScraper:
    """Sample scraper for fetching a small amount of API data"""
    
    def __init__(self, db_path: str = "sample_historic_england.db"):
        self.db = SampleHistoricEnglandDatabase(db_path)
        self.api_client = NHLEAPIClient()
        self.base_url = "https://services-eu1.arcgis.com/ZOdPfBS3aqqDYPUQ/arcgis/rest/services/National_Heritage_List_for_England_NHLE_v02_VIEW/FeatureServer/0/query"
    
    def get_total_count(self) -> Optional[int]:
        """Get total count of buildings from API"""
        try:
            params = {
                'where': '1=1',
                'returnCountOnly': 'true',
                'f': 'json'
            }
            
            response = requests.get(self.base_url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            return data.get('count')
        except Exception as e:
            print(f"❌ Error getting total count: {e}")
            return None
    
    def convert_timestamp(self, timestamp_ms: Optional[int]) -> Optional[str]:
        """Convert Unix timestamp in milliseconds to readable date format"""
        if timestamp_ms is None:
            return None
        try:
            dt = datetime.fromtimestamp(timestamp_ms / 1000)
            return dt.strftime('%d-%b-%Y')
        except:
            return None
    
    def fetch_sample(self, count: int) -> Tuple[List[Dict[str, Any]], int]:
        """Fetch a sample of buildings from the API"""
        try:
            params = {
                'where': '1=1',
                'outFields': '*',
                'returnGeometry': 'true',
                'f': 'json',
                'resultRecordCount': count
            }
            
            response = requests.get(self.base_url, params=params, timeout=60)
            response.raise_for_status()
            data = response.json()
            
            if 'features' not in data:
                return [], 0
            
            buildings = []
            for feature in data['features']:
                attrs = feature.get('attributes', {})
                geometry = feature.get('geometry', {})
                
                building = {
                    'name': attrs.get('Name'),
                    'grade': attrs.get('Grade'),
                    'list_entry': attrs.get('ListEntry'),
                    'list_date': self.convert_timestamp(attrs.get('ListDate')),
                    'amend_date': self.convert_timestamp(attrs.get('AmendDate')),
                    'category': attrs.get('Category'),
                    'ngr': attrs.get('NGR'),
                    'easting': attrs.get('Easting'),
                    'northing': attrs.get('Northing'),
                    'capture_scale': attrs.get('CaptureScale'),
                    'longitude': geometry.get('x') if geometry else None,
                    'latitude': geometry.get('y') if geometry else None,
                    'hyperlink': attrs.get('hyperlink')
                }
                buildings.append(building)
            
            return buildings, len(buildings)
            
        except Exception as e:
            print(f"❌ Error fetching sample: {e}")
            return [], 0
    
    def scrape_sample(self, count: int = 100) -> bool:
        """Scrape a sample of data"""
        print("🏛️  Historic England Sample Database Scraper")
        print("=" * 50)
        
        # Get total count
        print("📊 Getting total count...")
        total_count = self.get_total_count()
        if not total_count:
            print("❌ Could not get total count from API")
            return False
        
        print(f"📈 Total buildings available: {total_count:,}")
        print(f"📦 Fetching sample of {count:,} buildings...")
        print()
        
        # Fetch sample
        start_time = time.time()
        buildings, fetched_count = self.fetch_sample(count)
        
        if not buildings:
            print("❌ No data returned from API")
            return False
        
        print(f"✅ Fetched {fetched_count} buildings from API")
        
        # Insert buildings with progress bar
        success_count = 0
        error_count = 0
        
        print("💾 Saving to database...")
        with tqdm(total=len(buildings), desc="Saving buildings", unit="buildings") as pbar:
            for building in buildings:
                if self.db.insert_building(building):
                    success_count += 1
                else:
                    error_count += 1
                pbar.update(1)
        
        # Save sample metadata
        self.db.save_sample_metadata(count, total_count)
        
        elapsed_time = time.time() - start_time
        
        # Print results
        print("\n" + "=" * 50)
        print("📊 SAMPLE RESULTS")
        print("=" * 50)
        print(f"✅ Successfully saved: {success_count:,} buildings")
        print(f"❌ Errors: {error_count:,}")
        print(f"⏱️  Total time: {elapsed_time:.2f} seconds")
        print(f"💾 Database: {self.db.db_path}")
        
        # Database stats
        stats = self.db.get_stats()
        print(f"\n📊 DATABASE STATISTICS:")
        print(f"   Total buildings in DB: {stats['total_buildings']:,}")
        print(f"   Grade distribution:")
        for grade, count in stats['grade_distribution'].items():
            print(f"     {grade}: {count:,}")
        
        if stats['sample_info']:
            sample_size, total_available, scraped_at = stats['sample_info']
            print(f"   Sample size: {sample_size:,} of {total_available:,} total")
            print(f"   Scraped at: {scraped_at}")
        
        return success_count > 0


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Historic England Sample Database Scraper")
    parser.add_argument("--database", "-d", default="sample_historic_england.db", 
                       help="Database file path (default: sample_historic_england.db)")
    parser.add_argument("--count", "-c", type=int, default=100,
                       help="Number of buildings to fetch (default: 100)")
    parser.add_argument("--stats", "-s", action="store_true",
                       help="Show database statistics and exit")
    
    args = parser.parse_args()
    
    # Show stats if requested
    if args.stats:
        db = SampleHistoricEnglandDatabase(args.database)
        stats = db.get_stats()
        print("📊 SAMPLE DATABASE STATISTICS")
        print("=" * 35)
        print(f"Total buildings: {stats['total_buildings']:,}")
        print("Grade distribution:")
        for grade, count in stats['grade_distribution'].items():
            print(f"  {grade}: {count:,}")
        if stats['sample_info']:
            sample_size, total_available, scraped_at = stats['sample_info']
            print(f"Sample: {sample_size:,} of {total_available:,} total")
            print(f"Scraped: {scraped_at}")
        return 0
    
    # Create scraper and run
    scraper = SampleDatabaseScraper(args.database)
    
    try:
        success = scraper.scrape_sample(count=args.count)
        return 0 if success else 1
    except KeyboardInterrupt:
        print("\n⚠️  Interrupted by user")
        return 1
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
