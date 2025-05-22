# tasks.py

from invoke import task

@task
def build_data(ctx):
    """
    Build and preprocess association data CSV (including geocoding).
    """
    ctx.run("python -m sponsor_match.data.build_associations_csv", pty=True)

@task
def ingest_data(ctx):
    """
    Ingest the associations CSV into the MySQL database.
    """
    ctx.run("python -m sponsor_match.data.ingest_associations", pty=True)

@task(pre=[build_data, ingest_data])
def refresh_db(ctx):
    """
    Run build_data then ingest_data to refresh the database end-to-end.
    """
    # pre-tasks already ran; use ctx so the parameter isn't unused
    ctx.run("echo 'Database refresh complete.'", pty=True)

@task
def run(ctx):
    """
    Launch the Streamlit application.
    """
    ctx.run("streamlit run streamlit_app.py", pty=True)

@task
def test(ctx):
    """
    Run the test suite.
    """
    ctx.run("pytest --maxfail=1 --disable-warnings -q", pty=True)
