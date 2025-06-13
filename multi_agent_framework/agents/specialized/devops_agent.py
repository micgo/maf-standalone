import os
import sys
import json
import time
import uuid

# Use relative imports
from ..base_agent_configurable import BaseAgent
from ...core.project_config import ProjectConfig

class DevopsAgent(BaseAgent):
    """
    The DevopsAgent is responsible for generating deployment configurations, particularly for Vercel,
    and handling environment setup for Next.js applications integrated with Supabase.
    It can now propose direct modifications to existing configuration files.
    """
    def __init__(self, project_config=None, model_provider="gemini", model_name="gemini-1.5-flash"):  # Config generation is simple
        super().__init__("devops_agent", project_config, model_provider, model_name)
        
        # Roots for scanning existing configuration files
        self.config_scan_roots = [
            self.project_root, # For package.json, next.config.mjs, postcss.config.mjs, tailwind.config.ts, components.json
            os.path.abspath(os.path.join(self.project_root, '.github', 'workflows')), # For GitHub Actions CI/CD
            os.path.abspath(os.path.join(self.project_root, 'supabase')) # For supabase config.toml
        ]
        
        print(f"DevopsAgent initialized with intelligent integration system.")

    def run(self):
        """
        Main loop for the DevopsAgent to continuously receive and process messages.
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
            print(f"DevopsAgent received task {task_id}: {task_description}")
            self.state_manager.update_task_status(task_id, "in_progress")

            # Generate the DevOps configuration
            generated_config, target_file = self._generate_devops_config(task_description)

            if generated_config and generated_config.strip():
                # Use new integration system
                strategy = self.get_integration_strategy(task_description, 'config')
                result = self.integrate_generated_content(generated_config, strategy)

                if result['success']:
                    print(f"DevopsAgent: Successfully {result['action']} config: {result['path']}")
                    self.send_message("orchestrator", task_id, f"Successfully {result['action']} DevOps config: {result['path']}", "task_completed")
                else:
                    print(f"DevopsAgent: Integration failed: {result['error']}")
                    self.send_message("orchestrator", task_id, f"Failed to integrate DevOps config: {result['error']}", "task_failed")
            else:
                print("DevopsAgent: Failed to generate DevOps config (LLM response was None or empty).")
                self.send_message("orchestrator", task_id, "Failed to generate DevOps config (LLM response was empty or invalid).", "task_failed")

        elif msg["type"] == "review_and_retry":
            task_id = msg["task_id"]
            error_content = msg["content"]
            print(f"DevopsAgent: Received review and retry request for task {task_id}. Error: {error_content}")
            self.send_message("orchestrator", task_id, "Attempting retry after reviewing error.", "status_update")
            
            original_task_description = self.state_manager.get_task(task_id)['description']
            is_modification = any(keyword in original_task_description.lower() for keyword in ["modify", "update", "configure existing", "change", "alter"])
            generated_config, target_file_suggestion = self._generate_devops_config(original_task_description, is_modification)

            if generated_config and generated_config.strip():
                if is_modification and target_file_suggestion and os.path.exists(target_file_suggestion):
                    output_filename = os.path.basename(target_file_suggestion).replace(".json", f"_retry_{task_id[:4]}.json").replace(".yaml", f"_retry_{task_id[:4]}.yaml").replace(".yml", f"_retry_{task_id[:4]}.yml")
                    output_path = os.path.join(os.path.dirname(target_file_suggestion), output_filename)
                else:
                    output_filename = f"config_{task_id[:8]}_retry.json"
                    output_path = os.path.join(self.devops_root, output_filename)
                try:
                    os.makedirs(os.path.dirname(output_path), exist_ok=True)
                    with open(output_path, "w") as f:
                        f.write(generated_config)
                    print(f"DevopsAgent: Retried config saved to {output_path}")
                    self.send_message("orchestrator", task_id, f"Task retried and completed with new config: {output_path}", "task_completed")
                except Exception as e:
                    print(f"DevopsAgent: Error writing retried file {output_path}: {e}")
                    self.send_message("orchestrator", task_id, f"Failed retry attempt: {e}", "task_failed")
            else:
                print("DevopsAgent: Failed to generate DevOps config on retry (LLM response was None or empty).")
                self.send_message("orchestrator", task_id, "Failed to generate DevOps config on retry (LLM response was empty or invalid).", "task_failed")
        else:
            print(f"DevopsAgent: Unknown message type {msg['type']}")

    def _get_existing_devops_config_context(self, max_files=3):
        """
        Reads and returns the content of the most recently modified DevOps configuration files (e.g., vercel.json, CI/CD yamls, package.json)
        to provide context to the LLM. Returns (context_string, most_recent_file_path).
        """
        context = []
        found_files = []
        most_recent_file_path = None

        for scan_root in self.config_scan_roots:
            if not os.path.exists(scan_root):
                continue

            for root, _, files in os.walk(scan_root):
                for file_name in files:
                    # Target common config files, including package.json, next.config.mjs, etc.
                    if file_name in ['package.json', 'vercel.json', 'next.config.mjs', 'postcss.config.mjs', 'tailwind.config.ts', 'components.json', 'config.toml'] or \
                       file_name.endswith(('.yaml', '.yml')): # Generic YAML for CI/CD
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
                    lang_highlight = "json" if file_path.endswith('.json') else ("yaml" if file_path.endswith(('.yaml', '.yml')) else "typescript") # tsconfig etc.
                    context.append(f"--- Existing File: {relative_path} ---\n```{lang_highlight}\n{content}\n```\n")
            except Exception as e:
                print(f"ERROR: DevopsAgent - Could not read existing DevOps config from {file_path} for context: {e}")
        return "\n".join(context), most_recent_file_path

    def _generate_devops_config(self, task_description):
        """
        Uses the LLM to generate Vercel configuration or CI/CD steps for Next.js applications integrated with Supabase.
        Returns (generated_config, target_file_suggestion)
        """
        existing_config_context, most_recent_config_file = self._get_existing_devops_config_context()

        # Check if this is a modification task
        is_modification = any(keyword in task_description.lower() for keyword in ["modify", "update", "add to existing", "configure existing", "alter"])
        
        if is_modification and most_recent_config_file:
            prompt = f"""You are a DevOps & Infrastructure Agent specializing in Next.js deployments to Vercel,
            and integrating with Supabase.
            Your task is to **modify an existing configuration file (e.g., vercel.json, package.json, CI/CD YAML, or Supabase config.toml)** to address the following requirement:
            "{task_description}"

            Consider the most recent existing configuration file provided in the context below. Your output should be the full,
            revised content of that file, integrating the new functionality or changes.
            
            {f"Existing Configuration Context (most recent file first):\n{existing_config_context}\n" if existing_config_context else ""}

            Generate the full, complete code/configuration. Do NOT omit any parts or use placeholders like '...'.
            Do NOT include any explanatory text, comments outside the code, or formatting outside of the content.
            """
        else:
            prompt = f"""You are a DevOps & Infrastructure Agent specializing in Next.js deployments to Vercel,
            and integrating with Supabase.
            Your task is to generate a Vercel configuration (vercel.json) or relevant CI/CD pipeline steps
            for a Next.js application based on the following requirement:
            "{task_description}"

            Focus on Vercel-specific configurations for environment variables (especially for Supabase URL/keys),
            serverless functions, or build commands. If CI/CD is implied, provide a relevant YAML snippet for GitHub Actions or similar.
            
            {f"Consider the following existing configuration context from your project. Adapt your new configuration to fit with this existing structure and style:\n{existing_config_context}\n" if existing_config_context else ""}

            Generate the full, complete code/configuration. Do NOT omit any parts or use placeholders like '...'.
            Do NOT include any explanatory text, comments outside the code, or formatting outside of the content.
            """
        print(f"DevopsAgent: Requesting LLM to generate DevOps config for: {task_description[:50]}...")
        response = self._generate_response(prompt, max_tokens=1500)

        if response and isinstance(response, str):
            cleaned_response = response.strip()
            if cleaned_response.startswith("```json") or cleaned_response.startswith("```yaml") or cleaned_response.startswith("```typescript"):
                first_newline = cleaned_response.find('\n')
                cleaned_response = cleaned_response[first_newline+1:].strip() if first_newline != -1 else cleaned_response[len("```json"):].strip()
            elif cleaned_response.startswith("```"):
                first_newline = cleaned_response.find('\n')
                cleaned_response = cleaned_response[first_newline+1:].strip() if first_newline != -1 else cleaned_response[len("```"):].strip()
            if cleaned_response.endswith("```"):
                cleaned_response = cleaned_response[:-len("```")].strip()
            return cleaned_response, most_recent_config_file if is_modification else None
        return response, most_recent_config_file if is_modification else None

if __name__ == "__main__":
    devops_agent = DevopsAgent()  # Use default model from __init__
    devops_agent.run()
