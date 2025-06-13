"""
Event-Driven Documentation Agent

This agent handles documentation generation, API documentation, README files,
and code documentation in an event-driven manner.
"""

import os
import json
import time
from typing import Dict, Any

from .event_driven_base_agent import EventDrivenBaseAgent
from ..core.event_bus_interface import Event, EventType
from ..core.project_analyzer import ProjectAnalyzer
from ..core.file_integrator import FileIntegrator


class EventDrivenDocsAgent(EventDrivenBaseAgent):
    """
    Event-driven Documentation agent that generates and maintains project documentation
    """
    
    def __init__(self, model_provider="gemini", model_name="gemini-1.5-flash", project_config=None):
        super().__init__("docs_agent", model_provider, model_name, project_config)
        
        # Initialize integration components
        self.project_analyzer = ProjectAnalyzer(self.project_root)
        self.file_integrator = FileIntegrator(self.project_root)
        
        # Documentation types and their typical locations
        self.doc_types = {
            'api': ['docs/api', 'api-docs', 'documentation/api'],
            'readme': ['', 'docs'],
            'guide': ['docs/guides', 'documentation'],
            'component': ['docs/components', 'src/components'],
            'architecture': ['docs/architecture', 'docs/design']
        }
        
        print(f"EventDrivenDocsAgent initialized with documentation generation capabilities.")
    
    def process_task(self, task_id: str, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a documentation task
        """
        description = task_data.get('description', '')
        feature_id = task_data.get('feature_id')
        
        print(f"Docs Agent processing task: {description[:50]}...")
        
        try:
            # Analyze task to determine documentation context
            context = self._analyze_docs_context(description)
            
            # Generate documentation
            docs_content, target_file = self._generate_documentation(description, context)
            
            if docs_content and docs_content.strip():
                # Integrate documentation
                result = self._integrate_documentation(docs_content, target_file, context)
                
                if result['success']:
                    return {
                        'success': True,
                        'output': docs_content,
                        'file_path': result['path'],
                        'action': result['action'],
                        'message': f"Successfully {result['action']} {context['type']} documentation: {result['path']}"
                    }
                else:
                    return {
                        'success': False,
                        'error': result['error'],
                        'message': f"Failed to integrate documentation: {result['error']}"
                    }
            else:
                return {
                    'success': False,
                    'error': 'No content generated',
                    'message': 'Failed to generate documentation'
                }
                
        except Exception as e:
            print(f"Docs Agent error: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'error': str(e),
                'message': f'Error in documentation task: {str(e)}'
            }
    
    def _analyze_docs_context(self, task_description: str) -> Dict[str, Any]:
        """Analyze the task to determine documentation context"""
        context = {
            'type': 'general',
            'format': 'markdown',
            'target_audience': 'developers',
            'is_api_docs': False,
            'is_user_guide': False,
            'component_name': None
        }
        
        task_lower = task_description.lower()
        
        # Determine documentation type
        if 'api' in task_lower and ('doc' in task_lower or 'document' in task_lower):
            context['type'] = 'api'
            context['is_api_docs'] = True
            context['format'] = 'openapi' if 'openapi' in task_lower or 'swagger' in task_lower else 'markdown'
        elif 'readme' in task_lower:
            context['type'] = 'readme'
        elif 'guide' in task_lower or 'tutorial' in task_lower:
            context['type'] = 'guide'
            context['is_user_guide'] = True
        elif 'component' in task_lower:
            context['type'] = 'component'
            # Try to extract component name
            words = task_description.split()
            for i, word in enumerate(words):
                if word.lower() in ['component', 'for'] and i + 1 < len(words):
                    context['component_name'] = words[i + 1]
                    break
        elif 'architecture' in task_lower or 'design' in task_lower:
            context['type'] = 'architecture'
        elif 'function' in task_lower or 'method' in task_lower or 'class' in task_lower:
            context['type'] = 'code'
            context['format'] = 'jsdoc' if 'js' in task_lower else 'docstring'
        
        # Determine target audience
        if 'user' in task_lower or 'end-user' in task_lower:
            context['target_audience'] = 'end-users'
        elif 'internal' in task_lower or 'team' in task_lower:
            context['target_audience'] = 'internal-team'
        
        return context
    
    def _generate_documentation(self, task_description: str, context: Dict[str, Any]) -> tuple:
        """Generate documentation using the LLM"""
        # Build appropriate prompt
        prompt = self._build_docs_prompt(task_description, context)
        
        print(f"Docs Agent: Generating {context['type']} documentation...")
        generated_content = self._generate_response(prompt)
        
        # Determine target file
        target_file = self._determine_target_file(generated_content, context)
        
        return generated_content, target_file
    
    def _build_docs_prompt(self, task_description: str, context: Dict[str, Any]) -> str:
        """Build a context-aware prompt for documentation generation"""
        # Get project information
        project_type = 'unknown'
        if self.project_config:
            try:
                project_type = self.project_config._detect_project_type()
            except:
                pass
        
        # Get existing documentation context
        existing_docs = self._gather_docs_context(context)
        
        base_prompt = f"""You are a technical documentation specialist creating documentation for a {project_type} project.

Task: {task_description}

Documentation Type: {context['type']}
Format: {context['format']}
Target Audience: {context['target_audience']}
"""
        
        if context['is_api_docs']:
            prompt = base_prompt + f"""
{existing_docs}

Generate comprehensive API documentation that includes:
1. Endpoint descriptions with purpose and usage
2. Request/Response schemas with examples
3. Authentication requirements
4. Error codes and handling
5. Rate limiting information (if applicable)
6. Code examples in multiple languages

For each endpoint include:
- HTTP method and path
- Description
- Parameters (path, query, body)
- Request/Response examples
- Possible error responses

Use clear markdown formatting with proper headings.
"""
        elif context['type'] == 'readme':
            prompt = base_prompt + f"""
{existing_docs}

Generate a comprehensive README that includes:
1. Project title and description
2. Features list
3. Installation instructions
4. Usage examples
5. Configuration options
6. API reference (if applicable)
7. Contributing guidelines
8. License information

Make it engaging and easy to follow, with clear examples.
"""
        elif context['type'] == 'component':
            prompt = base_prompt + f"""
Component: {context.get('component_name', 'Unknown')}

{existing_docs}

Generate component documentation that includes:
1. Component purpose and usage
2. Props/Parameters with types and descriptions
3. Methods/Functions available
4. Events emitted (if applicable)
5. Usage examples
6. Styling options
7. Best practices and common patterns

Include code examples showing different use cases.
"""
        elif context['type'] == 'architecture':
            prompt = base_prompt + f"""
{existing_docs}

Generate architecture documentation that includes:
1. System overview and design principles
2. Component/Module structure
3. Data flow diagrams (using mermaid syntax)
4. Technology stack and rationale
5. Design patterns used
6. Scalability considerations
7. Security architecture

Use diagrams where appropriate to visualize the architecture.
"""
        else:
            prompt = base_prompt + f"""
{existing_docs}

Generate clear and comprehensive documentation following best practices for {context['type']} documentation.
Include examples, use cases, and any relevant diagrams or code snippets.
"""
        
        prompt += "\n\nReturn ONLY the documentation content, no explanations or meta-commentary."
        
        return prompt
    
    def _gather_docs_context(self, context: Dict[str, Any]) -> str:
        """Gather existing documentation for context"""
        existing_docs = []
        
        # Look for existing documentation files
        if os.path.exists(self.project_root):
            docs_dirs = ['docs', 'documentation', '.']
            for docs_dir in docs_dirs:
                docs_path = os.path.join(self.project_root, docs_dir)
                if os.path.exists(docs_path):
                    for file in os.listdir(docs_path):
                        if file.endswith(('.md', '.rst', '.txt')):
                            existing_docs.append(f"Found: {os.path.join(docs_dir, file)}")
        
        if existing_docs:
            return f"Existing documentation:\n" + "\n".join(existing_docs[:5])
        else:
            return "No existing documentation found. Creating new documentation."
    
    def _determine_target_file(self, content: str, context: Dict[str, Any]) -> str:
        """Determine the target file name based on content and context"""
        # Try to extract filename from content
        if content and '# File:' in content:
            lines = content.split('\n')
            for line in lines:
                if line.strip().startswith('# File:'):
                    return line.replace('# File:', '').strip()
        
        # Generate filename based on context
        timestamp = int(time.time())
        
        if context['type'] == 'api':
            if context['format'] == 'openapi':
                return 'docs/api/openapi.yaml'
            else:
                return 'docs/api/API.md'
        elif context['type'] == 'readme':
            return 'README.md'
        elif context['type'] == 'guide':
            return f"docs/guides/user-guide-{timestamp}.md"
        elif context['type'] == 'component':
            component = context.get('component_name', 'component').lower()
            return f"docs/components/{component}.md"
        elif context['type'] == 'architecture':
            return 'docs/architecture/ARCHITECTURE.md'
        else:
            return f"docs/documentation-{timestamp}.md"
    
    def _integrate_documentation(self, content: str, target_file: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Integrate documentation into the project"""
        # Use the intelligent integration system
        strategy = self.get_integration_strategy(
            f"{context['type']} documentation", 
            'documentation'
        )
        
        # Ensure proper directory structure
        target_dir = os.path.dirname(target_file)
        if target_dir and not os.path.isabs(target_file):
            # Create necessary directories
            full_path = os.path.join(self.project_root, target_dir)
            os.makedirs(full_path, exist_ok=True)
            strategy['target_dir'] = full_path
        
        # Set the filename in strategy
        strategy['filename'] = os.path.basename(target_file)
        
        # Integrate the content
        result = self.integrate_generated_content(content, strategy)
        
        return result


if __name__ == "__main__":
    # For testing purposes
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        agent = EventDrivenDocsAgent()
        print(f"EventDrivenDocsAgent initialized: {agent.name}")