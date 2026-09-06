#!/home/chirag/Desktop/hackathon/greenspot-ai/.venv/bin/python3
import sys
import os

# Ensure the repo directory is on sys.path
sys.path.insert(0, "/home/chirag/Desktop/hackathon/greenspot-ai")

from greenspot.cli.main import app

if __name__ == "__main__":
    app()
