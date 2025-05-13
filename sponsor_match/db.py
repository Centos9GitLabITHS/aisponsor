# sponsor_match/db.py
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
import os
from dotenv import load_dotenv

load_dotenv()                    # read .env in project root if present

def get_engine() -> Engine:
    url = (
        f"mysql+mysqlconnector://{os.getenv('MYSQL_USER', 'sponsor_user')}:"
        f"{os.getenv('MYSQL_PASSWORD', 'Sports-2025?!')}@"
        f"{os.getenv('MYSQL_HOST', 'localhost')}:"
        f"{os.getenv('MYSQL_PORT', '3306')}/"
        f"{os.getenv('MYSQL_DB', 'sponsor_registry')}"
    )
    return create_engine(url, pool_pre_ping=True)
