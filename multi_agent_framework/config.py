"""
Configuration settings for the Multi-Agent Framework
"""

# Retry configuration
MAX_RETRY_ATTEMPTS = 3  # Maximum number of retries for failed tasks
RETRY_DELAY_SECONDS = 5  # Delay between retries

# Task timeout configuration
TASK_TIMEOUT_MINUTES = 30  # Tasks running longer than this are considered stalled
HEALTH_CHECK_INTERVAL_SECONDS = 60  # How often to perform health checks

# Agent polling intervals
DEFAULT_POLL_INTERVAL_SECONDS = 5  # Default polling interval for agents
ORCHESTRATOR_POLL_INTERVAL_SECONDS = 10  # Orchestrator polling interval

# Message queue configuration
MESSAGE_RETENTION_HOURS = 24  # How long to keep processed messages

# Error handling
CRASH_RECOVERY_ENABLED = True  # Whether to attempt automatic recovery from crashes
DETAILED_ERROR_LOGGING = True  # Whether to log detailed error information

# State management
STATE_SYNC_INTERVAL_SECONDS = 30  # How often to sync state from disk
AUTO_CLEANUP_COMPLETED_TASKS = False  # Whether to automatically clean up completed tasks

# Performance tuning
MAX_CONCURRENT_TASKS_PER_AGENT = 1  # Maximum tasks an agent can handle concurrently
BATCH_TASK_ASSIGNMENT = True  # Whether to batch task assignments for efficiency

# Event Bus Configuration
EVENT_BUS_CONFIG = {
    # Event bus type: 'inmemory' or 'kafka'
    # Can be overridden by EVENT_BUS_TYPE environment variable
    'type': 'inmemory',
    
    # Kafka-specific configuration (only used when type='kafka')
    'kafka_config': {
        # Kafka broker addresses (comma-separated in env var KAFKA_BOOTSTRAP_SERVERS)
        'bootstrap_servers': ['localhost:9092'],
        
        # Consumer group for this application (env var KAFKA_CONSUMER_GROUP)
        'consumer_group': 'multi-agent-framework',
        
        # Maximum worker threads for event handling (env var KAFKA_MAX_WORKERS)
        'max_workers': 10
    }
}

# Event-driven mode configuration
EVENT_DRIVEN_MODE = True  # If True, agents use event-driven architecture instead of polling
EVENT_HEARTBEAT_INTERVAL = 30  # Seconds between agent heartbeats in event-driven mode