#!/usr/bin/env bash
(
    python -m pip install --upgrade pip build twine
    cd ../
    rm -rf build/ dist/ django_qr_code.egg-info/
    python -m build && twine check dist/* && twine upload dist/*
)
