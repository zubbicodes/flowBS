# Coolify Deployment

Use this folder as a Docker Compose deployment in Coolify.

## Coolify settings

- Resource type: Docker Compose
- Compose file: `docker/docker-compose.yml`
- Public service: `frappe`
- Domain: `https://your-hrms-domain.com:8000`

The `:8000` in the Coolify domain tells Coolify to route traffic to port 8000 inside the `frappe` container. It does not publish host port 8000, so you can deploy this compose stack multiple times for different clients on the same Coolify server.

The `frappe` service uses the public `frappe/bench:latest` image directly. It does not build a custom image, which avoids Coolify build timeouts on slow servers.

The HRMS app is fetched during first boot using `HRMS_GIT_URL` and `HRMS_BRANCH`. If your repository is private, set `HRMS_GIT_URL` to a tokenized HTTPS URL in Coolify, for example `https://x-access-token:<token>@github.com/owner/repo.git`.

## Required environment variables

Set these in Coolify before deploying:

```env
SITE_NAME=your-hrms-domain.com
ADMIN_PASSWORD=use-a-strong-admin-password
MYSQL_ROOT_PASSWORD=use-a-strong-db-root-password
DEVELOPER_MODE=0
HRMS_GIT_URL=https://github.com/syntaxusman/erphrm.git
HRMS_BRANCH=develop
```

`SITE_NAME` should match the public domain you assign to the `frappe` service.

## Persistent storage

The compose file defines these named volumes:

- `mariadb-data` for database data
- `frappe-bench` for the generated Frappe bench, installed apps, site config, and uploaded files

If an earlier deployment is stuck in a restart loop from a broken first boot, this startup script clears and recreates an incomplete `frappe-bench` volume automatically. If MariaDB was also partially initialized, delete the resource volumes once before redeploying.

## Notes

This compose file is suitable for a simple Coolify deployment. It still uses `bench start`, so treat it as a lightweight self-hosted setup rather than a fully tuned Frappe production stack.
