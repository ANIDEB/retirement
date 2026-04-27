import subprocess
import sys

from main import main


def test_main_prints_hello_world(capsys):
    main()
    captured = capsys.readouterr()
    assert captured.out == "Hello, World!\n"


def test_main_as_script():
    result = subprocess.run(
        [sys.executable, "main.py"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert result.stdout == "Hello, World!\n"
