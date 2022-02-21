#!/usr/bin/env bash

output_folder_name=tests_result
if [ -d "../${output_folder_name}" ]; then
    mv "../${output_folder_name}" "../${output_folder_name}.back"
fi
mkdir -p "../${output_folder_name}"
log_file_name=log.txt

(
    cd ../

    echo "--- Run type checking"
    pip install -r requirements-dev.txt
    mypy qr_code
    if [ $? -ne 0 ]; then
        echo
        echo --- Failed type checking. Abort tests!
        exit 1
    else
        echo
        echo --- Type checking OK!
        echo
    fi

    echo "--- Tests started on $(date)on $(hostname) ($(uname -a))"
    echo "--- Computer: $(hostname) ($(uname -a), CPU: $(nproc --all)"
    echo "--- CPU: $(nproc --all)"
    echo "--- RAM: $(free -h)"

    python_versions=("3.7 3.8 3.9 3.10")
    django_versions=("3.2.12 4.0.2")

    for python_version in ${python_versions[@]}
    do
        DOCKER_COMPOSE_COMMAND="docker-compose -f docker-compose.yml"
        for django_version in ${django_versions[@]}
        do
            ${DOCKER_COMPOSE_COMMAND} down
            build_cmd="${DOCKER_COMPOSE_COMMAND} build --build-arg PYTHON_VERSION=${python_version}"
            echo --- Build test container for Python ${python_version}: "${build_cmd}"
            ${build_cmd}

            echo --- Testing against: Python ${python_version} and Django ${django_version}

            ${DOCKER_COMPOSE_COMMAND} up -d

            echo --- Force Django version
            ${DOCKER_COMPOSE_COMMAND} exec django-qr-code pip install --upgrade "django~=${django_version}"
            echo Output code for tests with Python ${python_version} and Django ${django_version}: $?

            echo --- Setup test environment
            ${DOCKER_COMPOSE_COMMAND} exec django-qr-code python manage.py collectstatic --noinput

            # Run tests
            ${DOCKER_COMPOSE_COMMAND} exec django-qr-code python -Wd manage.py test | tee "${output_folder_name}/python_${python_version}-django_${django_version}-${log_file_name}"

            echo --- Stop containers and remove them.
            ${DOCKER_COMPOSE_COMMAND} down
         done
    done

    wait

    echo "--- Tests finished at $(date)"
) | tee "../${output_folder_name}/${log_file_name}"
