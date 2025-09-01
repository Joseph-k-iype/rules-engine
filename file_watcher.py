"""
File system watcher for monitoring rule changes and triggering automatic updates.
Uses watchdog for cross-platform file system monitoring.
"""

import asyncio
import logging
from pathlib import Path
from typing import List, Set, Dict, Any, Optional, TYPE_CHECKING
from datetime import datetime, timedelta

from .config import Config
from .event_system import Event, event_bus

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler, FileSystemEvent
    WATCHDOG_AVAILABLE = True
    
    # Type aliases for when watchdog is available
    ObserverType = Observer
    FileSystemEventType = FileSystemEvent
    
except ImportError:
    WATCHDOG_AVAILABLE = False
    
    # Type aliases for when watchdog is not available
    from typing import Any
    ObserverType = Any
    FileSystemEventType = Any
    
    # Placeholder classes for runtime
    class Observer:
        pass
    
    class FileSystemEventHandler:
        pass
    
    class FileSystemEvent:
        pass

logger = logging.getLogger(__name__)

class RuleFileHandler:
    """File system event handler for rule files."""
    
    def __init__(self, debounce_seconds: float = 2.0):
        if not WATCHDOG_AVAILABLE:
            raise ImportError("Watchdog library required for file monitoring")
        
        # Import the actual base class only if available
        from watchdog.events import FileSystemEventHandler
        
        # Make this class inherit from the handler at runtime
        self.__class__.__bases__ = (FileSystemEventHandler,)
        
        self.debounce_seconds = debounce_seconds
        self.pending_events: Dict[str, datetime] = {}
        self.processed_events: Set[str] = set()
        
    def on_modified(self, event: FileSystemEvent):
        """Handle file modification events."""
        if event.is_directory:
            return
        
        self._handle_file_event("file_modified", event.src_path)
    
    def on_created(self, event: FileSystemEvent):
        """Handle file creation events."""
        if event.is_directory:
            return
        
        self._handle_file_event("file_created", event.src_path)
    
    def on_deleted(self, event: FileSystemEvent):
        """Handle file deletion events."""
        if event.is_directory:
            return
        
        self._handle_file_event("file_deleted", event.src_path)
    
    def on_moved(self, event: FileSystemEvent):
        """Handle file move events."""
        if event.is_directory:
            return
        
        # Treat move as delete + create
        self._handle_file_event("file_deleted", event.src_path)
        if hasattr(event, 'dest_path'):
            self._handle_file_event("file_created", event.dest_path)
    
    def _handle_file_event(self, event_type: str, file_path: str):
        """Handle file events with debouncing."""
        path = Path(file_path)
        
        # Only monitor relevant file types
        if not self._should_monitor_file(path):
            return
        
        # Create unique event key for debouncing
        event_key = f"{event_type}:{file_path}"
        current_time = datetime.utcnow()
        
        # Add to pending events
        self.pending_events[event_key] = current_time
        
        # Schedule debounced processing
        asyncio.create_task(self._process_debounced_event(event_key, event_type, file_path))
    
    def _should_monitor_file(self, path: Path) -> bool:
        """Check if file should be monitored."""
        # Monitor JSON files in rules directories
        if path.suffix.lower() == '.json':
            path_str = str(path).lower()
            if any(keyword in path_str for keyword in ['rule', 'extract', 'legislation']):
                return True
        
        # Monitor ontology files
        if path.suffix.lower() in ['.ttl', '.jsonld', '.rdf']:
            return True
        
        # Monitor configuration files
        if path.name == 'legislation_metadata.json':
            return True
        
        return False
    
    async def _process_debounced_event(self, event_key: str, event_type: str, file_path: str):
        """Process events after debounce delay."""
        await asyncio.sleep(self.debounce_seconds)
        
        # Check if this is still the latest event for this key
        if event_key in self.pending_events:
            last_event_time = self.pending_events[event_key]
            time_since_event = datetime.utcnow() - last_event_time
            
            if time_since_event >= timedelta(seconds=self.debounce_seconds):
                # Process the event
                if event_key not in self.processed_events:
                    await self._publish_file_event(event_type, file_path)
                    self.processed_events.add(event_key)
                
                # Clean up
                del self.pending_events[event_key]
                
                # Clean processed events periodically
                if len(self.processed_events) > 1000:
                    self.processed_events.clear()
    
    async def _publish_file_event(self, event_type: str, file_path: str):
        """Publish file event to event bus."""
        try:
            await event_bus.publish_event(Event(
                event_type=event_type,
                data={
                    "file_path": file_path,
                    "timestamp": datetime.utcnow().isoformat()
                },
                source="file_watcher"
            ))
            
            logger.debug(f"Published file event: {event_type} for {file_path}")
            
        except Exception as e:
            logger.error(f"Error publishing file event: {e}")

class FileWatcher:
    """File system watcher for rule files and ontologies."""
    
    def __init__(self, watch_directories: List[Path] = None, debounce_seconds: float = 2.0):
        if not WATCHDOG_AVAILABLE:
            raise ImportError("Watchdog library not available. Install with: pip install watchdog")
        
        self.watch_directories = watch_directories or Config.WATCH_DIRECTORIES
        self.debounce_seconds = debounce_seconds
        self.observer: Optional[Observer] = None
        self.event_handler: Optional[RuleFileHandler] = None
        self.is_watching = False
        self.watches = []
        
        # Ensure watch directories exist
        for directory in self.watch_directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    async def start_watching(self):
        """Start file system monitoring."""
        if self.is_watching:
            logger.warning("File watcher is already running")
            return
        
        try:
            from watchdog.observers import Observer
            
            self.observer = Observer()
            self.event_handler = RuleFileHandler(self.debounce_seconds)
            
            # Schedule watches for each directory
            for directory in self.watch_directories:
                if directory.exists():
                    watch = self.observer.schedule(
                        self.event_handler, 
                        str(directory), 
                        recursive=True
                    )
                    self.watches.append(watch)
                    logger.info(f"Watching directory: {directory}")
                else:
                    logger.warning(f"Watch directory does not exist: {directory}")
            
            # Start the observer
            self.observer.start()
            self.is_watching = True
            
            logger.info("File watcher started successfully")
            
            # Publish startup event
            await event_bus.publish_event(Event(
                event_type="file_watcher_started",
                data={
                    "watch_directories": [str(d) for d in self.watch_directories],
                    "debounce_seconds": self.debounce_seconds
                },
                source="file_watcher"
            ))
            
        except Exception as e:
            logger.error(f"Error starting file watcher: {e}")
            raise
    
    async def stop_watching(self):
        """Stop file system monitoring."""
        if not self.is_watching:
            return
        
        try:
            if self.observer:
                # Stop the observer
                self.observer.stop()
                self.observer.join(timeout=5.0)  # Wait up to 5 seconds
            
            self.is_watching = False
            self.watches.clear()
            
            logger.info("File watcher stopped")
            
            # Publish shutdown event
            await event_bus.publish_event(Event(
                event_type="file_watcher_stopped",
                data={"timestamp": datetime.utcnow().isoformat()},
                source="file_watcher"
            ))
            
        except Exception as e:
            logger.error(f"Error stopping file watcher: {e}")
    
    def add_watch_directory(self, directory: Path):
        """Add a new directory to watch."""
        if directory not in self.watch_directories:
            self.watch_directories.append(directory)
            
            if self.is_watching and self.observer and directory.exists():
                watch = self.observer.schedule(
                    self.event_handler,
                    str(directory),
                    recursive=True
                )
                self.watches.append(watch)
                logger.info(f"Added watch for directory: {directory}")
    
    def remove_watch_directory(self, directory: Path):
        """Remove a directory from watching."""
        if directory in self.watch_directories:
            self.watch_directories.remove(directory)
            
            if self.observer:
                # Find and remove corresponding watch
                watches_to_remove = []
                for watch in self.watches:
                    if watch.path == str(directory):
                        watches_to_remove.append(watch)
                
                for watch in watches_to_remove:
                    self.observer.unschedule(watch)
                    self.watches.remove(watch)
                    logger.info(f"Removed watch for directory: {directory}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get file watcher status."""
        return {
            "is_watching": self.is_watching,
            "watch_directories": [str(d) for d in self.watch_directories],
            "debounce_seconds": self.debounce_seconds,
            "active_watches": len(self.watches),
            "watchdog_available": WATCHDOG_AVAILABLE
        }

class ManualChangeDetector:
    """Detects manual changes in rule files by comparing checksums."""
    
    def __init__(self, check_interval_seconds: int = 30):
        self.check_interval = check_interval_seconds
        self.file_checksums: Dict[str, str] = {}
        self.is_monitoring = False
        self._monitor_task: Optional[asyncio.Task[None]] = None
    
    async def start_monitoring(self, rule_files: List[Path]):
        """Start monitoring rule files for manual changes."""
        if self.is_monitoring:
            return
        
        self.is_monitoring = True
        self._monitor_task = asyncio.create_task(
            self._monitor_files(rule_files)
        )
        logger.info("Manual change detector started")
    
    async def stop_monitoring(self):
        """Stop monitoring files."""
        if not self.is_monitoring:
            return
        
        self.is_monitoring = False
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Manual change detector stopped")
    
    async def _monitor_files(self, rule_files: List[Path]):
        """Monitor files for changes."""
        while self.is_monitoring:
            try:
                for file_path in rule_files:
                    if file_path.exists():
                        await self._check_file_changes(file_path)
                
                await asyncio.sleep(self.check_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in file monitoring: {e}")
                await asyncio.sleep(self.check_interval)
    
    async def _check_file_changes(self, file_path: Path):
        """Check if a file has changed."""
        try:
            import hashlib
            
            # Calculate current checksum
            with open(file_path, 'rb') as f:
                content = f.read()
                current_checksum = hashlib.md5(content).hexdigest()
            
            file_key = str(file_path)
            previous_checksum = self.file_checksums.get(file_key)
            
            if previous_checksum is None:
                # First time seeing this file
                self.file_checksums[file_key] = current_checksum
            elif previous_checksum != current_checksum:
                # File has changed
                self.file_checksums[file_key] = current_checksum
                
                # Publish change event
                await event_bus.publish_event(Event(
                    event_type="manual_file_changed",
                    data={
                        "file_path": str(file_path),
                        "old_checksum": previous_checksum,
                        "new_checksum": current_checksum,
                        "detection_method": "checksum"
                    },
                    source="manual_change_detector"
                ))
                
                logger.info(f"Manual change detected in: {file_path}")
                
        except Exception as e:
            logger.error(f"Error checking file changes for {file_path}: {e}")

# Global file watcher instance
file_watcher: Optional[FileWatcher] = None

async def initialize_file_watcher() -> Optional[FileWatcher]:
    """Initialize the global file watcher."""
    global file_watcher
    
    if not WATCHDOG_AVAILABLE:
        logger.warning("Watchdog not available. File watching disabled.")
        return None
    
    try:
        file_watcher = FileWatcher()
        await file_watcher.start_watching()
        logger.info("File watcher initialized successfully")
        return file_watcher
        
    except Exception as e:
        logger.error(f"Failed to initialize file watcher: {e}")
        return None

async def shutdown_file_watcher():
    """Shutdown the global file watcher."""
    global file_watcher
    
    if file_watcher:
        await file_watcher.stop_watching()
        file_watcher = None
        logger.info("File watcher shutdown complete")

def is_file_watcher_available() -> bool:
    """Check if file watching is available."""
    return WATCHDOG_AVAILABLE

def get_file_watcher() -> Optional[FileWatcher]:
    """Get the global file watcher instance."""
    return file_watcher