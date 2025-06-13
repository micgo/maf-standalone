"""
Event-Driven DevOps Agent

This agent handles DevOps tasks including deployment configurations, CI/CD pipelines,
containerization, and infrastructure setup in an event-driven manner.
"""

import os
import json
import time
from typing import Dict, Any

from .event_driven_base_agent import EventDrivenBaseAgent
from ..core.event_bus_interface import Event, EventType
from ..core.project_analyzer import ProjectAnalyzer
from ..core.file_integrator import FileIntegrator


class EventDrivenDevOpsAgent(EventDrivenBaseAgent):
    """
    Event-driven DevOps agent that handles deployment, CI/CD, and infrastructure tasks
    """
    
    def __init__(self, model_provider="gemini", model_name="gemini-1.5-flash", project_config=None):
        super().__init__("devops_agent", model_provider, model_name, project_config)
        
        # Initialize integration components
        self.project_analyzer = ProjectAnalyzer(self.project_root)
        self.file_integrator = FileIntegrator(self.project_root)
        
        # Configuration scan roots
        self.config_scan_roots = [
            self.project_root,  # For package.json, configs
            os.path.join(self.project_root, '.github', 'workflows'),  # GitHub Actions
            os.path.join(self.project_root, 'docker'),  # Docker configs
            os.path.join(self.project_root, '.circleci'),  # CircleCI
            os.path.join(self.project_root, 'k8s'),  # Kubernetes
        ]
        
        print(f"EventDrivenDevOpsAgent initialized with intelligent integration system.")
    
    def process_task(self, task_id: str, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a DevOps task
        """
        description = task_data.get('description', '')
        feature_id = task_data.get('feature_id')
        
        print(f"DevOps Agent processing task: {description[:50]}...")
        
        try:
            # Analyze task to determine DevOps context
            context = self._analyze_devops_context(description)
            
            # Generate DevOps configuration/scripts
            generated_content, target_file = self._generate_devops_content(description, context)
            
            if generated_content and generated_content.strip():
                # Integrate into project
                result = self._integrate_devops_content(generated_content, target_file, context)
                
                if result['success']:
                    return {
                        'success': True,
                        'output': generated_content,
                        'file_path': result['path'],
                        'action': result['action'],
                        'message': f"Successfully {result['action']} DevOps config: {result['path']}"
                    }
                else:
                    return {
                        'success': False,
                        'error': result['error'],
                        'message': f"Failed to integrate DevOps config: {result['error']}"
                    }
            else:
                return {
                    'success': False,
                    'error': 'No content generated',
                    'message': 'Failed to generate DevOps configuration'
                }
                
        except Exception as e:
            print(f"DevOps Agent error: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'error': str(e),
                'message': f'Error in DevOps task: {str(e)}'
            }
    
    def _analyze_devops_context(self, task_description: str) -> Dict[str, Any]:
        """Analyze the task to determine DevOps context"""
        context = {
            'type': 'general',
            'technology': [],
            'is_modification': False,
            'target_platform': None
        }
        
        # Determine DevOps task type
        task_lower = task_description.lower()
        
        if any(word in task_lower for word in ['docker', 'container', 'dockerfile']):
            context['type'] = 'containerization'
            context['technology'].append('docker')
        elif any(word in task_lower for word in ['github action', 'ci/cd', 'pipeline', 'workflow']):
            context['type'] = 'ci_cd'
            context['technology'].append('github_actions')
        elif any(word in task_lower for word in ['kubernetes', 'k8s', 'helm']):
            context['type'] = 'orchestration'
            context['technology'].append('kubernetes')
        elif any(word in task_lower for word in ['vercel', 'netlify', 'deploy']):
            context['type'] = 'deployment'
        elif any(word in task_lower for word in ['terraform', 'infrastructure']):
            context['type'] = 'infrastructure'
            context['technology'].append('terraform')
        elif any(word in task_lower for word in ['nginx', 'apache', 'server']):
            context['type'] = 'server_config'
        elif any(word in task_lower for word in ['monitor', 'logging', 'observability']):
            context['type'] = 'monitoring'
        
        # Check if modifying existing config
        context['is_modification'] = any(word in task_lower 
                                       for word in ['modify', 'update', 'change', 'add to existing'])
        
        # Detect target platform
        if 'vercel' in task_lower:
            context['target_platform'] = 'vercel'
        elif 'aws' in task_lower:
            context['target_platform'] = 'aws'
        elif 'gcp' in task_lower or 'google cloud' in task_lower:
            context['target_platform'] = 'gcp'
        elif 'azure' in task_lower:
            context['target_platform'] = 'azure'
        
        return context
    
    def _generate_devops_content(self, task_description: str, context: Dict[str, Any]) -> tuple:
        """Generate DevOps configuration using the LLM"""
        # Build context-aware prompt
        prompt = self._build_devops_prompt(task_description, context)
        
        print(f"DevOps Agent: Generating {context['type']} configuration...")
        generated_content = self._generate_response(prompt)
        
        # Determine target file based on content and context
        target_file = self._determine_target_file(generated_content, context)
        
        return generated_content, target_file
    
    def _build_devops_prompt(self, task_description: str, context: Dict[str, Any]) -> str:
        """Build a context-aware prompt for DevOps content generation"""
        project_type = 'unknown'
        if self.project_config:
            try:
                project_type = self.project_config._detect_project_type()
            except:
                pass
        
        # Get existing configuration context
        existing_configs = self._gather_existing_configs(context)
        
        prompt = f"""You are a DevOps engineer creating {context['type']} configuration for a {project_type} project.

Task: {task_description}

Project Type: {project_type}
DevOps Context: {context['type']}
Technologies: {', '.join(context['technology'])}

Existing configurations found:
{existing_configs}

Generate appropriate DevOps configuration that:
1. Follows best practices for {context['type']}
2. Is production-ready and secure
3. Includes proper error handling and logging
4. Has clear comments explaining key sections
5. Is optimized for the target platform: {context.get('target_platform', 'general')}

For Docker: Include multi-stage builds, security scanning, and optimization
For CI/CD: Include testing, building, security checks, and deployment stages
For Kubernetes: Include resource limits, health checks, and scaling policies
For Infrastructure: Include proper tagging and security groups

Return ONLY the configuration code/script, no explanations.
"""
        
        if context['is_modification']:
            prompt += "\nThis is a modification to existing configuration. Ensure compatibility."
        
        return prompt
    
    def _gather_existing_configs(self, context: Dict[str, Any]) -> str:
        """Gather existing configuration files for context"""
        configs = []
        
        # Look for relevant existing configs
        for root in self.config_scan_roots:
            if not os.path.exists(root):
                continue
                
            if context['type'] == 'containerization':
                # Look for Dockerfiles
                dockerfile = os.path.join(root, 'Dockerfile')
                if os.path.exists(dockerfile):
                    configs.append(f"Found existing Dockerfile at {dockerfile}")
                    
            elif context['type'] == 'ci_cd':
                # Look for CI/CD configs
                if 'workflows' in root:
                    for file in os.listdir(root) if os.path.exists(root) else []:
                        if file.endswith('.yml') or file.endswith('.yaml'):
                            configs.append(f"Found workflow: {file}")
        
        return '\n'.join(configs) if configs else "No existing configurations found."
    
    def _determine_target_file(self, content: str, context: Dict[str, Any]) -> str:
        """Determine the target file name based on content and context"""
        # Try to extract filename from content
        if content and '# File:' in content:
            lines = content.split('\n')
            for line in lines:
                if line.strip().startswith('# File:'):
                    return line.replace('# File:', '').strip()
        
        # Generate filename based on context
        if context['type'] == 'containerization':
            return 'Dockerfile'
        elif context['type'] == 'ci_cd':
            if 'github_actions' in context['technology']:
                return '.github/workflows/deploy.yml'
            elif 'gitlab' in context['technology']:
                return '.gitlab-ci.yml'
            else:
                return 'ci-cd-pipeline.yml'
        elif context['type'] == 'orchestration':
            return 'k8s/deployment.yaml'
        elif context['type'] == 'deployment':
            if context.get('target_platform') == 'vercel':
                return 'vercel.json'
            else:
                return 'deploy.config.json'
        elif context['type'] == 'infrastructure':
            return 'infrastructure/main.tf'
        elif context['type'] == 'server_config':
            return 'nginx.conf'
        elif context['type'] == 'monitoring':
            return 'monitoring/prometheus.yml'
        else:
            return f"devops-config-{int(time.time())}.yml"
    
    def _integrate_devops_content(self, content: str, target_file: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Integrate DevOps content into the project"""
        # Use the intelligent integration system
        strategy = self.get_integration_strategy(
            f"{context['type']} configuration", 
            'config'
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
        agent = EventDrivenDevOpsAgent()
        print(f"EventDrivenDevOpsAgent initialized: {agent.name}")