import os
import sys
import json
import time
import uuid

# Use relative imports
from ..base_agent_configurable import BaseAgent
from ...core.project_config import ProjectConfig

class UxUiAgent(BaseAgent):
    """
    The UxUiAgent is responsible for generating UI/UX designs, flows, and components
    for Next.js/React applications with Tailwind CSS, considering existing styles and structure.
    """
    def __init__(self, project_config=None, model_provider="gemini", model_name="gemini-2.0-flash"):  # Fast design suggestions
        super().__init__("ux_ui_agent", project_config, model_provider, model_name)
        
        # Output directory for new generated UI components or design artifacts
        # Place them in a new sub-directory within the main 'components' folder
        self.output_ui_root = os.path.abspath(os.path.join(self.project_root, "components", "generated_ux_ui"))
        os.makedirs(self.output_ui_root, exist_ok=True)
        print(f"UxUiAgent initialized. Output path for new UI/UX artifacts: {self.output_ui_root}")

        # Roots for scanning existing UI/UX related code and assets
        self.app_scan_root = os.path.abspath(os.path.join(self.project_root, "app"))
        self.root_components_scan_root = os.path.abspath(os.path.join(self.project_root, "components"))
        self.public_assets_scan_root = os.path.abspath(os.path.join(self.project_root, "public")) # For existing assets like logos, avatars


    def run(self):
        """
        Main loop for the UxUiAgent to continuously receive and process messages.
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
            print(f"UxUiAgent received task {task_id}: {task_description}")
            self.state_manager.update_task_status(task_id, "in_progress")

            is_modification = any(keyword in task_description.lower() for keyword in ["modify", "update", "refactor", "add to existing", "change", "alter", "improve", "redesign"])
            generated_content, target_file_suggestion = self._generate_ui_elements(task_description, is_modification)

            if generated_content and generated_content.strip():
                output_path = None
                if is_modification and target_file_suggestion and os.path.exists(target_file_suggestion):
                    # For modifications, save a _modified version (or apply diff)
                    file_ext = os.path.splitext(target_file_suggestion)[1]
                    output_filename = os.path.basename(target_file_suggestion).replace(file_ext, f"_modified_{task_id[:4]}{file_ext}")
                    output_path = os.path.join(os.path.dirname(target_file_suggestion), output_filename)
                else:
                    # For new UI elements/designs, decide on filename and path
                    # Could be a new component (.tsx), or a markdown description (.md)
                    # Let's assume .tsx components for now, but prompt can influence
                    output_filename = f"UXUI_{task_id[:8].replace('-', '')}.tsx"
                    if "flow" in task_description.lower() or "wireframe" in task_description.lower() or "description" in task_description.lower():
                        output_filename = f"UXUI_{task_id[:8].replace('-', '')}.md"
                    
                    output_path = os.path.join(self.output_ui_root, output_filename)

                try:
                    os.makedirs(os.path.dirname(output_path), exist_ok=True)
                    with open(output_path, "w") as f:
                        f.write(generated_content)
                    print(f"UxUiAgent: Generated content saved to {output_path}")
                    self.send_message("orchestrator", task_id, f"Successfully developed UI/UX element: {output_path}", "task_completed")
                except Exception as e:
                    print(f"UxUiAgent: Error writing file {output_path}: {e}")
                    self.send_message("orchestrator", task_id, f"Failed to write UI/UX content to file: {e}", "task_failed")
            else:
                print("UxUiAgent: Failed to generate UI/UX content (LLM response was None or empty).")
                self.send_message("orchestrator", task_id, "Failed to generate UI/UX content (LLM response was empty or invalid).", "task_failed")

        elif msg["type"] == "review_and_retry":
            task_id = msg["task_id"]
            error_content = msg["content"]
            print(f"UxUiAgent: Received review and retry request for task {task_id}. Error: {error_content}")
            self.send_message("orchestrator", task_id, "Attempting retry after reviewing error.", "status_update")
            
            task = self.state_manager.get_task(task_id)
            if task is None:
                print(f"ERROR: {self.name} - Cannot retry task {task_id}. Task not found in state manager. Marking as permanently_failed.")
                self.state_manager.update_task_status(task_id, "permanently_failed", "Task not found for retry.")
                self.send_message("orchestrator", task_id, "Task could not be found for retry.", "task_failed")
                return
            
            original_task_description = task['description']
            is_modification = any(keyword in original_task_description.lower() for keyword in ["modify", "update", "refactor", "add to existing", "change", "alter", "improve", "redesign"])
            generated_content, target_file_suggestion = self._generate_ui_elements(original_task_description, is_modification)

            if generated_content and generated_content.strip():
                output_path = None
                if is_modification and target_file_suggestion and os.path.exists(target_file_suggestion):
                    file_ext = os.path.splitext(target_file_suggestion)[1]
                    output_filename = os.path.basename(target_file_suggestion).replace(file_ext, f"_retry_{task_id[:4]}{file_ext}")
                    output_path = os.path.join(os.path.dirname(target_file_suggestion), output_filename)
                else:
                    output_filename = f"UXUI_{task_id[:8].replace('-', '')}_retry.tsx"
                    if "flow" in original_task_description.lower() or "wireframe" in original_task_description.lower() or "description" in original_task_description.lower():
                        output_filename = f"UXUI_{task_id[:8].replace('-', '')}_retry.md"
                    output_path = os.path.join(self.output_ui_root, output_filename)
                try:
                    os.makedirs(os.path.dirname(output_path), exist_ok=True)
                    with open(output_path, "w") as f:
                        f.write(generated_content)
                    print(f"UxUiAgent: Retried content saved to {output_path}")
                    self.send_message("orchestrator", task_id, f"Task retried and completed with new content: {output_path}", "task_completed")
                except Exception as e:
                    print(f"UxUiAgent: Error writing retried file {output_path}: {e}")
                    self.send_message("orchestrator", task_id, f"Failed retry attempt: {e}", "task_failed")
            else:
                print("UxUiAgent: Failed to generate UI/UX content on retry (LLM response was None or empty).")
                self.send_message("orchestrator", task_id, "Failed to generate UI/UX content on retry (LLM response was empty or invalid).", "task_failed")
        else:
            print(f"UxUiAgent: Unknown message type {msg['type']}")

    def _get_existing_ui_context(self, max_files=5):
        """
        Reads and returns the content of the most recently modified UI-related files
        from the 'app' directory, root 'components', and relevant 'public' assets.
        Returns (context_string, most_recent_file_path).
        """
        context = []
        found_files = []
        most_recent_file_path = None

        scan_roots = [
            self.app_scan_root,
            self.root_components_scan_root,
            self.public_assets_scan_root # Include public directory for asset context
        ]

        for scan_root in scan_roots:
            if not os.path.exists(scan_root):
                continue

            for root, _, files in os.walk(scan_root):
                for file_name in files:
                    # Target common UI/UX files, components, styles, and relevant assets
                    if file_name.endswith(('.tsx', '.jsx', '.ts', '.js', '.css', '.md', '.json', '.png', '.jpg', '.svg', '.webp')) and \
                       (file_name.startswith('page.') or file_name.startswith('layout.') or \
                        file_name.startswith('loading.') or file_name == 'actions.ts' or \
                        'component' in file_name.lower() or 'form' in file_name.lower() or \
                        'globals.css' in file_name or 'tailwind.config.ts' in file_name or \
                        'hero' in file_name.lower() or 'logo' in file_name.lower() or \
                        'avatar' in file_name.lower() or 'ui' in root.lower()): # Broaden for typical UI elements, styling, and common assets
                        full_path = os.path.join(root, file_name)
                        if os.path.isfile(full_path):
                            found_files.append(full_path)
        
        found_files.sort(key=os.path.getmtime, reverse=True)

        if found_files:
            most_recent_file_path = found_files[0]

        for i, file_path in enumerate(found_files[:max_files]):
            try:
                with open(file_path, 'rb' if file_path.endswith(('.png', '.jpg', '.svg', '.webp')) else 'r') as f:
                    content = ""
                    if file_path.endswith(('.png', '.jpg', '.svg', '.webp')):
                        # For images, just include path and a description, not binary content
                        content = f"[Binary content for {os.path.basename(file_path)}. Refer to file path for details.]"
                    else:
                        content = f.read()
                    
                    relative_path = os.path.relpath(file_path, self.project_root)
                    lang_highlight = "text"
                    if file_path.endswith(('.tsx', '.ts')): lang_highlight = "typescript"
                    elif file_path.endswith(('.jsx', '.js')): lang_highlight = "javascript"
                    elif file_path.endswith('.css'): lang_highlight = "css"
                    elif file_path.endswith('.json'): lang_highlight = "json"
                    elif file_path.endswith('.md'): lang_highlight = "markdown"

                    file_context = f"--- Existing File: {relative_path} ---\n```{lang_highlight}\n{content}\n```\n"
                    context.append(file_context)
            except Exception as e:
                print(f"ERROR: UxUiAgent - Could not read existing UI/UX code from {file_path} for context: {e}")
        return "\n".join(context), most_recent_file_path

    def _generate_ui_elements(self, task_description, is_modification=False):
        """
        Uses the LLM to generate UI/UX design concepts, user flows, or React components
        with Tailwind CSS.
        Returns (generated_content, suggested_target_file_path)
        """
        existing_ui_context, most_recent_ui_file = self._get_existing_ui_context()
        
        # Extract f-string expressions to avoid backslash errors
        ui_context_text = f"Existing UI/UX Context (most recent file first):\n{existing_ui_context}\n"
        ui_context_guidance = f"Consider the following existing UI/UX context from your project. Adapt your new design/code to fit with this existing style, component library (e.g., Shadcn UI from components/ui), and overall visual language:\n{existing_ui_context}\n"
        
        if is_modification and most_recent_ui_file:
            prompt = f"""You are a UX/UI Design Agent specializing in Next.js (App Router), React, and Tailwind CSS.
            Your task is to **modify an existing UI component, page, or design artifact** to address the following requirement:
            "{task_description}"

            Consider the most recent existing file provided in the context below. Your output should be the full,
            revised content of that file, integrating the new design, component changes, or flow improvements.
            
            {ui_context_text if existing_ui_context else ""}

            Generate the full, complete code for the component file (e.g., a .tsx file) or a detailed Markdown description of the UI/UX changes.
            If generating code, use functional React components and Tailwind CSS classes.
            Do NOT omit any parts or use placeholders like '...'.
            Do NOT include any explanatory text, comments outside the content, or formatting outside of the main content.
            """
        else:
            prompt = f"""You are a UX/UI Design Agent specializing in Next.js (App Router), React, and Tailwind CSS.
            Your task is to generate a new UI component (React/TypeScript with Tailwind CSS), a user flow description,
            or a wireframe concept based on the following requirement:
            "{task_description}"

            If generating a component: ensure it's a functional React component, use Tailwind CSS for styling, and import necessary modules.
            If describing a flow/concept: provide a detailed Markdown explanation, including user steps, states, and rationale.

            {ui_context_guidance if existing_ui_context else ""}

            Generate the full, complete content. Do NOT omit any parts or use placeholders like '...'.
            Do NOT include any explanatory text, comments outside the content, or formatting outside of the main content.
            """
        print(f"UxUiAgent: Requesting LLM to generate UI/UX content for: {task_description[:50]}...")
        response = self._generate_response(prompt, max_tokens=2500) # Increased max_tokens for potentially larger UI descriptions/components
        
        if response and isinstance(response, str):
            cleaned_response = response.strip()
            # Generic stripping for various code blocks and markdown
            if cleaned_response.startswith("```"):
                first_newline = cleaned_response.find('\n')
                cleaned_response = cleaned_response[first_newline+1:].strip() if first_newline != -1 else cleaned_response[len("```"):].strip()
            if cleaned_response.endswith("```"):
                cleaned_response = cleaned_response[:-len("```")].strip()
            return cleaned_response, most_recent_ui_file
        return response, None

if __name__ == "__main__":
    ux_ui_agent = UxUiAgent()  # Use default model from __init__
    ux_ui_agent.run()
