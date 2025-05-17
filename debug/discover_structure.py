# debug/discover_structure.py
"""
Module Structure Discovery Tool

This script helps identify the actual structure of your SponsorMatchAI project
so we can fix import errors in the test scripts.
"""

import os
import sys
from pathlib import Path
import ast
import json

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def find_python_files(directory):
    """Find all Python files in the directory"""
    python_files = []
    for root, dirs, files in os.walk(directory):
        # Skip virtual environments and cache
        dirs[:] = [d for d in dirs if d not in {'venv', '.venv', '__pycache__', '.git'}]
        for file in files:
            if file.endswith('.py'):
                python_files.append(Path(root) / file)
    return python_files


def analyze_file(filepath):
    """Analyze a Python file to find classes and functions"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        tree = ast.parse(content)

        functions = []
        classes = []
        imports = []

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                functions.append(node.name)
            elif isinstance(node, ast.ClassDef):
                classes.append(node.name)
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.append(f"from {node.module}")

        return {
            'functions': functions,
            'classes': classes,
            'imports': imports
        }
    except Exception as e:
        return {'error': str(e)}


def main():
    print("SponsorMatchAI Structure Discovery")
    print("=" * 40)

    sponsor_match_dir = project_root / 'sponsor_match'

    if not sponsor_match_dir.exists():
        print(f"Error: sponsor_match directory not found at {sponsor_match_dir}")
        return

    print(f"Analyzing {sponsor_match_dir}...\n")

    # Find all Python files
    python_files = find_python_files(sponsor_match_dir)

    # Analyze structure
    structure = {}

    for file in python_files:
        relative_path = file.relative_to(project_root)
        analysis = analyze_file(file)

        if 'error' not in analysis:
            structure[str(relative_path)] = analysis
            print(f"\n{relative_path}")

            if analysis['classes']:
                print(f"  Classes: {', '.join(analysis['classes'][:5])}")

            if analysis['functions']:
                print(f"  Functions: {', '.join(analysis['functions'][:5])}")
                if len(analysis['functions']) > 5:
                    print(f"    ... and {len(analysis['functions']) - 5} more")

    # Look for specific modules we need
    print("\n\nSearching for key components:")
    print("-" * 30)

    key_patterns = {
        'database': ['db', 'database', 'connection'],
        'config': ['config', 'settings', 'Config'],
        'distance': ['distance', 'calculate_distance', 'haversine'],
        'matching': ['match', 'matcher', 'find_matches', 'search'],
        'streamlit': ['app', 'ui', 'streamlit'],
        'ingest': ['ingest', 'import', 'parse']
    }

    for component, patterns in key_patterns.items():
        print(f"\n{component.upper()}:")
        found = False
        for filepath, content in structure.items():
            for pattern in patterns:
                if pattern in filepath.lower():
                    print(f"  File: {filepath}")
                    found = True
                    break

                for func in content.get('functions', []):
                    if pattern in func.lower():
                        print(f"  Function '{func}' in {filepath}")
                        found = True

                for cls in content.get('classes', []):
                    if pattern in cls.lower():
                        print(f"  Class '{cls}' in {filepath}")
                        found = True

        if not found:
            print(f"  Not found - this component might not exist")

    # Save the structure for reference
    output_file = Path(__file__).parent / 'project_structure.json'

    with open(output_file, 'w') as f:
        json.dump(structure, f, indent=2)

    print(f"\n\nStructure saved to: {output_file}")
    print("\nNext steps:")
    print("1. Share the output with me")
    print("2. I'll create corrected versions of the test scripts")
    print("3. We'll fix the import errors properly")


if __name__ == "__main__":
    main()
