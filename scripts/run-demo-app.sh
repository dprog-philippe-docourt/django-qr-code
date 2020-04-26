#!/usr/bin/env bash
(
    cd ../

    DOCKER_COMPOSE_COMMAND='docker-compose -f docker-compose.yml'

    echo --- Build stage test container
    ${DOCKER_COMPOSE_COMMAND} stop && ${DOCKER_COMPOSE_COMMAND} --build-arg PYTHON_VERSION=3.8 build

    echo --- Fire up staging site
    ${DOCKER_COMPOSE_COMMAND} up -d --remove-orphans

    echo --- Listing containers
    ${DOCKER_COMPOSE_COMMAND} ps
)