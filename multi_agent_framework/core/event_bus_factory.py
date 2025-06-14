"""
Event Bus Factory - Creates the appropriate event bus implementation

This module provides a factory pattern for creating event bus instances
based on configuration, allowing easy switching between implementations.
"""

import os
import threading
from typing import Dict, Any, Optional

from .event_bus_interface import IEventBus
from .event_bus import InMemoryEventBus
from .kafka_event_bus import KafkaEventBus


class EventBusFactory:
    """Factory for creating event bus instances"""

    # Supported event bus types
    EVENT_BUS_TYPES = {
        'inmemory': InMemoryEventBus,
        'kafka': KafkaEventBus
    }

    @staticmethod
    def create_event_bus(config: Optional[Dict[str, Any]] = None) -> IEventBus:
        """
        Create an event bus instance based on configuration

        Args:
            config: Configuration dictionary with following keys:
                - type: 'inmemory' or 'kafka' (default: 'inmemory')
                - kafka_config: Configuration for Kafka (if type is 'kafka')
                    - bootstrap_servers: List of Kafka brokers
                    - consumer_group: Consumer group name
                    - max_workers: Maximum worker threads

        Returns:
            Event bus instance implementing IEventBus
        """
        if config is None:
            config = {}

        # Get event bus type from config or environment
        bus_type = config.get('type', os.getenv('EVENT_BUS_TYPE', 'inmemory')).lower()

        if bus_type not in EventBusFactory.EVENT_BUS_TYPES:
            raise ValueError(
                f"Unsupported event bus type: {bus_type}. "
                f"Supported types: {list(EventBusFactory.EVENT_BUS_TYPES.keys())}"
            )

        # Create the appropriate event bus
        if bus_type == 'inmemory':
            return InMemoryEventBus()

        elif bus_type == 'kafka':
            kafka_config = config.get('kafka_config', {})

            # Get Kafka configuration from environment if not in config
            bootstrap_servers = kafka_config.get(
                'bootstrap_servers',
                os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092').split(',')
            )
            consumer_group = kafka_config.get(
                'consumer_group',
                os.getenv('KAFKA_CONSUMER_GROUP', 'multi-agent-framework')
            )
            max_workers = kafka_config.get(
                'max_workers',
                int(os.getenv('KAFKA_MAX_WORKERS', '10'))
            )

            return KafkaEventBus(
                bootstrap_servers=bootstrap_servers,
                consumer_group=consumer_group,
                max_workers=max_workers
            )


# Global event bus instance management
_global_event_bus: Optional[IEventBus] = None
_global_event_bus_lock = threading.Lock()


def get_event_bus(config: Optional[Dict[str, Any]] = None) -> IEventBus:
    """
    Get the global event bus instance

    This function ensures a singleton pattern for the event bus.
    The first call creates the event bus with the provided config,
    subsequent calls return the same instance.

    Args:
        config: Configuration for event bus (only used on first call)

    Returns:
        Global event bus instance
    """
    global _global_event_bus

    if _global_event_bus is None:
        with _global_event_bus_lock:
            if _global_event_bus is None:
                _global_event_bus = EventBusFactory.create_event_bus(config)
                _global_event_bus.start()

    return _global_event_bus


def reset_event_bus() -> None:
    """
    Reset the global event bus instance

    This is useful for testing or when switching event bus implementations.
    """
    global _global_event_bus

    with _global_event_bus_lock:
        if _global_event_bus is not None:
            _global_event_bus.stop()
            _global_event_bus = None
