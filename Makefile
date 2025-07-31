# Simple Makefile for Decision Layer

.PHONY: help install test format lint clean

help:
	@echo "Available commands:"
	@echo "  install  - Install dependencies"
	@echo "  test     - Run tests"
	@echo "  format   - Format code with black and isort"
	@echo "  lint     - Run linting with flake8"
	@echo "  clean    - Clean up generated files"

install:
	pip install -e ".[dev]"

test:
	python3 -m pytest tests/

format:
	python3 -m black decision_layer tests

lint:
	python3 -m flake8 decision_layer tests

clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
