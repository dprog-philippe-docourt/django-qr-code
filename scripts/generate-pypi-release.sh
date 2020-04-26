#!/usr/bin/env bash
(
    python -m pip install --upgrade pip
    pip install --upgrade setuptools wheel twine
    cd ../
    rm -r build/ dist/ django_qr_code.egg-info/
    python setup.py check && python setup.py sdist && python setup.py bdist_wheel && twine upload dist/*
)