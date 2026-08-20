-- ZZ Digital — client portal schema (self-hosted Postgres).
-- Run once against your database:  psql "$DATABASE_URL" -f backend/schema.sql
-- Access control is enforced in the API (app-level), not via RLS.

create extension if not exists pgcrypto;   -- gen_random_uuid()

create table if not exists users (
  id            uuid primary key default gen_random_uuid(),
  email         text unique not null,
  password_hash text not null,
  name          text,
  business      text,
  is_admin      boolean not null default false,
  created_at    timestamptz not null default now()
);

create table if not exists projects (
  id         uuid primary key default gen_random_uuid(),
  user_id    uuid not null references users(id) on delete cascade,
  title      text not null,
  kind       text,
  status     text not null default 'In build',
  brief      text,
  notes      text,
  web_url    text,
  next_step  text,
  theme      jsonb,                                 -- client's preferred website theme (colours/font/mode)
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),   -- bumped when the studio changes the project (client's ping)
  client_updated_at timestamptz                    -- bumped when the client acts (admin's ping)
);
create index if not exists projects_user_idx on projects(user_id);

create table if not exists project_images (
  id         uuid primary key default gen_random_uuid(),
  project_id uuid not null references projects(id) on delete cascade,
  url        text not null,
  created_at timestamptz not null default now()
);
create index if not exists images_project_idx on project_images(project_id);

-- Typography perk (website projects): client makes named "sets" and uploads
-- reference images; the studio delivers result images + notes per set.
create table if not exists typography_sets (
  id                uuid primary key default gen_random_uuid(),
  project_id        uuid not null references projects(id) on delete cascade,
  title             text not null,
  brief             text,
  notes             text,
  status            text not null default 'requested',   -- requested / in progress / delivered
  created_at        timestamptz not null default now(),
  updated_at        timestamptz not null default now(),
  client_updated_at timestamptz
);
create index if not exists typo_sets_project_idx on typography_sets(project_id);

create table if not exists typography_images (
  id         uuid primary key default gen_random_uuid(),
  set_id     uuid not null references typography_sets(id) on delete cascade,
  url        text not null,
  role       text not null check (role in ('reference','result')),
  created_at timestamptz not null default now()
);
create index if not exists typo_images_set_idx on typography_images(set_id);

create table if not exists support_messages (
  id         uuid primary key default gen_random_uuid(),
  user_id    uuid not null references users(id) on delete cascade,
  project_id uuid references projects(id) on delete cascade,
  sender     text not null check (sender in ('client','studio')),
  body       text not null,
  created_at timestamptz not null default now()
);
create index if not exists messages_project_idx on support_messages(project_id);

-- Make an existing user an admin:
--   update users set is_admin = true where email = 'you@example.com';
