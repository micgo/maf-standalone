"""
Event-Driven Database Agent

This is the event-driven version of the database agent that handles
database schema design and migration tasks using events instead of polling.
"""

import os
import json
import re
import time
from typing import Dict, Any, Optional, List
from datetime import datetime

from .event_driven_base_agent import EventDrivenBaseAgent
from ..core.event_bus_interface import Event, EventType


class EventDrivenDatabaseAgent(EventDrivenBaseAgent):
    """
    Event-driven database agent for handling schema design and migrations
    """
    
    def __init__(self, model_provider="gemini", model_name="gemini-1.5-flash", project_config=None):
        super().__init__("db_agent", model_provider, model_name, project_config)
        
        # Define the root for SQL migration files
        self.db_root = os.path.abspath(os.path.join(self.project_root, "supabase", "migrations"))
        os.makedirs(self.db_root, exist_ok=True)
        
        # Track database operations
        self._migrations_created = 0
        self._schemas_designed = 0
        
        print(f"EventDrivenDatabaseAgent initialized. Output path: {self.db_root}")
    
    def _subscribe_to_events(self):
        """Subscribe to database-specific events"""
        super()._subscribe_to_events()
        
        # Subscribe to task retry events
        self.event_bus.subscribe(EventType.TASK_RETRY, self._handle_task_retry)
        
        # Subscribe to custom database events
        self.event_bus.subscribe(EventType.CUSTOM, self._handle_custom_event)
    
    def _handle_task_retry(self, event: Event):
        """Handle task retry events"""
        data = event.data
        
        # Check if retry is for this agent
        if data.get("assigned_agent") != self.name:
            return
        
        task_id = data.get("task_id")
        if not task_id:
            return
        
        print(f"{self.name}: Retrying task {task_id} (attempt {data.get('retry_count', 1)})")
        
        # Process as a new task assignment
        self._handle_task_assigned(Event(
            id=event.id,
            type=EventType.TASK_ASSIGNED,
            source=event.source,
            timestamp=event.timestamp,
            data=data,
            correlation_id=event.correlation_id
        ))
    
    def _handle_custom_event(self, event: Event):
        """Handle custom database events"""
        event_name = event.data.get('event_name', '')
        
        if event_name == 'schema_validation_request':
            # Handle schema validation requests
            schema_name = event.data.get('schema_name')
            print(f"{self.name}: Received schema validation request for {schema_name}")
            # Could trigger automatic validation
        
        elif event_name == 'api_created':
            # Handle new API creation - might need new tables
            api_path = event.data.get('path')
            print(f"{self.name}: New API created at {api_path}, checking if schema updates needed")
            # Could analyze API and suggest schema changes
    
    def process_task(self, task_id: str, task_data: Dict[str, Any]) -> Any:
        """
        Process database-related tasks
        
        Args:
            task_id: Unique task identifier
            task_data: Task information including description
            
        Returns:
            Task result
        """
        description = task_data.get('description', '')
        feature_id = task_data.get('feature_id', '')
        
        print(f"{self.name}: Processing task - {description}")
        
        try:
            # Analyze the task
            task_type = self._analyze_task_type(description)
            
            if task_type == "migration":
                result = self._create_migration(description, feature_id)
            elif task_type == "schema":
                result = self._design_schema(description, feature_id)
            elif task_type == "index":
                result = self._create_index(description, feature_id)
            elif task_type == "rls":
                result = self._create_rls_policies(description, feature_id)
            elif task_type == "update":
                result = self._update_schema(description, feature_id)
            else:
                result = self._handle_generic_task(description, feature_id)
            
            # Emit completion metrics
            self.emit_custom_event('database_metrics', {
                'migrations_created': self._migrations_created,
                'schemas_designed': self._schemas_designed,
                'task_type': task_type
            })
            
            return result
            
        except Exception as e:
            error_msg = f"Error processing database task: {str(e)}"
            print(f"{self.name}: {error_msg}")
            
            # Emit error event for monitoring
            self.emit_custom_event('database_error', {
                'task_id': task_id,
                'error': str(e),
                'task_type': task_type if 'task_type' in locals() else 'unknown'
            })
            
            raise
    
    def _analyze_task_type(self, description: str) -> str:
        """Analyze task description to determine type"""
        description_lower = description.lower()
        
        if any(word in description_lower for word in ['migration', 'migrate', 'alter']):
            return "migration"
        elif any(word in description_lower for word in ['schema', 'table', 'design', 'structure']):
            return "schema"
        elif any(word in description_lower for word in ['index', 'performance', 'optimize']):
            return "index"
        elif any(word in description_lower for word in ['rls', 'security', 'policy', 'permission']):
            return "rls"
        elif any(word in description_lower for word in ['update', 'modify', 'change']):
            return "update"
        else:
            return "generic"
    
    def _create_migration(self, description: str, feature_id: str) -> Dict[str, Any]:
        """Create a new database migration"""
        print(f"{self.name}: Creating migration for: {description}")
        
        # Analyze existing migrations
        existing_migrations = self._get_existing_migrations()
        existing_tables = self._extract_tables_from_migrations(existing_migrations)
        
        # Generate migration prompt
        prompt = self._build_migration_prompt(description, existing_tables)
        
        # Generate migration SQL
        migration_sql = self._generate_response(prompt, max_tokens=2000)
        
        if migration_sql:
            # Create migration file
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            migration_name = self._extract_migration_name(description)
            filename = f"{timestamp}_{migration_name}.sql"
            filepath = os.path.join(self.db_root, filename)
            
            # Write migration file
            with open(filepath, 'w') as f:
                f.write(migration_sql)
            
            self._migrations_created += 1
            
            # Emit migration created event
            self.emit_custom_event('migration_created', {
                'path': filepath,
                'feature_id': feature_id,
                'tables_affected': self._extract_affected_tables(migration_sql)
            })
            
            # Also emit schema updated event for other agents
            self.emit_custom_event('database_schema_updated', {
                'migration_file': filename,
                'changes': self._summarize_changes(migration_sql)
            })
            
            return {
                'status': 'success',
                'migration_file': filepath,
                'message': f"Successfully created migration: {filename}"
            }
        else:
            raise Exception("Failed to generate migration SQL")
    
    def _design_schema(self, description: str, feature_id: str) -> Dict[str, Any]:
        """Design a complete database schema"""
        print(f"{self.name}: Designing schema for: {description}")
        
        # Get existing schema information
        existing_tables = self._get_existing_schema()
        
        # Generate schema design prompt
        prompt = self._build_schema_prompt(description, existing_tables)
        
        # Generate schema SQL
        schema_sql = self._generate_response(prompt, max_tokens=3000)
        
        if schema_sql:
            # Create migration for the schema
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            schema_name = self._extract_schema_name(description)
            filename = f"{timestamp}_create_{schema_name}_schema.sql"
            filepath = os.path.join(self.db_root, filename)
            
            # Write schema file
            with open(filepath, 'w') as f:
                f.write(schema_sql)
            
            self._schemas_designed += 1
            
            return {
                'status': 'success',
                'schema_file': filepath,
                'tables_created': self._extract_table_names(schema_sql),
                'message': f"Successfully designed schema: {filename}"
            }
        else:
            raise Exception("Failed to generate schema design")
    
    def _create_index(self, description: str, feature_id: str) -> Dict[str, Any]:
        """Create database indexes for performance"""
        print(f"{self.name}: Creating indexes for: {description}")
        
        # Analyze which tables might need indexes
        prompt = self._build_index_prompt(description)
        
        index_sql = self._generate_response(prompt, max_tokens=1000)
        
        if index_sql:
            # Create index migration
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            filename = f"{timestamp}_add_indexes.sql"
            filepath = os.path.join(self.db_root, filename)
            
            with open(filepath, 'w') as f:
                f.write(index_sql)
            
            return {
                'status': 'success',
                'index_file': filepath,
                'message': f"Successfully created indexes: {filename}"
            }
        else:
            raise Exception("Failed to generate index SQL")
    
    def _create_rls_policies(self, description: str, feature_id: str) -> Dict[str, Any]:
        """Create Row Level Security policies"""
        print(f"{self.name}: Creating RLS policies for: {description}")
        
        # Generate RLS policies
        prompt = self._build_rls_prompt(description)
        
        rls_sql = self._generate_response(prompt, max_tokens=1500)
        
        if rls_sql:
            # Create RLS migration
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            filename = f"{timestamp}_add_rls_policies.sql"
            filepath = os.path.join(self.db_root, filename)
            
            with open(filepath, 'w') as f:
                f.write(rls_sql)
            
            return {
                'status': 'success',
                'rls_file': filepath,
                'message': f"Successfully created RLS policies: {filename}"
            }
        else:
            raise Exception("Failed to generate RLS policies")
    
    def _update_schema(self, description: str, feature_id: str) -> Dict[str, Any]:
        """Update existing schema"""
        print(f"{self.name}: Updating schema for: {description}")
        
        # Find the relevant migration or table
        target_table = self._find_target_table(description)
        
        if not target_table:
            raise Exception("Could not identify target table for update")
        
        # Generate update migration
        prompt = f"""
        Create a PostgreSQL migration to update the schema based on: {description}
        
        Target table: {target_table}
        
        Generate ALTER TABLE statements or other appropriate SQL to implement the changes.
        Include:
        1. The actual schema changes
        2. Any necessary data migrations
        3. Rollback comments if applicable
        
        Follow Supabase migration best practices.
        """
        
        update_sql = self._generate_response(prompt, max_tokens=1500)
        
        if update_sql:
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            filename = f"{timestamp}_update_{target_table}.sql"
            filepath = os.path.join(self.db_root, filename)
            
            with open(filepath, 'w') as f:
                f.write(update_sql)
            
            self._migrations_created += 1
            
            return {
                'status': 'success',
                'update_file': filepath,
                'table_updated': target_table,
                'message': f"Successfully created update migration: {filename}"
            }
        else:
            raise Exception("Failed to generate update SQL")
    
    def _handle_generic_task(self, description: str, feature_id: str) -> Dict[str, Any]:
        """Handle generic database tasks"""
        print(f"{self.name}: Handling generic database task: {description}")
        
        # Analyze what needs to be done
        prompt = f"""
        As a database architect, analyze this task: {description}
        
        Determine:
        1. What database changes are needed
        2. Which tables or schemas are affected
        3. The appropriate SQL approach for PostgreSQL/Supabase
        
        Provide a brief action plan.
        """
        
        analysis = self._generate_response(prompt, max_tokens=500)
        
        return {
            'status': 'success',
            'analysis': analysis,
            'message': "Task analyzed and plan created"
        }
    
    def _get_existing_migrations(self) -> List[str]:
        """Get list of existing migration files"""
        migrations = []
        if os.path.exists(self.db_root):
            for file in os.listdir(self.db_root):
                if file.endswith('.sql'):
                    migrations.append(os.path.join(self.db_root, file))
        return sorted(migrations)
    
    def _extract_tables_from_migrations(self, migrations: List[str]) -> Dict[str, List[str]]:
        """Extract table definitions from migrations"""
        tables = {}
        
        for migration_file in migrations:
            with open(migration_file, 'r') as f:
                content = f.read()
                
            # Extract CREATE TABLE statements
            table_pattern = r'CREATE TABLE\s+(?:IF NOT EXISTS\s+)?(\w+)\s*\((.*?)\);'
            matches = re.findall(table_pattern, content, re.IGNORECASE | re.DOTALL)
            
            for table_name, columns in matches:
                if table_name not in tables:
                    tables[table_name] = []
                # Simple column extraction
                column_lines = columns.strip().split(',')
                for line in column_lines:
                    col_match = re.match(r'\s*(\w+)\s+(\w+)', line.strip())
                    if col_match:
                        tables[table_name].append(f"{col_match.group(1)} {col_match.group(2)}")
        
        return tables
    
    def _get_existing_schema(self) -> Dict[str, Any]:
        """Get existing database schema information"""
        migrations = self._get_existing_migrations()
        tables = self._extract_tables_from_migrations(migrations)
        
        return {
            'tables': tables,
            'migration_count': len(migrations)
        }
    
    def _build_migration_prompt(self, description: str, existing_tables: dict) -> str:
        """Build prompt for migration generation"""
        tables_info = "\n".join([f"- {table}: {len(cols)} columns" 
                                for table, cols in existing_tables.items()])
        
        return f"""
        Create a PostgreSQL migration for Supabase based on: {description}
        
        Existing tables in the database:
        {tables_info}
        
        Generate a complete SQL migration that:
        1. Uses proper PostgreSQL syntax
        2. Includes IF NOT EXISTS clauses where appropriate
        3. Sets up proper foreign key relationships
        4. Includes appropriate indexes
        5. Enables RLS (Row Level Security) on tables
        6. Includes helpful comments
        7. Uses snake_case for table and column names
        8. Includes created_at and updated_at timestamps where appropriate
        
        The migration should be idempotent and safe to run.
        Provide only the SQL code, no explanations.
        """
    
    def _build_schema_prompt(self, description: str, existing_info: dict) -> str:
        """Build prompt for schema design"""
        return f"""
        Design a complete PostgreSQL database schema for: {description}
        
        Current database has {existing_info.get('migration_count', 0)} migrations.
        
        Design a schema that:
        1. Uses PostgreSQL best practices
        2. Normalizes data appropriately (3NF where suitable)
        3. Includes all necessary tables and relationships
        4. Uses appropriate data types
        5. Includes primary keys, foreign keys, and indexes
        6. Enables RLS on all tables
        7. Includes audit fields (created_at, updated_at)
        8. Uses snake_case naming convention
        9. Includes table and column comments
        
        Consider Supabase features like:
        - Auth integration (auth.users table)
        - Real-time subscriptions
        - Storage integration if needed
        
        Provide complete CREATE TABLE statements and related setup.
        """
    
    def _build_index_prompt(self, description: str) -> str:
        """Build prompt for index creation"""
        return f"""
        Create PostgreSQL indexes based on: {description}
        
        Generate CREATE INDEX statements that:
        1. Improve query performance for common access patterns
        2. Use appropriate index types (btree, gin, gist, etc.)
        3. Consider partial indexes where beneficial
        4. Include composite indexes for multi-column queries
        5. Name indexes descriptively
        6. Include comments explaining the index purpose
        
        Provide only the SQL statements.
        """
    
    def _build_rls_prompt(self, description: str) -> str:
        """Build prompt for RLS policy creation"""
        return f"""
        Create PostgreSQL Row Level Security policies based on: {description}
        
        Generate RLS policies that:
        1. Enable RLS on relevant tables
        2. Create policies for SELECT, INSERT, UPDATE, DELETE as needed
        3. Use auth.uid() for user-based access control
        4. Include appropriate role-based policies
        5. Ensure security while maintaining functionality
        6. Include policy descriptions
        
        Follow Supabase RLS best practices.
        Provide only the SQL statements.
        """
    
    def _extract_migration_name(self, description: str) -> str:
        """Extract a migration name from description"""
        # Remove special characters and convert to snake_case
        words = re.findall(r'\w+', description.lower())
        # Take first few meaningful words
        meaningful_words = [w for w in words if len(w) > 2 and w not in 
                           ['the', 'and', 'for', 'with', 'that', 'this']]
        return '_'.join(meaningful_words[:4])
    
    def _extract_schema_name(self, description: str) -> str:
        """Extract schema name from description"""
        # Look for key nouns
        words = re.findall(r'\b[A-Za-z]+\b', description)
        for word in words:
            if word.lower() in ['user', 'product', 'order', 'payment', 'auth', 
                               'subscription', 'notification', 'cart', 'inventory']:
                return word.lower()
        return 'schema'
    
    def _extract_affected_tables(self, sql: str) -> List[str]:
        """Extract table names affected by SQL"""
        tables = set()
        
        # Patterns to find table names
        patterns = [
            r'CREATE TABLE\s+(?:IF NOT EXISTS\s+)?(\w+)',
            r'ALTER TABLE\s+(\w+)',
            r'DROP TABLE\s+(?:IF EXISTS\s+)?(\w+)',
            r'INSERT INTO\s+(\w+)',
            r'UPDATE\s+(\w+)',
            r'DELETE FROM\s+(\w+)'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, sql, re.IGNORECASE)
            tables.update(matches)
        
        return list(tables)
    
    def _extract_table_names(self, sql: str) -> List[str]:
        """Extract created table names from SQL"""
        pattern = r'CREATE TABLE\s+(?:IF NOT EXISTS\s+)?(\w+)'
        return re.findall(pattern, sql, re.IGNORECASE)
    
    def _summarize_changes(self, sql: str) -> str:
        """Summarize the changes in a migration"""
        changes = []
        
        if 'CREATE TABLE' in sql.upper():
            tables = self._extract_table_names(sql)
            changes.append(f"Created tables: {', '.join(tables)}")
        
        if 'ALTER TABLE' in sql.upper():
            changes.append("Modified existing tables")
        
        if 'CREATE INDEX' in sql.upper():
            changes.append("Added indexes")
        
        if 'CREATE POLICY' in sql.upper():
            changes.append("Added RLS policies")
        
        return "; ".join(changes) if changes else "Database changes"
    
    def _find_target_table(self, description: str) -> Optional[str]:
        """Find target table from description"""
        # Look for table names in description
        existing_tables = self._get_existing_schema()['tables']
        
        description_lower = description.lower()
        for table_name in existing_tables:
            if table_name.lower() in description_lower:
                return table_name
        
        # Try to extract from common patterns
        patterns = [
            r'table\s+(\w+)',
            r'(\w+)\s+table',
            r'update\s+(\w+)',
            r'modify\s+(\w+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, description, re.IGNORECASE)
            if match:
                potential_table = match.group(1).lower()
                # Check if it exists
                for table_name in existing_tables:
                    if table_name.lower() == potential_table:
                        return table_name
        
        return None


if __name__ == "__main__":
    agent = EventDrivenDatabaseAgent()
    agent.run()