"""
Event-Driven Frontend Agent

This is the event-driven version of the frontend agent that handles
UI/frontend development tasks using events instead of polling.
"""

import os
import re
import json
from typing import Dict, Any, Optional

from .event_driven_base_agent import EventDrivenBaseAgent
from ..core.event_bus_interface import Event, EventType


class EventDrivenFrontendAgent(EventDrivenBaseAgent):
    """
    Event-driven frontend agent for handling UI development tasks
    """
    
    def __init__(self, model_provider="gemini", model_name="gemini-2.0-flash-thinking-exp-01-21", project_config=None):
        super().__init__("frontend_agent", model_provider, model_name, project_config)
        
        # Track component generation statistics
        self._components_created = 0
        self._components_modified = 0
    
    def _subscribe_to_events(self):
        """Subscribe to frontend-specific events"""
        super()._subscribe_to_events()
        
        # Subscribe to task retry events (for retrying failed tasks)
        self.event_bus.subscribe(EventType.TASK_RETRY, self._handle_task_retry)
        
        # Subscribe to custom frontend events
        self.event_bus.subscribe(EventType.CUSTOM, self._handle_custom_event)
    
    def _handle_task_retry(self, event: Event):
        """Handle task retry events"""
        data = event.data
        
        # Check if retry is for this agent
        if data.get("assigned_agent") != self.name:
            return
        
        task_id = data.get("task_id")
        if not task_id:
            return
        
        print(f"{self.name}: Retrying task {task_id} (attempt {data.get('retry_count', 1)})")
        
        # Process as a new task assignment
        self._handle_task_assigned(Event(
            id=event.id,
            type=EventType.TASK_ASSIGNED,
            source=event.source,
            timestamp=event.timestamp,
            data=data,
            correlation_id=event.correlation_id
        ))
    
    def _handle_custom_event(self, event: Event):
        """Handle custom frontend events"""
        event_name = event.data.get('event_name', '')
        
        if event_name == 'component_update_request':
            # Handle component update requests
            component_path = event.data.get('component_path')
            update_type = event.data.get('update_type')
            
            print(f"{self.name}: Received component update request for {component_path}")
            
            # Could trigger automatic updates or validations
    
    def process_task(self, task_id: str, task_data: Dict[str, Any]) -> Any:
        """
        Process frontend development tasks
        
        Args:
            task_id: Unique task identifier
            task_data: Task information including description
            
        Returns:
            Task result
        """
        description = task_data.get('description', '')
        feature_id = task_data.get('feature_id', '')
        
        print(f"{self.name}: Processing task - {description}")
        
        try:
            # Analyze the task
            task_type = self._analyze_task_type(description)
            
            if task_type == "component":
                result = self._create_component(description, feature_id)
            elif task_type == "page":
                result = self._create_page(description, feature_id)
            elif task_type == "form":
                result = self._create_form(description, feature_id)
            elif task_type == "update":
                result = self._update_component(description, feature_id)
            else:
                result = self._handle_generic_task(description, feature_id)
            
            # Emit completion metrics
            self.emit_custom_event('frontend_metrics', {
                'components_created': self._components_created,
                'components_modified': self._components_modified,
                'task_type': task_type
            })
            
            return result
            
        except Exception as e:
            error_msg = f"Error processing frontend task: {str(e)}"
            print(f"{self.name}: {error_msg}")
            
            # Emit error event for monitoring
            self.emit_custom_event('frontend_error', {
                'task_id': task_id,
                'error': str(e),
                'task_type': task_type if 'task_type' in locals() else 'unknown'
            })
            
            raise
    
    def _analyze_task_type(self, description: str) -> str:
        """Analyze task description to determine type"""
        description_lower = description.lower()
        
        if any(word in description_lower for word in ['component', 'button', 'card', 'modal']):
            return "component"
        elif any(word in description_lower for word in ['page', 'screen', 'view']):
            return "page"
        elif any(word in description_lower for word in ['form', 'input', 'field']):
            return "form"
        elif any(word in description_lower for word in ['update', 'modify', 'change', 'fix']):
            return "update"
        else:
            return "generic"
    
    def _create_component(self, description: str, feature_id: str) -> Dict[str, Any]:
        """Create a new UI component"""
        print(f"{self.name}: Creating component for: {description}")
        
        # Get project context
        project_info = self.project_analyzer.get_project_structure()
        frontend_files = self.project_analyzer.find_files_by_extension(['.tsx', '.jsx'])
        existing_components = [f for f in frontend_files if 'components' in f]
        
        # Determine integration strategy
        strategy = self.get_integration_strategy(description, 'component')
        
        # Generate component prompt
        prompt = self._build_component_prompt(description, existing_components, project_info)
        
        # Generate component code
        component_code = self._generate_response(prompt, max_tokens=2000)
        
        if component_code:
            # Integrate the component
            result = self.integrate_generated_content(component_code, strategy)
            
            if result['success']:
                self._components_created += 1
                
                # Emit component created event
                self.emit_custom_event('component_created', {
                    'path': result['path'],
                    'feature_id': feature_id,
                    'action': result['action']
                })
                
                return {
                    'status': 'success',
                    'component_path': result['path'],
                    'action': result['action'],
                    'message': f"Successfully created component at {result['path']}"
                }
            else:
                raise Exception(f"Failed to integrate component: {result.get('error', 'Unknown error')}")
        else:
            raise Exception("Failed to generate component code")
    
    def _create_page(self, description: str, feature_id: str) -> Dict[str, Any]:
        """Create a new page/view"""
        print(f"{self.name}: Creating page for: {description}")
        
        # Similar to component but for pages
        project_info = self.project_analyzer.get_project_structure()
        existing_pages = self.project_analyzer.find_files_by_pattern('app/**/page.tsx')
        
        strategy = self.get_integration_strategy(description, 'page')
        
        prompt = self._build_page_prompt(description, existing_pages, project_info)
        page_code = self._generate_response(prompt, max_tokens=2500)
        
        if page_code:
            result = self.integrate_generated_content(page_code, strategy)
            
            if result['success']:
                self._components_created += 1
                
                return {
                    'status': 'success',
                    'page_path': result['path'],
                    'action': result['action'],
                    'message': f"Successfully created page at {result['path']}"
                }
            else:
                raise Exception(f"Failed to integrate page: {result.get('error', 'Unknown error')}")
        else:
            raise Exception("Failed to generate page code")
    
    def _create_form(self, description: str, feature_id: str) -> Dict[str, Any]:
        """Create a form component"""
        print(f"{self.name}: Creating form for: {description}")
        
        # Forms often need validation and state management
        project_info = self.project_analyzer.get_project_structure()
        form_examples = self.project_analyzer.find_files_by_pattern('**/*[Ff]orm*.tsx')
        
        strategy = self.get_integration_strategy(description, 'form')
        
        prompt = self._build_form_prompt(description, form_examples, project_info)
        form_code = self._generate_response(prompt, max_tokens=3000)
        
        if form_code:
            result = self.integrate_generated_content(form_code, strategy)
            
            if result['success']:
                self._components_created += 1
                
                return {
                    'status': 'success',
                    'form_path': result['path'],
                    'action': result['action'],
                    'message': f"Successfully created form at {result['path']}"
                }
            else:
                raise Exception(f"Failed to integrate form: {result.get('error', 'Unknown error')}")
        else:
            raise Exception("Failed to generate form code")
    
    def _update_component(self, description: str, feature_id: str) -> Dict[str, Any]:
        """Update an existing component"""
        print(f"{self.name}: Updating component for: {description}")
        
        # Find the component to update
        target_file = self._find_target_file(description)
        
        if not target_file:
            raise Exception("Could not find target file to update")
        
        # Read existing content
        with open(target_file, 'r') as f:
            existing_content = f.read()
        
        # Generate update prompt
        prompt = f"""
        Update the following React component based on this requirement: {description}
        
        Current component code:
        ```tsx
        {existing_content}
        ```
        
        Provide the complete updated component code that fulfills the requirement.
        Maintain the existing code style and structure.
        """
        
        updated_code = self._generate_response(prompt, max_tokens=3000)
        
        if updated_code:
            # Write updated content
            with open(target_file, 'w') as f:
                f.write(updated_code)
            
            self._components_modified += 1
            
            return {
                'status': 'success',
                'updated_file': target_file,
                'message': f"Successfully updated {target_file}"
            }
        else:
            raise Exception("Failed to generate updated code")
    
    def _handle_generic_task(self, description: str, feature_id: str) -> Dict[str, Any]:
        """Handle generic frontend tasks"""
        print(f"{self.name}: Handling generic frontend task: {description}")
        
        # Analyze what needs to be done
        prompt = f"""
        As a frontend developer, analyze this task: {description}
        
        Determine:
        1. What type of frontend work is needed
        2. Which files need to be created or modified
        3. The appropriate approach
        
        Provide a brief action plan.
        """
        
        analysis = self._generate_response(prompt, max_tokens=500)
        
        # For now, return the analysis
        # In a real implementation, this would execute the plan
        return {
            'status': 'success',
            'analysis': analysis,
            'message': "Task analyzed and plan created"
        }
    
    def _build_component_prompt(self, description: str, existing_components: list, project_info: dict) -> str:
        """Build prompt for component generation"""
        components_list = "\n".join(existing_components[:5])  # Show first 5 as examples
        
        return f"""
        Create a React component based on this requirement: {description}
        
        Project context:
        - Framework: {project_info.get('framework', 'Next.js')}
        - Using TypeScript and Tailwind CSS
        - Existing components for reference:
        {components_list}
        
        Generate a complete, production-ready React component that:
        1. Uses TypeScript with proper typing
        2. Follows React best practices and hooks
        3. Implements responsive design with Tailwind CSS
        4. Includes proper error handling
        5. Is accessible (ARIA attributes where needed)
        
        Provide only the component code, no explanations.
        """
    
    def _build_page_prompt(self, description: str, existing_pages: list, project_info: dict) -> str:
        """Build prompt for page generation"""
        pages_list = "\n".join(existing_pages[:3])
        
        return f"""
        Create a Next.js page component based on this requirement: {description}
        
        Project context:
        - Using Next.js App Router
        - TypeScript and Tailwind CSS
        - Existing pages for reference:
        {pages_list}
        
        Generate a complete page component that:
        1. Uses proper Next.js 13+ conventions
        2. Implements server components where appropriate
        3. Handles loading and error states
        4. Is responsive and accessible
        5. Follows the project's layout structure
        
        Provide only the page component code.
        """
    
    def _build_form_prompt(self, description: str, form_examples: list, project_info: dict) -> str:
        """Build prompt for form generation"""
        examples_list = "\n".join(form_examples[:3])
        
        return f"""
        Create a form component based on this requirement: {description}
        
        Project context:
        - React with TypeScript
        - Form validation (using react-hook-form if available)
        - Tailwind CSS for styling
        - Example forms in project:
        {examples_list}
        
        Generate a complete form component that:
        1. Implements proper form validation
        2. Handles form submission with loading states
        3. Shows error messages clearly
        4. Is accessible with proper labels and ARIA
        5. Uses controlled components
        6. Follows the project's form patterns
        
        Provide only the form component code.
        """
    
    def _find_target_file(self, description: str) -> Optional[str]:
        """Find the target file to update based on description"""
        # Extract potential file names or component names from description
        matches = re.findall(r'(\w+(?:Component|Page|Form|Modal|Button))', description, re.I)
        
        if matches:
            for match in matches:
                # Search for files containing this name
                files = self.project_analyzer.find_files_by_pattern(f'**/*{match}*')
                if files:
                    return files[0]  # Return first match
        
        # Try to find based on keywords
        keywords = re.findall(r'\b(\w{4,})\b', description.lower())
        for keyword in keywords:
            files = self.project_analyzer.find_files_by_pattern(f'**/*{keyword}*.tsx')
            if files:
                return files[0]
        
        return None


if __name__ == "__main__":
    # Example usage
    agent = EventDrivenFrontendAgent()
    agent.run()