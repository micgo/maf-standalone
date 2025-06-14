#!/usr/bin/env python3
"""
Tests for EventBus (in-memory implementation)
"""
import time
import threading
from unittest import TestCase

from multi_agent_framework.core.event_bus import InMemoryEventBus
from multi_agent_framework.core.event_bus_interface import EventType


class TestEventBus(TestCase):
    """Test in-memory event bus functionality"""
    
    def setUp(self):
        """Create event bus for tests"""
        self.event_bus = InMemoryEventBus()
        
    def tearDown(self):
        """Stop event bus"""
        self.event_bus.stop()
    
    def test_publish_and_subscribe(self):
        """Test basic publish/subscribe"""
        received_events = []
        
        def handler(event):
            received_events.append(event)
        
        # Subscribe to event type
        self.event_bus.subscribe(EventType.TASK_CREATED, handler)
        
        # Publish event
        test_event = {
            'type': EventType.TASK_CREATED,
            'task_id': 'test-123',
            'description': 'Test task'
        }
        self.event_bus.publish(test_event)
        
        # Give time for processing
        time.sleep(0.1)
        
        # Check event received
        self.assertEqual(len(received_events), 1)
        self.assertEqual(received_events[0]['task_id'], 'test-123')
    
    def test_multiple_subscribers(self):
        """Test multiple subscribers to same event"""
        handler1_events = []
        handler2_events = []
        
        def handler1(event):
            handler1_events.append(event)
        
        def handler2(event):
            handler2_events.append(event)
        
        # Subscribe both handlers
        self.event_bus.subscribe(EventType.TASK_COMPLETED, handler1)
        self.event_bus.subscribe(EventType.TASK_COMPLETED, handler2)
        
        # Publish event
        test_event = {
            'type': EventType.TASK_COMPLETED,
            'task_id': 'test-456'
        }
        self.event_bus.publish(test_event)
        
        # Give time for processing
        time.sleep(0.1)
        
        # Both handlers should receive event
        self.assertEqual(len(handler1_events), 1)
        self.assertEqual(len(handler2_events), 1)
    
    def test_different_event_types(self):
        """Test subscribing to different event types"""
        created_events = []
        completed_events = []
        
        def created_handler(event):
            created_events.append(event)
        
        def completed_handler(event):
            completed_events.append(event)
        
        # Subscribe to different types
        self.event_bus.subscribe(EventType.TASK_CREATED, created_handler)
        self.event_bus.subscribe(EventType.TASK_COMPLETED, completed_handler)
        
        # Publish different events
        self.event_bus.publish({'type': EventType.TASK_CREATED, 'id': '1'})
        self.event_bus.publish({'type': EventType.TASK_COMPLETED, 'id': '2'})
        self.event_bus.publish({'type': EventType.TASK_CREATED, 'id': '3'})
        
        # Give time for processing
        time.sleep(0.1)
        
        # Check correct routing
        self.assertEqual(len(created_events), 2)
        self.assertEqual(len(completed_events), 1)
    
    def test_unsubscribe(self):
        """Test unsubscribing from events"""
        received_events = []
        
        def handler(event):
            received_events.append(event)
        
        # Subscribe
        self.event_bus.subscribe(EventType.TASK_FAILED, handler)
        
        # Publish first event
        self.event_bus.publish({'type': EventType.TASK_FAILED, 'id': '1'})
        time.sleep(0.1)
        
        # Unsubscribe
        self.event_bus.unsubscribe(EventType.TASK_FAILED, handler)
        
        # Publish second event
        self.event_bus.publish({'type': EventType.TASK_FAILED, 'id': '2'})
        time.sleep(0.1)
        
        # Should only receive first event
        self.assertEqual(len(received_events), 1)
        self.assertEqual(received_events[0]['id'], '1')
    
    def test_event_queue_processing(self):
        """Test that events are processed in order"""
        received_events = []
        
        def handler(event):
            received_events.append(event['id'])
        
        self.event_bus.subscribe(EventType.TASK_UPDATED, handler)
        
        # Publish multiple events quickly
        for i in range(10):
            self.event_bus.publish({'type': EventType.TASK_UPDATED, 'id': i})
        
        # Give time for processing
        time.sleep(0.2)
        
        # Check all received in order
        self.assertEqual(received_events, list(range(10)))
    
    def test_stop_event_bus(self):
        """Test stopping event bus"""
        received_events = []
        
        def handler(event):
            received_events.append(event)
        
        self.event_bus.subscribe(EventType.AGENT_STARTED, handler)
        
        # Publish event
        self.event_bus.publish({'type': EventType.AGENT_STARTED, 'id': '1'})
        time.sleep(0.1)
        
        # Stop event bus
        self.event_bus.stop()
        
        # Try to publish after stop
        self.event_bus.publish({'type': EventType.AGENT_STARTED, 'id': '2'})
        time.sleep(0.1)
        
        # Should only have first event
        self.assertEqual(len(received_events), 1)
    
    def test_concurrent_publishing(self):
        """Test concurrent event publishing"""
        received_events = []
        lock = threading.Lock()
        
        def handler(event):
            with lock:
                received_events.append(event)
        
        self.event_bus.subscribe(EventType.TASK_CREATED, handler)
        
        def publish_events(thread_id):
            for i in range(10):
                self.event_bus.publish({
                    'type': EventType.TASK_CREATED,
                    'thread': thread_id,
                    'id': i
                })
        
        # Create threads
        threads = []
        for i in range(3):
            thread = threading.Thread(target=publish_events, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for threads
        for thread in threads:
            thread.join()
        
        # Give time for processing
        time.sleep(0.3)
        
        # Should receive all events
        self.assertEqual(len(received_events), 30)
    
    def test_error_in_handler(self):
        """Test that errors in handlers don't crash event bus"""
        good_events = []
        
        def bad_handler(event):
            raise Exception("Test error")
        
        def good_handler(event):
            good_events.append(event)
        
        # Subscribe both handlers
        self.event_bus.subscribe(EventType.TASK_CREATED, bad_handler)
        self.event_bus.subscribe(EventType.TASK_CREATED, good_handler)
        
        # Publish event
        self.event_bus.publish({'type': EventType.TASK_CREATED, 'id': '1'})
        
        # Give time for processing
        time.sleep(0.1)
        
        # Good handler should still receive event
        self.assertEqual(len(good_events), 1)
    
    def test_all_event_types(self):
        """Test all defined event types"""
        received_events = {}
        
        def make_handler(event_type):
            def handler(event):
                received_events[event_type] = event
            return handler
        
        # Subscribe to all event types
        for event_type in EventType:
            self.event_bus.subscribe(event_type, make_handler(event_type))
        
        # Publish all event types
        for event_type in EventType:
            self.event_bus.publish({'type': event_type, 'test': True})
        
        # Give time for processing
        time.sleep(0.2)
        
        # Should receive all events
        self.assertEqual(len(received_events), len(EventType))
        for event_type in EventType:
            self.assertIn(event_type, received_events)


if __name__ == '__main__':
    import unittest
    unittest.main()