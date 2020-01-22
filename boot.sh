#!/bin/bash
cd gag && gunicorn --config ../gunicorn_config.py wsgi:app