"""
ZZ Digital — client portal backend (FastAPI + Postgres).

Replaces Supabase with your own Postgres + app-level auth, matching the
FastAPI / JWT-in-HttpOnly-cookie / bcrypt pattern used elsewhere.

Run (dev):
    cd backend
    cp .env.example .env          # then fill in DATABASE_URL + JWT_SECRET
    uvicorn app:app --reload --port 8000

Env vars:
    DATABASE_URL   postgres://user:pass@host:5432/dbname
    JWT_SECRET     long random string
    ALLOWED_ORIGINS  comma-separated origins allowed to call the API with cookies
                     (e.g. https://zzdigitaldesign.com). Omit if the portal is served
                     from this same backend.
    COOKIE_SECURE  "1" in production (HTTPS), "0" for local http.
"""
import os, datetime as dt, uuid
from contextlib import asynccontextmanager
from urllib.parse import quote, unquote

import asyncpg, jwt, bcrypt, boto3
from fastapi import FastAPI, Request, Response, HTTPException, Depends, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from starlette.concurrency import run_in_threadpool
from pydantic import BaseModel, EmailStr

DATABASE_URL   = os.environ["DATABASE_URL"]
JWT_SECRET     = os.environ.get("JWT_SECRET", "dev-only-change-me")
COOKIE_SECURE  = os.environ.get("COOKIE_SECURE", "0") == "1"
ALLOWED_ORIGINS= [o.strip() for o in os.environ.get("ALLOWED_ORIGINS", "").split(",") if o.strip()]
COOKIE_NAME    = "zz_session"
TOKEN_DAYS     = 30
UPLOADS_BUCKET = os.environ.get("UPLOADS_BUCKET", "zzdigital-client-uploads")
AWS_REGION     = os.environ.get("AWS_REGION", "ap-southeast-1")
ALLOWED_IMG    = {"image/jpeg", "image/png", "image/webp", "image/gif", "image/svg+xml", "image/avif"}
s3 = boto3.client("s3", region_name=AWS_REGION)   # AWS creds come from env (AWS_ACCESS_KEY_ID / SECRET)

def hash_pw(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8")[:72], bcrypt.gensalt()).decode("utf-8")

def verify_pw(password: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8")[:72], hashed.encode("utf-8"))
    except (ValueError, TypeError):
        return False

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.pool = await asyncpg.create_pool(DATABASE_URL, min_size=1, max_size=10)
    yield
    await app.state.pool.close()

app = FastAPI(title="ZZ Digital Portal API", lifespan=lifespan)
if ALLOWED_ORIGINS:
    app.add_middleware(CORSMiddleware, allow_origins=ALLOWED_ORIGINS,
                       allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

# ── auth helpers ─────────────────────────────────────────
def make_token(user_id: str) -> str:
    exp = dt.datetime.now(dt.timezone.utc) + dt.timedelta(days=TOKEN_DAYS)
    return jwt.encode({"sub": user_id, "exp": exp}, JWT_SECRET, algorithm="HS256")

def set_cookie(resp: Response, token: str):
    resp.set_cookie(COOKIE_NAME, token, httponly=True, secure=COOKIE_SECURE,
                    samesite="none" if COOKIE_SECURE else "lax",
                    max_age=TOKEN_DAYS * 86400, path="/")

async def current_user(request: Request):
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        raise HTTPException(401, "Not signed in")
    try:
        uid = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])["sub"]
    except jwt.PyJWTError:
        raise HTTPException(401, "Invalid session")
    row = await request.app.state.pool.fetchrow(
        "select id, email, name, business, is_admin from users where id = $1", uid)
    if not row:
        raise HTTPException(401, "User not found")
    return dict(row)

async def require_admin(user=Depends(current_user)):
    if not user["is_admin"]:
        raise HTTPException(403, "Admins only")
    return user

def pool(request: Request) -> asyncpg.Pool:
    return request.app.state.pool

# ── models ───────────────────────────────────────────────
class SignUp(BaseModel):
    email: EmailStr; password: str; name: str | None = None; business: str | None = None
class SignIn(BaseModel):
    email: EmailStr; password: str
class ProjectIn(BaseModel):
    user_id: str; title: str; kind: str | None = None; status: str = "In build"
    web_url: str | None = None; next_step: str | None = None
class ProjectPatch(BaseModel):
    brief: str | None = None; notes: str | None = None; status: str | None = None
    web_url: str | None = None; next_step: str | None = None
class ImageIn(BaseModel):
    url: str
class MessageIn(BaseModel):
    body: str

def public_user(u): return {k: u[k] for k in ("id", "email", "name", "business", "is_admin")}

# ── auth routes ──────────────────────────────────────────
@app.post("/api/auth/signup")
async def signup(body: SignUp, request: Request, resp: Response):
    p = pool(request)
    if await p.fetchrow("select 1 from users where email=$1", body.email.lower()):
        raise HTTPException(409, "That email already has an account")
    row = await p.fetchrow(
        "insert into users(email,password_hash,name,business) values($1,$2,$3,$4) returning *",
        body.email.lower(), hash_pw(body.password), body.name, body.business)
    set_cookie(resp, make_token(str(row["id"])))
    return public_user(row)

@app.post("/api/auth/signin")
async def signin(body: SignIn, request: Request, resp: Response):
    row = await pool(request).fetchrow("select * from users where email=$1", body.email.lower())
    if not row or not verify_pw(body.password, row["password_hash"]):
        raise HTTPException(401, "Wrong email or password")
    set_cookie(resp, make_token(str(row["id"])))
    return public_user(row)

@app.post("/api/auth/signout")
async def signout(resp: Response):
    resp.delete_cookie(COOKIE_NAME, path="/")
    return {"ok": True}

@app.get("/api/auth/me")
async def me(user=Depends(current_user)):
    return public_user(user)

# ── projects ─────────────────────────────────────────────
@app.get("/api/projects")
async def list_projects(request: Request, user=Depends(current_user), user_id: str | None = None):
    p = pool(request)
    if user["is_admin"]:
        if user_id:
            rows = await p.fetch("select * from projects where user_id=$1 order by created_at", user_id)
        else:
            rows = await p.fetch("select * from projects order by created_at")
    else:
        rows = await p.fetch("select * from projects where user_id=$1 order by created_at", user["id"])
    return [dict(r) for r in rows]

@app.post("/api/projects")
async def create_project(body: ProjectIn, request: Request, admin=Depends(require_admin)):
    row = await pool(request).fetchrow(
        """insert into projects(user_id,title,kind,status,web_url,next_step)
           values($1,$2,$3,$4,$5,$6) returning *""",
        body.user_id, body.title, body.kind, body.status, body.web_url, body.next_step)
    return dict(row)

def _slug(text, fallback):
    # Readable S3 folder/file name: keep letters/digits (incl. non-ASCII), turn
    # spaces & punctuation into single hyphens, trim, cap length.
    out = "".join(c if (c.isalnum() or c in " -_.") else "-" for c in (text or "").strip())
    out = "-".join(out.split())
    out = out.strip("-_.")[:60]
    return out or fallback

async def _owned_project(request, user, pid):
    row = await pool(request).fetchrow("select * from projects where id=$1", pid)
    if not row: raise HTTPException(404, "Project not found")
    if not user["is_admin"] and str(row["user_id"]) != str(user["id"]):
        raise HTTPException(403, "Not your project")
    return row

@app.patch("/api/projects/{pid}")
async def patch_project(pid: str, body: ProjectPatch, request: Request, user=Depends(current_user)):
    await _owned_project(request, user, pid)
    # clients may only edit brief/notes; admins may edit anything
    fields = {"brief": body.brief, "notes": body.notes}
    if user["is_admin"]:
        fields.update({"status": body.status, "web_url": body.web_url, "next_step": body.next_step})
    sets, vals = [], []
    for i, (k, v) in enumerate([(k, v) for k, v in fields.items() if v is not None], start=1):
        sets.append(f"{k}=${i}"); vals.append(v)
    if user["is_admin"]:
        sets.append("updated_at=now()")          # client's ping
    else:
        sets.append("client_updated_at=now()")   # admin's ping
    if not sets: return {"ok": True}
    vals.append(pid)
    row = await pool(request).fetchrow(
        f"update projects set {', '.join(sets)} where id=${len(vals)} returning *", *vals)
    return dict(row)

# ── images ───────────────────────────────────────────────
@app.get("/api/projects/{pid}/images")
async def list_images(pid: str, request: Request, user=Depends(current_user)):
    await _owned_project(request, user, pid)
    rows = await pool(request).fetch(
        "select * from project_images where project_id=$1 order by created_at", pid)
    return [dict(r) for r in rows]

@app.post("/api/projects/{pid}/images")
async def add_image(pid: str, body: ImageIn, request: Request, user=Depends(current_user)):
    await _owned_project(request, user, pid)
    if not body.url.lower().startswith(("http://", "https://")):
        raise HTTPException(400, "URL must start with http")
    row = await pool(request).fetchrow(
        "insert into project_images(project_id,url) values($1,$2) returning *", pid, body.url)
    if not user["is_admin"]:
        await pool(request).execute("update projects set client_updated_at=now() where id=$1", pid)
    return dict(row)

@app.delete("/api/images/{iid}")
async def del_image(iid: str, request: Request, user=Depends(current_user)):
    p = pool(request)
    img = await p.fetchrow("select project_id from project_images where id=$1", iid)
    if not img: raise HTTPException(404, "Not found")
    await _owned_project(request, user, str(img["project_id"]))
    await p.execute("delete from project_images where id=$1", iid)
    return {"ok": True}

@app.post("/api/projects/{pid}/upload")
async def upload_images(pid: str, request: Request, user=Depends(current_user), files: list[UploadFile] = File(...)):
    proj = await _owned_project(request, user, pid)
    owner = await pool(request).fetchrow(
        "select name, business, email from users where id=$1", proj["user_id"])
    client_name = (owner and (owner["name"] or owner["business"] or owner["email"].split("@")[0]))
    client_folder  = _slug(client_name, "client")
    project_folder = _slug(proj["title"], "project")
    # Names already used in this project (from the DB) so same-named uploads
    # never overwrite an existing image — they get photo-2.jpg, photo-3.jpg…
    existing = await pool(request).fetch(
        "select url from project_images where project_id=$1", pid)
    taken = {unquote(r["url"].rstrip("/").rsplit("/", 1)[-1]) for r in existing}
    saved = []
    for f in files:
        data = await f.read()
        if len(data) > 15 * 1024 * 1024:
            raise HTTPException(413, (f.filename or "file") + " is too large (max 15 MB)")
        ctype = (f.content_type or "").lower()
        if ctype not in ALLOWED_IMG:
            raise HTTPException(400, (f.filename or "file") + ": only image files are allowed")
        base = _slug(f.filename, "image")
        n, candidate = 1, base
        while candidate in taken:
            n += 1
            stem, dot, ext = base.rpartition(".")
            candidate = f"{stem}-{n}.{ext}" if dot else f"{base}-{n}"
        taken.add(candidate)
        base = candidate
        key = f"{client_folder}/{project_folder}/{base}"
        await run_in_threadpool(s3.put_object, Bucket=UPLOADS_BUCKET, Key=key, Body=data, ContentType=ctype)
        url = f"https://{UPLOADS_BUCKET}.s3.{AWS_REGION}.amazonaws.com/{quote(key)}"
        row = await pool(request).fetchrow(
            "insert into project_images(project_id,url) values($1,$2) returning *", pid, url)
        saved.append(dict(row))
    if not user["is_admin"]:
        await pool(request).execute("update projects set client_updated_at=now() where id=$1", pid)
    return saved

# ── messages ─────────────────────────────────────────────
@app.get("/api/projects/{pid}/messages")
async def list_messages(pid: str, request: Request, user=Depends(current_user)):
    await _owned_project(request, user, pid)
    rows = await pool(request).fetch(
        "select * from support_messages where project_id=$1 order by created_at", pid)
    return [dict(r) for r in rows]

@app.post("/api/projects/{pid}/messages")
async def add_message(pid: str, body: MessageIn, request: Request, user=Depends(current_user)):
    proj = await _owned_project(request, user, pid)
    sender = "studio" if user["is_admin"] else "client"
    row = await pool(request).fetchrow(
        "insert into support_messages(user_id,project_id,sender,body) values($1,$2,$3,$4) returning *",
        proj["user_id"], pid, sender, body.body)
    col = "updated_at" if sender == "studio" else "client_updated_at"
    await pool(request).execute(f"update projects set {col}=now() where id=$1", pid)
    return dict(row)

# ── admin ────────────────────────────────────────────────
@app.get("/api/clients")
async def list_clients(request: Request, admin=Depends(require_admin)):
    rows = await pool(request).fetch(
        """select u.id, u.name, u.business, u.email, u.created_at,
                  (select max(p.client_updated_at) from projects p where p.user_id = u.id) as client_activity
           from users u where u.is_admin = false order by u.created_at""")
    return [dict(r) for r in rows]

@app.get("/api/health")
async def health(request: Request):
    await pool(request).fetchval("select 1")
    return {"ok": True}

# ── serve the portal + admin static files ────────────────
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
_STATIC = os.environ.get("STATIC_DIR", "static")   # Docker copies the portal/ folder here

@app.get("/")
def _root():
    return RedirectResponse("/portal/")

if os.path.isdir(_STATIC):
    # /portal/ -> static/index.html, /portal/admin/ -> static/admin/index.html
    app.mount("/portal", StaticFiles(directory=_STATIC, html=True), name="portal")
