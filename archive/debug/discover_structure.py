# discover_structure.py
"""
Module Structure Discovery Tool

Parses the project directory to list Python modules, classes, functions, and imports,
helping to diagnose import errors in test scripts.
"""
import ast  # Abstract Syntax Tree parsing
import json  # For outputting structure as JSON
import os  # For directory traversal
import sys  # To modify import path
from pathlib import Path  # Object-oriented filesystem paths

# Ensure project root is on sys.path so imports resolve correctly
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def find_python_files(directory):
    """Recursively find all .py files, skipping virtual envs and caches."""
    python_files = []
    for root, dirs, files in os.walk(directory):
        # Exclude typical non-source directories
        dirs[:] = [d for d in dirs if d not in {'venv', '.venv', '__pycache__', '.git'}]
        for file in files:
            if file.endswith('.py'):
                python_files.append(Path(root) / file)
    return python_files


def analyze_file(filepath):
    """Parse a Python file to extract its classes, functions, and import statements."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        tree = ast.parse(content)

        functions, classes, imports = [], [], []
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                functions.append(node.name)
            elif isinstance(node, ast.ClassDef):
                classes.append(node.name)
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.append(f"from {node.module}")
        return {'functions': functions, 'classes': classes, 'imports': imports}
    except Exception as e:
        return {'error': str(e)}


def main():
    """Main routine: scan project structure and report key components."""
    print("SponsorMatchAI Structure Discovery")
    golden_goal_dir = project_root / 'golden_goal'
    if not golden_goal_dir.exists():
        print(f"Error: golden_goal directory not found at {golden_goal_dir}")
        return

    python_files = find_python_files(golden_goal_dir)
    structure = {}
    # Analyze each file
    for file in python_files:
        rel = file.relative_to(project_root)
        result = analyze_file(file)
        if 'error' not in result:
            structure[str(rel)] = result
            print(f"\n{rel}")
            if result['classes']:
                print(f"  Classes: {', '.join(result['classes'][:5])}")
            if result['functions']:
                funcs = result['functions']
                print(f"  Functions: {', '.join(funcs[:5])}" + (f" ... and {len(funcs)-5} more" if len(funcs)>5 else ""))

    # Search for essential components by keyword patterns
    print("\nSearching for key components:")
    key_patterns = {
        'database': ['db', 'database', 'connection'],
        'config': ['config', 'settings', 'Config'],
        'distance': ['distance', 'haversine'],
        'matching': ['match', 'matcher', 'search'],
        'streamlit': ['app', 'ui', 'streamlit'],
        'ingest': ['ingest', 'import', 'parse']
    }
    for component, patterns in key_patterns.items():
        print(f"\n{component.upper()}:")
        found = False
        for path, info in structure.items():
            for pat in patterns:
                if pat in path.lower() or any(pat in fn.lower() for fn in info.get('functions', [])) or any(pat in cls.lower() for cls in info.get('classes', [])):
                    print(f"  Found '{pat}' in {path}")
                    found = True
                    break
        if not found:
            print("  Not found - this component might not exist")

    # Save the full structure for reference
    output_file = Path(__file__).parent / 'project_structure.json'
    with open(output_file, 'w') as f:
        json.dump(structure, f, indent=2)
    print(f"\nStructure saved to: {output_file}")


if __name__ == "__main__":
    main()
