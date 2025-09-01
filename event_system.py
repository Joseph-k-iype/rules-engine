"""
Event-driven system for the Legislation Rules Converter.
Handles events, observers, and automatic triggers for system components.
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Callable, Any, Optional
from datetime import datetime
from dataclasses import dataclass, field

from .models import RuleChangeEvent, LegislationRule

logger = logging.getLogger(__name__)

@dataclass
class Event:
    """Base event class."""
    event_type: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    data: Dict[str, Any] = field(default_factory=dict)
    source: str = "system"

class EventHandler(ABC):
    """Abstract base class for event handlers."""
    
    @abstractmethod
    async def handle_event(self, event: Event) -> None:
        """Handle an event."""
        pass
    
    @abstractmethod
    def can_handle(self, event_type: str) -> bool:
        """Check if this handler can handle the event type."""
        pass

class EventBus:
    """Event bus for managing event distribution."""
    
    def __init__(self):
        self._handlers: List[EventHandler] = []
        self._event_queue: asyncio.Queue = asyncio.Queue()
        self._running = False
        self._task: Optional[asyncio.Task] = None
        
    def register_handler(self, handler: EventHandler) -> None:
        """Register an event handler."""
        self._handlers.append(handler)
        logger.info(f"Registered event handler: {handler.__class__.__name__}")
    
    def unregister_handler(self, handler: EventHandler) -> None:
        """Unregister an event handler."""
        if handler in self._handlers:
            self._handlers.remove(handler)
            logger.info(f"Unregistered event handler: {handler.__class__.__name__}")
    
    async def publish_event(self, event: Event) -> None:
        """Publish an event to the bus."""
        await self._event_queue.put(event)
        logger.debug(f"Published event: {event.event_type}")
    
    async def start(self) -> None:
        """Start the event bus."""
        if self._running:
            return
            
        self._running = True
        self._task = asyncio.create_task(self._process_events())
        logger.info("Event bus started")
    
    async def stop(self) -> None:
        """Stop the event bus."""
        if not self._running:
            return
            
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Event bus stopped")
    
    async def _process_events(self) -> None:
        """Process events from the queue."""
        while self._running:
            try:
                event = await asyncio.wait_for(self._event_queue.get(), timeout=1.0)
                await self._handle_event(event)
                self._event_queue.task_done()
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Error processing event: {e}")
    
    async def _handle_event(self, event: Event) -> None:
        """Handle an event by dispatching to appropriate handlers."""
        handlers = [h for h in self._handlers if h.can_handle(event.event_type)]
        
        if not handlers:
            logger.warning(f"No handlers found for event type: {event.event_type}")
            return
        
        # Handle events concurrently
        tasks = [handler.handle_event(event) for handler in handlers]
        try:
            await asyncio.gather(*tasks, return_exceptions=True)
        except Exception as e:
            logger.error(f"Error handling event {event.event_type}: {e}")

class RuleChangeHandler(EventHandler):
    """Handler for rule change events."""
    
    def __init__(self, ontology_manager, standards_converter):
        self.ontology_manager = ontology_manager
        self.standards_converter = standards_converter
    
    async def handle_event(self, event: Event) -> None:
        """Handle rule change events."""
        try:
            if event.event_type == "rule_created":
                await self._handle_rule_created(event)
            elif event.event_type == "rule_updated":
                await self._handle_rule_updated(event)
            elif event.event_type == "rule_deleted":
                await self._handle_rule_deleted(event)
            elif event.event_type == "rules_batch_updated":
                await self._handle_rules_batch_updated(event)
        except Exception as e:
            logger.error(f"Error handling rule change event: {e}")
    
    def can_handle(self, event_type: str) -> bool:
        """Check if this handler can handle the event type."""
        return event_type in ["rule_created", "rule_updated", "rule_deleted", "rules_batch_updated"]
    
    async def _handle_rule_created(self, event: Event) -> None:
        """Handle rule creation."""
        rule_data = event.data.get("rule")
        if rule_data:
            logger.info(f"Rule created: {rule_data.get('id', 'unknown')}")
            # Trigger ontology update
            await self.ontology_manager.update_single_rule(rule_data)
    
    async def _handle_rule_updated(self, event: Event) -> None:
        """Handle rule update."""
        rule_data = event.data.get("rule")
        old_rule_data = event.data.get("old_rule")
        if rule_data:
            logger.info(f"Rule updated: {rule_data.get('id', 'unknown')}")
            # Trigger ontology update
            await self.ontology_manager.update_single_rule(rule_data, old_rule_data)
    
    async def _handle_rule_deleted(self, event: Event) -> None:
        """Handle rule deletion."""
        rule_id = event.data.get("rule_id")
        if rule_id:
            logger.info(f"Rule deleted: {rule_id}")
            # Trigger ontology cleanup
            await self.ontology_manager.remove_rule(rule_id)
    
    async def _handle_rules_batch_updated(self, event: Event) -> None:
        """Handle batch rule updates."""
        rules_data = event.data.get("rules", [])
        logger.info(f"Batch rules update: {len(rules_data)} rules")
        # Trigger full ontology regeneration
        await self.ontology_manager.regenerate_ontologies(rules_data)

class FileChangeHandler(EventHandler):
    """Handler for file system change events."""
    
    def __init__(self, rule_manager, event_bus):
        self.rule_manager = rule_manager
        self.event_bus = event_bus
    
    async def handle_event(self, event: Event) -> None:
        """Handle file change events."""
        try:
            if event.event_type == "file_modified":
                await self._handle_file_modified(event)
            elif event.event_type == "file_created":
                await self._handle_file_created(event)
            elif event.event_type == "file_deleted":
                await self._handle_file_deleted(event)
        except Exception as e:
            logger.error(f"Error handling file change event: {e}")
    
    def can_handle(self, event_type: str) -> bool:
        """Check if this handler can handle the event type."""
        return event_type in ["file_modified", "file_created", "file_deleted"]
    
    async def _handle_file_modified(self, event: Event) -> None:
        """Handle file modification."""
        file_path = event.data.get("file_path")
        if file_path and str(file_path).endswith('.json'):
            logger.info(f"JSON file modified: {file_path}")
            
            # Check if it's a rules file
            if "rules" in str(file_path).lower():
                # Load updated rules and trigger rule change events
                try:
                    updated_rules = await self.rule_manager.load_rules_from_file(file_path)
                    if updated_rules:
                        # Publish batch update event
                        await self.event_bus.publish_event(Event(
                            event_type="rules_batch_updated",
                            data={"rules": [rule.model_dump() for rule in updated_rules]},
                            source="file_watcher"
                        ))
                except Exception as e:
                    logger.error(f"Error loading updated rules from {file_path}: {e}")
    
    async def _handle_file_created(self, event: Event) -> None:
        """Handle file creation."""
        file_path = event.data.get("file_path")
        logger.info(f"New file created: {file_path}")
    
    async def _handle_file_deleted(self, event: Event) -> None:
        """Handle file deletion."""
        file_path = event.data.get("file_path")
        logger.info(f"File deleted: {file_path}")

class ProcessingStatusHandler(EventHandler):
    """Handler for processing status events."""
    
    def __init__(self):
        self.job_status: Dict[str, Dict[str, Any]] = {}
    
    async def handle_event(self, event: Event) -> None:
        """Handle processing status events."""
        try:
            job_id = event.data.get("job_id")
            if not job_id:
                return
                
            if event.event_type == "processing_started":
                await self._handle_processing_started(event)
            elif event.event_type == "processing_progress":
                await self._handle_processing_progress(event)
            elif event.event_type == "processing_completed":
                await self._handle_processing_completed(event)
            elif event.event_type == "processing_failed":
                await self._handle_processing_failed(event)
        except Exception as e:
            logger.error(f"Error handling processing status event: {e}")
    
    def can_handle(self, event_type: str) -> bool:
        """Check if this handler can handle the event type."""
        return event_type in [
            "processing_started", "processing_progress", 
            "processing_completed", "processing_failed"
        ]
    
    async def _handle_processing_started(self, event: Event) -> None:
        """Handle processing start."""
        job_id = event.data["job_id"]
        self.job_status[job_id] = {
            "status": "started",
            "start_time": event.timestamp,
            "progress": 0.0
        }
        logger.info(f"Processing started for job: {job_id}")
    
    async def _handle_processing_progress(self, event: Event) -> None:
        """Handle processing progress."""
        job_id = event.data["job_id"]
        progress = event.data.get("progress", 0.0)
        
        if job_id in self.job_status:
            self.job_status[job_id]["progress"] = progress
            self.job_status[job_id]["last_update"] = event.timestamp
        
        logger.debug(f"Processing progress for job {job_id}: {progress}%")
    
    async def _handle_processing_completed(self, event: Event) -> None:
        """Handle processing completion."""
        job_id = event.data["job_id"]
        if job_id in self.job_status:
            self.job_status[job_id]["status"] = "completed"
            self.job_status[job_id]["end_time"] = event.timestamp
            self.job_status[job_id]["progress"] = 100.0
        
        logger.info(f"Processing completed for job: {job_id}")
    
    async def _handle_processing_failed(self, event: Event) -> None:
        """Handle processing failure."""
        job_id = event.data["job_id"]
        error = event.data.get("error", "Unknown error")
        
        if job_id in self.job_status:
            self.job_status[job_id]["status"] = "failed"
            self.job_status[job_id]["end_time"] = event.timestamp
            self.job_status[job_id]["error"] = error
        
        logger.error(f"Processing failed for job {job_id}: {error}")
    
    def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get status for a specific job."""
        return self.job_status.get(job_id)
    
    def get_all_jobs(self) -> Dict[str, Dict[str, Any]]:
        """Get all job statuses."""
        return self.job_status.copy()

# Global event bus instance
event_bus = EventBus()

async def initialize_event_system(ontology_manager, rule_manager, standards_converter) -> EventBus:
    """Initialize the event system with all handlers."""
    
    # Register handlers
    rule_change_handler = RuleChangeHandler(ontology_manager, standards_converter)
    file_change_handler = FileChangeHandler(rule_manager, event_bus)
    processing_status_handler = ProcessingStatusHandler()
    
    event_bus.register_handler(rule_change_handler)
    event_bus.register_handler(file_change_handler)
    event_bus.register_handler(processing_status_handler)
    
    # Start the event bus
    await event_bus.start()
    
    logger.info("Event system initialized successfully")
    return event_bus

async def shutdown_event_system() -> None:
    """Shutdown the event system."""
    await event_bus.stop()
    logger.info("Event system shutdown complete")