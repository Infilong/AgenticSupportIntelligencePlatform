SHELL := /bin/bash
ROOT_DIR := $(CURDIR)
UV ?= uv
NPM ?= npm

.PHONY: help setup setup-backend setup-frontend run test lint backend-test backend-lint frontend-install frontend-build frontend-test frontend-e2e backend-migrate

help:
	@echo "Targets: setup, run, test, lint, backend-test, backend-lint, backend-migrate, frontend-build, frontend-test, frontend-e2e"

setup: setup-backend setup-frontend

setup-backend:
	cd backend && $(UV) sync --extra dev

setup-frontend:
	cd frontend && $(NPM) install

run:
	docker compose up --build

test: backend-test frontend-test

lint: backend-lint

backend-test:
	cd backend && $(UV) run pytest -s

backend-lint:
	cd backend && $(UV) run ruff check .

backend-migrate:
	cd backend && $(UV) run alembic upgrade head

frontend-install:
	cd frontend && $(NPM) install

frontend-build:
	cd frontend && $(NPM) run build

frontend-test:
	cd frontend && $(NPM) test

frontend-e2e:
	cd frontend && $(NPM) run test:e2e
