#!/usr/bin/env python3

import os
import sys
import time
import json
import sqlite3
import logging
import signal
import threading
from datetime import datetime
from pathlib import Path
from typing import Dict, Set, Optional
import pyinotify

class EventHandler(pyinotify.ProcessEvent):
    """Handle inotify events"""
    
    def __init__(self, daemon):
        self.daemon = daemon
    
    def process_IN_CREATE(self, event):
        if not self.daemon.should_ignore_path(event.pathname):
            if self.daemon.db_updater.add_file(event.pathname):
                self.daemon.stats['files_added'] += 1
            else:
                self.daemon.stats['errors'] += 1
    
    def process_IN_DELETE(self, event):
        if not self.daemon.should_ignore_path(event.pathname):
            if self.daemon.db_updater.remove_file(event.pathname):
                self.daemon.stats['files_removed'] += 1
            else:
                self.daemon.stats['errors'] += 1
    
    def process_IN_MODIFY(self, event):
        if not self.daemon.should_ignore_path(event.pathname):
            if self.daemon.db_updater.update_file(event.pathname):
                self.daemon.stats['files_updated'] += 1
            else:
                self.daemon.stats['errors'] += 1
    
    def process_IN_ATTRIB(self, event):
        if not self.daemon.should_ignore_path(event.pathname):
            if self.daemon.db_updater.update_file(event.pathname):
                self.daemon.stats['files_updated'] += 1
            else:
                self.daemon.stats['errors'] += 1
    
    def process_IN_MOVED_FROM(self, event):
        if not self.daemon.should_ignore_path(event.pathname):
            if self.daemon.db_updater.remove_file(event.pathname):
                self.daemon.stats['files_removed'] += 1
            else:
                self.daemon.stats['errors'] += 1
    
    def process_IN_MOVED_TO(self, event):
        if not self.daemon.should_ignore_path(event.pathname):
            if self.daemon.db_updater.add_file(event.pathname):
                self.daemon.stats['files_added'] += 1
            else:
                self.daemon.stats['errors'] += 1

class FileIndexUpdater:
    """Updates the SQLite database incrementally based on filesystem changes"""
    
    def __init__(self, db_path: str = "file_index.db"):
        self.db_path = db_path
        self.conn = None
        self.setup_database_connection()
    
    def setup_database_connection(self):
        """Setup database connection with proper settings"""
        try:
            self.conn = sqlite3.connect(self.db_path, timeout=30.0)
            self.conn.execute("PRAGMA journal_mode = WAL")
            self.conn.execute("PRAGMA synchronous = NORMAL")
            self.conn.execute("PRAGMA cache_size = 1000")
            logging.info(f"Connected to database: {self.db_path}")
        except Exception as e:
            logging.error(f"Failed to connect to database: {e}")
            raise
    
    def add_file(self, file_path: str) -> bool:
        """Add a new file to the database"""
        try:
            if not os.path.exists(file_path):
                return False
                
            stat_info = os.stat(file_path)
            name = os.path.basename(file_path)
            
            # Convert timestamps
            mtime = datetime.fromtimestamp(stat_info.st_mtime).strftime('%Y-%m-%dT%H:%M:%SZ')
            
            # Insert into database
            cursor = self.conn.execute("""
                INSERT OR REPLACE INTO files 
                (path, name, inode, size, mtime, mode, is_dir, indexed_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (
                file_path, name, stat_info.st_ino, stat_info.st_size,
                mtime, stat_info.st_mode, os.path.isdir(file_path)
            ))
            
            # Update FTS index
            file_id = cursor.lastrowid
            self.conn.execute("""
                INSERT OR REPLACE INTO files_fts (rowid, name, path)
                VALUES (?, ?, ?)
            """, (file_id, name, file_path))
            
            self.conn.commit()
            logging.debug(f"Added file: {file_path}")
            return True
            
        except Exception as e:
            logging.error(f"Failed to add file {file_path}: {e}")
            return False
    
    def update_file(self, file_path: str) -> bool:
        """Update an existing file in the database"""
        try:
            if not os.path.exists(file_path):
                return self.remove_file(file_path)
                
            stat_info = os.stat(file_path)
            mtime = datetime.fromtimestamp(stat_info.st_mtime).strftime('%Y-%m-%dT%H:%M:%SZ')
            
            # Update database
            cursor = self.conn.execute("""
                UPDATE files SET 
                    size = ?, mtime = ?, mode = ?, is_dir = ?, indexed_at = CURRENT_TIMESTAMP
                WHERE path = ?
            """, (
                stat_info.st_size, mtime, stat_info.st_mode, 
                os.path.isdir(file_path), file_path
            ))
            
            if cursor.rowcount > 0:
                # Update FTS index
                self.conn.execute("""
                    UPDATE files_fts SET name = ?, path = ?
                    WHERE rowid = (SELECT id FROM files WHERE path = ?)
                """, (os.path.basename(file_path), file_path, file_path))
                
                self.conn.commit()
                logging.debug(f"Updated file: {file_path}")
                return True
            else:
                # File not in database, add it
                return self.add_file(file_path)
                
        except Exception as e:
            logging.error(f"Failed to update file {file_path}: {e}")
            return False
    
    def remove_file(self, file_path: str) -> bool:
        """Remove a file from the database"""
        try:
            # Get file ID before deletion
            cursor = self.conn.execute("SELECT id FROM files WHERE path = ?", (file_path,))
            result = cursor.fetchone()
            
            if result:
                file_id = result[0]
                
                # Remove from FTS index
                self.conn.execute("DELETE FROM files_fts WHERE rowid = ?", (file_id,))
                
                # Remove from main table
                self.conn.execute("DELETE FROM files WHERE path = ?", (file_path,))
                
                self.conn.commit()
                logging.debug(f"Removed file: {file_path}")
                return True
            else:
                logging.debug(f"File not in database: {file_path}")
                return False
                
        except Exception as e:
            logging.error(f"Failed to remove file {file_path}: {e}")
            return False
    
    def move_file(self, old_path: str, new_path: str) -> bool:
        """Handle file moves/renames"""
        try:
            if not os.path.exists(new_path):
                return self.remove_file(old_path)
            
            stat_info = os.stat(new_path)
            new_name = os.path.basename(new_path)
            mtime = datetime.fromtimestamp(stat_info.st_mtime).strftime('%Y-%m-%dT%H:%M:%SZ')
            
            # Update database
            cursor = self.conn.execute("""
                UPDATE files SET 
                    path = ?, name = ?, size = ?, mtime = ?, mode = ?, 
                    is_dir = ?, indexed_at = CURRENT_TIMESTAMP
                WHERE path = ?
            """, (
                new_path, new_name, stat_info.st_size, mtime, 
                stat_info.st_mode, os.path.isdir(new_path), old_path
            ))
            
            if cursor.rowcount > 0:
                # Update FTS index
                self.conn.execute("""
                    UPDATE files_fts SET name = ?, path = ?
                    WHERE rowid = (SELECT id FROM files WHERE path = ?)
                """, (new_name, new_path, new_path))
                
                self.conn.commit()
                logging.debug(f"Moved file: {old_path} -> {new_path}")
                return True
            else:
                # Old path not in database, add new path
                return self.add_file(new_path)
                
        except Exception as e:
            logging.error(f"Failed to move file {old_path} -> {new_path}: {e}")
            return False
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()

class InotifyDaemon:
    """Main inotify daemon class"""
    
    def __init__(self, config_path: str = "inotify_config.json"):
        self.config_path = config_path
        self.config = self.load_config()
        self.db_updater = FileIndexUpdater(self.config['database_path'])
        self.inotify = None
        self.running = False
        self.stats = {
            'files_added': 0,
            'files_updated': 0,
            'files_removed': 0,
            'files_moved': 0,
            'errors': 0,
            'start_time': None
        }
        
        # Setup signal handlers
        signal.signal(signal.SIGTERM, self.signal_handler)
        signal.signal(signal.SIGINT, self.signal_handler)
    
    def load_config(self) -> Dict:
        """Load configuration from JSON file"""
        default_config = {
            "watch_paths": ["/home"],
            "database_path": "file_index.db",
            "exclude_patterns": [
                "*.tmp", "*.swp", "*~", ".git/*", "__pycache__/*", 
                "*.pyc", ".cache/*", ".local/share/Trash/*"
            ],
            "max_depth": 10,
            "batch_size": 100,
            "log_level": "INFO"
        }
        
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    user_config = json.load(f)
                    default_config.update(user_config)
                    logging.info(f"Loaded config from {self.config_path}")
            else:
                # Create default config file
                with open(self.config_path, 'w') as f:
                    json.dump(default_config, f, indent=2)
                logging.info(f"Created default config at {self.config_path}")
                
        except Exception as e:
            logging.error(f"Failed to load config: {e}")
            
        return default_config
    
    def should_ignore_path(self, path: str) -> bool:
        """Check if path should be ignored based on exclude patterns"""
        import fnmatch
        
        for pattern in self.config['exclude_patterns']:
            if fnmatch.fnmatch(path, pattern) or fnmatch.fnmatch(os.path.basename(path), pattern):
                return True
        return False
    
    def setup_watches(self):
        """Setup inotify watches for configured paths"""
        # Create watch manager and notifier
        self.wm = pyinotify.WatchManager()
        
        # Set up event mask
        mask = (
            pyinotify.IN_CREATE |
            pyinotify.IN_DELETE |
            pyinotify.IN_MODIFY |
            pyinotify.IN_MOVED_FROM |
            pyinotify.IN_MOVED_TO |
            pyinotify.IN_ATTRIB
        )
        
        # Create event handler
        handler = EventHandler(self)
        self.notifier = pyinotify.Notifier(self.wm, handler)
        
        # Add watches for each path
        for watch_path in self.config['watch_paths']:
            self.wm.add_watch(watch_path, mask, rec=True)
            
        logging.info(f"Setup inotify watches for: {self.config['watch_paths']}")
    
    
    def print_stats(self):
        """Print daemon statistics"""
        if self.stats['start_time']:
            uptime = time.time() - self.stats['start_time']
            logging.info(f"Stats - Added: {self.stats['files_added']}, "
                        f"Updated: {self.stats['files_updated']}, "
                        f"Removed: {self.stats['files_removed']}, "
                        f"Errors: {self.stats['errors']}, "
                        f"Uptime: {uptime:.0f}s")
    
    def run(self):
        """Main daemon loop"""
        try:
            self.setup_watches()
            self.running = True
            self.stats['start_time'] = time.time()
            
            logging.info("Inotify daemon started - monitoring filesystem changes...")
            
            # Setup periodic stats logging in a separate thread
            def stats_logger():
                while self.running:
                    time.sleep(300)  # 5 minutes
                    if self.running:
                        self.print_stats()
            
            stats_thread = threading.Thread(target=stats_logger, daemon=True)
            stats_thread.start()
            
            # Start the notifier loop
            self.notifier.loop()
                    
        except KeyboardInterrupt:
            logging.info("Daemon stopped by user")
        except Exception as e:
            logging.error(f"Daemon error: {e}")
        finally:
            self.cleanup()
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logging.info(f"Received signal {signum}, shutting down...")
        self.running = False
    
    def cleanup(self):
        """Cleanup resources"""
        self.running = False
        if self.db_updater:
            self.db_updater.close()
        self.print_stats()
        logging.info("Daemon cleanup completed")

def setup_logging(log_level: str = "INFO", log_file: str = "inotify_daemon.log"):
    """Setup logging configuration"""
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )

def main():
    if len(sys.argv) > 1 and sys.argv[1] in ['-h', '--help']:
        print("Usage: python3 inotify_daemon.py [config_file]")
        print("Default config file: inotify_config.json")
        print("\nThe daemon monitors filesystem changes and updates the SQLite database in real-time.")
        return
    
    config_file = sys.argv[1] if len(sys.argv) > 1 else "inotify_config.json"
    
    # Setup logging
    setup_logging()
    
    try:
        daemon = InotifyDaemon(config_file)
        daemon.run()
    except Exception as e:
        logging.error(f"Failed to start daemon: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
