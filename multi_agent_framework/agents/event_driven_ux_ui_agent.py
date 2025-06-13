"""
Event-Driven UX/UI Agent

This agent handles user interface design, user experience improvements, styling,
and design system implementation in an event-driven manner.
"""

import os
import json
import time
from typing import Dict, Any

from .event_driven_base_agent import EventDrivenBaseAgent
from ..core.event_bus_interface import Event, EventType
from ..core.project_analyzer import ProjectAnalyzer
from ..core.file_integrator import FileIntegrator


class EventDrivenUXUIAgent(EventDrivenBaseAgent):
    """
    Event-driven UX/UI agent that handles design systems, UI components, and user experience
    """
    
    def __init__(self, model_provider="gemini", model_name="gemini-1.5-flash", project_config=None):
        super().__init__("ux_ui_agent", model_provider, model_name, project_config)
        
        # Initialize integration components
        self.project_analyzer = ProjectAnalyzer(self.project_root)
        self.file_integrator = FileIntegrator(self.project_root)
        
        # Design system components
        self.design_components = {
            'color_system': ['palette', 'theme', 'colors', 'dark mode', 'light mode'],
            'typography': ['fonts', 'headings', 'text styles', 'font sizes'],
            'spacing': ['padding', 'margin', 'gap', 'spacing system'],
            'components': ['button', 'card', 'modal', 'form', 'navbar', 'footer'],
            'layout': ['grid', 'flex', 'container', 'responsive', 'breakpoints'],
            'animations': ['transitions', 'animations', 'hover effects', 'micro-interactions']
        }
        
        print(f"EventDrivenUXUIAgent initialized with design system capabilities.")
    
    def process_task(self, task_id: str, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a UX/UI task
        """
        description = task_data.get('description', '')
        feature_id = task_data.get('feature_id')
        
        print(f"UX/UI Agent processing task: {description[:50]}...")
        
        try:
            # Analyze task to determine UX/UI context
            context = self._analyze_ux_context(description)
            
            # Generate UX/UI content
            design_content, target_file = self._generate_design_content(description, context)
            
            if design_content and design_content.strip():
                # Integrate design content
                result = self._integrate_design_content(design_content, target_file, context)
                
                if result['success']:
                    return {
                        'success': True,
                        'output': design_content,
                        'file_path': result['path'],
                        'action': result['action'],
                        'message': f"Successfully {result['action']} {context['type']} design: {result['path']}"
                    }
                else:
                    return {
                        'success': False,
                        'error': result['error'],
                        'message': f"Failed to integrate design content: {result['error']}"
                    }
            else:
                return {
                    'success': False,
                    'error': 'No content generated',
                    'message': 'Failed to generate design content'
                }
                
        except Exception as e:
            print(f"UX/UI Agent error: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'error': str(e),
                'message': f'Error in UX/UI task: {str(e)}'
            }
    
    def _analyze_ux_context(self, task_description: str) -> Dict[str, Any]:
        """Analyze the task to determine UX/UI context"""
        context = {
            'type': 'general_design',
            'design_areas': [],
            'is_component': False,
            'is_system': False,
            'target_framework': None,
            'output_format': 'css'
        }
        
        task_lower = task_description.lower()
        
        # Determine design task type
        if 'design system' in task_lower:
            context['type'] = 'design_system'
            context['is_system'] = True
        elif 'component' in task_lower:
            context['type'] = 'component_design'
            context['is_component'] = True
        elif any(word in task_lower for word in ['color', 'palette', 'theme']):
            context['type'] = 'color_system'
            context['design_areas'].append('colors')
        elif any(word in task_lower for word in ['typography', 'font', 'text']):
            context['type'] = 'typography'
            context['design_areas'].append('typography')
        elif any(word in task_lower for word in ['spacing', 'padding', 'margin']):
            context['type'] = 'spacing_system'
            context['design_areas'].append('spacing')
        elif any(word in task_lower for word in ['layout', 'grid', 'responsive']):
            context['type'] = 'layout_system'
            context['design_areas'].append('layout')
        elif any(word in task_lower for word in ['animation', 'transition', 'interaction']):
            context['type'] = 'animations'
            context['design_areas'].append('animations')
        elif 'accessibility' in task_lower or 'a11y' in task_lower:
            context['type'] = 'accessibility'
            context['design_areas'].append('accessibility')
        
        # Detect framework/technology
        if 'tailwind' in task_lower:
            context['target_framework'] = 'tailwind'
            context['output_format'] = 'tailwind'
        elif 'css-in-js' in task_lower or 'styled-components' in task_lower:
            context['target_framework'] = 'css-in-js'
            context['output_format'] = 'js'
        elif 'sass' in task_lower or 'scss' in task_lower:
            context['output_format'] = 'scss'
        elif 'figma' in task_lower:
            context['output_format'] = 'design-tokens'
        
        # Identify specific design areas from task
        for area, keywords in self.design_components.items():
            if any(keyword in task_lower for keyword in keywords):
                if area not in context['design_areas']:
                    context['design_areas'].append(area)
        
        return context
    
    def _generate_design_content(self, task_description: str, context: Dict[str, Any]) -> tuple:
        """Generate design content using the LLM"""
        # Build appropriate prompt
        prompt = self._build_design_prompt(task_description, context)
        
        print(f"UX/UI Agent: Generating {context['type']} design...")
        generated_content = self._generate_response(prompt)
        
        # Determine target file
        target_file = self._determine_target_file(generated_content, context)
        
        return generated_content, target_file
    
    def _build_design_prompt(self, task_description: str, context: Dict[str, Any]) -> str:
        """Build a context-aware prompt for design generation"""
        # Get project type
        project_type = 'web application'
        if self.project_config:
            try:
                detected = self.project_config._detect_project_type()
                if detected:
                    project_type = detected
            except:
                pass
        
        # Get existing design context
        existing_styles = self._gather_design_context(context)
        
        base_prompt = f"""You are a senior UX/UI designer creating design systems and components for a {project_type}.

Task: {task_description}

Design Type: {context['type']}
Output Format: {context['output_format']}
Framework: {context.get('target_framework', 'vanilla CSS')}
"""
        
        if context['type'] == 'design_system':
            prompt = base_prompt + f"""
{existing_styles}

Create a comprehensive design system that includes:
1. Color palette with semantic naming
2. Typography scale and font definitions
3. Spacing system with consistent units
4. Component tokens (border radius, shadows, etc.)
5. Responsive breakpoints
6. Animation/transition definitions

Follow these principles:
- Use CSS custom properties (variables) for flexibility
- Include both light and dark theme support
- Ensure accessibility (WCAG 2.1 AA compliance)
- Create a consistent, scalable system

Return the complete CSS/SCSS code with clear comments.
"""
        elif context['type'] == 'color_system':
            prompt = base_prompt + f"""
{existing_styles}

Create a color palette system that includes:
1. Primary, secondary, and accent colors
2. Neutral colors (grays)
3. Semantic colors (success, warning, error, info)
4. Both light and dark theme variants
5. Accessible color combinations with proper contrast ratios

Use CSS custom properties and include:
- Base colors
- Shade variations (50-900)
- Text colors for each background
- Border and shadow colors

Ensure WCAG AA compliance for all color combinations.
"""
        elif context['type'] == 'component_design':
            prompt = base_prompt + f"""
{existing_styles}

Create a reusable UI component with:
1. Multiple variants (primary, secondary, outline, etc.)
2. Different sizes (small, medium, large)
3. Interactive states (hover, focus, active, disabled)
4. Responsive behavior
5. Accessibility features (ARIA labels, keyboard navigation)
6. Smooth transitions and micro-interactions

Include all necessary CSS and structure guidelines.
"""
        elif context['type'] == 'typography':
            prompt = base_prompt + f"""
{existing_styles}

Create a typography system that includes:
1. Font family definitions with fallbacks
2. Type scale (headings h1-h6, body text, captions)
3. Line heights and letter spacing
4. Responsive font sizes
5. Font weights and styles
6. Text color variations

Ensure readability and consistency across all text elements.
"""
        else:
            prompt = base_prompt + f"""
{existing_styles}

Generate appropriate {context['type']} design implementation following best practices for:
- Visual hierarchy
- Consistency
- Accessibility
- Responsiveness
- User experience

Include detailed implementation code with comments.
"""
        
        if context['output_format'] == 'tailwind':
            prompt += "\n\nProvide Tailwind CSS configuration and utility classes."
        elif context['output_format'] == 'css-in-js':
            prompt += "\n\nProvide styled-components or CSS-in-JS implementation."
        
        prompt += "\n\nReturn ONLY the implementation code, no explanations."
        
        return prompt
    
    def _gather_design_context(self, context: Dict[str, Any]) -> str:
        """Gather existing design/style files for context"""
        style_files = []
        
        # Look for existing style files
        if os.path.exists(self.project_root):
            # Common style file patterns
            style_patterns = [
                'styles', 'css', 'scss', 'sass',
                'theme', 'design-system', 'tokens'
            ]
            
            for root, dirs, files in os.walk(self.project_root):
                # Skip node_modules
                if 'node_modules' in root:
                    continue
                    
                for file in files:
                    file_lower = file.lower()
                    if any(pattern in file_lower for pattern in style_patterns):
                        if file.endswith(('.css', '.scss', '.sass', '.js', '.ts')):
                            style_files.append(os.path.join(root, file))
        
        if style_files:
            return f"Found {len(style_files)} existing style files in the project."
        else:
            return "No existing style system found. Creating new design system."
    
    def _determine_target_file(self, content: str, context: Dict[str, Any]) -> str:
        """Determine the target file name based on content and context"""
        # Try to extract filename from content
        if content and '/* File:' in content:
            lines = content.split('\n')
            for line in lines:
                if line.strip().startswith('/* File:') or line.strip().startswith('// File:'):
                    return line.replace('/* File:', '').replace('// File:', '').replace('*/', '').strip()
        
        # Generate filename based on context and format
        if context['output_format'] == 'scss':
            ext = '.scss'
        elif context['output_format'] == 'js':
            ext = '.js'
        elif context['output_format'] == 'design-tokens':
            ext = '.json'
        else:
            ext = '.css'
        
        if context['type'] == 'design_system':
            return f"styles/design-system{ext}"
        elif context['type'] == 'color_system':
            return f"styles/colors{ext}"
        elif context['type'] == 'typography':
            return f"styles/typography{ext}"
        elif context['type'] == 'spacing_system':
            return f"styles/spacing{ext}"
        elif context['type'] == 'component_design':
            return f"styles/components{ext}"
        elif context['type'] == 'animations':
            return f"styles/animations{ext}"
        elif context['type'] == 'layout_system':
            return f"styles/layout{ext}"
        else:
            return f"styles/styles-{int(time.time())}{ext}"
    
    def _integrate_design_content(self, content: str, target_file: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Integrate design content into the project"""
        # Use the intelligent integration system
        content_type = 'styles' if context['output_format'] in ['css', 'scss'] else 'component'
        strategy = self.get_integration_strategy(
            f"{context['type']} design", 
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
        agent = EventDrivenUXUIAgent()
        print(f"EventDrivenUXUIAgent initialized: {agent.name}")