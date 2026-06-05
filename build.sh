#!/usr/bin/env bash
set -o errexit   # exit immediately on any error

pip install -r requirements.txt
python manage.py collectstatic --noinput
