import os
import re
import ast
from typing import Dict, List, Optional, Tuple
from .file_integrator import FileIntegrator
from .project_analyzer import ProjectAnalyzer

class SmartIntegrator:
    """
    Enhanced file integration that reduces file proliferation by intelligently
    consolidating related functionality and improving existing files.
    """
    
    def __init__(self, project_root: str):
        self.project_root = project_root
        self.file_integrator = FileIntegrator(project_root)
        self.project_analyzer = ProjectAnalyzer(project_root)
        
    def should_consolidate(self, new_content: str, existing_file: str, 
                          task_description: str) -> Tuple[bool, str]:
        """
        Determine if new content should be consolidated into existing file.
        Returns (should_consolidate, reason).
        """
        # Check file size - avoid making files too large
        if os.path.exists(existing_file):
            file_size = os.path.getsize(existing_file)
            if file_size > 5000:  # ~5KB threshold
                return False, "File is already large"
                
        # Analyze semantic relationship
        if self._is_semantically_related(new_content, existing_file, task_description):
            # Check if it's a utility function that belongs in existing file
            if self._is_utility_function(new_content):
                return True, "Utility function belongs in existing file"
                
            # Check if it's a related component (e.g., sub-component)
            if self._is_related_component(new_content, existing_file):
                return True, "Related component can be consolidated"
                
            # Check if it's an enhancement to existing functionality
            if self._is_enhancement(new_content, task_description):
                return True, "Enhancement to existing functionality"
                
        return False, "Content is independent"
    
    def _is_semantically_related(self, new_content: str, existing_file: str, 
                                task_description: str) -> bool:
        """Check if content is semantically related to existing file."""
        # Read existing file
        try:
            with open(existing_file, 'r') as f:
                existing_content = f.read()
        except:
            return False
            
        # Extract key identifiers from both contents
        new_identifiers = self._extract_identifiers(new_content)
        existing_identifiers = self._extract_identifiers(existing_content)
        
        # Check for shared imports/dependencies
        new_imports = self._extract_imports(new_content)
        existing_imports = self._extract_imports(existing_content)
        shared_imports = new_imports.intersection(existing_imports)
        
        # High overlap in imports suggests related functionality
        if len(shared_imports) > 3:
            return True
            
        # Check for similar function/component names
        name_similarity = self._check_name_similarity(new_identifiers, existing_identifiers)
        if name_similarity > 0.5:
            return True
            
        # Check task description for relationship keywords
        relationship_keywords = ['enhance', 'extend', 'add to', 'modify', 'update', 
                               'improve', 'refactor', 'integrate with']
        task_lower = task_description.lower()
        existing_name = os.path.basename(existing_file).split('.')[0]
        
        for keyword in relationship_keywords:
            if keyword in task_lower and existing_name.lower() in task_lower:
                return True
                
        return False
    
    def _is_utility_function(self, content: str) -> bool:
        """Check if content is a utility function that should be grouped."""
        # Look for standalone functions without component structure
        has_component = bool(re.search(r'(class|function)\s+\w+.*(?:Component|Page)', content))
        has_jsx = bool(re.search(r'return\s*\(?\s*<', content))
        
        if not has_component and not has_jsx:
            # Check for utility function patterns
            utility_patterns = [
                r'export\s+(?:const|function)\s+(?:get|set|calculate|validate|format|parse)',
                r'export\s+(?:const|function)\s+\w+(?:Helper|Util|Service)',
                r'const\s+\w+\s*=\s*\([^)]*\)\s*=>\s*{',  # Arrow functions
            ]
            
            for pattern in utility_patterns:
                if re.search(pattern, content):
                    return True
                    
        return False
    
    def _is_related_component(self, new_content: str, existing_file: str) -> bool:
        """Check if new content is a related component (e.g., sub-component)."""
        # Extract component names
        new_component = self._extract_component_name(new_content)
        existing_component = self._extract_component_name_from_file(existing_file)
        
        if new_component and existing_component:
            # Check for parent-child relationship
            if new_component.startswith(existing_component) or \
               existing_component.startswith(new_component):
                return True
                
            # Check for common prefix (e.g., UserProfile and UserAvatar)
            common_prefix = os.path.commonprefix([new_component, existing_component])
            if len(common_prefix) > 4:  # Meaningful prefix
                return True
                
        return False
    
    def _is_enhancement(self, content: str, task_description: str) -> bool:
        """Check if content is an enhancement to existing functionality."""
        enhancement_indicators = [
            'add', 'enhance', 'improve', 'extend', 'update', 'refactor',
            'optimize', 'fix', 'patch', 'modify'
        ]
        
        task_lower = task_description.lower()
        for indicator in enhancement_indicators:
            if indicator in task_lower:
                # Check if it's not creating something entirely new
                if not any(word in task_lower for word in ['new', 'create', 'build']):
                    return True
                    
        return False
    
    def consolidate_content(self, new_content: str, target_file: str, 
                          consolidation_strategy: str = 'append') -> str:
        """
        Consolidate new content into existing file using specified strategy.
        """
        with open(target_file, 'r') as f:
            existing_content = f.read()
            
        if consolidation_strategy == 'append':
            # Simply append new content at the end
            return self._append_content(existing_content, new_content)
            
        elif consolidation_strategy == 'merge_functions':
            # Merge utility functions into existing file
            return self._merge_functions(existing_content, new_content)
            
        elif consolidation_strategy == 'merge_components':
            # Merge related components
            return self._merge_components(existing_content, new_content)
            
        elif consolidation_strategy == 'enhance':
            # Enhance existing functionality
            return self._enhance_content(existing_content, new_content)
            
        else:
            # Default to append
            return self._append_content(existing_content, new_content)
    
    def _append_content(self, existing: str, new: str) -> str:
        """Append new content to existing file intelligently."""
        # Remove duplicate imports
        new_without_imports = self._remove_imports(new)
        
        # Find the best insertion point (before export default or at end)
        export_match = re.search(r'^export\s+default', existing, re.MULTILINE)
        if export_match:
            insert_pos = export_match.start()
            return existing[:insert_pos] + '\n' + new_without_imports + '\n\n' + existing[insert_pos:]
        else:
            return existing + '\n\n' + new_without_imports
    
    def _merge_functions(self, existing: str, new: str) -> str:
        """Merge utility functions into existing file."""
        # Extract functions from new content
        new_functions = self._extract_functions(new)
        
        # Remove imports from new content
        new_without_imports = self._remove_imports(new)
        
        # Find insertion point (before export default or at end)
        export_match = re.search(r'^export\s+default', existing, re.MULTILINE)
        if export_match:
            insert_pos = export_match.start()
            return existing[:insert_pos] + '\n' + new_without_imports + '\n\n' + existing[insert_pos:]
        else:
            return existing + '\n\n' + new_without_imports
    
    def _merge_components(self, existing: str, new: str) -> str:
        """Merge related components into same file."""
        # This is more complex - for now, append as separate export
        new_component = self._extract_component_name(new)
        
        # Remove any export default from new content
        new_modified = re.sub(r'export\s+default\s+', 'export ', new)
        
        # Remove imports that are already in existing
        new_without_imports = self._remove_duplicate_imports(existing, new_modified)
        
        # Append before the default export of existing
        export_match = re.search(r'^export\s+default', existing, re.MULTILINE)
        if export_match:
            insert_pos = export_match.start()
            return existing[:insert_pos] + '\n' + new_without_imports + '\n\n' + existing[insert_pos:]
        else:
            return existing + '\n\n' + new_without_imports
    
    def _enhance_content(self, existing: str, new: str) -> str:
        """Enhance existing content with new functionality."""
        # This requires more sophisticated parsing and merging
        # For now, use intelligent append
        return self._append_content(existing, new)
    
    def _extract_identifiers(self, content: str) -> set:
        """Extract function and variable names from content."""
        identifiers = set()
        
        # Function names
        func_pattern = r'(?:function|const|let|var)\s+(\w+)'
        identifiers.update(re.findall(func_pattern, content))
        
        # Class names
        class_pattern = r'class\s+(\w+)'
        identifiers.update(re.findall(class_pattern, content))
        
        return identifiers
    
    def _extract_imports(self, content: str) -> set:
        """Extract imported modules from content."""
        imports = set()
        
        # ES6 imports
        import_pattern = r'import.*from\s+[\'"]([^\'"]+)[\'"]'
        imports.update(re.findall(import_pattern, content))
        
        # CommonJS requires
        require_pattern = r'require\s*\([\'"]([^\'"]+)[\'"]\)'
        imports.update(re.findall(require_pattern, content))
        
        return imports
    
    def _check_name_similarity(self, names1: set, names2: set) -> float:
        """Check similarity between two sets of names."""
        if not names1 or not names2:
            return 0.0
            
        # Check for common prefixes/suffixes
        similarity_count = 0
        for name1 in names1:
            for name2 in names2:
                # Direct substring match
                if name1 in name2 or name2 in name1:
                    similarity_count += 1
                    continue
                    
                # Common prefix (at least 4 chars)
                common_prefix = os.path.commonprefix([name1, name2])
                if len(common_prefix) >= 4:
                    similarity_count += 0.5
                    
        max_possible = min(len(names1), len(names2))
        return similarity_count / max_possible if max_possible > 0 else 0
    
    def _extract_component_name(self, content: str) -> Optional[str]:
        """Extract React component name from content."""
        patterns = [
            r'(?:export\s+default\s+)?function\s+(\w+)',
            r'(?:export\s+)?const\s+(\w+)\s*=.*=>',
            r'class\s+(\w+)\s+extends',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content)
            if match:
                name = match.group(1)
                # Ensure it's likely a component (PascalCase)
                if name[0].isupper():
                    return name
                    
        return None
    
    def _extract_component_name_from_file(self, filepath: str) -> Optional[str]:
        """Extract component name from file path or content."""
        # First try from filename
        basename = os.path.basename(filepath).split('.')[0]
        if basename[0].isupper():
            return basename
            
        # Then try from content
        try:
            with open(filepath, 'r') as f:
                content = f.read()
                return self._extract_component_name(content)
        except:
            return None
    
    def _remove_imports(self, content: str) -> str:
        """Remove import statements from content."""
        # Remove ES6 imports
        content = re.sub(r'^import.*$', '', content, flags=re.MULTILINE)
        # Remove empty lines at the start
        content = content.lstrip('\n')
        return content
    
    def _extract_functions(self, content: str) -> List[str]:
        """Extract function definitions from content."""
        functions = []
        
        # Match function definitions
        func_pattern = r'((?:export\s+)?(?:async\s+)?function\s+\w+[^{]+{[^}]+})'
        functions.extend(re.findall(func_pattern, content, re.DOTALL))
        
        # Match arrow functions
        arrow_pattern = r'((?:export\s+)?const\s+\w+\s*=\s*(?:async\s+)?\([^)]*\)\s*=>\s*{[^}]+})'
        functions.extend(re.findall(arrow_pattern, content, re.DOTALL))
        
        return functions
    
    def _remove_duplicate_imports(self, existing: str, new: str) -> str:
        """Remove imports from new content that already exist in existing."""
        existing_imports = self._extract_imports(existing)
        
        lines = new.split('\n')
        filtered_lines = []
        
        for line in lines:
            # Check if this is an import line
            if re.match(r'^\s*import', line):
                # Extract the module being imported
                module_match = re.search(r'from\s+[\'"]([^\'"]+)[\'"]', line)
                if module_match and module_match.group(1) in existing_imports:
                    continue  # Skip this import
                    
            filtered_lines.append(line)
            
        return '\n'.join(filtered_lines)