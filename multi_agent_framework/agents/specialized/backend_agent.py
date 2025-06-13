import os
import sys
import json
import time
import uuid

# Use relative imports
from ..base_agent_configurable import BaseAgent
from ...core.naming_conventions import NamingConventions
from ...core.project_config import ProjectConfig

class BackendAgent(BaseAgent):
    """
    The BackendAgent is responsible for generating backend code, particularly Next.js API Routes,
    using the Supabase client for database interactions and integrating with Stripe API.
    """
    def __init__(self, project_config=None, model_provider="gemini", model_name="gemini-2.0-flash"):
        super().__init__("backend_agent", project_config, model_provider, model_name)  # Fast API code generation
        
        # Root for scanning existing backend utility code (e.g., lib/supabase)
        self.lib_scan_root = os.path.abspath(os.path.join(self.project_root, 'lib'))
        
        print(f"BackendAgent initialized with intelligent integration system.")


    def run(self):
        """
        Main loop for the BackendAgent to continuously receive and process messages.
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
        Creates both API routes and service layers when appropriate.
        """
        if msg["type"] == "new_task":
            task_id = msg["task_id"]
            task_description = msg["content"]
            print(f"BackendAgent received task {task_id}: {task_description}")
            self.state_manager.update_task_status(task_id, "in_progress")

            # Extract resource info for proper naming
            resource_info = NamingConventions.extract_resource_from_task(task_description)
            
            # Check if this task requires both API route and service layer
            needs_service_layer = any(keyword in task_description.lower() 
                                    for keyword in ['api', 'endpoint', 'fetch', 'crud', 'database'])
            
            created_files = []
            
            if needs_service_layer and resource_info.get('resource'):
                # First, generate and create the service layer
                service_code = self._generate_service_layer(task_description, resource_info)
                if service_code:
                    service_path = NamingConventions.generate_service_path(resource_info['resource'])
                    service_result = self._save_generated_file(service_code, service_path, task_id)
                    if service_result['success']:
                        created_files.append(service_path)
                        print(f"BackendAgent: Created service layer: {service_path}")

            # Generate the API route
            generated_code = self._generate_backend_code(task_description, has_service=needs_service_layer and bool(created_files))

            if generated_code and generated_code.strip():
                # Use proper naming for API route
                if resource_info.get('resource'):
                    api_path = NamingConventions.generate_api_route_path(resource_info['resource'])
                    # Ensure directory exists
                    os.makedirs(os.path.dirname(os.path.join(self.project_root, api_path)), exist_ok=True)
                    result = self._save_generated_file(generated_code, api_path, task_id)
                else:
                    # Fallback to integration system
                    strategy = self.get_integration_strategy(task_description, 'api')
                    result = self.integrate_generated_content(generated_code, strategy)

                if result['success']:
                    created_files.append(result.get('path', 'unknown'))
                    files_summary = ", ".join(created_files)
                    print(f"BackendAgent: Successfully created backend files: {files_summary}")
                    self.send_message("orchestrator", task_id, f"Successfully created backend files: {files_summary}", "task_completed")
                else:
                    print(f"BackendAgent: Integration failed: {result['error']}")
                    self.send_message("orchestrator", task_id, f"Failed to integrate backend code: {result['error']}", "task_failed")
            else:
                print("BackendAgent: Failed to generate backend code (LLM response was None or empty).")
                self.send_message("orchestrator", task_id, "Failed to generate backend code (LLM response was empty or invalid).", "task_failed")

        elif msg["type"] == "review_and_retry":
            task_id = msg["task_id"]
            error_content = msg["content"]
            print(f"BackendAgent: Received review and retry request for task {task_id}. Error: {error_content}")
            self.send_message("orchestrator", task_id, "Attempting retry after reviewing error.", "status_update")
            
            original_task_description = self.state_manager.get_task(task_id)['description']
            enhanced_description = f"{original_task_description}\n\nPrevious attempt failed with error: {error_content}\nPlease fix the issues and try again."
            
            # Generate improved code
            generated_code = self._generate_backend_code(enhanced_description)

            if generated_code and generated_code.strip():
                # Use integration system for retry
                strategy = self.get_integration_strategy(original_task_description, 'api')
                result = self.integrate_generated_content(generated_code, strategy)

                if result['success']:
                    print(f"BackendAgent: Successfully {result['action']} API route on retry: {result['path']}")
                    self.send_message("orchestrator", task_id, f"Task retried and completed: {result['path']}", "task_completed")
                else:
                    print(f"BackendAgent: Retry integration failed: {result['error']}")
                    self.send_message("orchestrator", task_id, f"Failed retry attempt: {result['error']}", "task_failed")
            else:
                print("BackendAgent: Failed to generate backend code on retry (LLM response was None or empty).")
                self.send_message("orchestrator", task_id, "Failed to generate backend code on retry (LLM response was empty or invalid).", "task_failed")

        else:
            print(f"BackendAgent: Unknown message type {msg['type']}")

    def _get_existing_backend_code_context(self, max_files=3):
        """
        Reads and returns the content of the most recently modified backend API route files (route.ts/js)
        within the Next.js App Router structure (app/api/**/route.ts) AND files in lib/.
        Returns (context_string, most_recent_file_path).
        """
        context = []
        found_files = []
        most_recent_file_path = None

        api_routes_root = os.path.abspath(os.path.join(self.project_root, 'app', 'api'))
        scan_roots = [api_routes_root, self.lib_scan_root]

        for scan_root in scan_roots:
            if not os.path.exists(scan_root):
                continue

            for root, _, files in os.walk(scan_root):
                for file_name in files:
                    # Target API route files and common utility/library files
                    if file_name in ['route.ts', 'route.js'] or \
                       file_name.endswith(('.ts', '.js')) and 'supabase' in root: # Include Supabase client files in lib/
                        full_path = os.path.join(root, file_name)
                        if os.path.isfile(full_path):
                            found_files.append(full_path)
            
        found_files.sort(key=os.path.getmtime, reverse=True)

        if found_files:
            most_recent_file_path = found_files[0]

        for i, file_path in enumerate(found_files[:max_files]):
            try:
                with open(file_path, 'r') as f:
                    content = f.read()
                    relative_path = os.path.relpath(file_path, self.project_root)
                    lang_highlight = "typescript" if file_path.endswith(('.ts')) else "javascript"
                    context.append(f"--- Existing File: {relative_path} ---\n```{lang_highlight}\n{content}\n```\n")
            except Exception as e:
                print(f"ERROR: BackendAgent - Could not read existing backend code from {file_path} for context: {e}")
        return "\n".join(context), most_recent_file_path

    def _save_generated_file(self, content, file_path, task_id):
        """Save generated content to a file with proper path"""
        try:
            full_path = os.path.join(self.project_root, file_path)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            
            with open(full_path, 'w') as f:
                f.write(content)
            
            return {'success': True, 'path': file_path, 'action': 'created'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _generate_service_layer(self, task_description, resource_info):
        """Generate a service layer for the resource"""
        resource_name = resource_info['resource']
        
        prompt = f"""You are a Backend Developer creating a TypeScript service layer for Next.js.
        Generate a complete service class for '{resource_name}' based on this requirement:
        "{task_description}"
        
        The service should:
        1. Use Supabase for database operations
        2. Include proper TypeScript types
        3. Handle errors appropriately
        4. Support common CRUD operations if applicable
        5. Be located at lib/{resource_name}Service.ts
        
        Include all necessary imports and complete implementations.
        Do NOT include explanatory text outside the code.
        """
        
        response = self._generate_response(prompt, max_tokens=2000)
        if response and isinstance(response, str):
            cleaned = response.strip()
            if cleaned.startswith("```"):
                # Remove code block markers
                lines = cleaned.split('\n')
                if lines[0].startswith("```"):
                    lines = lines[1:]
                if lines[-1] == "```":
                    lines = lines[:-1]
                cleaned = '\n'.join(lines)
            return cleaned
        return None

    def _generate_backend_code(self, task_description, has_service=False):
        """
        Uses the LLM to generate Next.js API route code, with Supabase client and Stripe API integration.
        Returns generated_code string.
        """
        existing_code_context, _ = self._get_existing_backend_code_context()
        
        # Extract resource info for service layer awareness
        resource_info = NamingConventions.extract_resource_from_task(task_description)
        service_import = ""
        
        if has_service and resource_info.get('resource'):
            # Generate the import statement for the service layer
            resource_name = resource_info['resource']
            service_class = f"{resource_name.capitalize()}Service"
            service_import = f"\nImport the {service_class} from '@/lib/{resource_name}Service' to handle business logic."
        
        prompt = f"""You are a Backend Developer Agent specializing in Next.js API Routes (App Router style),
        the Supabase client library for PostgreSQL database interactions, and Stripe API for payments.
        Your task is to generate a TypeScript code snippet for a Next.js API route (e.g., 'route.ts' within a route segment) that addresses the following requirement:
        "{task_description}"

        {service_import}
        
        Include necessary imports and a basic API route setup (`export async function GET(request: Request) {{...}}` for specific HTTP methods).
        {f"Since a service layer exists, use the {service_class} methods instead of direct database calls." if has_service else "Use Supabase client for database operations."}
        
        {f"Consider the following existing code context from your project. Adapt your new code to fit with this existing structure and style:\n{existing_code_context}\n" if existing_code_context else ""}

        Generate the full, complete code for the API route file. Do NOT omit any parts or use placeholders like '...'.
        Do NOT include any explanatory text, comments outside the code, or formatting outside of the API route content.
        """
        
        print(f"BackendAgent: Requesting LLM to generate code for: {task_description[:50]}...")
        response = self._generate_response(prompt, max_tokens=2000)

        if response and isinstance(response, str):
            cleaned_response = response.strip()
            if cleaned_response.startswith("```typescript"):
                first_newline = cleaned_response.find('\n')
                cleaned_response = cleaned_response[first_newline+1:].strip() if first_newline != -1 else cleaned_response[len("```typescript"):].strip()
            elif cleaned_response.startswith("```"):
                first_newline = cleaned_response.find('\n')
                cleaned_response = cleaned_response[first_newline+1:].strip() if first_newline != -1 else cleaned_response[len("```"):].strip()
            if cleaned_response.endswith("```"):
                cleaned_response = cleaned_response[:-len("```")].strip()
            return cleaned_response
        return response

if __name__ == "__main__":
    backend_agent = BackendAgent()  # Use default model from __init__
    backend_agent.run()
