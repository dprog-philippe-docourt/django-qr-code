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

    python_versions=("3.4" "3.5" "3.6")
    django_versions=("1.8.18" "1.10.7" "1.11.4")

    for python_version in ${python_versions[@]}
    do
        DOCKER_COMPOSE_COMMAND="docker-compose -f docker-compose-${python_version}.yml"

        cp "docker-compose.yml" "docker-compose-${python_version}.yml"
        sed -i "s/dockerfile: Dockerfile/dockerfile: Dockerfile-${python_version}/" "docker-compose-${python_version}.yml"
        cp "Dockerfile" "Dockerfile-${python_version}"
        sed -i "s/FROM python:3.6/FROM python:${python_version}/" "Dockerfile-${python_version}"

        for django_version in ${django_versions[@]}
        do
            echo --- Testing against: Python ${python_version} and Django ${django_version}

            echo --- Build test container
            ${DOCKER_COMPOSE_COMMAND} stop && ${DOCKER_COMPOSE_COMMAND} build

            echo --- Force Django version
            ${DOCKER_COMPOSE_COMMAND} run --rm --entrypoint "pip" django-qr-code install "django~=${django_version}"

            echo --- Setup test site
            ${DOCKER_COMPOSE_COMMAND} run --rm --entrypoint "python" django-qr-code manage.py collectstatic --noinput

            # Run tests
            ${DOCKER_COMPOSE_COMMAND} run --rm --entrypoint "python" django-qr-code manage.py test

            echo --- Stop container
            ${DOCKER_COMPOSE_COMMAND} stop
         done

         rm "docker-compose-${python_version}.yml" "Dockerfile-${python_version}"
    done

    echo "--- Tests finished at $(date)"
) | tee "${log_file_path}"