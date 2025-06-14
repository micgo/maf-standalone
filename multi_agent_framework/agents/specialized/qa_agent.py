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

class QaAgent(BaseAgent):
    """
    The QaAgent is responsible for generating unit, integration, or end-to-end tests
    for Next.js/React applications, suggesting frameworks like Jest, React Testing Library, Cypress, or Playwright.
    It can now propose direct modifications to existing test files.
    """
    def __init__(self, project_config=None, model_provider="gemini", model_name="gemini-1.5-flash"):  # Test generation doesn't need heavy reasoning
        super().__init__("qa_agent", project_config, model_provider, model_name)
        
        # Root for scanning existing code for context (the entire app directory and root components)
        self.app_code_scan_root = os.path.abspath(os.path.join(self.project_root, "app"))
        self.root_components_scan_root = os.path.abspath(os.path.join(self.project_root, "components"))
        
        # Initialize integration components
        self.project_analyzer = ProjectAnalyzer(self.project_root)
        self.file_integrator = FileIntegrator(self.project_root)
        print(f"QaAgent initialized with intelligent integration system.")


    def run(self):
        """
        Main loop for the QaAgent to continuously receive and process messages.
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
            print(f"QaAgent received task {task_id}: {task_description}")
            self.state_manager.update_task_status(task_id, "in_progress")

            # Generate the tests
            generated_tests, target_file = self._generate_tests(task_description)

            if generated_tests and generated_tests.strip():
                # Use new integration system - tests should be co-located with components
                strategy = self.get_integration_strategy(task_description, 'component')
                
                # For tests, we want to place them next to the component they're testing
                if strategy['mode'] == 'create' and strategy['target_dir']:
                    # Find the component being tested and place test next to it
                    test_filename = self._generate_test_filename_from_content(generated_tests)
                    target_path = os.path.join(strategy['target_dir'], test_filename)
                    strategy['target_dir'] = strategy['target_dir']  # Keep same directory
                
                result = self.integrate_generated_content(generated_tests, strategy)

                if result['success']:
                    print(f"QaAgent: Successfully {result['action']} test: {result['path']}")
                    self.send_message("orchestrator", task_id, f"Successfully {result['action']} test: {result['path']}", "task_completed")
                else:
                    print(f"QaAgent: Integration failed: {result['error']}")
                    self.send_message("orchestrator", task_id, f"Failed to integrate test: {result['error']}", "task_failed")
            else:
                print("QaAgent: Failed to generate tests (LLM response was None or empty).")
                self.send_message("orchestrator", task_id, "Failed to generate tests (LLM response was empty or invalid).", "task_failed")

        elif msg["type"] == "review_and_retry":
            task_id = msg["task_id"]
            error_content = msg["content"]
            print(f"QaAgent: Received review and retry request for task {task_id}. Error: {error_content}")
            self.send_message("orchestrator", task_id, "Attempting retry after reviewing error.", "status_update")
            
            original_task_description = self.state_manager.get_task(task_id)['description']
            is_modification = any(keyword in original_task_description.lower() for keyword in ["modify", "update", "refactor", "add to existing", "change", "alter"])
            generated_tests, target_file_suggestion = self._generate_tests(original_task_description, is_modification)

            if generated_tests and generated_tests.strip():
                if is_modification and target_file_suggestion and os.path.exists(target_file_suggestion):
                    output_filename = os.path.basename(target_file_suggestion).replace(".test.tsx", f"_retry_{task_id[:4]}.test.tsx").replace(".test.ts", f"_retry_{task_id[:4]}.test.ts")
                    output_path = os.path.join(os.path.dirname(target_file_suggestion), output_filename)
                else:
                    output_filename = f"test_{task_id[:8]}_retry.test.tsx"
                    output_path = os.path.join(self.tests_output_root, output_filename)
                try:
                    os.makedirs(os.path.dirname(output_path), exist_ok=True)
                    with open(output_path, "w") as f:
                        f.write(generated_tests)
                    print(f"QaAgent: Retried tests saved to {output_path}")
                    self.send_message("orchestrator", task_id, f"Task retried and completed with new tests: {output_path}", "task_completed")
                except Exception as e:
                    print(f"QaAgent: Error writing retried file {output_path}: {e}")
                    self.send_message("orchestrator", task_id, f"Failed retry attempt: {e}", "task_failed")
            else:
                print("QaAgent: Failed to generate tests on retry (LLM response was None or empty).")
                self.send_message("orchestrator", task_id, "Failed to generate tests on retry (LLM response was empty or invalid).", "task_failed")

        else:
            print(f"QaAgent: Unknown message type {msg['type']}")

    def _get_existing_tests_context(self, max_files=3):
        """
        Reads and returns the content of the most recently modified test files
        (.test.tsx, .test.ts) from the 'app' directory (recursively) and root-level 'components' directory.
        Returns (context_string, most_recent_file_path).
        """
        context = []
        found_files = []
        most_recent_file_path = None

        scan_roots = [self.app_code_scan_root, self.root_components_scan_root]

        for scan_root in scan_roots:
            if not os.path.exists(scan_root):
                continue

            for root, _, files in os.walk(scan_root):
                for file_name in files:
                    if file_name.endswith(('.test.tsx', '.test.ts')): # Specific test file patterns
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
                    file_context = f"--- Existing Test File: {relative_path} ---\n```{lang_highlight}\n{content}\n```\n"
                    context.append(file_context)
            except Exception as e:
                print(f"ERROR: QaAgent - Could not read existing test code from {file_path} for context: {e}")
        return "\n".join(context), most_recent_file_path

    def _generate_tests(self, task_description, is_modification=False):
        """
        Uses the LLM to generate test code for Next.js/React applications (e.g., Jest, React Testing Library, Cypress).
        Returns (generated_tests, suggested_target_file_path)
        """
        existing_tests_context, most_recent_test_file = self._get_existing_tests_context()

        # Extract f-string expressions to avoid backslash errors
        test_context_text = f"Existing Test Code Context (most recent file first):\n{existing_tests_context}\n"
        test_context_guidance = f"Consider the following existing test code context from your project. Adapt your new test code to fit with this existing structure and style, importing necessary modules or components if they are present in the context:\n{existing_tests_context}\n"

        if is_modification and most_recent_test_file:
            prompt = f"""You are a Quality Assurance (QA) & Testing Agent specializing in Next.js (App Router) and React applications.
            Your task is to **modify an existing test file** to address the following requirement:
            "{task_description}"

            Consider the most recent existing test file provided in the context below. Your output should be the full,
            revised content of that file, integrating the new test cases or changes.
            
            {test_context_text if existing_tests_context else ""}

            **Generate the full, complete code for the test file. Do NOT omit any parts or use placeholders like '...'**.
            Do NOT include any explanatory text, comments outside the code, or formatting outside of the test file content.
            """
        else:
            prompt = f"""You are a Quality Assurance (QA) & Testing Agent specializing in Next.js (App Router) and React applications.
            Your task is to generate a test file (e.g., using Jest, React Testing Library for unit/integration,
            or Playwright for E2E) for the following requirement:
            "{task_description}"

            Provide a complete, runnable test file. Include necessary imports (e.g., `import React from 'react'`, `import {{ render, screen }} from '@testing-library/react'`, or Playwright imports).
            
            {test_context_guidance if existing_tests_context else ""}

            **Generate the full, complete code for the test file. Do NOT omit any parts or use placeholders like '...'**.
            Do NOT include any explanatory text, comments outside the code, or formatting outside of the test file content.
            """
        print(f"QaAgent: Requesting LLM to generate tests for: {task_description[:50]}...")
        response = self._generate_response(prompt, max_tokens=2000)

        if response and isinstance(response, str):
            cleaned_response = response.strip()
            if cleaned_response.startswith("```javascript") or cleaned_response.startswith("```typescript") or \
               cleaned_response.startswith("```jsx") or cleaned_response.startswith("```tsx"):
                first_newline = cleaned_response.find('\n')
                cleaned_response = cleaned_response[first_newline+1:].strip() if first_newline != -1 else cleaned_response[len("```javascript"):].strip()
            elif cleaned_response.startswith("```"):
                first_newline = cleaned_response.find('\n')
                cleaned_response = cleaned_response[first_newline+1:].strip() if first_newline != -1 else cleaned_response[len("```"):].strip()
            if cleaned_response.endswith("```"):
                cleaned_response = cleaned_response[:-len("```")].strip()
            return cleaned_response, most_recent_test_file
        return response, None

    def _generate_test_filename_from_content(self, content):
        """Generate a test filename based on the content."""
        # Simple heuristic to generate test filename
        if 'describe(' in content:
            return f"component.test.tsx"
        return f"test.tsx"

if __name__ == "__main__":
    qa_agent = QaAgent()  # Use default model from __init__
    qa_agent.run()
