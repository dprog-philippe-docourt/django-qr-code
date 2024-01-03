#!/usr/bin/env bash
set -e

cd ..

echo --- Build stage test container
docker-compose down || true
docker-compose build --build-arg PYTHON_VERSION=3.11

echo --- Fire up staging site
docker-compose up -d --remove-orphans

echo --- Listing containers
docker-compose ps
