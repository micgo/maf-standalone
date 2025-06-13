"""
Event-Driven QA Agent

This agent handles test generation and quality assurance tasks in an event-driven manner.
It generates unit, integration, and end-to-end tests for applications.
"""

import os
import json
import time
import uuid
from typing import Dict, Any

from .event_driven_base_agent import EventDrivenBaseAgent
from ..core.event_bus_interface import Event, EventType
from ..core.project_analyzer import ProjectAnalyzer
from ..core.file_integrator import FileIntegrator


class EventDrivenQAAgent(EventDrivenBaseAgent):
    """
    Event-driven QA agent that generates tests and performs quality assurance tasks
    """
    
    def __init__(self, model_provider="gemini", model_name="gemini-1.5-flash", project_config=None):
        super().__init__("qa_agent", model_provider, model_name, project_config)
        
        # Initialize integration components
        self.project_analyzer = ProjectAnalyzer(self.project_root)
        self.file_integrator = FileIntegrator(self.project_root)
        
        # Test output directories based on project type
        self._setup_test_directories()
        
        print(f"EventDrivenQAAgent initialized with intelligent integration system.")
    
    def _setup_test_directories(self):
        """Setup test directories based on project type"""
        project_type = self.project_config._detect_project_type() if self.project_config else 'unknown'
        
        if project_type in ['nextjs', 'react']:
            # For Next.js/React, tests go next to components or in __tests__ directories
            self.app_code_scan_root = os.path.join(self.project_root, "app")
            self.components_scan_root = os.path.join(self.project_root, "components")
            self.tests_output_root = os.path.join(self.project_root, "__tests__")
        elif project_type == 'django':
            # For Django, tests go in app directories
            self.tests_output_root = self.project_root
        else:
            # Default test directory
            self.tests_output_root = os.path.join(self.project_root, "tests")
    
    def process_task(self, task_id: str, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a QA task - generate tests based on the task description
        """
        description = task_data.get('description', '')
        feature_id = task_data.get('feature_id')
        
        print(f"QA Agent processing task: {description[:50]}...")
        
        try:
            # Analyze what needs to be tested
            test_context = self._analyze_test_context(description)
            
            # Generate tests
            generated_tests, target_file = self._generate_tests(description, test_context)
            
            if generated_tests and generated_tests.strip():
                # Integrate tests into project
                result = self._integrate_tests(generated_tests, target_file, test_context)
                
                if result['success']:
                    return {
                        'success': True,
                        'output': generated_tests,
                        'file_path': result['path'],
                        'action': result['action'],
                        'message': f"Successfully {result['action']} test: {result['path']}"
                    }
                else:
                    return {
                        'success': False,
                        'error': result['error'],
                        'message': f"Failed to integrate test: {result['error']}"
                    }
            else:
                return {
                    'success': False,
                    'error': 'No tests generated',
                    'message': 'Failed to generate tests - LLM response was empty'
                }
                
        except Exception as e:
            print(f"QA Agent error: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'error': str(e),
                'message': f'Error generating tests: {str(e)}'
            }
    
    def _analyze_test_context(self, task_description: str) -> Dict[str, Any]:
        """Analyze the task to determine test context"""
        context = {
            'test_type': 'unit',  # default
            'is_modification': False,
            'component_to_test': None,
            'existing_tests': []
        }
        
        # Determine test type
        if any(word in task_description.lower() for word in ['integration', 'api', 'endpoint']):
            context['test_type'] = 'integration'
        elif any(word in task_description.lower() for word in ['e2e', 'end-to-end', 'ui test', 'user flow']):
            context['test_type'] = 'e2e'
        
        # Check if modifying existing tests
        context['is_modification'] = any(word in task_description.lower() 
                                       for word in ['modify', 'update', 'refactor', 'add to existing', 'change'])
        
        # Extract component name if mentioned
        # This is a simple heuristic - could be improved with better NLP
        words = task_description.split()
        for i, word in enumerate(words):
            if word.lower() in ['component', 'page', 'function', 'class', 'module']:
                if i > 0:
                    context['component_to_test'] = words[i-1]
                elif i < len(words) - 1:
                    context['component_to_test'] = words[i+1]
        
        return context
    
    def _generate_tests(self, task_description: str, context: Dict[str, Any]) -> tuple:
        """Generate tests using the LLM"""
        # Build context for test generation
        existing_code_context = self._gather_existing_code_context(context)
        
        prompt = self._build_test_generation_prompt(task_description, context, existing_code_context)
        
        # Generate tests
        print(f"QA Agent: Requesting LLM to generate {context['test_type']} tests...")
        generated_content = self._generate_response(prompt)
        
        # Extract target file from response or determine it
        target_file = self._determine_target_test_file(generated_content, context)
        
        return generated_content, target_file
    
    def _gather_existing_code_context(self, context: Dict[str, Any]) -> str:
        """Gather relevant existing code for context"""
        code_context = []
        
        # If we know what component to test, try to find it
        if context['component_to_test']:
            # Use the project analyzer to find related files
            existing_files = self.project_analyzer.find_existing_files('component')
            
            # Look for files that might contain our component
            component_name = context['component_to_test'].lower()
            for file_path in existing_files.get('component', []):
                if component_name in os.path.basename(file_path).lower():
                    try:
                        with open(file_path, 'r') as f:
                            content = f.read()
                            code_context.append(f"// File: {file_path}\n{content}\n")
                            if len(code_context) >= 3:  # Limit to 3 files
                                break
                    except:
                        pass
        
        return '\n'.join(code_context) if code_context else "No specific component code found."
    
    def _build_test_generation_prompt(self, task_description: str, context: Dict[str, Any], existing_code: str) -> str:
        """Build the prompt for test generation"""
        project_type = self.project_config._detect_project_type() if self.project_config else 'react'
        
        test_framework_map = {
            'nextjs': 'Jest with React Testing Library',
            'react': 'Jest with React Testing Library',
            'django': 'Django TestCase',
            'fastapi': 'pytest with FastAPI test client'
        }
        
        test_framework = test_framework_map.get(project_type, 'Jest')
        
        prompt = f"""You are a QA engineer generating {context['test_type']} tests for a {project_type} application.

Task: {task_description}

Testing Framework: {test_framework}
Test Type: {context['test_type']}

Relevant existing code:
{existing_code}

Generate comprehensive tests that:
1. Cover the main functionality described in the task
2. Include both positive and negative test cases
3. Follow best practices for {test_framework}
4. Are well-commented and easy to understand
5. Include proper setup and teardown if needed

For React/Next.js components:
- Test rendering, user interactions, and state changes
- Use data-testid attributes for reliable element selection
- Mock external dependencies appropriately

For API/Backend:
- Test different HTTP methods and status codes
- Validate request/response schemas
- Test error handling and edge cases

Return ONLY the test code, no explanations.
Start with appropriate imports and end with complete test suites.
"""
        
        if context['is_modification']:
            prompt += "\nThis is a modification to existing tests. Ensure compatibility with existing test structure."
        
        return prompt
    
    def _determine_target_test_file(self, generated_content: str, context: Dict[str, Any]) -> str:
        """Determine where to place the generated test file"""
        # Try to extract filename from generated content
        if generated_content and '// File:' in generated_content:
            lines = generated_content.split('\n')
            for line in lines:
                if line.strip().startswith('// File:'):
                    suggested_file = line.replace('// File:', '').strip()
                    if suggested_file:
                        return suggested_file
        
        # Generate filename based on context
        if context['component_to_test']:
            base_name = context['component_to_test']
        else:
            base_name = f"test_{int(time.time())}"
        
        # Add appropriate extension
        if context['test_type'] == 'e2e':
            return f"{base_name}.e2e.test.tsx"
        elif context['test_type'] == 'integration':
            return f"{base_name}.integration.test.tsx"
        else:
            return f"{base_name}.test.tsx"
    
    def _integrate_tests(self, generated_tests: str, target_file: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Integrate generated tests into the project"""
        # Use the intelligent integration system
        strategy = self.get_integration_strategy(f"test for {context.get('component_to_test', 'component')}", 'test')
        
        # For tests, we want to place them next to components or in test directories
        if context['component_to_test'] and strategy['mode'] == 'create':
            # Try to find the component and place test next to it
            existing_files = self.project_analyzer.find_existing_files('component')
            component_name = context['component_to_test'].lower()
            component_files = []
            
            for file_path in existing_files.get('component', []):
                if component_name in os.path.basename(file_path).lower():
                    component_files.append(file_path)
            
            if component_files:
                # Place test in same directory as component
                component_dir = os.path.dirname(component_files[0])
                target_path = os.path.join(component_dir, target_file)
                strategy['target_dir'] = component_dir
            else:
                # Fall back to test directory
                target_path = os.path.join(self.tests_output_root, target_file)
                strategy['target_dir'] = self.tests_output_root
        else:
            target_path = os.path.join(strategy.get('target_dir', self.tests_output_root), target_file)
        
        # Integrate the content
        result = self.integrate_generated_content(generated_tests, strategy)
        
        return result
    
    def _generate_test_filename_from_content(self, content: str) -> str:
        """Extract or generate an appropriate test filename"""
        # Look for component name in imports or test descriptions
        lines = content.split('\n')
        for line in lines:
            if 'import' in line and 'from' in line:
                # Try to extract component name from import
                parts = line.split('from')
                if len(parts) > 1:
                    path = parts[1].strip().strip('"\'')
                    if '/' in path:
                        component = path.split('/')[-1].replace('.tsx', '').replace('.ts', '')
                        return f"{component}.test.tsx"
        
        # Default fallback
        return f"test_{int(time.time())}.test.tsx"