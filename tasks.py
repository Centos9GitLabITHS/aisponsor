from invoke import task

@task
def setup(c):
    """Install package and development dependencies."""
    c.run("pip install -e '.[dev]'")

@task
def data(c):
    """Run data ingestion pipelines."""
    # Build associations CSV with coordinates
    c.run("python -m scripts.build_associations_csv data/associations_goteborg.csv")
    # Ingest company data from CSV
    c.run("python -m sponsor_match.data.ingest_csv")
    # Ingest club associations into the database
    c.run("python -m sponsor_match.data.ingest_associations data/associations_goteborg_with_coords.csv")

@task
def train(c):
    """Train K-Means clustering models."""
    c.run("python -m sponsor_match.models.clustering")

@task
def app(c):
    """Launch the Streamlit application."""
    c.run("streamlit run sponsor_match/app_v2.py", pty=True)
