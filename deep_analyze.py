# deep_analyze.py
import os
from collections import defaultdict


def analyze_project_structure():
    # Count files by directory and extension
    dir_counts = defaultdict(int)
    ext_counts = defaultdict(int)
    total_size_by_dir = defaultdict(int)
    total_size_by_ext = defaultdict(int)

    code_extensions = ('.py', '.yml', '.yaml', '.toml', '.cfg', '.ini')

    print("Analyzing project structure...\n")

    for root, dirs, files in os.walk('.'):
        # Get the top-level directory
        parts = root.split(os.sep)
        if len(parts) > 1:
            top_dir = parts[1]
        else:
            top_dir = "."

        for file in files:
            if any(file.endswith(ext) for ext in code_extensions):
                filepath = os.path.join(root, file)
                ext = os.path.splitext(file)[1]

                try:
                    size = os.path.getsize(filepath)
                    dir_counts[top_dir] += 1
                    ext_counts[ext] += 1
                    total_size_by_dir[top_dir] += size
                    total_size_by_ext[ext] += size
                except:
                    pass

    print("Files by top-level directory:")
    for dir_name, count in sorted(dir_counts.items(), key=lambda x: x[1], reverse=True)[:15]:
        size_mb = total_size_by_dir[dir_name] / (1024 * 1024)
        print(f"{dir_name:<30} {count:>6} files  {size_mb:>6.1f} MB")

    print("\n\nFiles by extension:")
    for ext, count in sorted(ext_counts.items(), key=lambda x: x[1], reverse=True):
        size_mb = total_size_by_ext[ext] / (1024 * 1024)
        print(f"{ext:<10} {count:>6} files  {size_mb:>6.1f} MB")

    # Find suspicious directories
    print("\n\nSuspicious directories (likely libraries):")
    lib_indicators = ['site-packages', 'lib', 'Lib', 'include', 'Include', '__pycache__',
                      'dist-packages', 'node_modules', '.eggs', 'build', 'dist']

    for root, dirs, files in os.walk('.'):
        for indicator in lib_indicators:
            if indicator in root:
                py_count = sum(1 for f in files if f.endswith('.py'))
                if py_count > 10:
                    print(f"{root}: {py_count} Python files")
                break


if __name__ == "__main__":
    analyze_project_structure()
