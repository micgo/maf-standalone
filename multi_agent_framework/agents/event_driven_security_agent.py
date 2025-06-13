"""
Event-Driven Security Agent

This agent handles security auditing, vulnerability detection, and security best
practices implementation in an event-driven manner.
"""

import os
import json
import time
from typing import Dict, Any

from .event_driven_base_agent import EventDrivenBaseAgent
from ..core.event_bus_interface import Event, EventType
from ..core.project_analyzer import ProjectAnalyzer
from ..core.file_integrator import FileIntegrator


class EventDrivenSecurityAgent(EventDrivenBaseAgent):
    """
    Event-driven Security agent that audits code for vulnerabilities and implements security best practices
    """
    
    def __init__(self, model_provider="gemini", model_name="gemini-1.5-flash", project_config=None):
        super().__init__("security_agent", model_provider, model_name, project_config)
        
        # Initialize integration components
        self.project_analyzer = ProjectAnalyzer(self.project_root)
        self.file_integrator = FileIntegrator(self.project_root)
        
        # Security scan patterns
        self.security_patterns = {
            'authentication': ['auth', 'login', 'session', 'password', 'token', 'jwt'],
            'authorization': ['role', 'permission', 'access', 'policy', 'rbac'],
            'data_protection': ['encrypt', 'hash', 'sanitize', 'validate', 'escape'],
            'api_security': ['cors', 'rate_limit', 'api_key', 'oauth', 'csrf'],
            'vulnerability': ['sql_injection', 'xss', 'csrf', 'command_injection', 'path_traversal']
        }
        
        print(f"EventDrivenSecurityAgent initialized with security scanning capabilities.")
    
    def process_task(self, task_id: str, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a security task
        """
        description = task_data.get('description', '')
        feature_id = task_data.get('feature_id')
        
        print(f"Security Agent processing task: {description[:50]}...")
        
        try:
            # Analyze task to determine security context
            context = self._analyze_security_context(description)
            
            # Perform security analysis or generate security implementations
            security_content, target_file = self._perform_security_analysis(description, context)
            
            if security_content and security_content.strip():
                # Integrate security findings/implementations
                result = self._integrate_security_content(security_content, target_file, context)
                
                if result['success']:
                    return {
                        'success': True,
                        'output': security_content,
                        'file_path': result['path'],
                        'action': result['action'],
                        'message': f"Successfully {result['action']} security {context['type']}: {result['path']}"
                    }
                else:
                    return {
                        'success': False,
                        'error': result['error'],
                        'message': f"Failed to integrate security content: {result['error']}"
                    }
            else:
                return {
                    'success': False,
                    'error': 'No content generated',
                    'message': 'Failed to generate security analysis or implementation'
                }
                
        except Exception as e:
            print(f"Security Agent error: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'error': str(e),
                'message': f'Error in security task: {str(e)}'
            }
    
    def _analyze_security_context(self, task_description: str) -> Dict[str, Any]:
        """Analyze the task to determine security context"""
        context = {
            'type': 'general_audit',
            'focus_areas': [],
            'is_audit': True,
            'is_implementation': False,
            'target_component': None
        }
        
        task_lower = task_description.lower()
        
        # Determine security task type
        if any(word in task_lower for word in ['audit', 'review', 'analyze', 'check', 'assess']):
            context['is_audit'] = True
            context['type'] = 'security_audit'
        elif any(word in task_lower for word in ['implement', 'add', 'create', 'secure']):
            context['is_implementation'] = True
            context['type'] = 'security_implementation'
            context['is_audit'] = False
        
        # Determine focus areas
        for area, keywords in self.security_patterns.items():
            if any(keyword in task_lower for keyword in keywords):
                context['focus_areas'].append(area)
        
        # Detect specific components
        if 'authentication' in task_lower or 'auth' in task_lower:
            context['target_component'] = 'authentication'
        elif 'api' in task_lower:
            context['target_component'] = 'api'
        elif 'database' in task_lower or 'sql' in task_lower:
            context['target_component'] = 'database'
        elif 'frontend' in task_lower or 'ui' in task_lower:
            context['target_component'] = 'frontend'
        
        return context
    
    def _perform_security_analysis(self, task_description: str, context: Dict[str, Any]) -> tuple:
        """Perform security analysis or generate security implementation"""
        # Build appropriate prompt based on context
        prompt = self._build_security_prompt(task_description, context)
        
        print(f"Security Agent: Performing {context['type']}...")
        generated_content = self._generate_response(prompt)
        
        # Determine target file based on content and context
        target_file = self._determine_target_file(generated_content, context)
        
        return generated_content, target_file
    
    def _build_security_prompt(self, task_description: str, context: Dict[str, Any]) -> str:
        """Build a context-aware prompt for security analysis"""
        # Get project type if available
        project_type = 'unknown'
        if self.project_config:
            try:
                project_type = self.project_config._detect_project_type()
            except:
                pass
        
        # Get existing code context
        existing_code = self._gather_security_context(context)
        
        if context['is_audit']:
            prompt = f"""You are a security engineer performing a security audit for a {project_type} project.

Task: {task_description}

Focus Areas: {', '.join(context['focus_areas']) if context['focus_areas'] else 'General security'}
Target Component: {context.get('target_component', 'All components')}

Existing Code Context:
{existing_code}

Perform a thorough security analysis and provide:
1. Identified vulnerabilities or security issues
2. Risk assessment (Critical, High, Medium, Low)
3. Specific code examples of issues found
4. Remediation recommendations with code examples
5. Best practices to follow

Format your response as a structured security report with clear sections.
"""
        else:
            prompt = f"""You are a security engineer implementing security features for a {project_type} project.

Task: {task_description}

Project Type: {project_type}
Security Context: {context['type']}
Focus Areas: {', '.join(context['focus_areas']) if context['focus_areas'] else 'General security'}

Existing Code Context:
{existing_code}

Generate secure implementation that:
1. Follows OWASP security best practices
2. Includes proper input validation and sanitization
3. Implements defense in depth
4. Has clear security-focused comments
5. Uses established security libraries when appropriate

Return ONLY the implementation code, no explanations.
"""
        
        return prompt
    
    def _gather_security_context(self, context: Dict[str, Any]) -> str:
        """Gather relevant code for security analysis"""
        # This is a simplified version - in production, would scan for security-relevant files
        relevant_files = []
        
        # Look for authentication files
        auth_patterns = ['auth', 'login', 'session', 'security']
        config_patterns = ['config', 'settings', 'env']
        
        # Scan for relevant files (simplified)
        if os.path.exists(self.project_root):
            for root, dirs, files in os.walk(self.project_root):
                # Skip node_modules and other non-source directories
                if any(skip in root for skip in ['node_modules', '.git', 'dist', 'build']):
                    continue
                    
                for file in files:
                    file_lower = file.lower()
                    if any(pattern in file_lower for pattern in auth_patterns + config_patterns):
                        relevant_files.append(os.path.join(root, file))
        
        # Return a summary (in production, would read and analyze files)
        if relevant_files:
            return f"Found {len(relevant_files)} security-relevant files in the project."
        else:
            return "No existing security-specific files found."
    
    def _determine_target_file(self, content: str, context: Dict[str, Any]) -> str:
        """Determine the target file name based on content and context"""
        # Try to extract filename from content
        if content and '# File:' in content:
            lines = content.split('\n')
            for line in lines:
                if line.strip().startswith('# File:'):
                    return line.replace('# File:', '').strip()
        
        # Generate filename based on context
        if context['is_audit']:
            return f"security/audit-report-{int(time.time())}.md"
        elif context['type'] == 'security_implementation':
            if context.get('target_component') == 'authentication':
                return 'src/security/auth-security.ts'
            elif context.get('target_component') == 'api':
                return 'src/middleware/security.ts'
            else:
                return f"src/security/security-implementation-{int(time.time())}.ts"
        else:
            return f"security/security-analysis-{int(time.time())}.md"
    
    def _integrate_security_content(self, content: str, target_file: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Integrate security content into the project"""
        # Use the intelligent integration system
        content_type = 'documentation' if context['is_audit'] else 'middleware'
        strategy = self.get_integration_strategy(
            f"{context['type']}", 
            content_type
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
        agent = EventDrivenSecurityAgent()
        print(f"EventDrivenSecurityAgent initialized: {agent.name}")