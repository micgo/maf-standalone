#!/usr/bin/env python3
"""
Tests for Kafka event bus implementation
"""
import os
import sys
import time
import json
import tempfile
import shutil
from typing import Dict, Any, List
from unittest import TestCase, main, skipIf
from threading import Event as ThreadingEvent

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from multi_agent_framework.core.event_bus_factory import get_event_bus
from multi_agent_framework.core.event_bus_interface import Event, EventType
from multi_agent_framework.core.kafka_event_bus import KafkaEventBus

# Check if Kafka is available
try:
    import kafka
    from kafka import KafkaProducer, KafkaConsumer
    from kafka.admin import KafkaAdminClient, NewTopic
    KAFKA_AVAILABLE = True
except ImportError:
    KAFKA_AVAILABLE = False

# Check if Kafka server is running
KAFKA_RUNNING = False
if KAFKA_AVAILABLE:
    try:
        admin = KafkaAdminClient(
            bootstrap_servers=['localhost:9092'],
            request_timeout_ms=5000
        )
        # Try to list topics to check if Kafka is running
        admin.list_topics()
        KAFKA_RUNNING = True
        admin.close()
    except:
        KAFKA_RUNNING = False


@skipIf(not KAFKA_AVAILABLE, "kafka-python not installed")
@skipIf(not KAFKA_RUNNING, "Kafka server not running on localhost:9092")
class KafkaEventBusTest(TestCase):
    """Test Kafka event bus functionality"""
    
    def setUp(self):
        """Set up test environment"""
        # Create unique test topics
        self.test_id = str(int(time.time() * 1000))
        self.test_topic = f'maf_test_{self.test_id}'
        
        # Initialize Kafka event bus
        self.event_bus = KafkaEventBus(
            bootstrap_servers=['localhost:9092'],
            consumer_group=f'test_group_{self.test_id}'
        )
        
        # Track received events
        self.received_events = []
        
    def tearDown(self):
        """Clean up test environment"""
        # Stop event bus
        self.event_bus.stop()
        
        # Clean up test topics
        try:
            admin = KafkaAdminClient(bootstrap_servers=['localhost:9092'])
            # Get all topics
            topics = admin.list_topics()
            # Find our test topics
            test_topics = [t for t in topics if t.startswith(f'maf_test_{self.test_id}')]
            if test_topics:
                admin.delete_topics(test_topics)
            admin.close()
        except:
            pass
            
    def _track_event(self, event: Event):
        """Track received events"""
        self.received_events.append(event)
        
    def test_publish_and_subscribe(self):
        """Test basic publish and subscribe functionality"""
        # Subscribe to task created events
        self.event_bus.subscribe(EventType.TASK_CREATED, self._track_event)
        
        # Publish an event
        test_event = Event(
            type=EventType.TASK_CREATED,
            data={
                'task_id': 'test_001',
                'description': 'Test task',
                'agent': 'test_agent'
            }
        )
        self.event_bus.publish(test_event)
        
        # Wait for event to be received
        timeout = 10
        start_time = time.time()
        while len(self.received_events) == 0 and time.time() - start_time < timeout:
            time.sleep(0.1)
            
        # Verify event was received
        self.assertEqual(len(self.received_events), 1)
        received = self.received_events[0]
        self.assertEqual(received.type, EventType.TASK_CREATED)
        self.assertEqual(received.data['task_id'], 'test_001')
        
    def test_multiple_subscribers(self):
        """Test multiple subscribers to same event type"""
        received_by_sub1 = []
        received_by_sub2 = []
        
        def subscriber1(event: Event):
            received_by_sub1.append(event)
            
        def subscriber2(event: Event):
            received_by_sub2.append(event)
            
        # Subscribe both handlers
        self.event_bus.subscribe(EventType.TASK_COMPLETED, subscriber1)
        self.event_bus.subscribe(EventType.TASK_COMPLETED, subscriber2)
        
        # Publish event
        test_event = Event(
            type=EventType.TASK_COMPLETED,
            data={'task_id': 'test_002', 'result': 'success'}
        )
        self.event_bus.publish(test_event)
        
        # Wait for events
        timeout = 10
        start_time = time.time()
        while (len(received_by_sub1) == 0 or len(received_by_sub2) == 0) and time.time() - start_time < timeout:
            time.sleep(0.1)
            
        # Both subscribers should receive the event
        self.assertEqual(len(received_by_sub1), 1)
        self.assertEqual(len(received_by_sub2), 1)
        
    def test_different_event_types(self):
        """Test subscribing to different event types"""
        task_events = []
        system_events = []
        
        def task_handler(event: Event):
            task_events.append(event)
            
        def system_handler(event: Event):
            system_events.append(event)
            
        # Subscribe to different event types
        self.event_bus.subscribe(EventType.TASK_ASSIGNED, task_handler)
        self.event_bus.subscribe(EventType.SYSTEM_SHUTDOWN, system_handler)
        
        # Publish different events
        task_event = Event(
            type=EventType.TASK_ASSIGNED,
            data={'task_id': 'test_003', 'agent': 'frontend_agent'}
        )
        system_event = Event(
            type=EventType.SYSTEM_SHUTDOWN,
            data={'reason': 'test'}
        )
        
        self.event_bus.publish(task_event)
        self.event_bus.publish(system_event)
        
        # Wait for events
        timeout = 10
        start_time = time.time()
        while (len(task_events) == 0 or len(system_events) == 0) and time.time() - start_time < timeout:
            time.sleep(0.1)
            
        # Each handler should only receive its subscribed event type
        self.assertEqual(len(task_events), 1)
        self.assertEqual(len(system_events), 1)
        self.assertEqual(task_events[0].type, EventType.TASK_ASSIGNED)
        self.assertEqual(system_events[0].type, EventType.SYSTEM_SHUTDOWN)
        
    def test_event_persistence(self):
        """Test that events are persisted in Kafka"""
        # Publish event before subscribing
        test_event = Event(
            type=EventType.TASK_CREATED,
            data={'task_id': 'persist_001', 'description': 'Persistence test'}
        )
        self.event_bus.publish(test_event)
        
        # Wait a bit to ensure event is in Kafka
        time.sleep(1)
        
        # Create new event bus instance with same consumer group
        new_event_bus = KafkaEventBus(
            bootstrap_servers=['localhost:9092'],
            consumer_group=f'test_group_{self.test_id}'
        )
        
        received = []
        new_event_bus.subscribe(EventType.TASK_CREATED, lambda e: received.append(e))
        
        # Should not receive the event immediately (already consumed by group)
        time.sleep(2)
        self.assertEqual(len(received), 0)
        
        # Create new consumer group - should see the event
        another_event_bus = KafkaEventBus(
            bootstrap_servers=['localhost:9092'],
            consumer_group=f'test_group_{self.test_id}_new'
        )
        
        new_received = []
        another_event_bus.subscribe(EventType.TASK_CREATED, lambda e: new_received.append(e))
        
        # Wait for event
        timeout = 10
        start_time = time.time()
        while len(new_received) == 0 and time.time() - start_time < timeout:
            time.sleep(0.1)
            
        # Should receive the persisted event
        self.assertEqual(len(new_received), 1)
        self.assertEqual(new_received[0].data['task_id'], 'persist_001')
        
        # Clean up
        new_event_bus.stop()
        another_event_bus.stop()
        
    def test_high_volume_events(self):
        """Test handling high volume of events"""
        num_events = 100
        received = []
        
        self.event_bus.subscribe(EventType.TASK_CREATED, lambda e: received.append(e))
        
        # Publish many events rapidly
        for i in range(num_events):
            event = Event(
                type=EventType.TASK_CREATED,
                data={'task_id': f'volume_{i:04d}', 'index': i}
            )
            self.event_bus.publish(event)
            
        # Wait for all events
        timeout = 30
        start_time = time.time()
        while len(received) < num_events and time.time() - start_time < timeout:
            time.sleep(0.1)
            
        # Should receive all events
        self.assertEqual(len(received), num_events)
        
        # Verify all indices are present
        indices = {e.data['index'] for e in received}
        self.assertEqual(len(indices), num_events)
        
    def test_error_handling(self):
        """Test error handling in event processing"""
        successful_events = []
        error_count = [0]
        
        def faulty_handler(event: Event):
            # Fail on specific events
            if 'fail' in event.data.get('task_id', ''):
                error_count[0] += 1
                raise Exception("Simulated error")
            successful_events.append(event)
            
        self.event_bus.subscribe(EventType.TASK_CREATED, faulty_handler)
        
        # Publish mix of good and bad events
        events = [
            Event(type=EventType.TASK_CREATED, data={'task_id': 'good_001'}),
            Event(type=EventType.TASK_CREATED, data={'task_id': 'fail_001'}),
            Event(type=EventType.TASK_CREATED, data={'task_id': 'good_002'}),
            Event(type=EventType.TASK_CREATED, data={'task_id': 'fail_002'}),
            Event(type=EventType.TASK_CREATED, data={'task_id': 'good_003'}),
        ]
        
        for event in events:
            self.event_bus.publish(event)
            
        # Wait for processing
        time.sleep(5)
        
        # Should process good events despite errors
        self.assertEqual(len(successful_events), 3)
        self.assertEqual(error_count[0], 2)
        
        # Verify correct events were processed
        processed_ids = {e.data['task_id'] for e in successful_events}
        self.assertEqual(processed_ids, {'good_001', 'good_002', 'good_003'})
        
    def test_graceful_shutdown(self):
        """Test graceful shutdown of event bus"""
        received = []
        shutdown_complete = ThreadingEvent()
        
        def slow_handler(event: Event):
            # Simulate slow processing
            time.sleep(0.5)
            received.append(event)
            if event.data['task_id'] == 'last':
                shutdown_complete.set()
                
        self.event_bus.subscribe(EventType.TASK_CREATED, slow_handler)
        
        # Publish several events
        for i in range(5):
            task_id = 'last' if i == 4 else f'task_{i}'
            event = Event(
                type=EventType.TASK_CREATED,
                data={'task_id': task_id}
            )
            self.event_bus.publish(event)
            
        # Start shutdown while events are being processed
        time.sleep(0.2)
        self.event_bus.stop()
        
        # Wait for shutdown to complete
        shutdown_complete.wait(timeout=10)
        
        # All events should have been processed before shutdown
        self.assertEqual(len(received), 5)


@skipIf(KAFKA_AVAILABLE and not KAFKA_RUNNING, "Kafka not running - integration tests skipped")
class EventBusFactoryTest(TestCase):
    """Test event bus factory functionality"""
    
    def test_inmemory_event_bus_creation(self):
        """Test creating in-memory event bus"""
        event_bus = get_event_bus('inmemory')
        self.assertIsNotNone(event_bus)
        
        # Should be able to publish and subscribe
        received = []
        event_bus.subscribe(EventType.TASK_CREATED, lambda e: received.append(e))
        
        event = Event(type=EventType.TASK_CREATED, data={'test': True})
        event_bus.publish(event)
        
        # In-memory is synchronous
        self.assertEqual(len(received), 1)
        
        event_bus.stop()
        
    @skipIf(not KAFKA_AVAILABLE, "kafka-python not installed")
    @skipIf(not KAFKA_RUNNING, "Kafka server not running")
    def test_kafka_event_bus_creation(self):
        """Test creating Kafka event bus"""
        event_bus = get_event_bus('kafka')
        self.assertIsNotNone(event_bus)
        self.assertIsInstance(event_bus, KafkaEventBus)
        event_bus.stop()
        
    def test_invalid_event_bus_type(self):
        """Test creating invalid event bus type"""
        with self.assertRaises(ValueError):
            get_event_bus('invalid_type')


if __name__ == '__main__':
    main()