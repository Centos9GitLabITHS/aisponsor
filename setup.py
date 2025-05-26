from setuptools import setup, find_packages

setup(
    name="golden_goal",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "streamlit",
        "pandas",
        "numpy",
        "folium",
        "streamlit-folium",
        "plotly",
        "sqlalchemy",
        "pymysql",
        "scikit-learn",
        "joblib",
    ],
)
