# sponsor_match/db_init.py
from textwrap import dedent
from sponsor_match.db import get_engine

eng = get_engine()          # ← we call it “eng”

DDL = dedent("""
    CREATE TABLE IF NOT EXISTS clubs (
        id INT PRIMARY KEY AUTO_INCREMENT,
        name         VARCHAR(120),
        size_bucket  ENUM('small','medium','large'),
        lat  DOUBLE, lon DOUBLE
    ) CHARACTER SET utf8mb4;

    CREATE TABLE IF NOT EXISTS companies (
        id INT PRIMARY KEY AUTO_INCREMENT,
        orgnr        CHAR(10),
        name         VARCHAR(200),
        revenue_ksek DOUBLE,
        employees    INT,
        year         INT,
        rev_per_emp  DOUBLE,
        size_bucket  ENUM('small','medium','large'),
        industry     VARCHAR(120),
        lat  DOUBLE, lon DOUBLE
    ) CHARACTER SET utf8mb4;
""")

if __name__ == "__main__":
    with eng.begin() as conn:          # ← use “eng”, not “engine”
        for stmt in DDL.strip().split(";"):
            if stmt.strip():
                conn.exec_driver_sql(stmt)
    print("✅  MySQL tables ready")
