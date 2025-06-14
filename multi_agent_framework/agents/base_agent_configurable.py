"""
Configurable Base Agent

Updated base agent that accepts project configuration instead of hardcoding paths.
"""

import os
import time
from abc import ABC, abstractmethod
from typing import Optional
from dotenv import load_dotenv
import openai
import anthropic
import google.generativeai as genai

from ..core.message_bus_configurable import MessageBus
from ..core.shared_state_manager import get_shared_state_manager
from ..core.project_analyzer import ProjectAnalyzer
from ..core.file_integrator import FileIntegrator
from ..core.intelligent_namer import IntelligentNamer
from ..core.smart_integrator import SmartIntegrator
from ..core.project_config import ProjectConfig

load_dotenv()  # Load environment variables from .env file


class BaseAgent(ABC):
    def __init__(self, name: str, project_config: Optional[ProjectConfig] = None, 
                 model_provider: Optional[str] = None, model_name: Optional[str] = None):
        """
        Initialize base agent with project configuration.
        
        Args:
            name: Agent name
            project_config: Project configuration instance
            model_provider: LLM provider (overrides config)
            model_name: LLM model name (overrides config)
        """
        self.name = name
        
        # Use provided config or create default
        self.project_config = project_config or ProjectConfig()
        self.project_root = self.project_config.get_project_root()
        
        # Get model config from project config if not provided
        if not model_provider or not model_name:
            model_config = self.project_config.get_model_config()
            model_provider = model_provider or model_config["provider"]
            model_name = model_name or model_config["name"]
        
        # Initialize message bus with configured directory
        self.message_bus = MessageBus(
            message_dir=self.project_config.get_message_queue_dir()
        )
        
        # Use shared state manager
        self.state_manager = get_shared_state_manager()
        
        # Initialize project analysis and integration tools
        self.project_analyzer = ProjectAnalyzer(self.project_root)
        self.file_integrator = FileIntegrator(self.project_root)
        self.intelligent_namer = IntelligentNamer(self.project_root)
        self.smart_integrator = SmartIntegrator(self.project_root)
        
        # Initialize LLM
        try:
            self.model_provider = model_provider
            self.model_name = model_name
            self.llm = self._initialize_llm()
        except Exception as e:
            print(f"CRITICAL ERROR: BaseAgent '{name}' failed to initialize LLM: {e}")
            raise
    
    def send_message(self, recipient_agent: str, task_id: str, content: str, msg_type: str = "task"):
        """Send message to another agent."""
        message = {
            "sender": self.name,
            "recipient": recipient_agent,
            "task_id": task_id,
            "type": msg_type,
            "content": content,
            "timestamp": time.time()
        }
        self.message_bus.send_message(recipient_agent, message)
    
    def receive_messages(self):
        """Receive messages from message bus."""
        return self.message_bus.receive_messages(self.name)
    
    @abstractmethod
    def run(self):
        """Main loop for the agent to receive and process messages."""
        pass
    
    def _initialize_llm(self):
        """Initialize the LLM based on provider."""
        if self.model_provider == "claude":
            api_key = os.getenv("ANTHROPIC_API_KEY")
            if not api_key:
                raise ValueError("ANTHROPIC_API_KEY environment variable not set.")
            return anthropic.Anthropic(api_key=api_key)
            
        elif self.model_provider == "gemini":
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                raise ValueError("GEMINI_API_KEY environment variable not set.")
            genai.configure(api_key=api_key)
            return genai.GenerativeModel(self.model_name)
            
        elif self.model_provider == "openai":
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY environment variable not set.")
            return openai.OpenAI(api_key=api_key)
            
        else:
            raise ValueError(f"Unsupported model provider: {self.model_provider}")
    
    def _generate_response(self, prompt, max_tokens=1000):
        """Generate response from LLM."""
        if self.model_provider == "claude":
            try:
                response = self.llm.messages.create(
                    model=self.model_name,
                    max_tokens=max_tokens,
                    messages=[
                        {"role": "user", "content": prompt}
                    ]
                )
                return response.content[0].text
            except Exception as e:
                print(f"Error calling Claude: {e}")
                return None
                
        elif self.model_provider == "gemini":
            try:
                response = self.llm.generate_content(prompt)
                return response.text
            except Exception as e:
                print(f"Error calling Gemini: {e}")
                return None
                
        elif self.model_provider == "openai":
            try:
                response = self.llm.chat.completions.create(
                    model=self.model_name,
                    messages=[
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=max_tokens
                )
                return response.choices[0].message.content
            except Exception as e:
                print(f"Error calling OpenAI: {e}")
                return None
                
        return None
    
    def get_integration_strategy(self, task_description: str, file_type: str = None):
        """Determine the best integration strategy for a task."""
        # Check if it's a modification task
        should_modify, target_file = self.project_analyzer.should_modify_existing(task_description)
        
        if should_modify and target_file:
            return {
                'mode': 'modify',
                'target_file': target_file,
                'target_dir': os.path.dirname(target_file)
            }
        else:
            # Find appropriate directory for new file
            target_dir = self.project_analyzer.suggest_target_file(task_description, file_type or 'component')
            related_files = self.project_analyzer.find_related_files(task_description)
            
            return {
                'mode': 'create',
                'target_dir': target_dir,
                'related_files': related_files,
                'naming_convention': self.project_analyzer.get_file_naming_convention(target_dir or ''),
                'task_description': task_description
            }
    
    def integrate_generated_content(self, content: str, strategy: dict, filename: str = None):
        """Integrate generated content using the determined strategy."""
        try:
            if strategy['mode'] == 'modify':
                # Modify existing file
                result_path = self.file_integrator.integrate_component(
                    content, 
                    strategy['target_file'], 
                    mode='modify'
                )
                return {'success': True, 'path': result_path, 'action': 'modified'}
            
            else:
                # Check if we should consolidate into existing file instead of creating new
                related_files = strategy.get('related_files', [])
                task_description = strategy.get('task_description', '')
                
                for related_file in related_files[:3]:  # Check top 3 related files
                    should_consolidate, reason = self.smart_integrator.should_consolidate(
                        content, related_file, task_description
                    )
                    
                    if should_consolidate:
                        # Determine consolidation strategy
                        if self.smart_integrator._is_utility_function(content):
                            consolidation_strategy = 'merge_functions'
                        elif self.smart_integrator._is_related_component(content, related_file):
                            consolidation_strategy = 'merge_components'
                        elif self.smart_integrator._is_enhancement(content, task_description):
                            consolidation_strategy = 'enhance'
                        else:
                            consolidation_strategy = 'append'
                        
                        # Consolidate content
                        consolidated_content = self.smart_integrator.consolidate_content(
                            content, related_file, consolidation_strategy
                        )
                        
                        # Use file integrator to merge properly
                        result_path = self.file_integrator.integrate_component(
                            consolidated_content, 
                            related_file, 
                            mode='modify'
                        )
                        
                        return {
                            'success': True, 
                            'path': result_path, 
                            'action': 'consolidated',
                            'consolidation_reason': reason
                        }
                
                # If no consolidation, create new file with intelligent naming
                if not filename:
                    filename = self._generate_filename_from_content(
                        content, 
                        strategy.get('naming_convention', {}),
                        task_description=strategy.get('task_description', '')
                    )
                
                target_path = os.path.join(strategy['target_dir'], filename)
                result_path = self.file_integrator.integrate_component(
                    content, 
                    target_path, 
                    mode='create'
                )
                return {'success': True, 'path': result_path, 'action': 'created'}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _generate_filename_from_content(self, content: str, naming_convention: dict, task_description: str = ''):
        """Generate appropriate filename from content using intelligent naming."""
        # Determine file type from naming convention
        file_type = 'component'  # default
        if 'api' in naming_convention.get('pattern', '').lower():
            file_type = 'api'
        elif 'test' in naming_convention.get('pattern', '').lower():
            file_type = 'test'
        elif 'migration' in naming_convention.get('pattern', '').lower():
            file_type = 'database'
        
        # Extract intelligent name from content
        component_name = self.intelligent_namer.extract_component_name(content, file_type)
        
        if component_name:
            # Get existing files to check for conflicts
            import glob
            target_dir = os.path.dirname(naming_convention.get('example', ''))
            if target_dir and os.path.exists(os.path.join(self.project_root, target_dir)):
                existing_files = glob.glob(os.path.join(self.project_root, target_dir, '*'))
                existing_names = [os.path.splitext(os.path.basename(f))[0] for f in existing_files]
            else:
                existing_names = []
            
            # Generate unique name if conflicts exist
            unique_name = self.intelligent_namer.generate_unique_name(
                component_name, existing_names, task_description
            )
            
            # Get appropriate filename with extension
            return self.intelligent_namer.suggest_filename(unique_name, file_type)
        
        # Fallback to old logic if intelligent naming fails
        import re
        component_match = re.search(r'(?:export\s+default\s+)?(?:function\s+|const\s+)(\w+)', content)
        if component_match:
            name = component_match.group(1)
            
            # Apply naming convention
            if 'PascalCase' in naming_convention.get('pattern', ''):
                name = self._to_pascal_case(name)
            
            # Add appropriate extension
            if '.tsx' in naming_convention.get('pattern', ''):
                return f"{name}.tsx"
            elif '.ts' in naming_convention.get('pattern', ''):
                return f"{name}.ts"
            else:
                return f"{name}.js"
        
        # Final fallback to generic name
        return naming_convention.get('example', 'GeneratedFile.tsx')
    
    def _to_pascal_case(self, text: str):
        """Convert text to PascalCase."""
        import re
        return ''.join(word.capitalize() for word in re.split(r'[_\-\s]+', text))
    
    def safe_process_message(self, process_func):
        """Wrapper to safely process messages with error handling"""
        def wrapper(msg):
            try:
                process_func(msg)
            except KeyError as e:
                error_msg = f"Missing required key in message: {e}"
                print(f"{self.name}: ERROR - {error_msg}")
                if 'task_id' in msg:
                    self.send_message("orchestrator", msg['task_id'], error_msg, "task_failed")
            except Exception as e:
                error_msg = f"Unexpected error processing message: {str(e)}"
                print(f"{self.name}: ERROR - {error_msg}")
                if 'task_id' in msg:
                    self.send_message("orchestrator", msg['task_id'], error_msg, "task_failed")
        return wrapper