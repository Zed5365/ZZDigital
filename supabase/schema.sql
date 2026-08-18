-- ZZ Digital — client portal schema
-- Run this ONCE in Supabase → SQL Editor → New query → paste → Run.
-- Safe to re-run: it uses "if not exists" / "or replace" where possible.

-- ── Tables ───────────────────────────────────────────────
-- One client per auth user.
create table if not exists public.clients (
  id         uuid primary key references auth.users(id) on delete cascade,
  name       text not null,
  business   text,
  created_at timestamptz default now()
);

create table if not exists public.projects (
  id         uuid primary key default gen_random_uuid(),
  client_id  uuid not null references public.clients(id) on delete cascade,
  title      text not null,
  kind       text,
  status     text default 'In build',
  brief      text,
  notes      text,
  web_url    text,
  next_step  text,
  created_at timestamptz default now()
);

create table if not exists public.project_images (
  id         uuid primary key default gen_random_uuid(),
  project_id uuid not null references public.projects(id) on delete cascade,
  url        text not null,
  created_at timestamptz default now()
);

create table if not exists public.support_messages (
  id         uuid primary key default gen_random_uuid(),
  client_id  uuid not null references public.clients(id) on delete cascade,
  project_id uuid references public.projects(id) on delete cascade,
  sender     text not null check (sender in ('client','studio')),
  body       text not null,
  created_at timestamptz default now()
);

-- ── Auto-create a client row when you add a user ─────────
create or replace function public.handle_new_user()
returns trigger language plpgsql security definer set search_path = public as $$
begin
  insert into public.clients (id, name, business)
  values (
    new.id,
    coalesce(new.raw_user_meta_data->>'name', split_part(new.email,'@',1)),
    new.raw_user_meta_data->>'business'
  )
  on conflict (id) do nothing;
  return new;
end; $$;

drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created
  after insert on auth.users
  for each row execute function public.handle_new_user();

-- ── Row-Level Security: each client sees only their data ─
alter table public.clients          enable row level security;
alter table public.projects         enable row level security;
alter table public.project_images   enable row level security;
alter table public.support_messages enable row level security;

drop policy if exists clients_self_select on public.clients;
create policy clients_self_select on public.clients for select using (auth.uid() = id);
drop policy if exists clients_self_update on public.clients;
create policy clients_self_update on public.clients for update using (auth.uid() = id);

drop policy if exists projects_own_select on public.projects;
create policy projects_own_select on public.projects for select using (client_id = auth.uid());
drop policy if exists projects_own_update on public.projects;
create policy projects_own_update on public.projects for update using (client_id = auth.uid());

drop policy if exists images_own_select on public.project_images;
create policy images_own_select on public.project_images for select using (
  exists (select 1 from public.projects p where p.id = project_id and p.client_id = auth.uid()));
drop policy if exists images_own_insert on public.project_images;
create policy images_own_insert on public.project_images for insert with check (
  exists (select 1 from public.projects p where p.id = project_id and p.client_id = auth.uid()));
drop policy if exists images_own_delete on public.project_images;
create policy images_own_delete on public.project_images for delete using (
  exists (select 1 from public.projects p where p.id = project_id and p.client_id = auth.uid()));

drop policy if exists messages_own_select on public.support_messages;
create policy messages_own_select on public.support_messages for select using (client_id = auth.uid());
drop policy if exists messages_own_insert on public.support_messages;
create policy messages_own_insert on public.support_messages for insert with check (
  client_id = auth.uid() and sender = 'client');

-- Note: you (the studio) manage everything from the Supabase dashboard,
-- which uses the service_role key and bypasses RLS — so you can add
-- projects, set status, and reply with sender = 'studio'.
