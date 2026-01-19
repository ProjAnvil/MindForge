#!/usr/bin/env python3
"""
add_files_to_xcode.py

Automatically detects and adds new source files to an Xcode project.
This script scans the project directory for files that exist on the filesystem
but are not yet referenced in the Xcode project file, and adds them appropriately.

Usage:
    python3 add_files_to_xcode.py [options]

Options:
    --project PROJECT           Specific .xcodeproj to use (name or path)
    --list-targets              List all targets in the project and exit
    --files FILE [FILE ...]     Specific files to add (relative to project root)
    --target TARGET             Target name to add files to (default: main target)
    --dry-run                   Preview changes without modifying project file
    --verbose                   Enable verbose output
    --help                      Show this help message

Requirements:
    - Python 3.7+
    - Must be run from Xcode project root directory or specify project path
    - Xcode project must have a .xcodeproj directory

Exit Codes:
    0: Success
    1: Project file not found
    2: Invalid project structure
    3: No files to add
"""

import os
import sys
import argparse
import uuid
import re
from pathlib import Path
from typing import List, Dict, Set, Tuple, Optional


class XcodeProject:
    """Manages Xcode project file operations."""
    
    def __init__(self, project_path: str):
        """Initialize with path to .xcodeproj directory."""
        self.project_path = Path(project_path)
        self.pbxproj_path = self.project_path / "project.pbxproj"
        
        if not self.pbxproj_path.exists():
            raise FileNotFoundError(f"Project file not found: {self.pbxproj_path}")
        
        with open(self.pbxproj_path, 'r', encoding='utf-8') as f:
            self.content = f.read()
        
        self.project_root = self.project_path.parent
        self._parse_project()
    
    def _parse_project(self):
        """Parse project file to extract key information."""
        # Extract all existing file references
        self.file_references = set()
        file_ref_pattern = r'(?:path|name)\s*=\s*"?([^";]+\.(?:swift|h|m|mm|cpp|c|storyboard|xib|xcassets|strings|plist|json|xml))"?;'
        for match in re.finditer(file_ref_pattern, self.content, re.IGNORECASE):
            self.file_references.add(match.group(1))
        
        # Extract main group UUID
        main_group_match = re.search(r'mainGroup\s*=\s*([A-F0-9]+);', self.content)
        self.main_group_id = main_group_match.group(1) if main_group_match else None
        
        # Extract targets
        self.targets = {}
        target_pattern = r'/\* (\w+) \*/\s*=\s*\{\s*isa\s*=\s*PBXNativeTarget;'
        for match in re.finditer(target_pattern, self.content):
            target_name = match.group(1)
            # Find target UUID
            target_uuid_match = re.search(
                rf'([A-F0-9]+)\s*/\* {re.escape(target_name)} \*/\s*=\s*\{{[^}}]*isa\s*=\s*PBXNativeTarget',
                self.content
            )
            if target_uuid_match:
                self.targets[target_name] = target_uuid_match.group(1)
        
        # Extract source build phase UUIDs
        self.sources_build_phase = {}
        self.resources_build_phase = {}
        
        for target_name, target_uuid in self.targets.items():
            # Find buildPhases for this target
            target_block_match = re.search(
                rf'{target_uuid}\s*/\* {re.escape(target_name)} \*/\s*=\s*\{{([^}}]+buildPhases[^}}]+)\}}',
                self.content,
                re.DOTALL
            )
            if target_block_match:
                target_block = target_block_match.group(1)
                # Find Sources phase
                sources_match = re.search(r'([A-F0-9]+)\s*/\* Sources \*/', target_block)
                if sources_match:
                    self.sources_build_phase[target_name] = sources_match.group(1)
                # Find Resources phase
                resources_match = re.search(r'([A-F0-9]+)\s*/\* Resources \*/', target_block)
                if resources_match:
                    self.resources_build_phase[target_name] = resources_match.group(1)
    
    def _generate_uuid(self) -> str:
        """Generate a unique 24-character hex UUID for Xcode."""
        while True:
            new_uuid = uuid.uuid4().hex[:24].upper()
            if new_uuid not in self.content:
                return new_uuid
    
    def _get_file_type(self, file_path: str) -> Tuple[str, str, str]:
        """
        Determine Xcode file type and build phase.
        
        Returns:
            (lastKnownFileType, fileType for comment, build_phase)
        """
        ext = Path(file_path).suffix.lower()
        
        type_mapping = {
            '.swift': ('sourcecode.swift', 'Swift', 'sources'),
            '.m': ('sourcecode.c.objc', 'Objective-C', 'sources'),
            '.mm': ('sourcecode.cpp.objcpp', 'Objective-C++', 'sources'),
            '.h': ('sourcecode.c.h', 'Header', 'sources'),
            '.c': ('sourcecode.c.c', 'C', 'sources'),
            '.cpp': ('sourcecode.cpp.cpp', 'C++', 'sources'),
            '.storyboard': ('file.storyboard', 'Storyboard', 'resources'),
            '.xib': ('file.xib', 'XIB', 'resources'),
            '.xcassets': ('folder.assetcatalog', 'Assets', 'resources'),
            '.strings': ('text.plist.strings', 'Strings', 'resources'),
            '.plist': ('text.plist.xml', 'Plist', 'resources'),
            '.json': ('text.json', 'JSON', 'resources'),
            '.xml': ('text.xml', 'XML', 'resources'),
        }
        
        return type_mapping.get(ext, ('text', 'File', 'resources'))
    
    def add_file(self, file_path: str, target_name: Optional[str] = None) -> bool:
        """
        Add a file to the Xcode project.
        
        Args:
            file_path: Path to file relative to project root
            target_name: Target to add file to (None = main target)
        
        Returns:
            True if file was added, False if already exists
        """
        # Normalize path
        file_path = file_path.replace(os.sep, '/')
        
        # Check if file already in project
        if any(file_path.endswith(ref) or ref.endswith(Path(file_path).name) for ref in self.file_references):
            return False
        
        # Determine target
        if target_name is None:
            if not self.targets:
                raise ValueError("No targets found in project")
            target_name = list(self.targets.keys())[0]
        elif target_name not in self.targets:
            raise ValueError(f"Target '{target_name}' not found. Available: {list(self.targets.keys())}")
        
        # Generate UUIDs
        file_ref_uuid = self._generate_uuid()
        build_file_uuid = self._generate_uuid()
        
        # Get file type info
        file_type, type_comment, build_phase = self._get_file_type(file_path)
        
        # Get relative path from project root
        rel_path = file_path
        file_name = Path(file_path).name
        
        # Create PBXFileReference entry
        file_ref_entry = f"\t\t{file_ref_uuid} /* {file_name} */ = {{isa = PBXFileReference; lastKnownFileType = {file_type}; path = {file_name}; sourceTree = \"<group>\"; }};\n"
        
        # Create PBXBuildFile entry
        build_file_entry = f"\t\t{build_file_uuid} /* {file_name} in Sources */ = {{isa = PBXBuildFile; fileRef = {file_ref_uuid} /* {file_name} */; }};\n"
        
        # Find insertion points
        # Insert PBXBuildFile in PBXBuildFile section
        build_file_section_match = re.search(
            r'(/\* Begin PBXBuildFile section \*/\n)',
            self.content
        )
        if build_file_section_match:
            insert_pos = build_file_section_match.end()
            self.content = self.content[:insert_pos] + build_file_entry + self.content[insert_pos:]
        
        # Insert PBXFileReference in PBXFileReference section
        file_ref_section_match = re.search(
            r'(/\* Begin PBXFileReference section \*/\n)',
            self.content
        )
        if file_ref_section_match:
            insert_pos = file_ref_section_match.end()
            self.content = self.content[:insert_pos] + file_ref_entry + self.content[insert_pos:]
        
        # Add to main group (file list)
        if self.main_group_id:
            main_group_pattern = rf'({self.main_group_id} /\* [^*]+ \*/\s*=\s*\{{[^}}]*children\s*=\s*\([^)]*)'
            main_group_match = re.search(main_group_pattern, self.content, re.DOTALL)
            if main_group_match:
                insert_pos = main_group_match.end()
                group_entry = f"\n\t\t\t\t{file_ref_uuid} /* {file_name} */,"
                self.content = self.content[:insert_pos] + group_entry + self.content[insert_pos:]
        
        # Add to appropriate build phase
        if build_phase == 'sources' and target_name in self.sources_build_phase:
            phase_uuid = self.sources_build_phase[target_name]
            phase_pattern = rf'({phase_uuid} /\* Sources \*/\s*=\s*\{{[^}}]*files\s*=\s*\([^)]*)'
            phase_match = re.search(phase_pattern, self.content, re.DOTALL)
            if phase_match:
                insert_pos = phase_match.end()
                phase_entry = f"\n\t\t\t\t{build_file_uuid} /* {file_name} in Sources */,"
                self.content = self.content[:insert_pos] + phase_entry + self.content[insert_pos:]
        
        elif build_phase == 'resources' and target_name in self.resources_build_phase:
            phase_uuid = self.resources_build_phase[target_name]
            phase_pattern = rf'({phase_uuid} /\* Resources \*/\s*=\s*\{{[^}}]*files\s*=\s*\([^)]*)'
            phase_match = re.search(phase_pattern, self.content, re.DOTALL)
            if phase_match:
                insert_pos = phase_match.end()
                phase_entry = f"\n\t\t\t\t{build_file_uuid} /* {file_name} in Resources */,"
                self.content = self.content[:insert_pos] + phase_entry + self.content[insert_pos:]
        
        # Update internal state
        self.file_references.add(file_name)
        
        return True
    
    def save(self):
        """Save modified project file."""
        with open(self.pbxproj_path, 'w', encoding='utf-8') as f:
            f.write(self.content)
    
    def list_targets(self):
        """List all targets in the project with their details."""
        if not self.targets:
            print("No targets found in project")
            return
        
        print(f"\nTargets in {self.project_path.name}:")
        print("=" * 60)
        
        for target_name in sorted(self.targets.keys()):
            target_uuid = self.targets[target_name]
            
            # Find target details
            target_pattern = rf'{target_uuid}\s*/\* {re.escape(target_name)} \*/\s*=\s*\{{([^}}]+)\}}'
            target_match = re.search(target_pattern, self.content, re.DOTALL)
            
            print(f"\n📱 {target_name}")
            print(f"   UUID: {target_uuid}")
            
            if target_match:
                target_block = target_match.group(1)
                
                # Extract product type
                product_type_match = re.search(r'productType\s*=\s*"([^"]+)"', target_block)
                if product_type_match:
                    product_type = product_type_match.group(1)
                    # Simplify product type display
                    type_map = {
                        'com.apple.product-type.application': 'Application',
                        'com.apple.product-type.framework': 'Framework',
                        'com.apple.product-type.library.static': 'Static Library',
                        'com.apple.product-type.library.dynamic': 'Dynamic Library',
                        'com.apple.product-type.bundle.unit-test': 'Unit Test Bundle',
                        'com.apple.product-type.bundle.ui-testing': 'UI Test Bundle',
                        'com.apple.product-type.app-extension': 'App Extension',
                    }
                    print(f"   Type: {type_map.get(product_type, product_type)}")
                
                # Check build phases
                has_sources = target_name in self.sources_build_phase
                has_resources = target_name in self.resources_build_phase
                phases = []
                if has_sources:
                    phases.append("Sources")
                if has_resources:
                    phases.append("Resources")
                if phases:
                    print(f"   Build Phases: {', '.join(phases)}")
        
        print("\n" + "=" * 60)
        print(f"Total: {len(self.targets)} target(s)")
        print("\nTip: Use --target <name> to specify which target to add files to")


def find_xcode_projects(start_dir: str = '.') -> List[Path]:
    """Find all .xcodeproj directories in current directory and parent directories."""
    projects = []
    current = Path(start_dir).resolve()
    
    # Check current directory
    for item in current.iterdir():
        if item.is_dir() and item.suffix == '.xcodeproj':
            projects.append(item)
    
    # If found in current dir, return immediately (most specific)
    if projects:
        return projects
    
    # Check parent directories
    for parent in current.parents:
        parent_projects = []
        for item in parent.iterdir():
            if item.is_dir() and item.suffix == '.xcodeproj':
                parent_projects.append(item)
        if parent_projects:
            return parent_projects
    
    return []


def find_xcode_project(start_dir: str = '.') -> Optional[Path]:
    """Find .xcodeproj directory, handling multiple projects."""
    projects = find_xcode_projects(start_dir)
    
    if not projects:
        return None
    
    if len(projects) == 1:
        return projects[0]
    
    # Multiple projects found - need user selection
    print("\nMultiple Xcode projects found:")
    for idx, proj in enumerate(projects, 1):
        print(f"  {idx}. {proj.name}")
    
    while True:
        try:
            choice = input("\nSelect project number (or 'q' to quit): ").strip()
            if choice.lower() == 'q':
                return None
            idx = int(choice)
            if 1 <= idx <= len(projects):
                return projects[idx - 1]
            else:
                print(f"Please enter a number between 1 and {len(projects)}")
        except (ValueError, KeyboardInterrupt):
            print("\nCancelled.")
            return None


def find_untracked_files(project_root: Path, existing_refs: Set[str]) -> List[str]:
    """Find source files not in Xcode project."""
    extensions = {'.swift', '.m', '.mm', '.h', '.c', '.cpp', '.storyboard', '.xib'}
    exclude_dirs = {'.git', '.build', 'Pods', 'Carthage', 'DerivedData', '.xcodeproj'}
    
    untracked = []
    
    for root, dirs, files in os.walk(project_root):
        # Remove excluded directories from search
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        
        for file in files:
            if Path(file).suffix in extensions:
                # Check if file is already in project
                if not any(file in ref or file == Path(ref).name for ref in existing_refs):
                    rel_path = os.path.relpath(os.path.join(root, file), project_root)
                    untracked.append(rel_path)
    
    return untracked


def main():
    parser = argparse.ArgumentParser(
        description='Automatically add new files to Xcode project',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument(
        '--project',
        help='Specific .xcodeproj to use (name or path)'
    )
    parser.add_argument(
        '--list-targets',
        action='store_true',
        help='List all targets in the project and exit'
    )
    parser.add_argument(
        '--files',
        nargs='+',
        help='Specific files to add (relative to project root)'
    )
    parser.add_argument(
        '--target',
        help='Target name to add files to (default: main target)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Preview changes without modifying project file'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose output'
    )
    
    args = parser.parse_args()
    
    # Find Xcode project
    if args.project:
        # User specified a project
        project_path = Path(args.project)
        if not project_path.suffix == '.xcodeproj':
            project_path = Path(f"{args.project}.xcodeproj")
        if not project_path.exists():
            # Try finding it in current directory
            for item in Path('.').iterdir():
                if item.name == project_path.name and item.is_dir():
                    project_path = item
                    break
            else:
                print(f"Error: Project not found: {args.project}", file=sys.stderr)
                return 1
    else:
        # Auto-detect project
        project_path = find_xcode_project()
        if not project_path:
            print("Error: No .xcodeproj found in current or parent directories", file=sys.stderr)
            print("Tip: Use --project to specify a project explicitly", file=sys.stderr)
            return 1
    
    if args.verbose:
        print(f"Found Xcode project: {project_path}")
    
    try:
        # Load project
        project = XcodeProject(str(project_path))
        
        # Handle --list-targets
        if args.list_targets:
            project.list_targets()
            return 0
        
        if args.verbose:
            print(f"Project root: {project.project_root}")
            print(f"Targets: {list(project.targets.keys())}")
            print(f"Existing file references: {len(project.file_references)}")
        
        # Determine files to add
        if args.files:
            files_to_add = args.files
        else:
            files_to_add = find_untracked_files(project.project_root, project.file_references)
        
        if not files_to_add:
            print("No files to add - all files are already in the project")
            return 3
        
        print(f"\nFiles to add ({len(files_to_add)}):")
        for file in files_to_add:
            print(f"  + {file}")
        
        if args.dry_run:
            print("\n[DRY RUN] No changes were made to the project file")
            return 0
        
        # Add files
        added_count = 0
        for file_path in files_to_add:
            if project.add_file(file_path, args.target):
                added_count += 1
                if args.verbose:
                    print(f"  Added: {file_path}")
        
        # Save project
        if added_count > 0:
            project.save()
            print(f"\n✓ Successfully added {added_count} file(s) to {project_path.name}")
        else:
            print("\n✓ No new files were added (all specified files already in project)")
        
        return 0
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 2


if __name__ == '__main__':
    sys.exit(main())
