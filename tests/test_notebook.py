from pathlib import Path
import pytest
nbformat = pytest.importorskip("nbformat")
nbclient = pytest.importorskip("nbclient")
NOTEBOOK = Path(__file__).resolve().parents[1] / "notebooks" / "analysis.ipynb"

def test_notebook_runs_without_errors():
    notebook = nbformat.read(NOTEBOOK, as_version=4)
    client = nbclient.NotebookClient(
        notebook,
        timeout=180,
        kernel_name="python3",
        resources={"metadata": {"path": str(NOTEBOOK.parent)}},
    )
    client.execute()