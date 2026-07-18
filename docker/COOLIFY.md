# FLOW Coolify Deployment

Use this folder as a Docker Compose deployment in Coolify.

## Coolify settings

- Resource type: Docker Compose
- Compose file: `docker/docker-compose.yml`
- Public service: `gateway`
- Domain: `https://flow.example.com:8080`

The `:8080` in the Coolify domain tells Coolify to route traffic to the Nginx
gateway. The gateway sends regular HTTP traffic to Frappe on port 8000 and
`/socket.io` traffic to Frappe's realtime server on port 9000. Both therefore
share the same public HTTPS origin, which is required for authenticated Raven
realtime messaging. It does not publish a host port, so you can deploy this
compose stack multiple times for different clients on the same Coolify server.

The `frappe` service uses the public `frappe/bench:latest` image directly. It does not build a custom image, which avoids Coolify build timeouts on slow servers.
The gateway image is a two-line Nginx build using only the small `docker`
directory as its build context. The Nginx configuration is copied into the
image so deployment does not depend on Coolify host bind mounts.

The HRMS app is fetched during first boot using `HRMS_GIT_URL`, `HRMS_BRANCH`, and `HRMS_APP_DIR`. It is cloned into `apps/hrms` by default so Frappe can install the `hrms` app even though the GitHub repository is named `erphrm`.

## Required environment variables

Set these in Coolify before deploying:

```env
SITE_NAME=your-hrms-domain.com
FLOW_SITE_URL=https://your-hrms-domain.com
FLOW_SUPPORT_EMAIL=support@yourcompany.com
FLOW_FIREBASE_WEB_CONFIG={"apiKey":"...","authDomain":"...firebaseapp.com","projectId":"...","storageBucket":"...firebasestorage.app","messagingSenderId":"...","appId":"..."}
FLOW_FIREBASE_VAPID_PUBLIC_KEY=your-public-web-push-certificate-key
FLOW_FIREBASE_SERVICE_ACCOUNT_B64=base64-encoded-service-account-json
ADMIN_PASSWORD=use-a-strong-admin-password
MYSQL_ROOT_PASSWORD=use-a-strong-db-root-password
DEVELOPER_MODE=0
HRMS_GIT_URL=https://github.com/zubbicodes/erphrm.git
HRMS_BRANCH=develop
HRMS_APP_DIR=hrms
RAVEN_GIT_URL=https://github.com/zubbicodes/raven.git
RAVEN_BRANCH=develop
RAVEN_APP_DIR=raven
RAVEN_BUILD_ASSETS=1
FAST_START=0
```

`SITE_NAME` should match the public domain you assign to the `frappe` service.

`FLOW_SITE_URL` is the complete public URL used by FLOW, while
`FLOW_SUPPORT_EMAIL` is the public support address shown by FlowHR and
FlowConnect. Keep deployment credentials and environment-specific values in
Coolify or an untracked `.env` file; do not commit them.

Use only the hostname for `SITE_NAME`, for example `client1.example.com`. Do not
include `https://` or a port. In Coolify, set the gateway service domain to
`https://client1.example.com:8080` so the proxy routes to container port 8080.

Do not assign the public domain directly to the `frappe` service. Doing so
bypasses the `/socket.io` route and Raven realtime events will not connect.

## Configure Web/PWA push notifications

FLOW uses one Firebase project for browser notifications in FlowHR and
FlowConnect. No Android or iOS Firebase app is required.

1. In Firebase Console, create or select the FLOW project and add a **Web app**.
2. Copy the Web app's `firebaseConfig` object as one-line JSON into
   `FLOW_FIREBASE_WEB_CONFIG`.
3. Under **Project settings > Cloud Messaging > Web configuration > Web Push
   certificates**, generate a key pair and put the public key in
   `FLOW_FIREBASE_VAPID_PUBLIC_KEY`.
4. Confirm that **Firebase Cloud Messaging API (HTTP v1)** is enabled for the
   project. Under **Project settings > Service accounts**, generate a new private key.
   Base64-encode the complete downloaded JSON file and store only that encoded
   value in `FLOW_FIREBASE_SERVICE_ACCOUNT_B64`.
5. Add all three values to Coolify and redeploy. The Compose file forwards them
   only to the `frappe` service. Never commit the service-account JSON or its
   encoded value.

PowerShell command for step 4:

```powershell
[Convert]::ToBase64String([IO.File]::ReadAllBytes("C:\path\flow-firebase-admin.json"))
```

After deployment, sign in to each PWA and enable notifications once. Browser
permission is shared by the site origin, while FLOW stores separate FlowHR and
FlowConnect registrations so each product can respect its own preferences.

To send a test from the signed-in browser console after enabling notifications:

```js
fetch('/api/method/hrms.api.push.send_test_notification', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'X-Frappe-CSRF-Token': window.csrf_token || window.frappe?.csrf_token,
  },
  body: JSON.stringify({ product: 'FlowConnect' }),
})
```

Use `FlowHR` instead to test the HR PWA. The request returns immediately and a
short-queue worker sends the notification. Delivery failures appear in Frappe's
Error Log. Standard Notification Log records, FlowHR PWA notifications, and
FlowConnect messages are routed automatically. Invalid Firebase registrations
are removed after rejected sends, and registrations not refreshed for two
months are pruned by the scheduler.

## Verify realtime messaging

After redeploying, sign in and open FlowConnect. Go to **Settings > Help and
Support** and run the **Realtime Connection Test**. It should report `Pass` and
usually show `websocket` as the transport.

You can also verify the Socket.IO handshake from a terminal:

```sh
curl -i 'https://flow.example.com/socket.io/?EIO=4&transport=polling'
```

A working endpoint returns HTTP 200 and a response beginning with `0{`.

## Persistent storage

The compose file defines these named volumes:

- `mariadb-data` for database data
- `frappe-bench` for the generated Frappe bench, installed apps, site config, and uploaded files

If an earlier deployment is stuck in a restart loop from a broken first boot, this startup script clears and recreates an incomplete `frappe-bench` volume automatically. If MariaDB was also partially initialized, delete the resource volumes once before redeploying.

The `frappe` container starts as `root` only long enough to fix ownership on the mounted `frappe-bench` volume and expose the image's `bench`/Node/Yarn binaries on PATH, then runs Bench as the `frappe` user. It uses `restart: on-failure:3` so failures do not churn forever while you are reading logs.

The startup check validates that the existing bench can actually `import frappe`; if a previous first boot left a copied virtualenv pointing at a temporary path, it recreates the bench.

On existing benches, startup also verifies that the `hrms` app is present and installed on `SITE_NAME`; this covers earlier deployments that reached ERPNext but skipped Frappe HR.

On every redeploy, the existing `apps/hrms` checkout is updated from `HRMS_GIT_URL` and `HRMS_BRANCH`, then dependencies/assets/migrations are refreshed so pushed repository changes are reflected.

Startup also removes the stale legacy app entry `erpnexthrms` from `sites/apps.txt` before building, because the current Frappe HR module name is `hrms`.

## Notes

This compose file is suitable for a simple Coolify deployment. It still uses `bench start`, so treat it as a lightweight self-hosted setup rather than a fully tuned Frappe production stack. Run one `frappe` service instance with this setup; Redis carries Frappe realtime events, but horizontal scaling also requires deliberate proxy and worker configuration.
