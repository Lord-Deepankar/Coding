#!/usr/bin/env python3

import sqlite3
import sys
import os
import time
import argparse
from pathlib import Path

class OptimizedFileSearch:
    def __init__(self, db_path="file_index.db"):
        self.db_path = db_path
        if not os.path.exists(db_path):
            print(f"Error: Database '{db_path}' not found. Run indexer first.")
            sys.exit(1)
        
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row  # For named column access
        
        # Advanced performance optimizations
        self.optimize_performance()
        
    def optimize_performance(self):
        """Apply advanced SQLite performance optimizations"""
        
        # Memory optimizations
        self.conn.execute("PRAGMA cache_size = 50000")      # 200MB cache
        self.conn.execute("PRAGMA temp_store = MEMORY")     # Keep temp data in memory
        self.conn.execute("PRAGMA mmap_size = 268435456")   # 256MB memory mapping
        
        # I/O optimizations
        self.conn.execute("PRAGMA synchronous = NORMAL")    # Faster writes
        self.conn.execute("PRAGMA journal_mode = WAL")      # Write-ahead logging
        
        # Query optimizations
        self.conn.execute("PRAGMA optimize")                # Optimize query planner
        
        # Pre-warm critical queries
        self.prewarm_cache()
        
    def prewarm_cache(self):
        """Pre-warm database cache with common queries"""
        try:
            # Touch main indexes
            self.conn.execute("SELECT COUNT(*) FROM files").fetchone()
            
            # Touch name index
            self.conn.execute("SELECT name FROM files LIMIT 100").fetchall()
            
            # Touch FTS index  
            self.conn.execute("SELECT rowid FROM files_fts LIMIT 100").fetchall()
            
        except Exception:
            pass  # Silently ignore prewarming errors
    
    def search_smart(self, query, limit=100, dirs_only=False, files_only=False):
        """Intelligent search that chooses the best strategy"""
        
        # Choose search strategy based on query
        if len(query) <= 2:
            # Short queries: use prefix search
            return self.search_prefix(query, limit, dirs_only, files_only)
        elif query.startswith('*') or query.endswith('*'):
            # Wildcard queries: use pattern matching
            return self.search_pattern(query, limit, dirs_only, files_only)
        else:
            # Try FTS first (fastest), fallback to substring
            try:
                results = self.search_fts(query, limit)
                if results:
                    return results
            except:
                pass
            return self.search_substring(query, limit, dirs_only, files_only)
    
    def search_prefix(self, query, limit=100, dirs_only=False, files_only=False):
        """Optimized prefix search"""
        conditions = ["name >= ? AND name < ? || 'z'"]  # Range query for index
        params = [query, query]
        
        if dirs_only:
            conditions.append("is_dir = 1")
        elif files_only:
            conditions.append("is_dir = 0")
        
        sql = f"""
            SELECT path, name, size, mtime, is_dir, inode
            FROM files 
            WHERE {' AND '.join(conditions)}
            ORDER BY name
            LIMIT ?
        """
        
        params.append(limit)
        return self.conn.execute(sql, params).fetchall()
    
    def search_pattern(self, query, limit=100, dirs_only=False, files_only=False):
        """Pattern/wildcard search"""
        # Convert shell-style wildcards to SQL LIKE
        sql_pattern = query.replace('*', '%').replace('?', '_')
        
        conditions = ["name LIKE ?"]
        params = [sql_pattern]
        
        if dirs_only:
            conditions.append("is_dir = 1")
        elif files_only:
            conditions.append("is_dir = 0")
        
        sql = f"""
            SELECT path, name, size, mtime, is_dir, inode
            FROM files 
            WHERE {' AND '.join(conditions)}
            ORDER BY length(name), name
            LIMIT ?
        """
        
        params.append(limit)
        return self.conn.execute(sql, params).fetchall()
    
    def search_substring(self, query, limit=100, dirs_only=False, files_only=False):
        """Substring search with optimization"""
        conditions = ["name LIKE '%' || ? || '%'"]
        params = [query]
        
        if dirs_only:
            conditions.append("is_dir = 1")
        elif files_only:
            conditions.append("is_dir = 0")
        
        sql = f"""
            SELECT path, name, size, mtime, is_dir, inode
            FROM files 
            WHERE {' AND '.join(conditions)}
            ORDER BY 
                CASE WHEN name LIKE ? || '%' THEN 1 ELSE 2 END,
                length(name),
                name
            LIMIT ?
        """
        
        params.extend([query, limit])
        return self.conn.execute(sql, params).fetchall()
    
    def search_fts(self, query, limit=100):
        """Full-text search using FTS5"""
        # Optimize FTS query
        fts_query = query.replace("*", "").replace("?", "")  # Clean wildcards
        
        sql = """
            SELECT f.path, f.name, f.size, f.mtime, f.is_dir, f.inode
            FROM files_fts fts
            JOIN files f ON f.id = fts.rowid
            WHERE files_fts MATCH ?
            ORDER BY bm25(files_fts)
            LIMIT ?
        """
        return self.conn.execute(sql, [fts_query, limit]).fetchall()
    
    def search_by_size(self, min_size=None, max_size=None, limit=100):
        """Size-based search with index optimization"""
        conditions = ["is_dir = 0"]  # Only files have meaningful sizes
        params = []
        
        if min_size is not None:
            conditions.append("size >= ?")
            params.append(min_size)
        
        if max_size is not None:
            conditions.append("size <= ?")
            params.append(max_size)
        
        sql = f"""
            SELECT path, name, size, mtime, is_dir, inode
            FROM files 
            WHERE {' AND '.join(conditions)}
            ORDER BY size DESC
            LIMIT ?
        """
        params.append(limit)
        return self.conn.execute(sql, params).fetchall()
    
    def search_recent(self, days=7, limit=100):
        """Recent files search with date index"""
        from datetime import datetime, timedelta
        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
        
        sql = """
            SELECT path, name, size, mtime, is_dir, inode
            FROM files 
            WHERE mtime >= ? AND is_dir = 0
            ORDER BY mtime DESC
            LIMIT ?
        """
        return self.conn.execute(sql, [cutoff_date, limit]).fetchall()
    
    def get_stats(self):
        """Database statistics"""
        cursor = self.conn.execute("""
            SELECT 
                COUNT(*) as total,
                COUNT(CASE WHEN is_dir = 1 THEN 1 END) as dirs,
                COUNT(CASE WHEN is_dir = 0 THEN 1 END) as files,
                SUM(CASE WHEN is_dir = 0 THEN size ELSE 0 END) as total_size
            FROM files
        """)
        return cursor.fetchone()
    
    def get_memory_stats(self):
        """Get memory usage statistics"""
        try:
            cursor = self.conn.execute("PRAGMA cache_size")
            cache_size = cursor.fetchone()[0]
            
            cursor = self.conn.execute("PRAGMA page_count")
            page_count = cursor.fetchone()[0]
            
            cursor = self.conn.execute("PRAGMA page_size")
            page_size = cursor.fetchone()[0]
            
            db_size_mb = (page_count * page_size) / (1024 * 1024)
            cache_size_mb = (cache_size * page_size) / (1024 * 1024)
            
            return {
                'cache_size_mb': cache_size_mb,
                'db_size_mb': db_size_mb,
                'cache_ratio': (cache_size_mb / db_size_mb) * 100 if db_size_mb > 0 else 0
            }
        except:
            return {}
    
    def format_size(self, size):
        """Format file size in human-readable format"""
        if size < 1024:
            return f"{size} B"
        elif size < 1024**2:
            return f"{size/1024:.1f} KB"
        elif size < 1024**3:
            return f"{size/(1024**2):.1f} MB"
        else:
            return f"{size/(1024**3):.2f} GB"
    
    def format_time(self, iso_time):
        """Format ISO timestamp"""
        try:
            from datetime import datetime
            dt = datetime.fromisoformat(iso_time.replace('Z', '+00:00'))
            return dt.strftime('%Y-%m-%d %H:%M')
        except:
            return iso_time[:16]  # Fallback
    
    def display_results(self, results, show_details=False, show_performance=False):
        """Display search results with optional performance info"""
        if not results:
            print("No results found.")
            return
        
        print(f"\nFound {len(results)} results:")
        print("-" * 80)
        
        for i, row in enumerate(results, 1):
            path = row['path']
            name = row['name']
            size = row['size']
            mtime = row['mtime']
            is_dir = row['is_dir']
            
            # Icon for file type
            icon = "📁" if is_dir else "📄"
            
            if show_details:
                size_str = "DIR" if is_dir else self.format_size(size)
                time_str = self.format_time(mtime)
                print(f"{i:3d}. {icon} {path}")
                print(f"     Size: {size_str:>10} | Modified: {time_str}")
            else:
                print(f"{i:3d}. {icon} {path}")
        
        if show_performance:
            mem_stats = self.get_memory_stats()
            if mem_stats:
                print(f"\n📊 Performance Info:")
                print(f"   Cache: {mem_stats.get('cache_size_mb', 0):.1f} MB")
                print(f"   Database: {mem_stats.get('db_size_mb', 0):.1f} MB")
                print(f"   Cache ratio: {mem_stats.get('cache_ratio', 0):.1f}%")

def parse_size(size_str):
    """Parse size string like '100MB' into bytes"""
    if not size_str:
        return None
    
    size_str = size_str.upper()
    multipliers = {'B': 1, 'KB': 1024, 'MB': 1024**2, 'GB': 1024**3}
    
    for unit, mult in multipliers.items():
        if size_str.endswith(unit):
            try:
                return int(float(size_str[:-len(unit)]) * mult)
            except ValueError:
                break
    
    try:
        return int(size_str)
    except ValueError:
        return None

def interactive_mode(searcher):
    """Interactive search mode"""
    print("🔍 Interactive Search Mode")
    print("Commands: .stats, .memory, .exit")
    print("-" * 40)
    
    while True:
        try:
            query = input("\nSearch> ").strip()
            
            if not query:
                continue
                
            if query in ['.exit', '.quit', 'exit', 'quit']:
                break
            elif query == '.stats':
                stats = searcher.get_stats()
                print(f"\nDatabase Statistics:")
                print(f"  Total entries: {stats['total']:,}")
                print(f"  Directories: {stats['dirs']:,}")
                print(f"  Files: {stats['files']:,}")
                if stats['total_size']:
                    print(f"  Total size: {searcher.format_size(stats['total_size'])}")
                continue
            elif query == '.memory':
                mem_stats = searcher.get_memory_stats()
                print(f"\nMemory Statistics:")
                print(f"  Cache size: {mem_stats.get('cache_size_mb', 0):.1f} MB")
                print(f"  Database size: {mem_stats.get('db_size_mb', 0):.1f} MB")
                print(f"  Cache ratio: {mem_stats.get('cache_ratio', 0):.1f}%")
                continue
            
            # Perform search with timing
            start_time = time.time()
            results = searcher.search_smart(query, limit=50)
            search_time = time.time() - start_time
            
            searcher.display_results(results, show_details=False)
            print(f"\nSearch completed in {search_time*1000:.1f}ms")
            
        except (KeyboardInterrupt, EOFError):
            break
    
    print("\nGoodbye!")

def main():
    parser = argparse.ArgumentParser(description="Optimized file search using Btrfs metadata")
    parser.add_argument("query", nargs="?", help="Search query")
    parser.add_argument("-d", "--database", default="file_index.db", help="Database path")
    parser.add_argument("-l", "--limit", type=int, default=100, help="Result limit")
    parser.add_argument("--dirs-only", action="store_true", help="Search directories only")
    parser.add_argument("--files-only", action="store_true", help="Search files only")
    parser.add_argument("-p", "--path", action="store_true", help="Search in full paths")
    parser.add_argument("-s", "--substring", action="store_true", help="Force substring search")
    parser.add_argument("--size-min", help="Minimum file size (e.g., 10MB)")
    parser.add_argument("--size-max", help="Maximum file size (e.g., 1GB)")
    parser.add_argument("--recent", type=int, help="Files modified in last N days")
    parser.add_argument("--stats", action="store_true", help="Show database statistics")
    parser.add_argument("--memory", action="store_true", help="Show memory statistics")
    parser.add_argument("--details", action="store_true", help="Show detailed results")
    parser.add_argument("--performance", action="store_true", help="Show performance info")
    parser.add_argument("--interactive", "-i", action="store_true", help="Interactive mode")
    parser.add_argument("--warm-cache", action="store_true", help="Pre-warm database cache")
    
    args = parser.parse_args()
    
    # Initialize optimized searcher
    searcher = OptimizedFileSearch(args.database)
    
    # Warm cache if requested
    if args.warm_cache:
        print("🔥 Warming database cache...")
        start_time = time.time()
        searcher.prewarm_cache()
        warm_time = time.time() - start_time
        print(f"Cache warmed in {warm_time*1000:.1f}ms")
    
    # Interactive mode
    if args.interactive:
        interactive_mode(searcher)
        return
    
    # Statistics
    if args.stats:
        stats = searcher.get_stats()
        print(f"Database Statistics:")
        print(f"  Total entries: {stats['total']:,}")
        print(f"  Directories: {stats['dirs']:,}")
        print(f"  Files: {stats['files']:,}")
        if stats['total_size']:
            print(f"  Total size: {searcher.format_size(stats['total_size'])}")
        return
    
    # Memory statistics
    if args.memory:
        mem_stats = searcher.get_memory_stats()
        print(f"Memory Statistics:")
        print(f"  Cache size: {mem_stats.get('cache_size_mb', 0):.1f} MB")
        print(f"  Database size: {mem_stats.get('db_size_mb', 0):.1f} MB")
        print(f"  Cache ratio: {mem_stats.get('cache_ratio', 0):.1f}%")
        return
    
    if not args.query:
        parser.print_help()
        return
    
    # Perform search with timing
    start_time = time.time()
    
    if args.recent:
        results = searcher.search_recent(args.recent, args.limit)
    elif args.size_min or args.size_max:
        min_size = parse_size(args.size_min)
        max_size = parse_size(args.size_max)
        results = searcher.search_by_size(min_size, max_size, args.limit)
    else:
        results = searcher.search_smart(args.query, args.limit, args.dirs_only, args.files_only)
    
    search_time = time.time() - start_time
    
    # Display results
    searcher.display_results(results, args.details, args.performance)
    print(f"\nSearch completed in {search_time*1000:.1f}ms")

if __name__ == "__main__":
    main()
