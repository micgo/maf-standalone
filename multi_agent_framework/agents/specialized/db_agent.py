import os
import sys
import json
import time
import uuid

# Use relative imports
from ..base_agent_configurable import BaseAgent
from ...core.project_config import ProjectConfig
from ...core.project_analyzer import ProjectAnalyzer
from ...core.file_integrator import FileIntegrator

class DbAgent(BaseAgent):
    """
    The DbAgent is responsible for designing PostgreSQL schemas and generating SQL migration files,
    aligned with Supabase's approach to database management, and can now propose direct modifications
    to existing schema/migration files.
    """
    def __init__(self, project_config=None, model_provider="gemini", model_name="gemini-1.5-flash"):  # SQL generation is straightforward
        super().__init__("db_agent", project_config, model_provider, model_name)
        # Define the root for SQL migration files
        self.db_root = os.path.abspath(os.path.join(self.project_root, "supabase", "migrations"))
        os.makedirs(self.db_root, exist_ok=True)
        # Initialize integration components
        self.project_analyzer = ProjectAnalyzer(self.project_root)
        self.file_integrator = FileIntegrator(self.project_root)
        print(f"DbAgent initialized. Output path: {self.db_root}")

    def run(self):
        """
        Main loop for the DbAgent to continuously receive and process messages.
        """
        print(f"{self.name} started. Waiting for tasks...")
        while True:
            messages = self.receive_messages()
            for msg in messages:
                self._process_message(msg)
            time.sleep(3) # Poll every 3 seconds

    def _process_message(self, msg):
        """
        Processes incoming messages from the message bus.
        Handles 'new_task' and 'review_and_retry' message types.
        """
        if msg["type"] == "new_task":
            task_id = msg["task_id"]
            task_description = msg["content"]
            print(f"DbAgent received task {task_id}: {task_description}")
            self.state_manager.update_task_status(task_id, "in_progress")

            is_modification = any(keyword in task_description.lower() for keyword in ["alter", "modify", "update", "add column", "drop column"])

            # Generate database schema
            generated_sql, target_file = self._generate_db_schema(task_description)

            if generated_sql and generated_sql.strip():
                # For DB migrations, we need to create a new migration file
                # Use proper timestamp format: YYYYMMDDHHmmss
                from datetime import datetime
                timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                
                # Extract table name from task description for filename
                table_name = "event_rsvps"  # Default
                if "event_rsvps" in task_description.lower():
                    table_name = "event_rsvps"
                elif "table" in task_description.lower():
                    # Try to extract table name from description
                    import re
                    match = re.search(r"'(\w+)'|\"(\w+)\"|`(\w+)`", task_description)
                    if match:
                        table_name = match.group(1) or match.group(2) or match.group(3)
                
                migration_filename = f"{timestamp}_create_{table_name}_table.sql"
                migration_path = os.path.join(self.project_root, "supabase", "migrations", migration_filename)
                
                # Write the migration file
                os.makedirs(os.path.dirname(migration_path), exist_ok=True)
                with open(migration_path, 'w') as f:
                    f.write(generated_sql)
                
                result = {'success': True, 'path': migration_path, 'action': 'created'}

                if result['success']:
                    print(f"DbAgent: Successfully {result['action']} migration: {result['path']}")
                    self.send_message("orchestrator", task_id, f"Successfully designed DB schema migration: {result['path']}", "task_completed")
                else:
                    print(f"DbAgent: Integration failed: {result['error']}")
                    self.send_message("orchestrator", task_id, f"Failed to integrate migration: {result['error']}", "task_failed")
            else:
                print("DbAgent: Failed to generate DB schema (LLM response was None or empty).")
                self.send_message("orchestrator", task_id, "Failed to generate DB schema (LLM response was empty or invalid).", "task_failed")

        elif msg["type"] == "review_and_retry":
            task_id = msg["task_id"]
            error_content = msg["content"]
            print(f"DbAgent: Received review and retry request for task {task_id}. Error: {error_content}")
            self.send_message("orchestrator", task_id, "Attempting retry after reviewing error.", "status_update")
            
            original_task_description = self.state_manager.get_task(task_id)['description']
            is_modification = any(keyword in original_task_description.lower() for keyword in ["alter", "modify", "update", "add column", "drop column"])
            generated_sql, target_file_suggestion = self._generate_db_schema(original_task_description)

            if generated_sql and generated_sql.strip():
                if is_modification and target_file_suggestion and os.path.exists(target_file_suggestion):
                    output_filename = os.path.basename(target_file_suggestion).replace(".sql", f"_retry_{task_id[:4]}.sql")
                    output_path = os.path.join(os.path.dirname(target_file_suggestion), output_filename)
                else:
                    from datetime import datetime
                    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                    output_filename = f"{timestamp}_retry_{task_id[:8]}.sql"
                    output_path = os.path.join(self.db_root, output_filename)
                try:
                    os.makedirs(os.path.dirname(output_path), exist_ok=True)
                    with open(output_path, "w") as f:
                        f.write(generated_sql)
                    print(f"DbAgent: Retried schema saved to {output_path}")
                    self.send_message("orchestrator", task_id, f"Task retried and completed with new schema: {output_path}", "task_completed")
                except Exception as e:
                    print(f"DbAgent: Error writing retried file {output_path}: {e}")
                    self.send_message("orchestrator", task_id, f"Failed retry attempt: {e}", "task_failed")
            else:
                print("DbAgent: Failed to generate DB schema on retry (LLM response was None or empty).")
                self.send_message("orchestrator", task_id, "Failed to generate DB schema on retry (LLM response was empty or invalid).", "task_failed")
        else:
            print(f"DbAgent: Unknown message type {msg['type']}")

    def _get_existing_db_schema_context(self, max_files=3):
        """
        Reads and returns the content of the most recently modified SQL schema/migration files
        to provide context to the LLM. Also returns the path to the most recent file.
        """
        context = []
        most_recent_file_path = None
        try:
            if not os.path.exists(self.db_root):
                return "", None

            files_in_dir = [os.path.join(self.db_root, f) for f in os.listdir(self.db_root)
                            if f.endswith(('.sql')) and os.path.isfile(os.path.join(self.db_root, f))]
            
            files_in_dir.sort(key=os.path.getmtime, reverse=True)

            if files_in_dir:
                most_recent_file_path = files_in_dir[0]
                
            for i, file_path in enumerate(files_in_dir[:max_files]):
                with open(file_path, 'r') as f:
                    content = f.read()
                    relative_path = os.path.relpath(file_path, self.project_root)
                    context.append(f"--- Existing File: {relative_path} ---\n```sql\n{content}\n```\n")
        except Exception as e:
            print(f"ERROR: DbAgent - Could not read existing DB schema for context: {e}")
        
        return "\n".join(context), most_recent_file_path


    def _generate_db_schema(self, task_description):
        """
        Uses the LLM to generate PostgreSQL SQL DDL, aligned with Supabase migrations.
        If is_modification is True, it prompts for a direct update to an existing schema.
        Returns (generated_sql, suggested_target_file_path)
        """
        existing_schema_context, most_recent_sql_file = self._get_existing_db_schema_context()
        
        # Check if this is a modification task
        is_modification = any(keyword in task_description.lower() for keyword in ["alter", "modify", "update", "add column", "drop column"])
        
        if is_modification and most_recent_sql_file:
            prompt = f"""You are a Database Architect Agent specializing in PostgreSQL databases,
            managed through Supabase.
            Your task is to **modify an existing SQL migration file** to address the following requirement:
            "{task_description}"

            You should propose the exact SQL `ALTER TABLE`, `CREATE INDEX`, or other statements
            needed to implement this change within the context of an existing migration.
            
            Consider the most recent existing SQL migration file provided in the context below. Your output
            should be a self-contained SQL snippet that can be appended to or inserted into such a file.
            If the change is complex, provide a full updated migration file.
            
            {f"Existing SQL Context (most recent migration first):\n{existing_schema_context}\n" if existing_schema_context else ""}

            Generate the full, complete SQL code. Do NOT omit any parts or use placeholders like '...'.
            Do NOT include any explanatory text, comments outside the code, or formatting outside of the SQL content.
            """
        else:
            prompt = f"""You are a Database Architect Agent specializing in PostgreSQL databases,
            managed through Supabase.
            Your task is to generate a new SQL DDL (Data Definition Language) script for the following requirement,
            suitable for a Supabase migration:
            "{task_description}"

            Include `CREATE TABLE`, `ALTER TABLE`, `CREATE INDEX`, or other relevant SQL statements.
            Ensure schemas are designed for efficient use with Supabase's API.
            
            {f"Consider the following existing SQL schema context from your project. Adapt your new schema/migration to fit with this existing structure and style:\n{existing_schema_context}\n" if existing_schema_context else ""}

            Generate the full, complete SQL code. Do NOT omit any parts or use placeholders like '...'.
            Do NOT include any explanatory text, comments outside the code, or formatting outside of the SQL content.
            """

        print(f"DbAgent: Requesting LLM to generate schema for: {task_description[:50]}...")
        response = self._generate_response(prompt, max_tokens=1500)

        if response and isinstance(response, str):
            cleaned_response = response.strip()
            if cleaned_response.startswith("```sql"):
                first_newline = cleaned_response.find('\n')
                cleaned_response = cleaned_response[first_newline+1:].strip() if first_newline != -1 else cleaned_response[len("```sql"):].strip()
            elif cleaned_response.startswith("```"):
                first_newline = cleaned_response.find('\n')
                cleaned_response = cleaned_response[first_newline+1:].strip() if first_newline != -1 else cleaned_response[len("```"):].strip()
            if cleaned_response.endswith("```"):
                cleaned_response = cleaned_response[:-len("```")].strip()
            return cleaned_response, most_recent_sql_file
        return response, most_recent_sql_file

if __name__ == "__main__":
    db_agent = DbAgent()  # Use default model from __init__
    db_agent.run()
