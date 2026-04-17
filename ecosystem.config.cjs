/**
 * PM2 ecosystem file for the FastAPI backend.
 *
 * Runs two independent uvicorn processes, one per FastAPI app:
 *   - lms-client-api  -> app.client_main:app  on port 5001
 *   - lms-admin-api   -> app.admin_main:app   on port 5002
 *
 * Matches the legacy (Node/Express) port layout so nginx upstreams
 * do not need to change during cutover.
 *
 * Requirements on the VPS:
 *   - Python 3.11+ available at ./venv/bin/python
 *   - pip install -r requirements.txt already run inside the venv
 *   - .env present in the project root (loaded by pydantic-settings)
 */
module.exports = {
  apps: [
    {
      name: "lms-client-api",
      cwd: ".",
      script: "./venv/bin/uvicorn",
      args: [
        "app.client_main:app",
        "--host", "127.0.0.1",
        "--port", "5001",
        "--workers", "2",
        "--proxy-headers",
        "--forwarded-allow-ips=*",
      ].join(" "),
      interpreter: "none",
      instances: 1,
      exec_mode: "fork",
      autorestart: true,
      watch: false,
      max_memory_restart: "400M",
      kill_timeout: 5000,
      env: {
        ENVIRONMENT: "production",
        NODE_ENV: "production",
        CLIENT_PORT: "5001",
        PYTHONUNBUFFERED: "1",
      },
    },
    {
      name: "lms-admin-api",
      cwd: ".",
      script: "./venv/bin/uvicorn",
      args: [
        "app.admin_main:app",
        "--host", "127.0.0.1",
        "--port", "5002",
        "--workers", "1",
        "--proxy-headers",
        "--forwarded-allow-ips=*",
      ].join(" "),
      interpreter: "none",
      instances: 1,
      exec_mode: "fork",
      autorestart: true,
      watch: false,
      max_memory_restart: "300M",
      kill_timeout: 5000,
      env: {
        ENVIRONMENT: "production",
        NODE_ENV: "production",
        ADMIN_PORT: "5002",
        PYTHONUNBUFFERED: "1",
      },
    },
  ],
};
