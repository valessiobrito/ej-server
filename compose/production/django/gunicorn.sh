#!/usr/bin/env bash

set -o errexit
set -o pipefail
set -o nounset

python /app/manage.py migrate
# inv db-assets
# inv db-fake --safe
# echo 'production' > /app/local/build.info

/usr/local/bin/gunicorn config.wsgi -w 4 -b 0.0.0.0:5000 --chdir=/app \
    --error-logfile=- \
    --access-logfile=- \
    --log-level info
