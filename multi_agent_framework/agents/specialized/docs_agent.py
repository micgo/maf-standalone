import os
import sys
import json
import time
import uuid

# Use relative imports
from ..base_agent_configurable import BaseAgent
from ...core.project_config import ProjectConfig
from ...core.naming_conventions import NamingConventions

class DocsAgent(BaseAgent):
    """
    The DocsAgent is responsible for generating project documentation relevant to Next.js, React, and Supabase.
    It can now propose direct modifications to existing documentation files.
    """
    def __init__(self, project_config=None, model_provider="gemini", model_name="gemini-1.5-flash"):  # Documentation is straightforward
        super().__init__("docs_agent", project_config, model_provider, model_name)
        
        # Roots for scanning existing documentation and project plan files
        self.doc_scan_roots = [
            os.path.abspath(os.path.join(self.project_root, 'project-plan')),
            os.path.abspath(os.path.join(self.project_root, 'docs'))
        ]
        
        print(f"DocsAgent initialized with intelligent integration system.")

    def run(self):
        """
        Main loop for the DocsAgent to continuously receive and process messages.
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
            print(f"DocsAgent received task {task_id}: {task_description}")
            self.state_manager.update_task_status(task_id, "in_progress")

            # Generate the documentation
            generated_doc, target_file = self._generate_documentation(task_description)

            if generated_doc and generated_doc.strip():
                # Use new integration system
                strategy = self.get_integration_strategy(task_description, 'docs')
                result = self.integrate_generated_content(generated_doc, strategy)

                if result['success']:
                    print(f"DocsAgent: Successfully {result['action']} documentation: {result['path']}")
                    self.send_message("orchestrator", task_id, f"Successfully {result['action']} documentation: {result['path']}", "task_completed")
                else:
                    print(f"DocsAgent: Integration failed: {result['error']}")
                    self.send_message("orchestrator", task_id, f"Failed to integrate documentation: {result['error']}", "task_failed")
            else:
                print("DocsAgent: Failed to generate documentation (LLM response was None or empty).")
                self.send_message("orchestrator", task_id, "Failed to generate documentation (LLM response was empty or invalid).", "task_failed")

        elif msg["type"] == "review_and_retry":
            task_id = msg["task_id"]
            error_content = msg["content"]
            print(f"DocsAgent: Received review and retry request for task {task_id}. Error: {error_content}")
            self.send_message("orchestrator", task_id, "Attempting retry after reviewing error.", "status_update")
            
            original_task_description = self.state_manager.get_task(task_id)['description']
            error_details = f"\n\nPrevious attempt failed with error: {error_content}\nPlease fix the issues and try again."
            enhanced_description = f"{original_task_description}{error_details}"
            
            # Generate improved documentation
            generated_doc = self._generate_documentation(enhanced_description)

            if generated_doc and generated_doc.strip():
                # Use integration system for retry
                strategy = self.get_integration_strategy(original_task_description, 'docs')
                result = self.integrate_generated_content(generated_doc, strategy)

                if result['success']:
                    print(f"DocsAgent: Successfully {result['action']} documentation on retry: {result['path']}")
                    self.send_message("orchestrator", task_id, f"Task retried and completed: {result['path']}", "task_completed")
                else:
                    print(f"DocsAgent: Retry integration failed: {result['error']}")
                    self.send_message("orchestrator", task_id, f"Failed retry attempt: {result['error']}", "task_failed")
            else:
                print("DocsAgent: Failed to generate documentation on retry (LLM response was None or empty).")
                self.send_message("orchestrator", task_id, "Failed to generate documentation on retry (LLM response was empty or invalid).", "task_failed")

        else:
            print(f"DocsAgent: Unknown message type {msg['type']}")

    def _get_existing_docs_context(self, max_files=3):
        """
        Reads and returns the content of the most recently modified documentation files
        from various documentation scan roots (e.g., 'docs', 'project-plan').
        Returns (context_string, most_recent_file_path).
        """
        context = []
        found_files = []
        most_recent_file_path = None

        for scan_root in self.doc_scan_roots:
            if not os.path.exists(scan_root):
                continue
            
            for root, _, files in os.walk(scan_root):
                for file_name in files:
                    if file_name.endswith(('.md', '.txt')):
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
                    file_context = f"--- Existing Document: {relative_path} ---\n```markdown\n{content}\n```\n"
                    context.append(file_context)
            except Exception as e:
                print(f"ERROR: DocsAgent - Could not read existing docs from {file_path} for context: {e}")
        return "\n".join(context), most_recent_file_path

    def _generate_documentation(self, task_description):
        """
        Uses the LLM to generate Markdown documentation for Next.js, React, and Supabase.
        Returns (generated_doc, suggested_target_file_path).
        """
        existing_docs_context, most_recent_doc_file = self._get_existing_docs_context()

        # Extract f-string expressions to avoid backslash errors
        docs_context_guidance = f"Consider the following existing documentation context from your project. Adapt your new documentation to fit with this existing style and content:\n{existing_docs_context}\n"

        prompt = f"""You are a Documentation Agent.
        Your task is to generate concise Markdown documentation for a Next.js application,
        covering aspects related to React components, Next.js API Routes, Supabase database integration, or Stripe API integration.
        The requirement is: "{task_description}"

        Structure it with clear headings, code snippets (with language highlighting), and bullet points where appropriate.
        Focus on clarity and completeness for the specific documentation piece.
        
        {docs_context_guidance if existing_docs_context else ""}

        Do NOT include any text or formatting outside of the Markdown content.
        """
        
        print(f"DocsAgent: Requesting LLM to generate documentation for: {task_description[:50]}...")
        response = self._generate_response(prompt, max_tokens=1500)

        if response and isinstance(response, str):
            cleaned_response = response.strip()
            if cleaned_response.startswith("```markdown"):
                first_newline = cleaned_response.find('\n')
                cleaned_response = cleaned_response[first_newline+1:].strip() if first_newline != -1 else cleaned_response[len("```markdown"):].strip()
            elif cleaned_response.startswith("```"):
                first_newline = cleaned_response.find('\n')
                cleaned_response = cleaned_response[first_newline+1:].strip() if first_newline != -1 else cleaned_response[len("```"):].strip()
            if cleaned_response.endswith("```"):
                cleaned_response = cleaned_response[:-len("```")].strip()
            return cleaned_response, most_recent_doc_file
        return response, most_recent_doc_file

if __name__ == "__main__":
    docs_agent = DocsAgent()  # Use default model from __init__
    docs_agent.run()
