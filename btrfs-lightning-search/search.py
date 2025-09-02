#!/usr/bin/env python3

import sqlite3
import sys
import os
import time
import argparse
from pathlib import Path

class FileSearch:
    def __init__(self, db_path="file_index.db"):
        self.db_path = db_path
        if not os.path.exists(db_path):
            print(f"Error: Database '{db_path}' not found. Run indexer first.")
            sys.exit(1)
        
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row  # For named column access
        
        # Optimize for read performance
        self.conn.execute("PRAGMA cache_size = 10000")
        self.conn.execute("PRAGMA temp_store = MEMORY")
        
    def search_prefix(self, query, limit=100, dirs_only=False, files_only=False):
        """Fast prefix search using indexes"""
        sql_conditions = ["name LIKE ? || '%'"]
        params = [query]
        
        if dirs_only:
            sql_conditions.append("is_dir = 1")
        elif files_only:
            sql_conditions.append("is_dir = 0")
        
        sql = f"""
            SELECT path, name, size, mtime, is_dir, inode
            FROM files 
            WHERE {' AND '.join(sql_conditions)}
            ORDER BY 
                CASE WHEN name = ? THEN 1 ELSE 2 END,
                length(name),
                name
            LIMIT ?
        """
        
        params.extend([query, limit])
        return self.conn.execute(sql, params).fetchall()
    
    def search_substring(self, query, limit=100, dirs_only=False, files_only=False):
        """Substring search with fallback"""
        sql_conditions = ["name LIKE '%' || ? || '%'"]
        params = [query]
        
        if dirs_only:
            sql_conditions.append("is_dir = 1")
        elif files_only:
            sql_conditions.append("is_dir = 0")
        
        sql = f"""
            SELECT path, name, size, mtime, is_dir, inode
            FROM files 
            WHERE {' AND '.join(sql_conditions)}
            ORDER BY 
                CASE 
                    WHEN name = ? THEN 1 
                    WHEN name LIKE ? || '%' THEN 2 
                    ELSE 3 
                END,
                length(name),
                name
            LIMIT ?
        """
        
        params.extend([query, query, limit])
        return self.conn.execute(sql, params).fetchall()
    
    def search_path(self, query, limit=100):
        """Search in full paths"""
        sql = """
            SELECT path, name, size, mtime, is_dir, inode
            FROM files 
            WHERE path LIKE '%' || ? || '%'
            ORDER BY 
                CASE WHEN path LIKE ? || '%' THEN 1 ELSE 2 END,
                length(path),
                path
            LIMIT ?
        """
        return self.conn.execute(sql, [query, query, limit]).fetchall()
    
    def search_fts(self, query, limit=100):
        """Full-text search using FTS"""
        sql = """
            SELECT f.path, f.name, f.size, f.mtime, f.is_dir, f.inode
            FROM files_fts fts
            JOIN files f ON f.id = fts.rowid
            WHERE files_fts MATCH ?
            ORDER BY rank
            LIMIT ?
        """
        return self.conn.execute(sql, [query, limit]).fetchall()
    
    def search_by_size(self, min_size=None, max_size=None, limit=100):
        """Search by file size"""
        conditions = []
        params = []
        
        if min_size is not None:
            conditions.append("size >= ?")
            params.append(min_size)
        
        if max_size is not None:
            conditions.append("size <= ?")
            params.append(max_size)
        
        if not conditions:
            return []
        
        sql = f"""
            SELECT path, name, size, mtime, is_dir, inode
            FROM files 
            WHERE {' AND '.join(conditions)} AND is_dir = 0
            ORDER BY size DESC
            LIMIT ?
        """
        params.append(limit)
        return self.conn.execute(sql, params).fetchall()
    
    def search_recent(self, days=7, limit=100):
        """Search for recently modified files"""
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
        """Get database statistics"""
        cursor = self.conn.execute("""
            SELECT 
                COUNT(*) as total,
                COUNT(CASE WHEN is_dir = 1 THEN 1 END) as dirs,
                COUNT(CASE WHEN is_dir = 0 THEN 1 END) as files,
                SUM(CASE WHEN is_dir = 0 THEN size ELSE 0 END) as total_size
            FROM files
        """)
        return cursor.fetchone()
    
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
    
    def display_results(self, results, show_details=False):
        """Display search results"""
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
            
            if i >= 50 and len(results) > 50:  # Limit display for large results
                print(f"... and {len(results) - i} more results")
                break

def parse_size(size_str):
    """Parse size string like '10MB', '5.5GB' etc."""
    if not size_str:
        return None
    
    size_str = size_str.upper().strip()
    units = {'B': 1, 'K': 1024, 'KB': 1024, 'M': 1024**2, 'MB': 1024**2, 
             'G': 1024**3, 'GB': 1024**3, 'T': 1024**4, 'TB': 1024**4}
    
    # Extract number and unit
    for unit in sorted(units.keys(), key=len, reverse=True):
        if size_str.endswith(unit):
            try:
                number = float(size_str[:-len(unit)])
                return int(number * units[unit])
            except ValueError:
                break
    
    # Try just number (assume bytes)
    try:
        return int(size_str)
    except ValueError:
        raise ValueError(f"Invalid size format: {size_str}")

def main():
    parser = argparse.ArgumentParser(description="Fast file search using Btrfs metadata")
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
    parser.add_argument("--details", action="store_true", help="Show detailed results")
    parser.add_argument("--interactive", "-i", action="store_true", help="Interactive mode")
    
    args = parser.parse_args()
    
    searcher = FileSearch(args.database)
    
    if args.stats:
        stats = searcher.get_stats()
        print("Database Statistics:")
        print(f"  Total entries: {stats['total']:,}")
        print(f"  Directories: {stats['dirs']:,}")
        print(f"  Files: {stats['files']:,}")
        print(f"  Total size: {searcher.format_size(stats['total_size'])}")
        return
    
    if args.interactive:
        print("Interactive File Search (type 'quit' to exit)")
        print("Commands: !stats, !recent [days], !size [min] [max]")
        print("-" * 50)
        
        while True:
            try:
                query = input("\nSearch: ").strip()
                if query.lower() in ['quit', 'exit', 'q']:
                    break
                
                if query.startswith('!'):
                    if query == '!stats':
                        stats = searcher.get_stats()
                        print(f"Database: {stats['total']:,} entries, {searcher.format_size(stats['total_size'])}")
                    elif query.startswith('!recent'):
                        parts = query.split()
                        days = int(parts[1]) if len(parts) > 1 else 7
                        results = searcher.search_recent(days, 50)
                        searcher.display_results(results, True)
                    continue
                
                if not query:
                    continue
                
                start_time = time.time()
                
                # Try prefix search first (fastest)
                results = searcher.search_prefix(query, args.limit, args.dirs_only, args.files_only)
                
                # If no prefix results, try substring
                if not results:
                    results = searcher.search_substring(query, args.limit, args.dirs_only, args.files_only)
                
                end_time = time.time()
                
                searcher.display_results(results, args.details)
                print(f"\nSearch completed in {(end_time - start_time)*1000:.1f}ms")
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"Error: {e}")
        
        print("\nGoodbye!")
        return
    
    # Handle size search
    if args.size_min or args.size_max:
        try:
            min_size = parse_size(args.size_min) if args.size_min else None
            max_size = parse_size(args.size_max) if args.size_max else None
            results = searcher.search_by_size(min_size, max_size, args.limit)
            searcher.display_results(results, True)
        except ValueError as e:
            print(f"Error: {e}")
        return
    
    # Handle recent files
    if args.recent:
        results = searcher.search_recent(args.recent, args.limit)
        searcher.display_results(results, True)
        return
    
    # Regular search
    if not args.query:
        parser.print_help()
        return
    
    start_time = time.time()
    
    if args.path:
        results = searcher.search_path(args.query, args.limit)
    elif args.substring:
        results = searcher.search_substring(args.query, args.limit, args.dirs_only, args.files_only)
    else:
        # Try prefix first, then substring
        results = searcher.search_prefix(args.query, args.limit, args.dirs_only, args.files_only)
        if not results:
            results = searcher.search_substring(args.query, args.limit, args.dirs_only, args.files_only)
    
    end_time = time.time()
    
    searcher.display_results(results, args.details)
    print(f"\nSearch completed in {(end_time - start_time)*1000:.1f}ms")

if __name__ == "__main__":
    main()