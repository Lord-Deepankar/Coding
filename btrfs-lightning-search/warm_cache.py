#!/usr/bin/env python3

import sqlite3
import sys
import time
import os

def warm_database_cache(db_path="file_index.db"):
    """Pre-warm SQLite cache by reading key data into memory"""
    
    print("🔥 Warming database cache...")
    start_time = time.time()
    
    try:
        # Connect with optimized settings
        conn = sqlite3.connect(db_path)
        conn.execute("PRAGMA cache_size = 50000")  # 200MB cache
        conn.execute("PRAGMA mmap_size = 268435456")  # 256MB memory mapping
        
        # Pre-load critical data
        print("  📊 Loading file statistics...")
        cursor = conn.execute("SELECT COUNT(*) FROM files")
        file_count = cursor.fetchone()[0]
        
        print("  📁 Pre-loading file names...")
        cursor = conn.execute("SELECT name FROM files LIMIT 10000")
        cursor.fetchall()  # Force load into memory
        
        print("  🔍 Warming FTS index...")
        cursor = conn.execute("SELECT rowid FROM files_fts LIMIT 5000")
        cursor.fetchall()
        
        print("  📂 Pre-loading directory data...")
        cursor = conn.execute("SELECT path FROM files WHERE is_dir = 1 LIMIT 1000")
        cursor.fetchall()
        
        # Touch index pages
        print("  🗂️  Touching index pages...")
        cursor = conn.execute("SELECT name FROM files ORDER BY name LIMIT 1000")
        cursor.fetchall()
        
        conn.close()
        
        elapsed = time.time() - start_time
        print(f"✅ Cache warmed successfully!")
        print(f"   Files: {file_count:,}")
        print(f"   Time: {elapsed:.2f}s")
        
        return True
        
    except Exception as e:
        print(f"❌ Cache warming failed: {e}")
        return False

def preload_database_to_memory(db_path="file_index.db"):
    """Load entire database file into OS page cache"""
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found: {db_path}")
        return False
        
    print("💾 Pre-loading database to memory...")
    start_time = time.time()
    
    try:
        # Get file size
        db_size = os.path.getsize(db_path)
        print(f"   Database size: {db_size / (1024*1024):.1f} MB")
        
        # Read entire file to force OS caching
        with open(db_path, 'rb') as f:
            chunk_size = 1024 * 1024  # 1MB chunks
            chunks_read = 0
            
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                chunks_read += 1
                
                # Show progress for large databases
                if chunks_read % 50 == 0:
                    print(f"   Loaded {chunks_read} MB...")
        
        elapsed = time.time() - start_time
        print(f"✅ Database pre-loaded to memory!")
        print(f"   Time: {elapsed:.2f}s")
        print(f"   Speed: {(db_size / (1024*1024)) / elapsed:.1f} MB/s")
        
        return True
        
    except Exception as e:
        print(f"❌ Pre-loading failed: {e}")
        return False

def optimize_system_cache():
    """Optimize Linux system cache settings"""
    
    print("⚙️ Optimizing system cache...")
    
    # Check available memory
    try:
        with open('/proc/meminfo', 'r') as f:
            lines = f.readlines()
            
        memory_info = {}
        for line in lines:
            if 'MemTotal' in line or 'MemAvailable' in line or 'Cached' in line:
                key, value = line.split(':')
                memory_info[key.strip()] = int(value.strip().split()[0]) * 1024
        
        total_mb = memory_info.get('MemTotal', 0) // (1024*1024)
        available_mb = memory_info.get('MemAvailable', 0) // (1024*1024)
        cached_mb = memory_info.get('Cached', 0) // (1024*1024)
        
        print(f"   Total RAM: {total_mb:,} MB")
        print(f"   Available: {available_mb:,} MB") 
        print(f"   Currently cached: {cached_mb:,} MB")
        
        # Recommendations
        if available_mb > 1000:
            print("✅ Sufficient memory for database caching")
        else:
            print("⚠️  Limited memory - cache warming may be slower")
            
    except Exception as e:
        print(f"⚠️  Could not read memory info: {e}")

def main():
    """Main cache warming function"""
    
    print("🚀 Database Cache Optimizer")
    print("=" * 40)
    
    db_path = sys.argv[1] if len(sys.argv) > 1 else "file_index.db"
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found: {db_path}")
        print("Usage: python3 warm_cache.py [database_path]")
        return 1
    
    # Show system info
    optimize_system_cache()
    print()
    
    # Warm the cache
    success1 = preload_database_to_memory(db_path)
    print()
    success2 = warm_database_cache(db_path)
    
    if success1 and success2:
        print()
        print("🎉 Cache optimization complete!")
        print("   Your next searches should be lightning fast!")
        print()
        print("💡 To maintain performance:")
        print("   - Add to startup: python3 warm_cache.py")
        print("   - Run periodically: */30 * * * * /path/to/warm_cache.py")
        return 0
    else:
        return 1

if __name__ == "__main__":
    sys.exit(main())
