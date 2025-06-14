import os
import sys
import json
import time
import uuid

# Use relative imports
from ..base_agent_configurable import BaseAgent
from ...core.naming_conventions import NamingConventions
from ...core.project_config import ProjectConfig

class FrontendAgent(BaseAgent):
    """
    The FrontendAgent is responsible for generating UI components using Next.js, React, and Tailwind CSS.
    It receives tasks from the orchestrator, generates relevant code, and reports back.
    """
    def __init__(self, project_config=None, model_provider="gemini", model_name="gemini-2.0-flash"):
        super().__init__("frontend_agent", project_config, model_provider, model_name)  # Fast code generation
        
        # Roots for scanning existing frontend code (the entire app directory and root components)
        self.app_pages_scan_root = os.path.abspath(os.path.join(self.project_root, "app"))
        self.root_components_scan_root = os.path.abspath(os.path.join(self.project_root, "components"))
        
        print(f"FrontendAgent initialized with intelligent integration system.")

    def run(self):
        """
        Main loop for the FrontendAgent to continuously receive and process messages.
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
            print(f"FrontendAgent received task {task_id}: {task_description}")
            self.state_manager.update_task_status(task_id, "in_progress")

            # Extract resource info for proper naming
            resource_info = NamingConventions.extract_resource_from_task(task_description)
            
            # Check if corresponding API exists
            api_exists = False
            if resource_info.get('resource'):
                api_path = NamingConventions.generate_api_route_path(resource_info['resource'])
                api_full_path = os.path.join(self.project_root, api_path)
                api_exists = os.path.exists(api_full_path)

            # Generate the frontend code
            generated_code = self._generate_frontend_code(task_description, api_exists=api_exists, resource_info=resource_info)

            if generated_code and generated_code.strip():
                # Determine the type of component based on task description
                if any(word in task_description.lower() for word in ['page', 'view', 'screen']):
                    component_type = 'page'
                else:
                    component_type = 'component'
                    
                # Use naming conventions for proper file placement
                if resource_info.get('resource') and component_type == 'page':
                    # Generate page path
                    page_path = NamingConventions.generate_page_path(resource_info['resource'])
                    result = self._save_generated_file(generated_code, page_path, task_id)
                elif resource_info.get('resource'):
                    # Generate component path
                    component_name = resource_info.get('component') or f"{resource_info['resource'].capitalize()}Component"
                    category = resource_info.get('category', resource_info['resource'])
                    component_path = NamingConventions.generate_component_path(component_name, category)
                    result = self._save_generated_file(generated_code, component_path, task_id)
                else:
                    # Fallback to integration system
                    strategy = self.get_integration_strategy(task_description, 'component')
                    result = self.integrate_generated_content(generated_code, strategy)

                if result['success']:
                    print(f"FrontendAgent: Successfully {result['action']} component: {result['path']}")
                    self.send_message("orchestrator", task_id, f"Successfully {result['action']} frontend component: {result['path']}", "task_completed")
                else:
                    print(f"FrontendAgent: Integration failed: {result['error']}")
                    self.send_message("orchestrator", task_id, f"Failed to integrate frontend code: {result['error']}", "task_failed")
            else:
                print("FrontendAgent: Failed to generate frontend code (LLM response was None or empty).")
                self.send_message("orchestrator", task_id, "Failed to generate frontend code (LLM response was empty or invalid).", "task_failed")

        elif msg["type"] == "review_and_retry":
            task_id = msg["task_id"]
            error_content = msg["content"]
            print(f"FrontendAgent: Received review and retry request for task {task_id}. Error: {error_content}")
            self.send_message("orchestrator", task_id, "Attempting retry after reviewing error.", "status_update")
            
            original_task_description = self.state_manager.get_task(task_id)['description']
            error_details = f"\n\nPrevious attempt failed with error: {error_content}\nPlease fix the issues and try again."
            enhanced_description = f"{original_task_description}{error_details}"
            
            # Extract resource info for retry
            resource_info = NamingConventions.extract_resource_from_task(original_task_description)
            api_exists = False
            if resource_info.get('resource'):
                api_path = NamingConventions.generate_api_route_path(resource_info['resource'])
                api_full_path = os.path.join(self.project_root, api_path)
                api_exists = os.path.exists(api_full_path)
            
            # Generate improved code
            generated_code = self._generate_frontend_code(enhanced_description, api_exists=api_exists, resource_info=resource_info)

            if generated_code and generated_code.strip():
                # Use integration system for retry
                strategy = self.get_integration_strategy(original_task_description, 'component')
                result = self.integrate_generated_content(generated_code, strategy)

                if result['success']:
                    print(f"FrontendAgent: Successfully {result['action']} component on retry: {result['path']}")
                    self.send_message("orchestrator", task_id, f"Task retried and completed: {result['path']}", "task_completed")
                else:
                    print(f"FrontendAgent: Retry integration failed: {result['error']}")
                    self.send_message("orchestrator", task_id, f"Failed retry attempt: {result['error']}", "task_failed")
            else:
                print("FrontendAgent: Failed to generate frontend code on retry (LLM response was None or empty).")
                self.send_message("orchestrator", task_id, "Failed to generate frontend code on retry (LLM response was empty or invalid).", "task_failed")
        else:
            print(f"FrontendAgent: Unknown message type {msg['type']}")

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

    def _get_existing_frontend_code_context(self, max_files=3):
        """
        Reads and returns the content of the most recently modified Next.js App Router files
        (e.g., page.tsx, layout.tsx, components, actions.ts) from the 'app' directory
        AND root-level 'components' directory to provide context to the LLM.
        Returns (context_string, most_recent_file_path).
        """
        context = []
        found_files = []
        most_recent_file_path = None

        scan_roots = [self.app_pages_scan_root, self.root_components_scan_root]

        for scan_root in scan_roots:
            if not os.path.exists(scan_root):
                continue

            for root, _, files in os.walk(scan_root):
                for file_name in files:
                    # Target common Next.js App Router files, components, and actions
                    if file_name.endswith(('.tsx', '.jsx', '.ts', '.js')) and \
                       (file_name.startswith('page.') or file_name.startswith('layout.') or \
                        file_name.startswith('loading.') or file_name == 'actions.ts' or \
                        'component' in file_name.lower() or 'form' in file_name.lower()): # Broaden for typical component/form names
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
                    lang_highlight = "typescript" if file_path.endswith(('.tsx', '.ts')) else "javascript"
                    file_context = f"--- Existing File: {relative_path} ---\n```{lang_highlight}\n{content}\n```\n"
                    context.append(file_context)
            except Exception as e:
                print(f"ERROR: FrontendAgent - Could not read existing frontend code from {file_path} for context: {e}")
        return "\n".join(context), most_recent_file_path

    def _generate_frontend_code(self, task_description, api_exists=False, resource_info=None):
        """
        Uses the LLM to generate Next.js/React components with Tailwind CSS.
        Returns generated_code string.
        """
        existing_code_context, _ = self._get_existing_frontend_code_context()
        
        # Extract f-string expressions to avoid backslash errors
        frontend_context_guidance = f"Consider the following existing code context from your project. Adapt your new code to fit with this existing structure and style, importing necessary modules or components if they are present in the context:\n{existing_code_context}\n"
        
        # Build API context if API exists
        api_context = ""
        if api_exists and resource_info and resource_info.get('resource'):
            api_path = f"/api/{resource_info['resource']}"
            api_context = f"\n\nThe API endpoint for this resource is available at '{api_path}'. Use fetch() or a data fetching library to interact with it."
        
        prompt = f"""You are a Frontend Developer Agent specializing in Next.js (App Router) and React,
        with styling implemented using Tailwind CSS.
        Your task is to generate the code for a React component (e.g., a shared component, page.tsx, or layout.tsx)
        based on the following requirement:
        "{task_description}"

        Ensure the component is a functional React component, and use Tailwind CSS classes for all styling.
        If applicable, assume Next.js specific features like `useRouter`, `useSearchParams`, `server components`,
        `page.tsx`, `layout.tsx`, or `actions.ts` can be relevant.
        {api_context}
        
        {frontend_context_guidance if existing_code_context else ""}

        Generate the full, complete code for the component file (e.g., a .tsx or .jsx file).
        Do NOT omit any parts or use placeholders like '...'.
        Do NOT include any explanatory text, comments outside the code, or formatting outside of the component content.
        """
        
        print(f"FrontendAgent: Requesting LLM to generate code for: {task_description[:50]}...")
        response = self._generate_response(prompt, max_tokens=2000)
        
        if response and isinstance(response, str):
            cleaned_response = response.strip()
            if cleaned_response.startswith("```jsx") or cleaned_response.startswith("```tsx") or \
               cleaned_response.startswith("```typescript") or cleaned_response.startswith("```javascript"):
                first_newline = cleaned_response.find('\n')
                cleaned_response = cleaned_response[first_newline+1:].strip() if first_newline != -1 else cleaned_response[len("```jsx"):].strip()
            
            if cleaned_response.endswith("```"):
                cleaned_response = cleaned_response[:-len("```")].strip()
            return cleaned_response
        return response

if __name__ == "__main__":
    frontend_agent = FrontendAgent()  # Use default model from __init__
    frontend_agent.run()
