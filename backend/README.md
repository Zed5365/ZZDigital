# ZZ Digital Portal — Postgres backend

Replaces Supabase with a self-hosted **Postgres + FastAPI** backend (bcrypt passwords,
JWT in an HttpOnly cookie). Access control is enforced in the API, not by RLS.

## What's here
- `schema.sql` — Postgres tables (`users`, `projects`, `project_images`, `support_messages`)
- `app.py` — FastAPI app: auth + projects/images/messages + admin endpoints
- `requirements.txt`, `.env.example`

## Run locally
1. **Create a database** and load the schema:
   ```bash
   createdb zzportal            # or use an existing Postgres
   psql "$DATABASE_URL" -f schema.sql
   ```
2. **Configure + install:**
   ```bash
   cp .env.example .env         # fill in DATABASE_URL + a long JWT_SECRET
   python -m venv .venv && . .venv/bin/activate   # (Windows: .venv\Scripts\activate)
   pip install -r requirements.txt
   ```
3. **Run:**
   ```bash
   uvicorn app:app --reload --port 8000
   ```
   Health check: http://localhost:8000/api/health

## Make yourself an admin
Sign up once through the portal (or insert a user), then:
```sql
update users set is_admin = true where email = 'you@example.com';
```

## API (mirrors the old Supabase behaviour)
- `POST /api/auth/signup` · `POST /api/auth/signin` · `POST /api/auth/signout` · `GET /api/auth/me`
- `GET /api/projects` (client: own; admin: all, or `?user_id=`)
- `POST /api/projects` (admin) · `PATCH /api/projects/{id}` (client: brief/notes; admin: all)
- `GET/POST /api/projects/{id}/images` · `DELETE /api/images/{id}`
- `GET/POST /api/projects/{id}/messages` (sender is `studio` for admins, else `client`)
- `GET /api/clients` (admin)

## Still to do (next steps)
1. **Rewire the frontend** — `portal/index.html` and `portal/admin/index.html` currently call the
   Supabase JS SDK; point them at these `/api/...` endpoints via `fetch` (with `credentials: "include"`).
2. **Decide hosting** for this backend (it can't run on the static S3 site): e.g. a small
   container on Fargate/EC2/Render/Railway, with **Postgres on RDS** (or your existing Postgres).
   Ideally serve the portal HTML from this backend too, so cookies are same-origin.
3. **Dockerfile + start/stop scripts** (to match the Prelegal project layout).

## Migrating existing Supabase data (optional)
Export `clients/projects/project_images/support_messages` from Supabase and load into these tables.
`clients` → `users` (set a password or send reset links); the columns line up otherwise.
