#!/usr/bin/env bash


log_file_path=tests_result.txt
if [ -f "${log_file_path}" ]; then
    cp "${log_file_path}" "${log_file_path}.back"
fi
(
    echo "--- Tests started on $(date)on $(hostname) ($(uname -a))"
    echo "--- Computer: $(hostname) ($(uname -a), CPU: $(nproc --all)"
    echo "--- CPU: $(nproc --all)"
    echo "--- RAM: $(free -h)"

    DOCKER_COMPOSE_COMMAND='docker-compose -f docker-compose.yml'

    echo --- Build stage test container
    ${DOCKER_COMPOSE_COMMAND} stop && ${DOCKER_COMPOSE_COMMAND} build

    echo --- Generate stage test site
    ${DOCKER_COMPOSE_COMMAND} run --rm --entrypoint "python" django-qr-code manage.py collectstatic --noinput

    # Run tests
    ${DOCKER_COMPOSE_COMMAND} run --rm --entrypoint python django-qr-code manage.py test

    echo --- Stop containers
    ${DOCKER_COMPOSE_COMMAND} stop

    echo "--- Tests finished at $(date)"
) | tee "${log_file_path}"