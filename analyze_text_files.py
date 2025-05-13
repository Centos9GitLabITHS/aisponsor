# create_selective_dump.py
import os
from pathlib import Path


def create_selective_dump(output_file='project_dump_selective.txt'):
    # Only include actual source code files
    code_extensions = ('.py', '.yml', '.yaml', '.toml', '.cfg', '.ini')
    exclude_dirs = {'venv', '.venv312', '__pycache__', '.git', '.idea', 'build', 'dist'}
    max_file_size = 500 * 1024  # 500KB max per file

    included_count = 0
    excluded_count = 0

    with open(output_file, 'w', encoding='utf-8') as f:
        # Write project structure first
        f.write("PROJECT STRUCTURE:\n")
        f.write("=" * 50 + "\n\n")

        for root, dirs, files in os.walk('.'):
            dirs[:] = [d for d in dirs if d not in exclude_dirs]

            level = root.replace('.', '').count(os.sep)
            indent = '  ' * level
            dir_name = os.path.basename(root) or 'SponsorMatchAI'
            f.write(f'{indent}{dir_name}/\n')

            sub_indent = '  ' * (level + 1)
            for file in files:
                if any(file.endswith(ext) for ext in code_extensions):
                    f.write(f'{sub_indent}{file}\n')

        f.write("\n\nFILE CONTENTS:\n")
        f.write("=" * 50 + "\n\n")

        # Write file contents
        for root, dirs, files in os.walk('.'):
            dirs[:] = [d for d in dirs if d not in exclude_dirs]

            for file in files:
                if any(file.endswith(ext) for ext in code_extensions):
                    file_path = os.path.join(root, file)
                    relative_path = os.path.relpath(file_path, '.')

                    try:
                        file_size = os.path.getsize(file_path)

                        if file_size > max_file_size:
                            f.write(f"\n{'=' * 30}\n")
                            f.write(f"FILE: {relative_path} (EXCLUDED - {file_size // 1024}KB)\n")
                            f.write(f"{'=' * 30}\n\n")
                            excluded_count += 1
                            continue

                        f.write(f"\n{'=' * 30}\n")
                        f.write(f"FILE: {relative_path}\n")
                        f.write(f"{'=' * 30}\n\n")

                        with open(file_path, 'r', encoding='utf-8') as source_file:
                            f.write(source_file.read())

                        included_count += 1

                    except Exception as e:
                        f.write(f"Error reading file: {e}\n")

                    f.write("\n")

    print(f"Created {output_file}")
    print(f"Included files: {included_count}")
    print(f"Excluded large files: {excluded_count}")

    # Check final size
    dump_size = os.path.getsize(output_file)
    print(f"Dump size: {dump_size // 1024 // 1024}MB")


# Also create a list of large files that were excluded
def list_excluded_files():
    with open('excluded_files.txt', 'w') as f:
        f.write("Large files excluded from dump:\n\n")

        for root, dirs, files in os.walk('.'):
            dirs[:] = [d for d in dirs if d not in {'venv', '.venv312', '__pycache__', '.git'}]

            for file in files:
                if file.endswith(('.json', '.csv', '.txt', '.md')):
                    file_path = os.path.join(root, file)
                    try:
                        size = os.path.getsize(file_path)
                        if size > 500 * 1024:  # >500KB
                            f.write(f"{file_path}: {size // 1024}KB\n")
                    except:
                        pass


if __name__ == "__main__":
    create_selective_dump()
    list_excluded_files()
