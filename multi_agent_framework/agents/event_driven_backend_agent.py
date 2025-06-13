"""
Event-Driven Backend Agent

This is the event-driven version of the backend agent that handles
API development tasks using events instead of polling.
"""

import os
import json
import re
from typing import Dict, Any, Optional, List

from .event_driven_base_agent import EventDrivenBaseAgent
from ..core.event_bus_interface import Event, EventType
from ..core.naming_conventions import NamingConventions


class EventDrivenBackendAgent(EventDrivenBaseAgent):
    """
    Event-driven backend agent for handling API and server-side development tasks
    """
    
    def __init__(self, model_provider="gemini", model_name="gemini-2.0-flash", project_config=None):
        super().__init__("backend_agent", model_provider, model_name, project_config)
        
        # Root for scanning existing backend utility code
        self.lib_scan_root = os.path.abspath(os.path.join(self.project_root, 'lib'))
        
        # Track API endpoints created
        self._apis_created = 0
        self._apis_modified = 0
        
        print(f"EventDrivenBackendAgent initialized with intelligent integration system.")
    
    def _subscribe_to_events(self):
        """Subscribe to backend-specific events"""
        super()._subscribe_to_events()
        
        # Subscribe to task retry events
        self.event_bus.subscribe(EventType.TASK_RETRY, self._handle_task_retry)
        
        # Subscribe to custom backend events
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
        """Handle custom backend events"""
        event_name = event.data.get('event_name', '')
        
        if event_name == 'api_validation_request':
            # Handle API validation requests
            api_path = event.data.get('api_path')
            print(f"{self.name}: Received API validation request for {api_path}")
            # Could trigger automatic validation or testing
        
        elif event_name == 'database_schema_updated':
            # Handle database schema updates
            print(f"{self.name}: Database schema updated, may need to update API endpoints")
            # Could trigger API regeneration or validation
    
    def process_task(self, task_id: str, task_data: Dict[str, Any]) -> Any:
        """
        Process backend development tasks
        
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
            
            if task_type == "api_route":
                result = self._create_api_route(description, feature_id)
            elif task_type == "service":
                result = self._create_service(description, feature_id)
            elif task_type == "middleware":
                result = self._create_middleware(description, feature_id)
            elif task_type == "integration":
                result = self._create_integration(description, feature_id)
            elif task_type == "update":
                result = self._update_backend_code(description, feature_id)
            else:
                result = self._handle_generic_task(description, feature_id)
            
            # Emit completion metrics
            self.emit_custom_event('backend_metrics', {
                'apis_created': self._apis_created,
                'apis_modified': self._apis_modified,
                'task_type': task_type
            })
            
            return result
            
        except Exception as e:
            error_msg = f"Error processing backend task: {str(e)}"
            print(f"{self.name}: {error_msg}")
            
            # Emit error event for monitoring
            self.emit_custom_event('backend_error', {
                'task_id': task_id,
                'error': str(e),
                'task_type': task_type if 'task_type' in locals() else 'unknown'
            })
            
            raise
    
    def _analyze_task_type(self, description: str) -> str:
        """Analyze task description to determine type"""
        description_lower = description.lower()
        
        if any(word in description_lower for word in ['api', 'endpoint', 'route', 'rest']):
            return "api_route"
        elif any(word in description_lower for word in ['service', 'business logic', 'handler']):
            return "service"
        elif any(word in description_lower for word in ['middleware', 'auth', 'validation']):
            return "middleware"
        elif any(word in description_lower for word in ['integration', 'third-party', 'external']):
            return "integration"
        elif any(word in description_lower for word in ['update', 'modify', 'change', 'fix']):
            return "update"
        else:
            return "generic"
    
    def _create_api_route(self, description: str, feature_id: str) -> Dict[str, Any]:
        """Create a new API route"""
        print(f"{self.name}: Creating API route for: {description}")
        
        # Analyze existing project structure
        project_info = self.project_analyzer.get_project_structure()
        existing_apis = self.project_analyzer.find_files_by_pattern('app/api/**/route.ts')
        lib_files = self._scan_lib_directory()
        
        # Determine integration strategy
        strategy = self.get_integration_strategy(description, 'api')
        
        # Generate API route prompt
        prompt = self._build_api_route_prompt(description, existing_apis, lib_files, project_info)
        
        # Generate API code
        api_code = self._generate_response(prompt, max_tokens=2500)
        
        if api_code:
            # Integrate the API route
            result = self.integrate_generated_content(api_code, strategy)
            
            if result['success']:
                self._apis_created += 1
                
                # Check if we need to create a service layer
                if self._should_create_service_layer(description):
                    service_result = self._create_service_for_api(description, api_code)
                    
                    if service_result['success']:
                        result['service_path'] = service_result['path']
                
                # Emit API created event
                self.emit_custom_event('api_created', {
                    'path': result['path'],
                    'feature_id': feature_id,
                    'has_service': 'service_path' in result
                })
                
                return {
                    'status': 'success',
                    'api_path': result['path'],
                    'service_path': result.get('service_path'),
                    'action': result['action'],
                    'message': f"Successfully created API route at {result['path']}"
                }
            else:
                raise Exception(f"Failed to integrate API route: {result.get('error', 'Unknown error')}")
        else:
            raise Exception("Failed to generate API route code")
    
    def _create_service(self, description: str, feature_id: str) -> Dict[str, Any]:
        """Create a service layer component"""
        print(f"{self.name}: Creating service for: {description}")
        
        # Find existing services
        existing_services = self.project_analyzer.find_files_by_pattern('lib/services/**/*.ts')
        
        strategy = self.get_integration_strategy(description, 'service')
        
        prompt = self._build_service_prompt(description, existing_services)
        service_code = self._generate_response(prompt, max_tokens=2000)
        
        if service_code:
            result = self.integrate_generated_content(service_code, strategy)
            
            if result['success']:
                return {
                    'status': 'success',
                    'service_path': result['path'],
                    'action': result['action'],
                    'message': f"Successfully created service at {result['path']}"
                }
            else:
                raise Exception(f"Failed to integrate service: {result.get('error', 'Unknown error')}")
        else:
            raise Exception("Failed to generate service code")
    
    def _create_middleware(self, description: str, feature_id: str) -> Dict[str, Any]:
        """Create middleware component"""
        print(f"{self.name}: Creating middleware for: {description}")
        
        existing_middleware = self.project_analyzer.find_files_by_pattern('middleware/**/*.ts')
        
        strategy = self.get_integration_strategy(description, 'middleware')
        
        prompt = self._build_middleware_prompt(description, existing_middleware)
        middleware_code = self._generate_response(prompt, max_tokens=1500)
        
        if middleware_code:
            result = self.integrate_generated_content(middleware_code, strategy)
            
            if result['success']:
                return {
                    'status': 'success',
                    'middleware_path': result['path'],
                    'action': result['action'],
                    'message': f"Successfully created middleware at {result['path']}"
                }
            else:
                raise Exception(f"Failed to integrate middleware: {result.get('error', 'Unknown error')}")
        else:
            raise Exception("Failed to generate middleware code")
    
    def _create_integration(self, description: str, feature_id: str) -> Dict[str, Any]:
        """Create third-party integration"""
        print(f"{self.name}: Creating integration for: {description}")
        
        # Similar to service but for external integrations
        existing_integrations = self.project_analyzer.find_files_by_pattern('lib/integrations/**/*.ts')
        
        strategy = self.get_integration_strategy(description, 'integration')
        
        prompt = self._build_integration_prompt(description, existing_integrations)
        integration_code = self._generate_response(prompt, max_tokens=2000)
        
        if integration_code:
            result = self.integrate_generated_content(integration_code, strategy)
            
            if result['success']:
                return {
                    'status': 'success',
                    'integration_path': result['path'],
                    'action': result['action'],
                    'message': f"Successfully created integration at {result['path']}"
                }
            else:
                raise Exception(f"Failed to integrate: {result.get('error', 'Unknown error')}")
        else:
            raise Exception("Failed to generate integration code")
    
    def _update_backend_code(self, description: str, feature_id: str) -> Dict[str, Any]:
        """Update existing backend code"""
        print(f"{self.name}: Updating backend code for: {description}")
        
        # Find the target file to update
        target_file = self._find_target_file(description)
        
        if not target_file:
            raise Exception("Could not find target file to update")
        
        # Read existing content
        with open(target_file, 'r') as f:
            existing_content = f.read()
        
        # Generate update prompt
        prompt = f"""
        Update the following backend code based on this requirement: {description}
        
        Current code:
        ```typescript
        {existing_content}
        ```
        
        Provide the complete updated code that fulfills the requirement.
        Maintain the existing code style and patterns.
        Ensure all imports and exports are preserved.
        """
        
        updated_code = self._generate_response(prompt, max_tokens=3000)
        
        if updated_code:
            # Write updated content
            with open(target_file, 'w') as f:
                f.write(updated_code)
            
            self._apis_modified += 1
            
            return {
                'status': 'success',
                'updated_file': target_file,
                'message': f"Successfully updated {target_file}"
            }
        else:
            raise Exception("Failed to generate updated code")
    
    def _handle_generic_task(self, description: str, feature_id: str) -> Dict[str, Any]:
        """Handle generic backend tasks"""
        print(f"{self.name}: Handling generic backend task: {description}")
        
        # Analyze what needs to be done
        prompt = f"""
        As a backend developer, analyze this task: {description}
        
        Determine:
        1. What type of backend work is needed
        2. Which files need to be created or modified
        3. The appropriate approach for a Next.js/Supabase/Stripe stack
        
        Provide a brief action plan.
        """
        
        analysis = self._generate_response(prompt, max_tokens=500)
        
        return {
            'status': 'success',
            'analysis': analysis,
            'message': "Task analyzed and plan created"
        }
    
    def _scan_lib_directory(self) -> List[str]:
        """Scan the lib directory for utility files"""
        lib_files = []
        if os.path.exists(self.lib_scan_root):
            for root, dirs, files in os.walk(self.lib_scan_root):
                for file in files:
                    if file.endswith('.ts') or file.endswith('.js'):
                        lib_files.append(os.path.join(root, file))
        return lib_files
    
    def _should_create_service_layer(self, description: str) -> bool:
        """Determine if a service layer should be created"""
        # Check if the task involves complex business logic
        complex_keywords = ['business logic', 'validation', 'multiple', 'complex', 'service']
        return any(keyword in description.lower() for keyword in complex_keywords)
    
    def _create_service_for_api(self, description: str, api_code: str) -> Dict[str, Any]:
        """Create a service layer for an API route"""
        # Extract the main functionality from the API code
        service_prompt = f"""
        Based on this API route requirement: {description}
        
        And this API route code:
        ```typescript
        {api_code}
        ```
        
        Create a service layer that encapsulates the business logic.
        The service should:
        1. Be reusable across different API routes
        2. Handle data validation and transformation
        3. Interact with the database through Supabase
        4. Return typed responses
        
        Follow the existing service patterns in the project.
        """
        
        service_code = self._generate_response(service_prompt, max_tokens=2000)
        
        if service_code:
            # Determine where to place the service
            service_name = self._extract_service_name(description)
            service_path = f"lib/services/{service_name}.ts"
            
            strategy = {
                'mode': 'create',
                'target_dir': 'lib/services',
                'naming_convention': {'pattern': 'camelCase.ts'}
            }
            
            return self.integrate_generated_content(service_code, strategy, service_path)
        
        return {'success': False, 'error': 'Failed to generate service code'}
    
    def _build_api_route_prompt(self, description: str, existing_apis: list, 
                               lib_files: list, project_info: dict) -> str:
        """Build prompt for API route generation"""
        apis_list = "\n".join(existing_apis[:5])
        libs_list = "\n".join([os.path.basename(f) for f in lib_files[:10]])
        
        return f"""
        Create a Next.js 13+ API route based on this requirement: {description}
        
        Project context:
        - Using Next.js App Router with TypeScript
        - Database: Supabase
        - Payment: Stripe (if applicable)
        - Authentication: Supabase Auth
        
        Existing API routes for reference:
        {apis_list}
        
        Available utilities in lib/:
        {libs_list}
        
        Generate a complete API route that:
        1. Uses proper Next.js 13+ route handler syntax (export async function GET/POST/etc)
        2. Implements proper error handling and status codes
        3. Uses TypeScript with proper typing
        4. Integrates with Supabase for data operations
        5. Includes input validation
        6. Returns consistent JSON responses
        7. Uses existing utilities from lib/ when appropriate
        
        Provide only the route.ts file content, no explanations.
        """
    
    def _build_service_prompt(self, description: str, existing_services: list) -> str:
        """Build prompt for service generation"""
        services_list = "\n".join(existing_services[:5])
        
        return f"""
        Create a TypeScript service layer based on this requirement: {description}
        
        Project context:
        - TypeScript service in lib/services/
        - Database: Supabase client
        - Should be reusable across API routes
        
        Existing services for reference:
        {services_list}
        
        Generate a complete service module that:
        1. Exports typed functions for business operations
        2. Handles data validation and transformation
        3. Uses Supabase client for database operations
        4. Implements proper error handling
        5. Returns consistent typed responses
        6. Is testable and modular
        
        Provide only the service code, no explanations.
        """
    
    def _build_middleware_prompt(self, description: str, existing_middleware: list) -> str:
        """Build prompt for middleware generation"""
        middleware_list = "\n".join(existing_middleware[:3])
        
        return f"""
        Create a Next.js middleware based on this requirement: {description}
        
        Existing middleware for reference:
        {middleware_list}
        
        Generate middleware that:
        1. Uses Next.js middleware conventions
        2. Implements the required functionality
        3. Has proper TypeScript typing
        4. Handles errors gracefully
        5. Is performant and secure
        
        Provide only the middleware code.
        """
    
    def _build_integration_prompt(self, description: str, existing_integrations: list) -> str:
        """Build prompt for integration generation"""
        integrations_list = "\n".join(existing_integrations[:3])
        
        return f"""
        Create a third-party integration based on this requirement: {description}
        
        Existing integrations for reference:
        {integrations_list}
        
        Generate an integration module that:
        1. Provides a clean interface for the external service
        2. Handles authentication/API keys securely
        3. Implements retry logic and error handling
        4. Uses TypeScript for type safety
        5. Is configurable via environment variables
        6. Includes usage documentation in comments
        
        Provide only the integration code.
        """
    
    def _find_target_file(self, description: str) -> Optional[str]:
        """Find the target file to update based on description"""
        # Extract potential file paths or API routes from description
        path_patterns = [
            r'/api/([a-zA-Z0-9/_-]+)',
            r'route\.ts in ([a-zA-Z0-9/_-]+)',
            r'([a-zA-Z0-9/_-]+)\.ts'
        ]
        
        for pattern in path_patterns:
            matches = re.findall(pattern, description)
            if matches:
                for match in matches:
                    # Try to find the file
                    potential_paths = [
                        f"app/api/{match}/route.ts",
                        f"lib/services/{match}.ts",
                        f"lib/{match}.ts",
                        match if match.endswith('.ts') else f"{match}.ts"
                    ]
                    
                    for path in potential_paths:
                        full_path = os.path.join(self.project_root, path)
                        if os.path.exists(full_path):
                            return full_path
        
        return None
    
    def _extract_service_name(self, description: str) -> str:
        """Extract a service name from the description"""
        # Try to extract meaningful name
        words = re.findall(r'\b[A-Z][a-z]+|\b[a-z]+', description)
        
        # Look for key nouns
        for word in words:
            if word.lower() in ['user', 'auth', 'payment', 'order', 'product', 'cart', 
                               'subscription', 'notification', 'email', 'file', 'image']:
                return word.lower()
        
        # Fallback to generic name
        return 'service'


if __name__ == "__main__":
    agent = EventDrivenBackendAgent()
    agent.run()