#!/bin/bash
set -e

SITE_NAME="${SITE_NAME:-hrms.localhost}"
ADMIN_PASSWORD="${ADMIN_PASSWORD:-admin}"
MYSQL_ROOT_PASSWORD="${MYSQL_ROOT_PASSWORD:-123}"
DEVELOPER_MODE="${DEVELOPER_MODE:-0}"
BENCH_DIR="/home/frappe/frappe-bench"

if [ -d "${BENCH_DIR}/apps/frappe" ]; then
    echo "Bench already exists, skipping init"
    cd "${BENCH_DIR}"
    bench start
fi

export PATH="${NVM_DIR}/versions/node/v${NODE_VERSION_DEVELOP}/bin/:${PATH}"
git config --global --add safe.directory /workspace
git config --global --add safe.directory /workspace/.git

echo "Creating new bench..."
if [ -d "${BENCH_DIR}" ]; then
    find "${BENCH_DIR}" -mindepth 1 -maxdepth 1 -exec rm -rf {} +
fi

bench init --skip-redis-config-generation frappe-bench

cd "${BENCH_DIR}"

# Use containers instead of localhost
bench set-mariadb-host mariadb
bench set-redis-cache-host redis://redis:6379
bench set-redis-queue-host redis://redis:6379
bench set-redis-socketio-host redis://redis:6379

# Remove redis, watch from Procfile
sed -i '/redis/d' ./Procfile
sed -i '/watch/d' ./Procfile

bench get-app erpnext
bench get-app /workspace

if [ ! -f "sites/${SITE_NAME}/site_config.json" ]; then
    bench new-site "${SITE_NAME}" \
    --force \
    --mariadb-root-password "${MYSQL_ROOT_PASSWORD}" \
    --admin-password "${ADMIN_PASSWORD}" \
    --no-mariadb-socket

    bench --site "${SITE_NAME}" install-app erpnext
    bench --site "${SITE_NAME}" install-app hrms
else
    echo "Site ${SITE_NAME} already exists, skipping site creation"
fi

bench --site "${SITE_NAME}" set-config developer_mode "${DEVELOPER_MODE}"
bench --site "${SITE_NAME}" enable-scheduler
bench --site "${SITE_NAME}" clear-cache
bench use "${SITE_NAME}"

bench start
