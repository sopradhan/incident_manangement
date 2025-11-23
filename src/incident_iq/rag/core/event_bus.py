"""
Phase II: Event Bus for Event-Driven Architecture
Decouples agents from MasterOrchestrator
Agents communicate via events instead of direct method calls

Events:
  - DOC_INGEST_REQUEST: Master -> Ingestion
  - DOC_INGEST_COMPLETE: Ingestion -> Subscribers
  - QUERY_REQUEST: Master -> Retrieval
  - QUERY_COMPLETE: Retrieval -> Subscribers
  - OPTIMIZATION_REQUEST: Master -> Healing
  - OPTIMIZATION_COMPLETE: Healing -> Subscribers
"""
import json
import logging
from typing import Dict, Callable, List, Optional
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


class EventType(Enum):
    """Event types for agent communication"""
    # Ingestion events
    DOC_INGEST_REQUEST = "doc_ingest_request"
    DOC_INGEST_COMPLETE = "doc_ingest_complete"
    DOC_INGEST_FAILED = "doc_ingest_failed"
    
    # Retrieval events
    QUERY_REQUEST = "query_request"
    QUERY_COMPLETE = "query_complete"
    QUERY_FAILED = "query_failed"
    
    # Healing/Optimization events
    OPTIMIZATION_REQUEST = "optimization_request"
    OPTIMIZATION_COMPLETE = "optimization_complete"
    OPTIMIZATION_FAILED = "optimization_failed"
    
    # System events
    SYSTEM_HEALTH_CHECK = "system_health_check"
    METRICS_UPDATED = "metrics_updated"


@dataclass
class Event:
    """Base event structure"""
    event_type: EventType
    source: str  # Which agent/service published this
    timestamp: str
    payload: Dict
    event_id: str = None
    
    def to_dict(self):
        return {
            'event_type': self.event_type.value,
            'source': self.source,
            'timestamp': self.timestamp,
            'payload': self.payload,
            'event_id': self.event_id
        }
    
    def to_json(self):
        return json.dumps(self.to_dict())


class EventBus:
    """
    Central event bus for agent communication
    
    Implements Observer pattern:
      - Agents subscribe to event types
      - EventBus publishes events
      - Subscribers are notified automatically
    """
    
    def __init__(self):
        """Initialize event bus"""
        self.subscribers: Dict[str, List[Callable]] = {}
        self.event_history: List[Event] = []
        self.max_history = 10000
        logger.info("✓ EventBus initialized")
    
    # =========================================================================
    # CORE EVENT BUS OPERATIONS
    # =========================================================================
    
    def subscribe(self, event_type: EventType, handler: Callable) -> None:
        """
        Subscribe to an event type
        
        Args:
            event_type: EventType to subscribe to
            handler: Callable that handles the event
        """
        event_key = event_type.value
        
        if event_key not in self.subscribers:
            self.subscribers[event_key] = []
        
        self.subscribers[event_key].append(handler)
        logger.info(f"✓ Subscribed {handler.__name__} to {event_key}")
    
    def unsubscribe(self, event_type: EventType, handler: Callable) -> None:
        """Unsubscribe from an event type"""
        event_key = event_type.value
        
        if event_key in self.subscribers:
            self.subscribers[event_key] = [h for h in self.subscribers[event_key] if h != handler]
    
    def publish(self, event: Event) -> None:
        """
        Publish an event to subscribers
        
        Args:
            event: Event to publish
        """
        event_key = event.event_type.value
        
        # Store in history
        self._add_to_history(event)
        
        logger.info(f"📢 Publishing {event_key} from {event.source}")
        
        # Notify all subscribers
        if event_key in self.subscribers:
            for handler in self.subscribers[event_key]:
                try:
                    handler(event)
                except Exception as e:
                    logger.error(f"✗ Handler {handler.__name__} failed: {e}")
        else:
            logger.warning(f"⚠️  No subscribers for {event_key}")
    
    def publish_async(self, event: Event) -> None:
        """
        Publish event asynchronously (for future: Redis/RabbitMQ implementation)
        
        Args:
            event: Event to publish
        """
        # TODO: Implement async publishing with Redis/RabbitMQ
        self.publish(event)
    
    # =========================================================================
    # CONVENIENCE METHODS FOR AGENTS
    # =========================================================================
    
    def request_ingestion(self, document_id: str, content: str, 
                         metadata: Dict, rbac_namespace: str) -> Event:
        """
        Publish DOC_INGEST_REQUEST event
        
        Called by: MasterOrchestrator
        Handled by: IngestionAgent
        """
        event = Event(
            event_type=EventType.DOC_INGEST_REQUEST,
            source="MasterOrchestrator",
            timestamp=datetime.now().isoformat(),
            payload={
                "document_id": document_id,
                "content": content,
                "metadata": metadata,
                "rbac_namespace": rbac_namespace
            }
        )
        self.publish(event)
        return event
    
    def ingestion_complete(self, document_id: str, chunks_count: int, 
                          status: str, metadata: Dict) -> Event:
        """
        Publish DOC_INGEST_COMPLETE event
        
        Called by: IngestionAgent
        Handled by: MasterOrchestrator, HealingAgent
        """
        event = Event(
            event_type=EventType.DOC_INGEST_COMPLETE,
            source="IngestionAgent",
            timestamp=datetime.now().isoformat(),
            payload={
                "document_id": document_id,
                "chunks_count": chunks_count,
                "status": status,
                "metadata": metadata
            }
        )
        self.publish(event)
        return event
    
    def request_query(self, query: str, user_id: str, filters: Dict = None) -> Event:
        """
        Publish QUERY_REQUEST event
        
        Called by: MasterOrchestrator
        Handled by: RetrievalAgent
        """
        event = Event(
            event_type=EventType.QUERY_REQUEST,
            source="MasterOrchestrator",
            timestamp=datetime.now().isoformat(),
            payload={
                "query": query,
                "user_id": user_id,
                "filters": filters or {}
            }
        )
        self.publish(event)
        return event
    
    def query_complete(self, query: str, results_count: int, 
                      execution_time_ms: int, status: str) -> Event:
        """
        Publish QUERY_COMPLETE event
        
        Called by: RetrievalAgent
        Handled by: MasterOrchestrator
        """
        event = Event(
            event_type=EventType.QUERY_COMPLETE,
            source="RetrievalAgent",
            timestamp=datetime.now().isoformat(),
            payload={
                "query": query,
                "results_count": results_count,
                "execution_time_ms": execution_time_ms,
                "status": status
            }
        )
        self.publish(event)
        return event
    
    def request_optimization(self, document_id: str, strategy: str, 
                            metadata: Dict = None) -> Event:
        """
        Publish OPTIMIZATION_REQUEST event
        
        Called by: MasterOrchestrator
        Handled by: HealingAgent
        """
        event = Event(
            event_type=EventType.OPTIMIZATION_REQUEST,
            source="MasterOrchestrator",
            timestamp=datetime.now().isoformat(),
            payload={
                "document_id": document_id,
                "strategy": strategy,
                "metadata": metadata or {}
            }
        )
        self.publish(event)
        return event
    
    def optimization_complete(self, document_id: str, strategy: str, 
                             quality_before: float, quality_after: float,
                             status: str) -> Event:
        """
        Publish OPTIMIZATION_COMPLETE event
        
        Called by: HealingAgent
        Handled by: MasterOrchestrator
        """
        event = Event(
            event_type=EventType.OPTIMIZATION_COMPLETE,
            source="HealingAgent",
            timestamp=datetime.now().isoformat(),
            payload={
                "document_id": document_id,
                "strategy": strategy,
                "quality_before": quality_before,
                "quality_after": quality_after,
                "status": status,
                "improvement": quality_after - quality_before
            }
        )
        self.publish(event)
        return event
    
    # =========================================================================
    # HISTORY & MONITORING
    # =========================================================================
    
    def _add_to_history(self, event: Event) -> None:
        """Add event to history with size limit"""
        self.event_history.append(event)
        if len(self.event_history) > self.max_history:
            self.event_history.pop(0)
    
    def get_recent_events(self, event_type: Optional[EventType] = None, 
                         limit: int = 100) -> List[Event]:
        """Get recent events, optionally filtered by type"""
        events = self.event_history[-limit:]
        
        if event_type:
            events = [e for e in events if e.event_type == event_type]
        
        return events
    
    def get_event_stats(self) -> Dict:
        """Get statistics about events"""
        stats = {
            "total_events": len(self.event_history),
            "events_by_type": {}
        }
        
        for event_type in EventType:
            count = sum(1 for e in self.event_history if e.event_type == event_type)
            if count > 0:
                stats["events_by_type"][event_type.value] = count
        
        return stats
    
    def clear_history(self) -> None:
        """Clear event history"""
        self.event_history.clear()
        logger.info("✓ Event history cleared")


# ============================================================================
# GLOBAL EVENT BUS INSTANCE
# ============================================================================

# Single global event bus instance
_event_bus: Optional[EventBus] = None


def get_event_bus() -> EventBus:
    """Get or create global event bus"""
    global _event_bus
    if _event_bus is None:
        _event_bus = EventBus()
    return _event_bus


# ============================================================================
# USAGE EXAMPLES
# ============================================================================

def example_usage():
    """Example usage of Event Bus"""
    
    bus = get_event_bus()
    
    # Handler for ingestion complete
    def handle_ingestion_complete(event: Event):
        print(f"✓ Ingestion complete: {event.payload['chunks_count']} chunks")
    
    # Handler for optimization complete
    def handle_optimization_complete(event: Event):
        improvement = event.payload.get('improvement', 0)
        print(f"✓ Optimization complete: {improvement:+.2f} quality improvement")
    
    # Subscribe handlers
    bus.subscribe(EventType.DOC_INGEST_COMPLETE, handle_ingestion_complete)
    bus.subscribe(EventType.OPTIMIZATION_COMPLETE, handle_optimization_complete)
    
    # Publish events
    print("\n=== Publishing Events ===")
    bus.ingestion_complete("doc_123", chunks_count=42, status="success", metadata={})
    bus.optimization_complete("doc_123", strategy="reindex", quality_before=0.75, 
                            quality_after=0.88, status="success")
    
    # Get statistics
    print("\n=== Event Statistics ===")
    stats = bus.get_event_stats()
    print(json.dumps(stats, indent=2))


if __name__ == "__main__":
    example_usage()
