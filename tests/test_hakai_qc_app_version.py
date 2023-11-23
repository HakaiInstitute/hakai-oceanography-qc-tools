from pathlib import Path

from hakai_qc_app.__version__ import __version__


def test_versions():
    pyproject = Path(__file__).parent / ".." / "pyproject.toml"
    assert pyproject.exists(), "Unable to retrieve pyproject.toml"
    pyproject_content = pyproject.read_text()
    version = f'version = "{__version__}"'
    assert version in pyproject_content, f"{version} is missing from pyproject.toml"
