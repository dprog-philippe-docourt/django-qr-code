#!/usr/bin/env bash

# Move to project root dir.
cd "$(dirname "$0")/.." && scripts_dir="$(pwd)/scripts"

output_folder_name=tests_result
if [ -d "${output_folder_name}" ]; then
    mv "${output_folder_name}" "${output_folder_name}.back"
fi
mkdir -p "${output_folder_name}"
log_file_name=log.txt

echo "--- Run type checking"
pip install -r requirements-dev.txt
mypy qr_code || (echo "mypy" >> ${output_folder_name}/fail.flag)

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

python_versions=("3.10 3.11 3.12")
django_versions=("4.2.13 5.0.6")

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
        ${DOCKER_COMPOSE_COMMAND} exec django-qr-code pip install --upgrade "django~=${django_version}" || (echo "pip install - Python: ${python_version}, Django: ${django_version}" >> ${output_folder_name}/fail.flag)
        echo Output code for tests with Python ${python_version} and Django ${django_version}: $?

        echo --- Setup test environment
        ${DOCKER_COMPOSE_COMMAND} exec django-qr-code python manage.py collectstatic --noinput || (echo "collectstatic - Python: ${python_version}, Django: ${django_version}" >> ${output_folder_name}/fail.flag)

        # Run tests
        (${DOCKER_COMPOSE_COMMAND} exec django-qr-code python -Wd manage.py test || (echo "test - Python: ${python_version}, Django: ${django_version}" >> ${output_folder_name}/fail.flag)) | tee "${output_folder_name}/python_${python_version}-django_${django_version}-${log_file_name}"

        echo --- Stop containers and remove them.
        ${DOCKER_COMPOSE_COMMAND} down
     done
done

wait

echo
echo --- End of tests at $(date)
echo

success=false
if [ -f "${output_folder_name}/fail.flag" ]; then
  success=false
  error_msg=$(<"${output_folder_name}/fail.flag")
  rm -f "${output_folder_name}/fail.flag"
  echo "--- Fail to run some of the tests! Error(s) in:"
  echo "${error_msg}"
  cat "${output_folder_name}/"*${log_file_name} | grep "FAILED"
else
  cat "${output_folder_name}/"*${log_file_name} | grep "FAILED" || success=true
fi
cat "${output_folder_name}/"*${log_file_name} | grep "Ran "
cat "${output_folder_name}/"*${log_file_name} | grep -A 40 -B 1 "ERROR:"
cat "${output_folder_name}/"*${log_file_name} | grep -A 20 -B 1 "FAILURE:"

if [ "${success}" == "false" ]; then
  echo --- Tests failed!
  exit 2
else
  echo --- Tests success!
fi
