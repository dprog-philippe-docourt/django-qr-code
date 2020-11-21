#!/usr/bin/env bash
cd ..

echo --- Build stage test container
docker-compose down
docker-compose build --build-arg PYTHON_VERSION=3.8

echo --- Fire up staging site
docker-compose up -d --remove-orphans

echo --- Listing containers
docker-compose ps
