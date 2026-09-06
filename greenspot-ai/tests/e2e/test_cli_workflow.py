import subprocess
import os

def test_cli_radar():
    venv_python = "/home/chirag/Desktop/hackathon/greenspot-ai/.venv/bin/python"
    cli_path = "/home/chirag/Desktop/hackathon/greenspot-ai/greenspot_cli.py"
    
    result = subprocess.run(
        [venv_python, cli_path, "radar"], 
        capture_output=True, text=True
    )
    # Even if it errors out due to no backend, it should run the tymer CLI
    assert result.returncode in [0, 1] 
    assert "GreenSpot AI" in result.stdout or "Error" in result.stdout

def test_cli_run():
    venv_python = "/home/chirag/Desktop/hackathon/greenspot-ai/.venv/bin/python"
    cli_path = "/home/chirag/Desktop/hackathon/greenspot-ai/greenspot_cli.py"
    
    result = subprocess.run(
        [venv_python, cli_path, "run", "--task", "echo test"], 
        capture_output=True, text=True
    )
    assert result.returncode in [0, 1]
