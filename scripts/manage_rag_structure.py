#!/usr/bin/env python3
"""
RAG Structure Management - Consolidates folder organization and removes duplicates
Manages:
- Duplicate services cleanup
- Config consolidation 
- Import path fixes
"""

import os
import json
import shutil
from pathlib import Path
from typing import List, Dict, Tuple


class RAGStructureManager:
    """Manages RAG folder structure and consolidation"""
    
    def __init__(self, rag_root: str):
        """Initialize with RAG root directory"""
        self.rag_root = Path(rag_root)
        self.report = {
            'duplicates_found': [],
            'empty_dirs': [],
            'config_status': {},
            'import_issues': []
        }
    
    def audit_structure(self) -> Dict:
        """Audit current RAG structure"""
        print("\n" + "="*60)
        print("AUDITING RAG STRUCTURE")
        print("="*60)
        
        # 1. Check for duplicate services
        self._find_duplicate_services()
        
        # 2. Check for empty directories
        self._find_empty_directories()
        
        # 3. Check config status
        self._check_config_status()
        
        # 4. Check import paths
        self._check_import_paths()
        
        return self.report
    
    def _find_duplicate_services(self):
        """Find duplicate service files"""
        print("\n[1] Checking for duplicate services...")
        
        services_locations = {
            'core/services': self.rag_root / 'core' / 'services',
            'tools/services': self.rag_root / 'tools' / 'services'
        }
        
        for location_name, path in services_locations.items():
            if path.exists():
                files = list(path.glob('*.py'))
                print(f"    {location_name}: {len(files)} files")
                for f in files:
                    if f.name != '__init__.py':
                        print(f"      - {f.name}")
                        self.report['duplicates_found'].append({
                            'file': f.name,
                            'location': location_name,
                            'path': str(f)
                        })
    
    def _find_empty_directories(self):
        """Find empty directories"""
        print("\n[2] Checking for empty directories...")
        
        # Check core/config
        core_config = self.rag_root / 'core' / 'config'
        if core_config.exists():
            py_files = list(core_config.glob('*.py'))
            json_files = list(core_config.glob('*.json'))
            
            if len(py_files) <= 2 and len(json_files) == 0:  # Only __init__.py, loader.py
                print(f"    core/config: EMPTY (no JSON files, only Python files)")
                self.report['empty_dirs'].append({
                    'path': 'core/config',
                    'reason': 'No JSON config files present',
                    'py_files': len(py_files),
                    'json_files': len(json_files)
                })
        
        # Check core/services
        core_services = self.rag_root / 'core' / 'services'
        if core_services.exists():
            py_files = list(core_services.glob('*.py'))
            if len(py_files) <= 1:  # Only __init__.py
                print(f"    core/services: EMPTY (only __init__.py)")
                self.report['empty_dirs'].append({
                    'path': 'core/services',
                    'reason': 'Only __init__.py, services re-exported',
                    'py_files': len(py_files)
                })
    
    def _check_config_status(self):
        """Check config file locations"""
        print("\n[3] Checking config file status...")
        
        # Check canonical location
        canonical_config = self.rag_root / 'config'
        if canonical_config.exists():
            json_files = list(canonical_config.glob('*.json'))
            print(f"    rag/config: {len(json_files)} JSON files found")
            self.report['config_status']['canonical'] = {
                'path': 'config',
                'files': [f.name for f in json_files]
            }
        
        # Check duplicate location
        core_config = self.rag_root / 'core' / 'config'
        if core_config.exists():
            json_files = list(core_config.glob('*.json'))
            py_files = [f for f in core_config.glob('*.py') if f.name != '__init__.py']
            print(f"    core/config: {len(json_files)} JSON files, {len(py_files)} Python files")
            self.report['config_status']['core'] = {
                'path': 'core/config',
                'json_files': len(json_files),
                'py_files': [f.name for f in py_files]
            }
    
    def _check_import_paths(self):
        """Check for import path issues"""
        print("\n[4] Checking import paths...")
        
        # Search for imports referencing core/config
        agents_dir = self.rag_root / 'agents'
        if agents_dir.exists():
            for agent_file in agents_dir.glob('*.py'):
                with open(agent_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if 'from ..core.config' in content:
                        print(f"    ✗ {agent_file.name}: imports from core.config")
                        self.report['import_issues'].append({
                            'file': agent_file.name,
                            'issue': 'imports from core.config'
                        })
                    elif 'ConfigLoader' in content:
                        print(f"    ✓ {agent_file.name}: uses ConfigLoader")
    
    def print_report(self):
        """Print audit report"""
        print("\n" + "="*60)
        print("AUDIT REPORT")
        print("="*60)
        
        print(f"\nDuplicate Services Found: {len(self.report['duplicates_found'])}")
        for dup in self.report['duplicates_found']:
            print(f"  - {dup['file']} in {dup['location']}")
        
        print(f"\nEmpty/Deprecated Directories: {len(self.report['empty_dirs'])}")
        for empty_dir in self.report['empty_dirs']:
            print(f"  - {empty_dir['path']}: {empty_dir['reason']}")
        
        print(f"\nConfig Status:")
        for location, config_info in self.report['config_status'].items():
            print(f"  - {location} ({config_info['path']})")
            if 'files' in config_info:
                for file in config_info['files']:
                    print(f"      • {file}")
        
        if self.report['import_issues']:
            print(f"\nImport Issues Found: {len(self.report['import_issues'])}")
            for issue in self.report['import_issues']:
                print(f"  - {issue['file']}: {issue['issue']}")
    
    def cleanup_redundant_files(self, dry_run: bool = True):
        """Clean up redundant/duplicate files"""
        print("\n" + "="*60)
        print("CLEANUP - REDUNDANT FILES")
        print("="*60)
        
        if dry_run:
            print("\n[DRY RUN - No files will be deleted]\n")
        
        # Strategy: Keep canonical, remove duplicates
        actions = []
        
        # 1. Remove core/services duplicate if tools/services exists
        core_services = self.rag_root / 'core' / 'services'
        tools_services = self.rag_root / 'tools' / 'services'
        
        if core_services.exists() and tools_services.exists():
            print(f"\nFound both core/services and tools/services")
            print(f"  Canonical: tools/services")
            print(f"  Duplicate: core/services")
            print(f"  Action: {'WOULD DELETE' if dry_run else 'DELETING'} core/services")
            actions.append({
                'action': 'delete_dir',
                'path': core_services,
                'reason': 'Duplicate services (canonical is tools/services)'
            })
        
        # 2. Remove core/config if empty and config exists in rag root
        core_config = self.rag_root / 'core' / 'config'
        canonical_config = self.rag_root / 'config'
        
        if core_config.exists():
            json_files = list(core_config.glob('*.json'))
            if len(json_files) == 0 and canonical_config.exists():
                print(f"\nFound empty core/config (no JSON files)")
                print(f"  Canonical: rag/config (has {len(list(canonical_config.glob('*.json')))} JSON files)")
                print(f"  Action: {'WOULD DELETE' if dry_run else 'DELETING'} core/config")
                actions.append({
                    'action': 'delete_dir',
                    'path': core_config,
                    'reason': 'Empty config folder (canonical is rag/config)'
                })
        
        if not dry_run:
            for action in actions:
                if action['action'] == 'delete_dir':
                    try:
                        shutil.rmtree(action['path'])
                        print(f"  ✓ Deleted: {action['path']}")
                    except Exception as e:
                        print(f"  ✗ Failed to delete {action['path']}: {e}")
        
        return actions
    
    def print_structure_recommendations(self):
        """Print structure recommendations"""
        print("\n" + "="*60)
        print("RECOMMENDATIONS")
        print("="*60)
        
        print("""
1. KEEP - rag/config/ 
   - Contains all JSON config files (agent_config, llm_config, etc.)
   - Used by ConfigLoader in all agents
   - Should be the CANONICAL config location

2. DELETE - core/config/
   - Contains empty directory with only loader.py
   - No JSON files present
   - Creates confusion with canonical location
   - ConfigLoader can be moved to tools/services or kept as utility

3. DELETE - core/services/
   - Contains duplicate re-exports of tools/services
   - Confusing for imports and maintenance
   - Keep only tools/services as canonical

4. UPDATE - All imports to use absolute paths
   - From: from ..core.config.loader import ConfigLoader
   - To: from incident_iq.rag.core.config.loader import ConfigLoader
     OR: from incident_iq.rag.tools.config.loader import ConfigLoader

5. CREATE - tools/config/ (Optional)
   - Move ConfigLoader to tools/config/ for better organization
   - Keep tools/ as utilities location
        """)


def main():
    """Run RAG structure audit"""
    rag_root = Path("e:\\ai-projects\\incident_manangement\\src\\incident_iq\\rag")
    
    if not rag_root.exists():
        print(f"Error: RAG root not found at {rag_root}")
        return
    
    manager = RAGStructureManager(str(rag_root))
    
    # Run audit
    manager.audit_structure()
    manager.print_report()
    
    # Show cleanup actions (dry run)
    manager.cleanup_redundant_files(dry_run=True)
    
    # Print recommendations
    manager.print_structure_recommendations()
    
    print("\n" + "="*60)
    print("Run with --cleanup flag to perform actual cleanup")
    print("="*60)


if __name__ == '__main__':
    import sys
    main()
