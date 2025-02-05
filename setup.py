"""
Author: Anton Pastoriza & Jose Luis Martin
"""

from setuptools import setup, find_packages


def parse_requirements(filename: str):
    """Load requirements from a pip requirements file."""
    line_iter = (line.strip() for line in open(filename, encoding="utf-8"))
    return [line for line in line_iter if line and not line.startswith("#")]


setup(
    packages=find_packages(),  # Automatically discover all packages and sub-packages
    include_package_data=True,
    install_requires=parse_requirements("requirements.txt"),
    entry_points={
        "console_scripts": [
            # Add console script entry points here
        ]
    }
)
