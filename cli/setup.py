from setuptools import setup, find_packages

setup(
    name="edqmp",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "typer>=0.9.0",
        "rich>=13.7.0",
        "httpx>=0.26.0",
        "pyyaml>=6.0.1",
    ],
    entry_points={
        "console_scripts": [
            "edqmp=edqmp.main:app",
        ],
    },
    python_requires=">=3.9",
)
