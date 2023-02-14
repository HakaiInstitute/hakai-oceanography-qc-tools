from setuptools import setup

setup(
    name="hakai_qc",
    version="1.0",
    description="Sets of tools used to qc hakai datasets",
    author="Jessy Barrette",
    author_email="jessy.barrette@hakai.org",
    packages=["hakai_qc"],
    install_requires=[
        "hakai_api",
        "pandas",
        "plotly",
        "ipywidgets",
        "ioos_qc==2.1",
        "openpyxl",
    ],
)
