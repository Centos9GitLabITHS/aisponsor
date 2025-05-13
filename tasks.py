from invoke import task, run

@task
def setup(c):           c.run("pip install -e '.[dev]'")

@task
def data(c):
    c.run("python -m scripts.build_associations_csv data/associations_goteborg.csv")
    c.run("python -m sponsor_match.ingest_excel")
    c.run("python -m sponsor_match.ingest_associations data/associations_goteborg_with_coords.csv")

@task
def train(c):
    c.run("python -m sponsor_match.clustering")

@task
def app(c):
    c.run("streamlit run sponsor_match/app.py", pty=True)
