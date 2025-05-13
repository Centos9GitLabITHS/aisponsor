# create_simple_dump.py
import os


def create_simple_dump():
    """Super simple dump - just Python files from your main directories"""

    # Just get Python files from these specific directories
    target_dirs = [
        'sponsor_match',
        'scripts',
        'app',
        '.'  # root directory files like setup.py
    ]

    with open('project_dump_simple.txt', 'w', encoding='utf-8') as f:
        f.write("SPONSORMATCHAI PROJECT DUMP\n")
        f.write("=" * 50 + "\n\n")

        file_count = 0

        for target_dir in target_dirs:
            if not os.path.exists(target_dir):
                continue

            if target_dir == '.':
                # For root, only get Python files directly in root
                files = [f for f in os.listdir('.') if f.endswith('.py')]
                if files:
                    f.write(f"\nRoot directory files:\n")
                    f.write("-" * 30 + "\n")
                    for file in files:
                        f.write(f"  {file}\n")

                    for file in files:
                        f.write(f"\n{'=' * 40}\n")
                        f.write(f"FILE: {file}\n")
                        f.write(f"{'=' * 40}\n\n")

                        try:
                            with open(file, 'r', encoding='utf-8') as src:
                                f.write(src.read())
                            file_count += 1
                        except Exception as e:
                            f.write(f"Error: {e}\n")
                        f.write("\n")
            else:
                # For other directories, walk through them
                for root, dirs, files in os.walk(target_dir):
                    # Skip __pycache__
                    if '__pycache__' in root:
                        continue

                    py_files = [f for f in files if f.endswith('.py')]
                    if py_files:
                        f.write(f"\n{root}/\n")
                        f.write("-" * 30 + "\n")
                        for file in py_files:
                            f.write(f"  {file}\n")

                        for file in py_files:
                            filepath = os.path.join(root, file)
                            f.write(f"\n{'=' * 40}\n")
                            f.write(f"FILE: {filepath}\n")
                            f.write(f"{'=' * 40}\n\n")

                            try:
                                with open(filepath, 'r', encoding='utf-8') as src:
                                    f.write(src.read())
                                file_count += 1
                            except Exception as e:
                                f.write(f"Error: {e}\n")
                            f.write("\n")

    size = os.path.getsize('project_dump_simple.txt')
    print(f"Created project_dump_simple.txt")
    print(f"Included {file_count} Python files")
    print(f"Size: {size / 1024:.1f} KB")


if __name__ == "__main__":
    create_simple_dump()
