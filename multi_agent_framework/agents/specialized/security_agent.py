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

class SecurityAgent(BaseAgent):
    """
    The SecurityAgent is responsible for identifying potential security vulnerabilities
    and suggesting remediation strategies for Next.js, Supabase, and Stripe integrations.
    It can now propose direct modifications to existing security reports.
    """
    def __init__(self, project_config=None, model_provider="gemini", model_name="gemini-2.5-pro-preview-06-05"):  # Thorough security analysis
        super().__init__("security_agent", project_config, model_provider, model_name)
        # Define the root for security reports
        self.security_root = os.path.abspath(os.path.join(self.project_root, 'security_reports'))
        os.makedirs(self.security_root, exist_ok=True)
        # Initialize integration components
        self.project_analyzer = ProjectAnalyzer(self.project_root)
        self.file_integrator = FileIntegrator(self.project_root)
        print(f"SecurityAgent initialized. Output path: {self.security_root}")

        # Roots for scanning existing security-related files or documentation
        self.security_scan_roots = [
            self.security_root, # Existing security reports
            os.path.abspath(os.path.join(self.project_root, 'lib')), # For supabaseClient.ts, server.ts (potential security-relevant code)
            os.path.abspath(os.path.join(self.project_root, 'app', 'api')) # For API route security context
        ]


    def run(self):
        """
        Main loop for the SecurityAgent to continuously receive and process messages.
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
            print(f"SecurityAgent received task {task_id}: {task_description}")
            self.state_manager.update_task_status(task_id, "in_progress")

            is_modification = any(keyword in task_description.lower() for keyword in ["modify", "update", "add to existing", "revise", "re-evaluate"])
            # Generate security report
            security_report, target_file = self._analyze_security(task_description)

            if security_report and security_report.strip():
                # Check if this is an RLS policy task (should create SQL migration)
                if 'rls' in task_description.lower() or 'row level security' in task_description.lower():
                    # Create SQL migration file for RLS policies
                    result = self._create_rls_migration(security_report, task_description)
                else:
                    # Use new integration system for security reports
                    strategy = self.get_integration_strategy(task_description, 'security')
                    if strategy and strategy.get('target_dir'):
                        result = self.integrate_generated_content(security_report, strategy)
                    else:
                        # Fallback: create security report in security_reports directory
                        result = self._create_security_report(security_report, task_description)

                if result['success']:
                    print(f"SecurityAgent: Successfully {result['action']} security analysis: {result['path']}")
                    self.send_message("orchestrator", task_id, f"Successfully completed security analysis: {result['path']}", "task_completed")
                else:
                    print(f"SecurityAgent: Integration failed: {result['error']}")
                    self.send_message("orchestrator", task_id, f"Failed to integrate security report: {result['error']}", "task_failed")
            else:
                print("SecurityAgent: Failed to generate security report (LLM response was None or empty).")
                self.send_message("orchestrator", task_id, "Failed to generate security report (LLM response was empty or invalid).", "task_failed")

        elif msg["type"] == "review_and_retry":
            task_id = msg["task_id"]
            error_content = msg["content"]
            print(f"SecurityAgent: Received review and retry request for task {task_id}. Error: {error_content}")
            self.send_message("orchestrator", task_id, "Attempting retry after reviewing error.", "status_update")
            
            # Get the task from state manager and handle None case
            task_data = self.state_manager.get_task(task_id)
            if not task_data:
                # Check if task exists in the orchestrator's state
                # This might be a synchronization issue
                print(f"SecurityAgent: ERROR - Task {task_id} not found in local state manager")
                # Don't fail immediately - instead, try to get task description from the message
                if "description" in msg:
                    original_task_description = msg["description"]
                else:
                    self.send_message("orchestrator", task_id, f"Task {task_id} not found in state manager and no description provided.", "task_failed")
                    return
            else:
                original_task_description = task_data['description']
                
            is_modification = any(keyword in original_task_description.lower() for keyword in ["modify", "update", "add to existing", "revise", "re-evaluate"])
            security_report, target_file_suggestion = self._analyze_security(original_task_description, is_modification)

            if security_report and security_report.strip():
                if is_modification and target_file_suggestion and os.path.exists(target_file_suggestion):
                    output_filename = os.path.basename(target_file_suggestion).replace(".md", f"_retry_{task_id[:4]}.md").replace(".txt", f"_retry_{task_id[:4]}.txt")
                    output_path = os.path.join(os.path.dirname(target_file_suggestion), output_filename)
                else:
                    output_filename = f"security_report_{task_id[:8]}_retry.md"
                    output_path = os.path.join(self.security_root, output_filename)
                try:
                    os.makedirs(os.path.dirname(output_path), exist_ok=True)
                    with open(output_path, "w") as f:
                        f.write(security_report)
                    print(f"SecurityAgent: Retried security report saved to {output_path}")
                    self.send_message("orchestrator", task_id, f"Task retried and completed with new security report: {output_path}", "task_completed")
                except Exception as e:
                    print(f"SecurityAgent: Error writing retried file {output_path}: {e}")
                    self.send_message("orchestrator", task_id, f"Failed retry attempt: {e}", "task_failed")
            else:
                print("SecurityAgent: Failed to generate security report on retry (LLM response was None or empty).")
                self.send_message("orchestrator", task_id, "Failed to generate security report on retry (LLM response was empty or invalid).", "task_failed")
        else:
            print(f"SecurityAgent: Unknown message type {msg['type']}")

    def _get_existing_security_reports_context(self, max_files=3):
        """
        Reads and returns the content of the most recently modified security report files
        from various security-relevant scan roots (e.g., 'security_reports', 'lib', 'app/api').
        Returns (context_string, most_recent_file_path).
        """
        context = []
        found_files = []
        most_recent_file_path = None

        for scan_root in self.security_scan_roots:
            if not os.path.exists(scan_root):
                continue
            
            for root, _, files in os.walk(scan_root):
                for file_name in files:
                    # Target security reports, but also relevant code files for context
                    if file_name.endswith(('.md', '.txt', '.ts', '.js')):
                        full_path = os.path.join(root, file_name)
                        # Filter for specific files like route.ts, server.ts, supabaseClient.ts
                        if os.path.isfile(full_path) and \
                           (file_name.endswith(('.md', '.txt')) or \
                           ('route.ts' in file_name or 'route.js' in file_name or \
                            'supabaseClient.ts' in file_name or 'server.ts' in file_name or \
                            'actions.ts' in file_name)):
                            found_files.append(full_path)
            
        found_files.sort(key=os.path.getmtime, reverse=True)

        if found_files:
            most_recent_file_path = found_files[0]
            
        for i, file_path in enumerate(found_files[:max_files]):
            try:
                with open(file_path, 'r') as f:
                    content = f.read()
                    relative_path = os.path.relpath(file_path, self.project_root)
                    lang_highlight = "markdown"
                    if file_path.endswith(('.ts', '.js')):
                        lang_highlight = "typescript" if file_path.endswith('.ts') else "javascript"
                    file_context = f"--- Existing {os.path.basename(file_path)}: {relative_path} ---\n```{lang_highlight}\n{content}\n```\n"
                    context.append(file_context)
            except Exception as e:
                print(f"ERROR: SecurityAgent - Could not read existing security reports/code from {file_path} for context: {e}")
        return "\n".join(context), most_recent_file_path

    def _analyze_security(self, task_description):
        """
        Uses the LLM to simulate security analysis and generate a report
        for Next.js, Supabase, and Stripe related security considerations.
        Returns (security_report, suggested_target_file_path)
        """
        existing_reports_context, most_recent_report_file = self._get_existing_security_reports_context()

        # Extract f-string expressions to avoid backslash errors
        security_context_text = f"Existing Security Context (most recent file first):\n{existing_reports_context}\n"
        security_context_guidance = f"Consider the following existing security context from your project. Adapt your new analysis to build upon or align with these findings:\n{existing_reports_context}\n"

        # Check if this is a modification task
        is_modification = any(keyword in task_description.lower() for keyword in ["modify", "update", "add to existing", "revise", "re-evaluate"])
        
        # Check if this is an RLS policy task
        is_rls_task = 'rls' in task_description.lower() or 'row level security' in task_description.lower()
        
        if is_rls_task:
            # Generate SQL for RLS policies
            prompt = f"""You are a Security Agent specializing in Supabase Row Level Security (RLS) policies.
            Your task is to create RLS policies for the following requirement:
            "{task_description}"

            Generate SQL statements to create appropriate RLS policies. Include:
            1. Enable RLS on the table if not already enabled
            2. Policies for different user roles (authenticated users, public access, etc.)
            3. Proper security constraints based on the table structure

            For a photos table, typical policies might include:
            - Public read access for photos marked as public
            - Member-only read access for photos marked as member_only
            - Admin/moderator write access

            Provide ONLY the SQL statements, no markdown formatting or explanations.
            """
        elif is_modification and most_recent_report_file:
            prompt = f"""You are a Security Agent for web applications, specializing in Next.js, Supabase, and Stripe API integrations.
            Your task is to **modify an existing security report file** to identify potential security considerations or vulnerabilities
            related to the following development task or area, and suggest general remediation strategies.
            "{task_description}"

            Consider the most recent existing security report file (or relevant code file) provided in the context below. Your output should be the full,
            revised content of that file, integrating the new analysis or changes.
            
            {security_context_text if existing_reports_context else ""}

            Focus on security best practices for Next.js API routes, Supabase Row Level Security (RLS),
            secure handling of Supabase client keys and Stripe webhooks, and general web application security (e.g., OWASP Top 10).
            Provide a concise report in Markdown format, listing potential issues and general solutions.
            Do NOT include any text or formatting outside of the Markdown content.
            """
        else:
            prompt = f"""You are a Security Agent for web applications, specializing in Next.js, Supabase, and Stripe API integrations.
            Your task is to identify potential security considerations or vulnerabilities
            related to the following development task or area, and suggest general remediation strategies.
            "{task_description}"

            Focus on security best practices for Next.js API routes, Supabase Row Level Security (RLS),
            secure handling of Supabase client keys and Stripe webhooks, and general web application security (e.g., OWASP Top 10).
            
            {security_context_guidance if existing_reports_context else ""}

            Provide a concise report in Markdown format, listing potential issues and general solutions.
            Do NOT include any text or formatting outside of the Markdown content.
            """
        print(f"SecurityAgent: Requesting LLM to analyze security for: {task_description[:50]}...")
        response = self._generate_response(prompt, max_tokens=1500)

        if response and isinstance(response, str):
            cleaned_response = response.strip()
            if not is_rls_task:
                # Clean markdown formatting for regular reports
                if cleaned_response.startswith("```markdown"):
                    first_newline = cleaned_response.find('\n')
                    cleaned_response = cleaned_response[first_newline+1:].strip() if first_newline != -1 else cleaned_response[len("```markdown"):].strip()
                elif cleaned_response.startswith("```"):
                    first_newline = cleaned_response.find('\n')
                    cleaned_response = cleaned_response[first_newline+1:].strip() if first_newline != -1 else cleaned_response[len("```"):].strip()
                if cleaned_response.endswith("```"):
                    cleaned_response = cleaned_response[:-len("```")].strip()
            return cleaned_response, most_recent_report_file
        return response, None

    def _create_rls_migration(self, sql_content, task_description):
        """Create an SQL migration file for RLS policies."""
        try:
            from datetime import datetime
            
            if not sql_content or not sql_content.strip():
                return {
                    'success': False,
                    'error': 'No SQL content provided for RLS migration'
                }
            
            # Generate timestamp for migration filename
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            
            # Create migration filename
            if 'photos' in task_description.lower():
                migration_name = f"{timestamp}_photos_rls_policies.sql"
            else:
                migration_name = f"{timestamp}_rls_policies.sql"
            
            # Migration file path
            migrations_dir = os.path.join(self.project_root, 'supabase', 'migrations')
            os.makedirs(migrations_dir, exist_ok=True)
            migration_path = os.path.join(migrations_dir, migration_name)
            
            # Write SQL content to migration file
            with open(migration_path, 'w') as f:
                f.write(sql_content)
            
            return {
                'success': True,
                'path': migration_path,
                'action': 'created'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def _create_security_report(self, content, task_description):
        """Create a security report file."""
        try:
            from datetime import datetime
            
            # Generate filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            if 'photos' in task_description.lower():
                filename = f"photos_security_analysis_{timestamp}.md"
            else:
                filename = f"security_analysis_{timestamp}.md"
            
            # Report file path
            report_path = os.path.join(self.security_root, filename)
            
            # Write content to file
            with open(report_path, 'w') as f:
                f.write(content)
            
            return {
                'success': True,
                'path': report_path,
                'action': 'created'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

if __name__ == "__main__":
    security_agent = SecurityAgent()  # Use default model from __init__
    security_agent.run()
