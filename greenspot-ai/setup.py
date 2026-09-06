from setuptools import setup, find_packages

setup(
    name="greenspot-ai",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "typer>=0.12.0",
        "rich>=13.0.0",
        "fastapi>=0.110.0",
        "uvicorn>=0.28.0",
        "pydantic>=2.6.0",
        "httpx>=0.27.0",
        "tenacity>=8.2.0",
        "numpy>=1.26.0",
        "boto3>=1.26.0",
    ],
    entry_points={
        "console_scripts": [
            "greenspot=greenspot.cli.main:app",
        ],
    },
)
