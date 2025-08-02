# Contributing to Django QR-Code

Thank you for considering contributing to this project! Contributions from the community help us improve and maintain this extension. Please follow these guidelines for an effective and smooth collaboration.

## How to Contribute

### 1. Fork and Clone

* Fork the repository.
* Clone your fork to your local machine:

```sh
git clone https://github.com/dprog-philippe-docourt/django-qr-code.git
cd django-qr-code
```

### 2. Create a Virtual Environment

Always use a virtual environment for your local development:

```sh
python -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

Install the development dependencies:

```sh
pip install -r requirements.txt -r requirements-dev.txt
```

Do not forget to collect static assets before the very first run:

```sh
python manage.py collectstatic --no-input
```

### 4. Writing Code

* Follow Python coding standards as outlined in [PEP8](https://pep8.org/).
* Use clear and descriptive names for variables and functions.
* Always include **type hints** in your code to maintain clarity.
* Keep the code simple, readable, and focused.

### 5. Tests

* All contributions must include relevant test coverage.
* Write unit tests for each new feature or fix.
* Ensure existing tests pass before submitting your PR:

Get the source code from GitHub, follow the installation instructions above, and run the test command of Django:

```sh
python manage.py test
```

This will run the test suite with the locally installed version of Python and Django.

If you have Docker Compose installed, you can simply run the following from a terminal (this will save you the burden of setting up a proper python environment):

```sh
cd scripts
./run-tests.sh
```

This will run the test suite with all supported versions of Python and Django. The test results are stored within tests_result folder.

### 6. Document Your Changes

* Clearly document new features or changes in the codebase.
* Update relevant sections in the `README.md` file when applicable.

### 7. Submitting a Pull Request (PR)

* Push your changes to a branch on your fork.
* Open a PR with a clear title and description detailing the changes and improvements made.
* Reference any related issues in your PR description.

### 8. Code Review

* Be open to feedback and discussions.
* Address review comments promptly.

## Coding Style

* Use [Black](https://github.com/psf/black) for automatic formatting.
* Sort imports with [isort](https://github.com/PyCQA/isort).

```sh
black .
isort .
```

## License

By contributing to this project, you agree to license your contribution under the MIT license, as detailed in the [LICENSE](LICENSE.md) file.
