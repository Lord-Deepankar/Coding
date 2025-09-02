#!/usr/bin/env python3

import json
import sqlite3
import sys
import os
import time
from datetime import datetime
from pathlib import Path

class FileIndexer:
    def __init__(self, db_path="file_index.db"):
        self.db_path = db_path
        self.conn = None
        self.setup_database()
    
    def setup_database(self):
        """Initialize the SQLite database with optimized schema"""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.execute("PRAGMA journal_mode = WAL")
        self.conn.execute("PRAGMA synchronous = NORMAL")
        self.conn.execute("PRAGMA cache_size = 10000")
        self.conn.execute("PRAGMA temp_store = MEMORY")
        
        # Create main files table
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS files (
                id INTEGER PRIMARY KEY,
                path TEXT NOT NULL,
                name TEXT NOT NULL,
                inode INTEGER,
                size INTEGER,
                mtime TEXT,
                mode INTEGER,
                is_dir BOOLEAN,
                indexed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create indexes for fast searching
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_name ON files(name)")
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_path ON files(path)")
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_name_prefix ON files(name)")
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_size ON files(size)")
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_mtime ON files(mtime)")
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_is_dir ON files(is_dir)")
        
        # Create FTS (Full Text Search) virtual table for instant search
        self.conn.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS files_fts USING fts5(
                name, path, 
                content='files',
                content_rowid='id'
            )
        """)
        
        # Create metadata table
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS metadata (
                key TEXT PRIMARY KEY,
                value TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        self.conn.commit()
        print(f"Database initialized: {self.db_path}")
    
    def clear_database(self):
        """Clear existing data"""
        print("Clearing existing data...")
        self.conn.execute("DELETE FROM files")
        self.conn.execute("DELETE FROM files_fts")
        self.conn.execute("DELETE FROM metadata WHERE key != 'db_version'")
        self.conn.commit()
    
    def process_json_file(self, json_file_path):
        """Process the JSON file from btrfs-indexer"""
        print(f"Processing {json_file_path}...")
        
        try:
            with open(json_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON file: {e}")
            return False
        except FileNotFoundError:
            print(f"Error: File not found: {json_file_path}")
            return False
        
        if 'files' not in data:
            print("Error: No 'files' key found in JSON")
            return False
        
        files = data['files']
        metadata = data.get('metadata', {})
        
        print(f"Found {len(files)} files to index")
        
        # Store metadata
        for key, value in metadata.items():
            self.conn.execute(
                "INSERT OR REPLACE INTO metadata (key, value) VALUES (?, ?)",
                (key, str(value))
            )
        
        # Process files in batches for better performance
        batch_size = 1000
        total_files = len(files)
        
        for i in range(0, total_files, batch_size):
            batch = files[i:i + batch_size]
            self.process_batch(batch)
            
            progress = min(i + batch_size, total_files)
            print(f"\rProcessed {progress}/{total_files} files ({progress/total_files*100:.1f}%)", end='', flush=True)
        
        print(f"\nCompleted indexing {total_files} files")
        self.conn.commit()
        return True
    
    def process_batch(self, files_batch):
        """Process a batch of files"""
        # Prepare data for batch insert
        file_data = []
        fts_data = []
        
        for file_info in files_batch:
            try:
                path = file_info.get('path', '')
                name = file_info.get('name', '')
                inode = file_info.get('inode', 0)
                size = file_info.get('size', 0)
                mtime = file_info.get('mtime', '')
                mode = file_info.get('mode', 0)
                is_dir = file_info.get('is_dir', False)
                
                file_data.append((path, name, inode, size, mtime, mode, is_dir))
                
            except Exception as e:
                print(f"\nError processing file entry: {e}")
                continue
        
        # Batch insert into files table
        self.conn.executemany("""
            INSERT INTO files (path, name, inode, size, mtime, mode, is_dir)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, file_data)
        
        # Update FTS index
        self.conn.execute("INSERT INTO files_fts(files_fts) VALUES('rebuild')")
    
    def create_additional_indexes(self):
        """Create additional indexes for performance"""
        print("Creating additional performance indexes...")
        
        # Trigram indexes for partial matching (if supported)
        try:
            self.conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_name_trigram 
                ON files(name) WHERE length(name) >= 3
            """)
        except:
            pass
        
        # Composite indexes
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_dir_name ON files(is_dir, name)")
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_size_name ON files(size, name)")
        
        self.conn.commit()
        print("Additional indexes created")
    
    def update_statistics(self):
        """Update database statistics"""
        cursor = self.conn.execute("""
            SELECT 
                COUNT(*) as total_files,
                COUNT(CASE WHEN is_dir = 1 THEN 1 END) as directories,
                COUNT(CASE WHEN is_dir = 0 THEN 1 END) as files,
                SUM(size) as total_size,
                MAX(mtime) as latest_mtime
            FROM files
        """)
        
        stats = cursor.fetchone()
        if stats:
            print(f"\nDatabase Statistics:")
            print(f"  Total entries: {stats[0]:,}")
            print(f"  Directories: {stats[1]:,}")
            print(f"  Files: {stats[2]:,}")
            print(f"  Total size: {stats[3]:,} bytes ({stats[3]/(1024**3):.2f} GB)")
            print(f"  Latest file: {stats[4]}")
        
        # Store stats in metadata
        self.conn.execute("INSERT OR REPLACE INTO metadata (key, value) VALUES (?, ?)",
                         ("last_index_time", datetime.now().isoformat()))
        self.conn.execute("INSERT OR REPLACE INTO metadata (key, value) VALUES (?, ?)",
                         ("total_files", str(stats[0])))
        self.conn.commit()
    
    def optimize_database(self):
        """Optimize database for faster searches"""
        print("Optimizing database...")
        self.conn.execute("ANALYZE")
        self.conn.execute("VACUUM")
        self.conn.commit()
        print("Database optimization complete")
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 indexer.py <json_file> [db_file]")
        print("Example: python3 indexer.py files.json file_index.db")
        sys.exit(1)
    
    json_file = sys.argv[1]
    db_file = sys.argv[2] if len(sys.argv) > 2 else "file_index.db"
    
    if not os.path.exists(json_file):
        print(f"Error: JSON file '{json_file}' not found")
        sys.exit(1)
    
    print("File Indexer - Building database from Btrfs metadata")
    print("=" * 50)
    
    start_time = time.time()
    
    try:
        # Initialize indexer
        indexer = FileIndexer(db_file)
        
        # Clear existing data
        indexer.clear_database()
        
        # Process the JSON file
        if indexer.process_json_file(json_file):
            # Create additional indexes
            indexer.create_additional_indexes()
            
            # Update statistics
            indexer.update_statistics()
            
            # Optimize database
            indexer.optimize_database()
            
            end_time = time.time()
            print(f"\nIndexing completed in {end_time - start_time:.2f} seconds")
            print(f"Database saved as: {db_file}")
            print(f"Database size: {os.path.getsize(db_file) / (1024*1024):.2f} MB")
        
        indexer.close()
        
    except KeyboardInterrupt:
        print("\nIndexing interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"Error during indexing: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()