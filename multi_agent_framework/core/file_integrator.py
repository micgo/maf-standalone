import os
import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Union

class FileIntegrator:
    """Handles intelligent file integration and modification."""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
    
    def integrate_component(self, content: str, target_path: str, mode: str = 'create') -> str:
        """Integrate component code into the project structure."""
        target = self.project_root / target_path
        
        if mode == 'create':
            return self._create_new_file(content, target)
        elif mode == 'modify':
            return self._modify_existing_file(content, target)
        elif mode == 'append':
            return self._append_to_file(content, target)
        else:
            raise ValueError(f"Unknown integration mode: {mode}")
    
    def _create_new_file(self, content: str, target: Path) -> str:
        """Create a new file with proper naming."""
        # Ensure directory exists
        target.parent.mkdir(parents=True, exist_ok=True)
        
        # Handle naming conflicts
        if target.exists():
            target = self._get_unique_filename(target)
        
        target.write_text(content)
        return str(target.relative_to(self.project_root))
    
    def _modify_existing_file(self, content: str, target: Path) -> str:
        """Modify existing file intelligently."""
        if not target.exists():
            return self._create_new_file(content, target)
        
        existing_content = target.read_text()
        
        # Determine modification type
        if self._is_component_file(target):
            modified_content = self._merge_component_code(existing_content, content)
        elif self._is_api_file(target):
            modified_content = self._merge_api_code(existing_content, content)
        elif self._is_config_file(target):
            modified_content = self._merge_config_file(existing_content, content, target.suffix)
        else:
            # Default: append with clear separation
            modified_content = f"{existing_content}\n\n// --- Added by Framework ---\n{content}"
        
        # Create backup
        backup_path = target.with_suffix(f".backup{target.suffix}")
        backup_path.write_text(existing_content)
        
        target.write_text(modified_content)
        return str(target.relative_to(self.project_root))
    
    def _append_to_file(self, content: str, target: Path) -> str:
        """Append content to existing file."""
        if target.exists():
            existing = target.read_text()
            content = f"{existing}\n\n{content}"
        
        return self._create_new_file(content, target)
    
    def _merge_component_code(self, existing: str, new: str) -> str:
        """Intelligently merge React component code."""
        # Extract imports, component definition, and exports
        existing_imports = self._extract_imports(existing)
        new_imports = self._extract_imports(new)
        
        # Merge imports (remove duplicates)
        merged_imports = list(dict.fromkeys(existing_imports + new_imports))
        
        # Try to merge component functions
        if "export default" in new:
            # New code has a default export - likely a complete component
            # Keep existing component but add new functions/types
            new_functions = self._extract_functions(new)
            new_types = self._extract_types(new)
            
            merged_content = "\n".join(merged_imports) + "\n\n"
            merged_content += existing + "\n\n"
            merged_content += "// --- Added Functions ---\n"
            merged_content += "\n".join(new_functions) + "\n\n"
            merged_content += "// --- Added Types ---\n"
            merged_content += "\n".join(new_types)
            
            return merged_content
        else:
            # New code is partial - integrate into existing
            imports_str = '\n'.join(merged_imports)
            return f"{imports_str}\n\n{existing}\n\n// --- Added Code ---\n{new}"
    
    def _merge_api_code(self, existing: str, new: str) -> str:
        """Merge API route code."""
        # Check if new code has HTTP methods
        http_methods = ['GET', 'POST', 'PUT', 'DELETE', 'PATCH']
        
        for method in http_methods:
            if f"export async function {method}" in new:
                # Check if method already exists
                if f"export async function {method}" in existing:
                    # Replace existing method
                    pattern = rf"export async function {method}[^}}]+}}}}"
                    existing = re.sub(pattern, '', existing, flags=re.DOTALL)
                
        return f"{existing}\n\n// --- Added Methods ---\n{new}"
    
    def _merge_config_file(self, existing: str, new: str, file_ext: str) -> str:
        """Merge configuration files based on type."""
        if file_ext == '.json':
            return self._merge_json_config(existing, new)
        elif file_ext in ['.js', '.ts', '.mjs']:
            return self._merge_js_config(existing, new)
        else:
            return f"{existing}\n\n# --- Added Configuration ---\n{new}"
    
    def _merge_json_config(self, existing: str, new: str) -> str:
        """Merge JSON configuration files."""
        try:
            existing_data = json.loads(existing)
            new_data = json.loads(new)
            
            # Deep merge
            merged = self._deep_merge_dict(existing_data, new_data)
            return json.dumps(merged, indent=2)
        except json.JSONDecodeError:
            return f"{existing}\n\n/* --- Added Configuration ---\n{new}\n*/"
    
    def _merge_js_config(self, existing: str, new: str) -> str:
        """Merge JavaScript/TypeScript config files."""
        # Simple append for now - could be enhanced for specific configs
        return f"{existing}\n\n// --- Added Configuration ---\n{new}"
    
    def _deep_merge_dict(self, base: dict, override: dict) -> dict:
        """Deep merge two dictionaries."""
        result = base.copy()
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge_dict(result[key], value)
            else:
                result[key] = value
        return result
    
    def _extract_imports(self, content: str) -> List[str]:
        """Extract import statements from code."""
        import_pattern = r'^import\s+.*?;?$'
        return re.findall(import_pattern, content, re.MULTILINE)
    
    def _extract_functions(self, content: str) -> List[str]:
        """Extract function definitions from code."""
        function_pattern = r'(?:export\s+)?(?:async\s+)?function\s+\w+[^{]*\{[^}]*\}'
        return re.findall(function_pattern, content, re.DOTALL)
    
    def _extract_types(self, content: str) -> List[str]:
        """Extract type definitions from code."""
        type_pattern = r'(?:export\s+)?(?:type|interface)\s+\w+[^{]*\{[^}]*\}'
        return re.findall(type_pattern, content, re.DOTALL)
    
    def _is_component_file(self, path: Path) -> bool:
        """Check if file is a React component."""
        return path.suffix in ['.tsx', '.jsx'] or 'component' in path.name.lower()
    
    def _is_api_file(self, path: Path) -> bool:
        """Check if file is an API route."""
        return 'api' in str(path) and path.name in ['route.ts', 'route.js']
    
    def _is_config_file(self, path: Path) -> bool:
        """Check if file is a configuration file."""
        config_names = ['package.json', 'tsconfig.json', 'next.config', 'tailwind.config', 'vercel.json']
        return any(name in path.name for name in config_names)
    
    def _get_unique_filename(self, path: Path) -> Path:
        """Generate unique filename if file exists."""
        counter = 1
        base = path.stem
        suffix = path.suffix
        parent = path.parent
        
        while True:
            new_name = f"{base}_{counter}{suffix}"
            new_path = parent / new_name
            if not new_path.exists():
                return new_path
            counter += 1
    
    def organize_generated_files(self, files: List[str]) -> Dict[str, List[str]]:
        """Organize generated files by category for better integration."""
        organized = {
            'components': [],
            'pages': [],
            'api': [],
            'types': [],
            'utils': [],
            'docs': [],
            'config': [],
            'other': []
        }
        
        for file_path in files:
            path = Path(file_path)
            
            if 'component' in file_path.lower() or path.suffix in ['.tsx', '.jsx']:
                organized['components'].append(file_path)
            elif 'page' in file_path.lower() or '/app/' in file_path:
                organized['pages'].append(file_path)
            elif '/api/' in file_path or 'route.' in file_path:
                organized['api'].append(file_path)
            elif 'type' in file_path.lower() or '.d.ts' in file_path:
                organized['types'].append(file_path)
            elif '/lib/' in file_path or 'util' in file_path.lower():
                organized['utils'].append(file_path)
            elif path.suffix == '.md':
                organized['docs'].append(file_path)
            elif self._is_config_file(path):
                organized['config'].append(file_path)
            else:
                organized['other'].append(file_path)
        
        return organized