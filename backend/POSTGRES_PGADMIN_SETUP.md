# Postgres setup with pgAdmin (Windows / Local)

This guide walks through setting up PostgreSQL locally and connecting with pgAdmin, creating the `quantumreview` database and user, running Alembic migrations, and starting the backend and frontend for development.

> Quick checklist
> - Install PostgreSQL (or use Docker)
> - Install pgAdmin
> - Create `quantumreview` database and a dedicated DB user
> - Set `DATABASE_URL` in your environment or `backend/.env`
> - Run migrations and start the backend

---

## 1) Install PostgreSQL (two options)

Option A — Native Windows installer

1. Download the Postgres Windows installer from https://www.postgresql.org/download/windows/ and run the installer (choose a known password for the `postgres` superuser).
2. Ensure the installer adds `psql` to your PATH (checkbox in installer) or note the installation path.

Option B — Docker (recommended if you don't want to alter your system)

```powershell
# Pull and run Postgres in Docker (creates DB 'quantumreview' with user postgres/postgres)
docker run --name qr-postgres -e POSTGRES_PASSWORD=postgres -e POSTGRES_USER=postgres -e POSTGRES_DB=quantumreview -p 5432:5432 -d postgres:15
```

Check container status:

```powershell
docker ps -a | findstr qr-postgres
```

If you later need to remove the container:

```powershell
docker rm -f qr-postgres
```

---

## 2) Install pgAdmin (GUI)

1. Download pgAdmin from https://www.pgadmin.org/download/ and install.
2. Launch pgAdmin and add a new server connection.

### Add new server in pgAdmin
- Right-click `Servers` → `Create` → `Server...`
- In `General` tab: set `Name`: `quantumreview-local` (any name)
- In `Connection` tab:
  - `Host name/address`: `localhost` (or the host where Postgres runs)
  - `Port`: `5432`
  - `Maintenance database`: `postgres` (default)
  - `Username`: `postgres` (or your chosen user)
  - `Password`: the password you set in installer or `postgres` if you used the Docker command above

Click `Save`.

You should now see the server in the tree and be able to expand databases, schemas, and tables.

---

## 3) Create database and user (pgAdmin or psql)

Option A — Create using pgAdmin UI

1. Expand the server → Databases → Right click `Databases` → `Create` → `Database...`
2. `Database` name: `quantumreview`
3. Owner: `postgres` (or the user you want)
4. Save.

Option B — Create using `psql` (or Docker exec into the container)

If you have psql on PATH (native install):

```powershell
psql -U postgres -c "CREATE DATABASE quantumreview;"
```

If using Docker container:

```powershell
docker exec -it qr-postgres psql -U postgres -c "CREATE DATABASE quantumreview;"
```

(Optional) Create a dedicated DB user

```powershell
# run inside psql (or docker exec)
psql -U postgres -c "CREATE USER qr_user WITH PASSWORD 'qr_password';"
psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE quantumreview TO qr_user;"
```

---

## 4) Configure application `DATABASE_URL`

The project expects `DATABASE_URL` to use the async driver `asyncpg` when running the app. You can set this in your shell (temporary) or add it to `backend/.env` (permanent for local dev).

Example (temporary PowerShell environment variable):

```powershell
# If you used default postgres/postgres credentials
$env:DATABASE_URL = 'postgresql+asyncpg://postgres:postgres@127.0.0.1:5432/quantumreview'

# Or if you created qr_user/qr_password
$env:DATABASE_URL = 'postgresql+asyncpg://qr_user:qr_password@127.0.0.1:5432/quantumreview'
```

To permanently set this for the repo, edit `backend/.env` and set the `DATABASE_URL` value.

> Note: `app/config.py` provides a helper `database_url_sync` which strips `+asyncpg` for Alembic.

---

## 5) Run database migrations (Alembic)

The repository includes helper scripts to run Alembic programmatically. Use the same Python executable you'll use to run the app.

Install dependencies if needed (run in your Python virtual env):

```powershell
python -m pip install -r requirements.txt
python -m pip install alembic
```

Run the migration helper (from the `backend` folder):

```powershell
cd 'C:\Users\Palguna\Desktop\QuantumReview\backend'
python .\scripts\run_migrations.py
```

Expected output:
- `Using DB: postgresql+asyncpg://<user>:<redacted>@host...`
- `Migrations applied successfully.`

If you don't have Alembic available on PATH, the helper will instruct how to install it.

---

## 6) Verify tables exist

Using Docker (or psql):

```powershell
docker exec -it qr-postgres psql -U postgres -d quantumreview -c "\dt"
```

You should see tables like `users`, `repos`, `issues`, etc.

If you use pgAdmin, expand `Databases` → `quantumreview` → `Schemas` → `public` → `Tables` to confirm.

---

## 7) Start backend and frontend

Start backend (in `backend` folder):

```powershell
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 --log-level debug
```

Start frontend (in `frontend` folder):

```powershell
cd 'C:\Users\Palguna\Desktop\QuantumReview\frontend'
npm install
npm run dev
```

Open the app at: `http://localhost:8080`

---

## 8) Test login flow and health

1. In a browser, open `http://localhost:8080`, click Login (GitHub) and walk through OAuth.
2. Watch the backend terminal — you should see requests to `/auth/github` (start) and `/auth/callback` (after redirect).
3. Confirm backend can create/update `users` by checking the `users` table in pgAdmin.
4. Health check: `http://localhost:8000/health` should return JSON `{"status":"healthy","version":"..."}`.

---

## 9) Common troubleshooting

- `psql` not found: add Postgres bin folder to your PATH or use Docker `exec` to run `psql` in the container.
- `UndefinedTableError` when backend handles requests: migrations weren't applied. Run `python .\scripts\run_migrations.py` and restart backend.
- Connection refused from frontend (Vite): ensure Vite proxy points to `http://127.0.0.1:8000` (the repo's `frontend/vite.config.ts` was updated to use 127.0.0.1 to avoid IPv6 issues).
- DNS issues with remote DB: ensure the host in `DATABASE_URL` is resolvable and if using remote providers you include `?sslmode=require` if necessary.

---

## 10) Reverting any temporary Mongo changes

If you enabled `MONGODB_URI` earlier for testing, you can just unset it before running the app to keep the app strictly Postgres-only:

```powershell
# Remove the variable in this shell
Remove-Item Env:\MONGODB_URI
```

Or delete the `MONGODB_URI` line from `backend/.env`.

---

## 11) Useful commands summary

```powershell
# Start Postgres via Docker (one-liner)
docker run --name qr-postgres -e POSTGRES_PASSWORD=postgres -e POSTGRES_USER=postgres -e POSTGRES_DB=quantumreview -p 5432:5432 -d postgres:15

# Create DB (if not created)
docker exec -it qr-postgres psql -U postgres -c "CREATE DATABASE quantumreview;"

# Set env var for this shell
$env:DATABASE_URL = 'postgresql+asyncpg://postgres:postgres@127.0.0.1:5432/quantumreview'

# Run migrations
python .\scripts\run_migrations.py

# Start backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 --log-level debug

# Start frontend
cd '..\frontend'
npm install
npm run dev
```

---

If you'd like, I can now:
- Update `backend/.env` to set `DATABASE_URL` to the local Postgres and remove `MONGODB_URI` (I won't overwrite secrets without confirmation), or
- Revert the Mongo adapter changes I previously added.

Tell me which of the two you prefer, and I will apply that change next. 
