import subprocess
import sys
from unittest.mock import patch

from main import main


def test_main_runs_projection(capsys):
    main()
    captured = capsys.readouterr()
    assert "Projection complete" in captured.out
    assert "30 years" in captured.out


def test_main_as_script():
    result = subprocess.run(
        [sys.executable, "main.py"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "Projection complete" in result.stdout
