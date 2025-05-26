#!/usr/bin/env python3
"""Diagnose and fix SQL execution issues in SponsorMatch AI"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import text, inspect
from sponsor_match.core.db import get_engine


def diagnose_sql_issues():
    """Diagnose SQL execution problems"""
    print("🔍 Diagnosing SQL execution issues...")

    engine = get_engine()

    # Test 1: Basic connection
    try:
        with engine.connect() as conn:
            # This should work with text()
            result = conn.execute(text("SELECT 1"))
            print("✅ Basic SQL execution works")
    except Exception as e:
        print(f"❌ Basic SQL failed: {e}")
        print("   This indicates a fundamental connection issue")
        return False

    # Test 2: Table queries
    try:
        with engine.connect() as conn:
            # Get table names
            inspector = inspect(engine)
            tables = inspector.get_table_names()
            print(f"✅ Found tables: {tables}")

            # Test each table
            for table in tables:
                try:
                    result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                    count = result.scalar()
                    print(f"✅ Table '{table}' has {count} records")
                except Exception as e:
                    print(f"❌ Error querying table '{table}': {e}")
    except Exception as e:
        print(f"❌ Table inspection failed: {e}")
        return False

    # Test 3: Pandas integration
    try:
        import pandas as pd
        with engine.connect() as conn:
            df = pd.read_sql(text("SELECT * FROM associations LIMIT 5"), conn)
            print(f"✅ Pandas integration works, loaded {len(df)} associations")
    except Exception as e:
        print(f"❌ Pandas SQL failed: {e}")
        return False

    return True


def fix_sql_in_file(filepath):
    """Fix SQL execution issues in a Python file"""
    print(f"\n📝 Fixing SQL in {filepath}...")

    with open(filepath, 'r') as f:
        content = f.read()

    # Count fixes needed
    fixes_needed = 0

    # Pattern 1: conn.execute("SELECT...")
    if 'conn.execute("SELECT' in content or "conn.execute('SELECT" in content:
        fixes_needed += content.count('conn.execute("SELECT') + content.count("conn.execute('SELECT")

    # Pattern 2: conn.execute(f"SELECT...")
    if 'conn.execute(f"SELECT' in content or "conn.execute(f'SELECT" in content:
        fixes_needed += content.count('conn.execute(f"SELECT') + content.count("conn.execute(f'SELECT")

    # Pattern 3: pd.read_sql("SELECT...")
    if 'pd.read_sql("SELECT' in content or "pd.read_sql('SELECT" in content:
        fixes_needed += content.count('pd.read_sql("SELECT') + content.count("pd.read_sql('SELECT")

    if fixes_needed == 0:
        print(f"✅ No SQL fixes needed in {filepath}")
        return

    print(f"⚠️ Found {fixes_needed} SQL statements that need text() wrapper")

    # Apply fixes
    import re

    # Add import if not present
    if 'from sqlalchemy import' in content and 'text' not in content.split('from sqlalchemy import')[1].split('\n')[0]:
        content = content.replace('from sqlalchemy import', 'from sqlalchemy import text,')
    elif 'from sqlalchemy import' not in content:
        # Add import after other imports
        lines = content.split('\n')
        import_idx = 0
        for i, line in enumerate(lines):
            if line.startswith('import ') or line.startswith('from '):
                import_idx = i
        lines.insert(import_idx + 1, 'from sqlalchemy import text')
        content = '\n'.join(lines)

    # Fix patterns
    content = re.sub(r'conn\.execute\(("SELECT[^"]+"|\'SELECT[^\']+\')\)', r'conn.execute(text(\1))', content)
    content = re.sub(r'conn\.execute\((f"SELECT[^"]+"|f\'SELECT[^\']+\')\)', r'conn.execute(text(\1))', content)
    content = re.sub(r'pd\.read_sql\(("SELECT[^"]+"|\'SELECT[^\']+\'),', r'pd.read_sql(text(\1),', content)
    content = re.sub(r'pd\.read_sql\((f"SELECT[^"]+"|f\'SELECT[^\']+\'),', r'pd.read_sql(text(\1),', content)

    # Write back
    with open(filepath, 'w') as f:
        f.write(content)

    print(f"✅ Fixed SQL statements in {filepath}")


def main():
    print("🔧 SQL Execution Diagnostic and Fix Tool")
    print("=" * 50)

    # Run diagnostics
    if diagnose_sql_issues():
        print("\n✅ SQL execution is working correctly!")
    else:
        print("\n❌ SQL execution issues detected")
        print("\nPossible solutions:")
        print("1. Ensure all SQL queries are wrapped with text()")
        print("2. Check SQLAlchemy version (2.0+ requires text())")
        print("3. Verify database connection string")

    # Fix common files
    print("\n🔧 Checking and fixing common files...")

    files_to_check = [
        'sponsor_match/utils/check_db.py',
        'sponsor_match/services/service.py',
        'sponsor_match/ml/pipeline.py',
        'sponsor_match/utils/setup_database.py',
        'sponsor_match/utils/train_clustering_models.py'
    ]

    for file_path in files_to_check:
        full_path = Path(file_path)
        if full_path.exists():
            fix_sql_in_file(full_path)
        else:
            print(f"⚠️ File not found: {file_path}")

    print("\n✅ SQL fix complete!")
    print("\nNext steps:")
    print("1. Run: python fix_all.py")
    print("2. Then: streamlit run sponsor_match/ui/simple_app.py")


if __name__ == "__main__":
    main()
