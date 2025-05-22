import pandas as pd
import pytest

from sponsor_match.models.clustering import train, load_model, predict


@pytest.fixture(autouse=True)
def clear_env(monkeypatch):
    # Ensure clustering environment variables are set for the test
    monkeypatch.setenv("N_CLUSTERS", "2")
    monkeypatch.setenv("CLUSTER_RANDOM_STATE", "42")
    return monkeypatch

def test_train_and_persistence(tmp_path, clear_env):
    # Build a tiny CSV with two distinct points
    csv_path = tmp_path / "points.csv"
    df = pd.DataFrame({
        "latitude": [0.0, 10.0],
        "longitude": [0.0, 10.0],
    })
    df.to_csv(csv_path, index=False)

    # Point the model directory into tmp_path
    model_file = tmp_path / "kmeans_test.pkl"
    # Call train()
    train(input_csv=csv_path, model_file=model_file)

    # The model file must exist
    assert model_file.exists()

    # Load it back
    model = load_model(model_file)
    assert hasattr(model, "predict")

    # Predictions should return a valid cluster label (0 or 1)
    label0 = predict(0.0, 0.0, model)
    label1 = predict(10.0, 10.0, model)
    assert isinstance(label0, int) and label0 in (0, 1)
    assert isinstance(label1, int) and label1 in (0, 1)
    # The two extreme points should not be in the same cluster
    assert label0 != label1
