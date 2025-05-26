# This script has been annotated with comments in British English.
# Detailed comments explaining each section have been added as requested.

import pytest
from sqlalchemy import create_engine, text

from golden_goal import search, recommend


@pytest.fixture
def engine(tmp_path, monkeypatch):
    """
    Create an in-memory SQLite engine with minimal schema and sample data.
    """
    # Use SQLite in-memory for tests
    engine = create_engine("sqlite:///:memory:")

    # Create tables
    with engine.begin() as conn:
        conn.execute(text("""
            CREATE TABLE clubs (
                id INTEGER PRIMARY KEY,
                name TEXT,
                address TEXT,
                latitude REAL,
                longitude REAL
            )
        """))
        conn.execute(text("""
            CREATE TABLE sponsors (
                id INTEGER PRIMARY KEY,
                name TEXT,
                latitude REAL,
                longitude REAL,
                preferred_cluster INTEGER
            )
        """))

        # Insert one club and one sponsor
        conn.execute(text("""
            INSERT INTO clubs (id, name, address, latitude, longitude)
            VALUES (1, 'Test Club', '123 Main St', 10.0, 20.0)
        """))
        conn.execute(text("""
            INSERT INTO sponsors (id, name, latitude, longitude, preferred_cluster)
            VALUES (1, 'Test Sponsor', 10.1, 20.1, NULL)
        """))

    # Monkey-patch get_engine if your code calls it directly
    monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")
    return engine

def test_search_finds_club_and_sponsor(engine, monkeypatch):
    # If your search() calls get_engine(), patch it; otherwise pass engine directly
    # monkeypatch.setattr("golden_goal.services.service.get_engine", lambda: engine)

    # Search for "Test" should return the club entry
    df = search(engine, "Test")
    assert not df.empty
    assert "Test Club" in df["name"].values

def test_recommend_no_match_returns_empty(engine):
    # Nonexistent club name should yield empty DataFrame
    df = recommend(engine, "No Such Club", top_n=5)
    assert df.empty

def test_recommend_fallback_by_distance(engine, monkeypatch):
    # Force clustering to fail so fallback logic kicks in
    monkeypatch.setattr("golden_goal.services.service.load_model", lambda: None)
    monkeypatch.setattr("golden_goal.services.service.predict", lambda lat, lon, model=None: None)

    df = recommend(engine, "Test Club", top_n=1)
    assert not df.empty
    # Should compute a 'distance' column
    assert "distance" in df.columns
    # The nearest sponsor (only one) should appear
    assert df.iloc[0]["name"] == "Test Sponsor"
