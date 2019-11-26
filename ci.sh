#!/usr/bin/env bash

PY_VERSION=$(python --version)
PY_INTERPRETER=$(which python)
echo "Building with ${PY_VERSION} from ${PY_INTERPRETER} ..."
pip install -r requirements.txt
pip install -r requirements-dev.txt
python setup.py install
pytest .
