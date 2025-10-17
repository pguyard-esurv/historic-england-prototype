#!/usr/bin/env python3
"""
Historic England Database Scraper

Fetches all available API data from the Historic England NHLE API and saves it to a SQLite database.

This script:
1. Connects to the NHLE API
2. Fetches all available buildings in batches
3. Saves the data to a SQLite database with proper schema
4. Provides progress tracking and error handling
5. Supports resuming interrupted downloads

Usage:
    python database_scraper.py [--batch-size 1000] [--database historic_england.db] [--resume]
"""

import argparse
import json
import os
import sqlite3
import sys
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import requests
from sqlalchemy import create_engine, text
from tqdm import tqdm

# Import our existing API client
from shared.api_client import NHLEAPIClient


class HistoricEnglandDatabase:
    """Database manager for Historic England data"""
    
    def __init__(self, db_path: str = "historic_england.db"):
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
            
            # API metadata table for tracking
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS api_metadata (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    total_count INTEGER,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    batch_size INTEGER,
                    status TEXT
                )
            """))
            
            # Scraping progress table
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS scraping_progress (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    batch_start INTEGER,
                    batch_end INTEGER,
                    records_processed INTEGER,
                    success_count INTEGER,
                    error_count INTEGER,
                    started_at TIMESTAMP,
                    completed_at TIMESTAMP,
                    status TEXT
                )
            """))
            
            conn.commit()
    
    def get_total_count(self) -> Optional[int]:
        """Get total count from database metadata"""
        with self.engine.connect() as conn:
            result = conn.execute(text("""
                SELECT total_count FROM api_metadata 
                ORDER BY last_updated DESC LIMIT 1
            """)).fetchone()
            return result[0] if result else None
    
    def update_metadata(self, total_count: int, batch_size: int, status: str):
        """Update API metadata"""
        with self.engine.connect() as conn:
            conn.execute(text("""
                INSERT INTO api_metadata (total_count, batch_size, status)
                VALUES (:total_count, :batch_size, :status)
            """), {"total_count": total_count, "batch_size": batch_size, "status": status})
            conn.commit()
    
    def get_last_processed_offset(self) -> int:
        """Get the last successfully processed offset"""
        with self.engine.connect() as conn:
            result = conn.execute(text("""
                SELECT MAX(batch_end) FROM scraping_progress 
                WHERE status = 'completed'
            """)).fetchone()
            return result[0] if result[0] else 0
    
    def start_batch(self, batch_start: int, batch_end: int) -> int:
        """Start tracking a new batch"""
        with self.engine.connect() as conn:
            result =             conn.execute(text("""
                INSERT INTO scraping_progress 
                (batch_start, batch_end, records_processed, success_count, error_count, started_at, status)
                VALUES (:batch_start, :batch_end, 0, 0, 0, CURRENT_TIMESTAMP, 'in_progress')
            """), {"batch_start": batch_start, "batch_end": batch_end})
            conn.commit()
            return result.lastrowid
    
    def complete_batch(self, batch_id: int, records_processed: int, success_count: int, error_count: int):
        """Mark a batch as completed"""
        with self.engine.connect() as conn:
            conn.execute(text("""
                UPDATE scraping_progress 
                SET records_processed = :records_processed, success_count = :success_count, error_count = :error_count, 
                    completed_at = CURRENT_TIMESTAMP, status = 'completed'
                WHERE id = :batch_id
            """), {"records_processed": records_processed, "success_count": success_count, "error_count": error_count, "batch_id": batch_id})
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
            
            # Recent activity
            recent_activity = conn.execute(text("""
                SELECT COUNT(*) FROM buildings 
                WHERE created_at > datetime('now', '-1 day')
            """)).fetchone()[0]
            
            return {
                'total_buildings': total_buildings,
                'grade_distribution': dict(grade_stats),
                'recent_activity': recent_activity
            }


class DatabaseScraper:
    """Main scraper class for fetching all API data to database"""
    
    def __init__(self, db_path: str = "historic_england.db", batch_size: int = 1000):
        self.db = HistoricEnglandDatabase(db_path)
        self.api_client = NHLEAPIClient()
        self.batch_size = batch_size
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
    
    def fetch_batch(self, offset: int, limit: int) -> Tuple[List[Dict[str, Any]], int]:
        """Fetch a batch of buildings from the API"""
        try:
            params = {
                'where': '1=1',
                'outFields': '*',
                'returnGeometry': 'true',
                'f': 'json',
                'resultOffset': offset,
                'resultRecordCount': limit
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
            print(f"❌ Error fetching batch at offset {offset}: {e}")
            return [], 0
    
    def scrape_all(self, resume: bool = False) -> bool:
        """Scrape all available data"""
        print("🏛️  Historic England Database Scraper")
        print("=" * 50)
        
        # Get total count
        print("📊 Getting total count...")
        total_count = self.get_total_count()
        if not total_count:
            print("❌ Could not get total count from API")
            return False
        
        print(f"📈 Total buildings available: {total_count:,}")
        
        # Update metadata
        self.db.update_metadata(total_count, self.batch_size, 'in_progress')
        
        # Determine starting point
        start_offset = 0
        if resume:
            start_offset = self.db.get_last_processed_offset()
            print(f"🔄 Resuming from offset: {start_offset:,}")
        
        # Calculate total batches
        total_batches = (total_count - start_offset + self.batch_size - 1) // self.batch_size
        
        print(f"📦 Processing {total_batches:,} batches of {self.batch_size:,} records each")
        print(f"🚀 Starting from offset {start_offset:,}")
        print()
        
        # Process batches
        success_count = 0
        error_count = 0
        processed_count = 0
        
        with tqdm(total=total_count - start_offset, desc="Processing buildings", unit="buildings") as pbar:
            for batch_num in range(total_batches):
                batch_start = start_offset + (batch_num * self.batch_size)
                batch_end = min(batch_start + self.batch_size - 1, total_count - 1)
                
                # Start tracking this batch
                batch_id = self.db.start_batch(batch_start, batch_end)
                
                # Fetch batch
                buildings, fetched_count = self.fetch_batch(batch_start, self.batch_size)
                
                if not buildings:
                    print(f"⚠️  No data returned for batch {batch_num + 1}")
                    self.db.complete_batch(batch_id, 0, 0, 1)
                    error_count += 1
                    continue
                
                # Insert buildings
                batch_success = 0
                batch_errors = 0
                
                for building in buildings:
                    if self.db.insert_building(building):
                        batch_success += 1
                        success_count += 1
                    else:
                        batch_errors += 1
                        error_count += 1
                    
                    processed_count += 1
                    pbar.update(1)
                
                # Complete batch tracking
                self.db.complete_batch(batch_id, fetched_count, batch_success, batch_errors)
                
                # Progress update
                if (batch_num + 1) % 10 == 0:
                    print(f"📊 Batch {batch_num + 1}/{total_batches}: {batch_success} success, {batch_errors} errors")
                
                # Small delay to be respectful to the API
                time.sleep(0.1)
        
        # Update final metadata
        self.db.update_metadata(total_count, self.batch_size, 'completed')
        
        # Print final stats
        print("\n" + "=" * 50)
        print("📊 FINAL STATISTICS")
        print("=" * 50)
        print(f"✅ Successfully processed: {success_count:,} buildings")
        print(f"❌ Errors: {error_count:,}")
        print(f"📈 Total processed: {processed_count:,}")
        print(f"💾 Database: {self.db.db_path}")
        
        # Database stats
        stats = self.db.get_stats()
        print(f"\n📊 DATABASE STATISTICS:")
        print(f"   Total buildings in DB: {stats['total_buildings']:,}")
        print(f"   Grade distribution:")
        for grade, count in stats['grade_distribution'].items():
            print(f"     {grade}: {count:,}")
        print(f"   Recent activity (last 24h): {stats['recent_activity']:,}")
        
        return success_count > 0


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Historic England Database Scraper")
    parser.add_argument("--database", "-d", default="historic_england.db", 
                       help="Database file path (default: historic_england.db)")
    parser.add_argument("--batch-size", "-b", type=int, default=1000,
                       help="Batch size for API requests (default: 1000)")
    parser.add_argument("--resume", "-r", action="store_true",
                       help="Resume from last processed offset")
    parser.add_argument("--stats", "-s", action="store_true",
                       help="Show database statistics and exit")
    
    args = parser.parse_args()
    
    # Show stats if requested
    if args.stats:
        db = HistoricEnglandDatabase(args.database)
        stats = db.get_stats()
        print("📊 DATABASE STATISTICS")
        print("=" * 30)
        print(f"Total buildings: {stats['total_buildings']:,}")
        print("Grade distribution:")
        for grade, count in stats['grade_distribution'].items():
            print(f"  {grade}: {count:,}")
        print(f"Recent activity: {stats['recent_activity']:,}")
        return 0
    
    # Create scraper and run
    scraper = DatabaseScraper(args.database, args.batch_size)
    
    try:
        success = scraper.scrape_all(resume=args.resume)
        return 0 if success else 1
    except KeyboardInterrupt:
        print("\n⚠️  Interrupted by user")
        return 1
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
