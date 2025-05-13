"""
Load a club CSV (with lat/lon) into MariaDB table `clubs`.
id is PRIMARY KEY, so re-running is idempotent.
"""
import pathlib, pandas as pd, sqlalchemy as sa
from sponsor_match.db import get_engine

def main(csv_file: str):
    df = pd.read_csv(csv_file)
    eng = get_engine()
    with eng.begin() as con:
        con.exec_driver_sql("""
        CREATE TABLE IF NOT EXISTS clubs(
          id           INT PRIMARY KEY,
          name         TEXT,
          member_count INT,
          address      TEXT,
          size_bucket  ENUM('small','medium','large'),
          lat          DOUBLE,
          lon          DOUBLE
        ) CHARACTER SET utf8mb4""")

        df.to_sql("clubs", con, if_exists="replace", index=False)  # overwrite whole table

if __name__ == "__main__":
    main("data/associations_goteborg_with_coords.csv")
