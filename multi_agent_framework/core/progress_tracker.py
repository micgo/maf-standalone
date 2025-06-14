#!/usr/bin/env python3
"""
Progress tracking system for the Multi-Agent Framework
"""
import time
import json
import os
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from datetime import datetime, timedelta
import click


class ProgressTracker:
    """Track and display progress of tasks and features"""
    
    def __init__(self, state_file: str = ".maf/state.json"):
        """Initialize progress tracker with state file location"""
        self.state_file = Path(state_file)
        self._ensure_state_file()
        
    def _ensure_state_file(self):
        """Ensure state file exists"""
        if not self.state_file.exists():
            self.state_file.parent.mkdir(parents=True, exist_ok=True)
            self._save_state({
                'features': {},
                'tasks': {},
                'agents': {}
            })
            
    def _load_state(self) -> Dict:
        """Load state from file"""
        try:
            with open(self.state_file, 'r') as f:
                return json.load(f)
        except:
            return {'features': {}, 'tasks': {}, 'agents': {}}
            
    def _save_state(self, state: Dict):
        """Save state to file"""
        with open(self.state_file, 'w') as f:
            json.dump(state, f, indent=2)
            
    def create_feature(self, feature_id: str, description: str) -> None:
        """Create a new feature to track"""
        state = self._load_state()
        state['features'][feature_id] = {
            'id': feature_id,
            'description': description,
            'status': 'pending',
            'created_at': time.time(),
            'updated_at': time.time(),
            'tasks': [],
            'progress': 0
        }
        self._save_state(state)
        
    def create_task(self, task_id: str, feature_id: str, description: str, 
                   assigned_agent: str) -> None:
        """Create a new task"""
        state = self._load_state()
        
        state['tasks'][task_id] = {
            'id': task_id,
            'feature_id': feature_id,
            'description': description,
            'assigned_agent': assigned_agent,
            'status': 'pending',
            'created_at': time.time(),
            'updated_at': time.time(),
            'progress': 0
        }
        
        # Add task to feature
        if feature_id in state['features']:
            state['features'][feature_id]['tasks'].append(task_id)
            state['features'][feature_id]['updated_at'] = time.time()
            
        self._save_state(state)
        
    def update_task_status(self, task_id: str, status: str, progress: int = None) -> None:
        """Update task status and progress"""
        state = self._load_state()
        
        if task_id in state['tasks']:
            state['tasks'][task_id]['status'] = status
            state['tasks'][task_id]['updated_at'] = time.time()
            
            if progress is not None:
                state['tasks'][task_id]['progress'] = max(0, min(100, progress))
                
            # Update feature progress
            feature_id = state['tasks'][task_id]['feature_id']
            if feature_id in state['features']:
                self._update_feature_progress(state, feature_id)
                
        self._save_state(state)
        
    def _update_feature_progress(self, state: Dict, feature_id: str) -> None:
        """Update feature progress based on task progress"""
        feature = state['features'][feature_id]
        
        if not feature['tasks']:
            feature['progress'] = 0
            return
            
        total_progress = 0
        completed_count = 0
        
        for task_id in feature['tasks']:
            if task_id in state['tasks']:
                task = state['tasks'][task_id]
                total_progress += task.get('progress', 0)
                
                if task['status'] == 'completed':
                    completed_count += 1
                    
        feature['progress'] = int(total_progress / len(feature['tasks']))
        
        # Update feature status
        if completed_count == len(feature['tasks']):
            feature['status'] = 'completed'
        elif completed_count > 0 or total_progress > 0:
            feature['status'] = 'in_progress'
            
        feature['updated_at'] = time.time()
        
    def get_feature_progress(self, feature_id: str) -> Dict:
        """Get progress information for a feature"""
        state = self._load_state()
        
        if feature_id not in state['features']:
            return None
            
        feature = state['features'][feature_id]
        tasks = []
        
        for task_id in feature['tasks']:
            if task_id in state['tasks']:
                tasks.append(state['tasks'][task_id])
                
        return {
            'feature': feature,
            'tasks': tasks
        }
        
    def get_all_features(self) -> List[Dict]:
        """Get all features with their progress"""
        state = self._load_state()
        features = []
        
        for feature_id, feature in state['features'].items():
            feature_data = self.get_feature_progress(feature_id)
            if feature_data:
                features.append(feature_data)
                
        # Sort by created_at descending
        features.sort(key=lambda x: x['feature']['created_at'], reverse=True)
        return features
        
    def display_progress(self, detailed: bool = False) -> None:
        """Display progress using click with progress bars"""
        features = self.get_all_features()
        
        if not features:
            click.echo("📭 No features in progress")
            return
            
        click.echo("\n📊 Feature Development Progress\n")
        
        for feature_data in features:
            feature = feature_data['feature']
            tasks = feature_data['tasks']
            
            # Feature header
            status_emoji = {
                'pending': '⏳',
                'in_progress': '🔄',
                'completed': '✅',
                'failed': '❌'
            }.get(feature['status'], '❓')
            
            click.echo(f"{status_emoji} {feature['description'][:60]}...")
            
            # Progress bar
            with click.progressbar(
                length=100,
                label='   Progress',
                show_percent=True,
                show_pos=True,
                width=40,
                fill_char='█',
                empty_char='░'
            ) as bar:
                bar.update(feature['progress'])
                
            # Time estimate
            elapsed = time.time() - feature['created_at']
            if feature['progress'] > 0 and feature['progress'] < 100:
                estimated_total = elapsed / (feature['progress'] / 100)
                remaining = estimated_total - elapsed
                eta = datetime.now() + timedelta(seconds=remaining)
                click.echo(f"   ⏱️  ETA: {eta.strftime('%H:%M:%S')} ({self._format_duration(remaining)} remaining)")
            elif feature['status'] == 'completed':
                click.echo(f"   ✨ Completed in {self._format_duration(elapsed)}")
                
            # Task details
            if detailed and tasks:
                click.echo("   📋 Tasks:")
                for task in tasks:
                    task_status = {
                        'pending': '⏸️',
                        'in_progress': '▶️',
                        'completed': '✅',
                        'failed': '❌'
                    }.get(task['status'], '❓')
                    
                    agent_emoji = {
                        'orchestrator': '🎯',
                        'frontend_agent': '🎨',
                        'backend_agent': '⚙️',
                        'db_agent': '💾',
                        'devops_agent': '🚀',
                        'qa_agent': '🧪',
                        'docs_agent': '📚',
                        'security_agent': '🔒',
                        'ux_ui_agent': '✨'
                    }.get(task['assigned_agent'], '🤖')
                    
                    click.echo(f"      {task_status} {agent_emoji} {task['assigned_agent']}: {task['description'][:50]}...")
                    
                    if task['status'] == 'in_progress' and task.get('progress', 0) > 0:
                        # Mini progress bar for task
                        progress_width = 20
                        filled = int(task['progress'] / 100 * progress_width)
                        bar = '█' * filled + '░' * (progress_width - filled)
                        click.echo(f"         [{bar}] {task['progress']}%")
                        
            click.echo()  # Empty line between features
            
    def _format_duration(self, seconds: float) -> str:
        """Format duration in human readable format"""
        if seconds < 60:
            return f"{int(seconds)}s"
        elif seconds < 3600:
            minutes = int(seconds / 60)
            secs = int(seconds % 60)
            return f"{minutes}m {secs}s"
        else:
            hours = int(seconds / 3600)
            minutes = int((seconds % 3600) / 60)
            return f"{hours}h {minutes}m"
            
    def get_active_features_count(self) -> Tuple[int, int]:
        """Get count of active and total features"""
        state = self._load_state()
        active = sum(1 for f in state['features'].values() 
                    if f['status'] in ['pending', 'in_progress'])
        total = len(state['features'])
        return active, total


# Singleton instance
_progress_tracker = None

def get_progress_tracker(state_file: str = ".maf/state.json") -> ProgressTracker:
    """Get or create progress tracker instance"""
    global _progress_tracker
    if _progress_tracker is None:
        _progress_tracker = ProgressTracker(state_file)
    return _progress_tracker