-- ZZ Digital — admin access add-on.
-- Run ONCE in Supabase → SQL Editor AFTER schema.sql. Safe to re-run.
-- Gives designated admin users full access to every client's data,
-- enforced by the database (no service_role key in the browser).

-- ── 1. Store each client's email (so the admin screen can identify them) ──
alter table public.clients add column if not exists email text;
update public.clients c set email = u.email
  from auth.users u where u.id = c.id and c.email is null;

-- keep email + metadata in sync as users are created
create or replace function public.handle_new_user()
returns trigger language plpgsql security definer set search_path = public as $$
begin
  insert into public.clients (id, name, business, email)
  values (
    new.id,
    coalesce(new.raw_user_meta_data->>'name', split_part(new.email,'@',1)),
    new.raw_user_meta_data->>'business',
    new.email
  )
  on conflict (id) do update set email = excluded.email;
  return new;
end; $$;

-- ── 2. Admins list + helper ──────────────────────────────
create table if not exists public.admins (
  user_id uuid primary key references auth.users(id) on delete cascade
);
alter table public.admins enable row level security;  -- locked: only is_admin() reads it

create or replace function public.is_admin()
returns boolean language sql stable security definer set search_path = public as $$
  select exists (select 1 from public.admins where user_id = auth.uid());
$$;

-- ── 3. Admin policies (added alongside the per-client ones) ──
drop policy if exists clients_admin_all  on public.clients;
create policy clients_admin_all  on public.clients          for all using (public.is_admin()) with check (public.is_admin());
drop policy if exists projects_admin_all on public.projects;
create policy projects_admin_all on public.projects         for all using (public.is_admin()) with check (public.is_admin());
drop policy if exists images_admin_all   on public.project_images;
create policy images_admin_all   on public.project_images   for all using (public.is_admin()) with check (public.is_admin());
drop policy if exists messages_admin_all on public.support_messages;
create policy messages_admin_all on public.support_messages for all using (public.is_admin()) with check (public.is_admin());

-- ── 4. Make YOURSELF an admin ────────────────────────────
-- Find your user UUID in Authentication → Users, then run (uncomment):
-- insert into public.admins (user_id) values ('YOUR-USER-UUID') on conflict do nothing;
