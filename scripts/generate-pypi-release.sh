#!/usr/bin/env bash
(
    cd ../
    rm -r build/ dist/ django_qr_code.egg-info/
    python setup.py check && python setup.py sdist && python setup.py bdist_wheel && twine upload dist/*
)