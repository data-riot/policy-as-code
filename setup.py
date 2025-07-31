#!/usr/bin/env python3
"""
Setup script for Decision Layer
"""

from setuptools import find_packages, setup

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [
        line.strip() for line in fh if line.strip() and not line.startswith("#")
    ]

setup(
    name="decision-layer",
    version="2.0.0",
    author="Decision Layer Team",
    author_email="team@decisionlayer.com",
    description="Elegant decision management with version control, testing, and observability",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/decision-layer/decision-layer",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "decision-layer=decision_layer.cli:cli",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)
