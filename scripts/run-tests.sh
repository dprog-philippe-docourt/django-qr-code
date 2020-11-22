#!/usr/bin/env bash

log_file_path=tests_result.txt
if [ -f "${log_file_path}" ]; then
    cp "${log_file_path}" "${log_file_path}.back"
fi
(
    cd ../

    echo "--- Tests started on $(date)on $(hostname) ($(uname -a))"
    echo "--- Computer: $(hostname) ($(uname -a), CPU: $(nproc --all)"
    echo "--- CPU: $(nproc --all)"
    echo "--- RAM: $(free -h)"

    python_versions=("3.6 3.7 3.8")
    django_versions=("2.2.17" "3.0.11" "3.1.3")

    for python_version in ${python_versions[@]}
    do
        DOCKER_COMPOSE_COMMAND="docker-compose -f docker-compose.yml"
        for django_version in ${django_versions[@]}
        do
            ${DOCKER_COMPOSE_COMMAND} stop
            build_cmd=${DOCKER_COMPOSE_COMMAND} build --build-arg PYTHON_VERSION=${python_version}
            echo --- Build test container for Python ${python_version}: "${build_cmd}"
            ${build_cmd}

            echo --- Testing against: Python ${python_version} and Django ${django_version}

            ${DOCKER_COMPOSE_COMMAND} up -d

            echo --- Force Django version
            ${DOCKER_COMPOSE_COMMAND} exec django-qr-code pip install "django~=${django_version}"
            echo Output code for tests with Python ${python_version} and Django ${django_version}: $?

            echo --- Setup test environment
            ${DOCKER_COMPOSE_COMMAND} exec django-qr-code python manage.py collectstatic --noinput

            # Run tests
            ${DOCKER_COMPOSE_COMMAND} exec django-qr-code python -Wd manage.py test

            echo --- Stop containers and remove them.
            ${DOCKER_COMPOSE_COMMAND} down
         done
    done

    echo "--- Tests finished at $(date)"
) | tee "${log_file_path}"
