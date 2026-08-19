# ZZ Digital — Website & Client Portal

## Overview

Marketing website **and** client portal for **ZZ Digital**, a one-person web-design
studio in Chiang Mai, Thailand. Legal entity: **Quickeasy Asia Co.,Ltd.**
(Tax ID `0505569001285`, 108 Moo 8 T. Ontai, San Kamphaeng, Chiang Mai 50130).

Two parts live in this one repo:
1. **Marketing site** — a fast, hand-coded, **bilingual (EN + TH)** static site. Services:
   web design, logo & brand, hosting & maintenance, local SEO. Portfolio + pricing + FAQ + contact.
2. **Client portal** — a Supabase-backed app where clients log in, see their projects,
   submit info + image URLs, and message support. Plus an admin screen for the studio.

Public site: **https://zzdigitaldesign.com** · Repo: **github.com/Zed5365/ZZDigital** (branch `main`).

## Tech / architecture

- **No framework.** Hand-written HTML. The homepage (`index.html`) inlines its CSS + JS.
  Service subpages share `assets/service.css`. Portal/admin inline their own CSS + JS.
- **Hosting:** AWS S3 static-website bucket **`zzdigitaldesign.com`** (region `ap-southeast-1`)
  behind **CloudFront `EBJNRLIZ8CTTY`** (HTTPS via an ACM wildcard cert in `us-east-1`).
  - Domain in **Route 53** hosted zone `Z00211972T0UGXJIDKRSH`; apex + `www` both alias CloudFront.
  - `www → apex` 301 via CloudFront Function **`zzdigital-www-to-apex`**; `http → https` via viewer policy.
- **Images:** separate **public** S3 bucket **`zzdigital-website-images`** (region `us-east-1`).
- **Bilingual build:** English is the source of truth in `index.html`, which carries
  `data-i18n` attributes and a `const TH = {…}` dictionary in its inline script.
  **`build/build-th.js`** bakes Thai into **`th/index.html`** (translated text, `<html lang="th">`,
  Thai `<title>`/meta, reciprocal `hreflang`, `/services/…` → `/th/services/…` link rewrites).
  Service pages are hand-written in both languages.
- **Portal backend:** **Supabase** (project ref `vdgdbjesjoyfkfhqgdna`,
  URL `https://vdgdbjesjoyfkfhqgdna.supabase.co`) — Postgres + Auth + Row-Level Security.
  Anon (public) key is embedded in the portal HTML (safe — RLS protects data).
- **Contact form:** Web3Forms (access key in `index.html`) → **`info@zzdigital.awsapps.com`**.

> ⚠️ A migration off Supabase to self-hosted Postgres is under consideration (do it on a
> separate branch, e.g. `postgres-portal`). Note: a static browser page cannot talk to raw
> Postgres — that path requires adding a backend API server + hosting.

## Repo layout

```
index.html                     English homepage — SOURCE for the Thai build (has TH dict + data-i18n)
th/index.html                  GENERATED — never hand-edit; run: node build/build-th.js
build/build-th.js              Thai homepage generator
build/og-image.html            Source for the 1200×630 OG image (rendered via headless Chrome)
assets/service.css             Shared styles for all service subpages
services/<name>/index.html     EN service pages (web-design, logo-brand, hosting, local-seo)
th/services/<name>/index.html  TH service pages (hand-written)
portal/index.html              Client portal (Supabase auth + data)
portal/admin/index.html        Admin screen (gated by is_admin)
supabase/schema.sql            Portal DB schema + RLS (run once in Supabase SQL Editor)
supabase/admin.sql             Admin add-on (admins table, is_admin(), admin policies)
robots.txt, sitemap.xml        SEO (sitemap has EN+TH homepage + all service pages, with hreflang)
og-image.png                   1200×630 social share image
docs/SEO-PLAYBOOK.md           Full SEO plan + current-state audit for this site
CLAUDE.md                      This file
```

## Deploy process  (READ BEFORE DEPLOYING)

Deployment is **manual `aws s3 cp` per changed file + a CloudFront invalidation.** There is
**no `sync .`** (that would ship `docs/`, `build/`, `*.md`, `CLAUDE.md` to the public bucket).

1. If `index.html` or its `TH` dictionary changed: **rebuild Thai first** →
   ```bash
   node build/build-th.js
   ```
2. Upload each changed file with **no-cache** + the right content-type. HTML example:
   ```bash
   aws s3 cp index.html s3://zzdigitaldesign.com/index.html \
     --cache-control "no-cache, must-revalidate" --content-type "text/html; charset=utf-8"
   ```
   Content-types: HTML `text/html; charset=utf-8` · CSS `text/css; charset=utf-8` ·
   sitemap `application/xml; charset=utf-8` · robots `text/plain; charset=utf-8` · images by type.
3. Invalidate CloudFront — **always use `"/*"`** (a multi-path list containing `/` is rejected):
   ```bash
   aws cloudfront create-invalidation --distribution-id EBJNRLIZ8CTTY --paths "/*"
   ```
- Images go to the **other** bucket: `s3://zzdigital-website-images/…` (they're already served via that bucket's public URL; no CloudFront invalidation needed there).
- HTML is `no-cache`, so a change is live after invalidation + a browser hard-refresh (Ctrl+Shift+R).

## Git conventions

- Branch `main`; push to `github.com/Zed5365/ZZDigital`.
- Big/risky work (e.g. the Postgres migration) goes on its **own branch**, not `main`.
- End commit messages with the `Co-Authored-By: Claude` trailer.

## Portal data model (Supabase / Postgres)

Tables (all with RLS): `clients` (id = auth user, name, business, email), `projects`
(client_id, title, kind, status, brief, notes, web_url, next_step), `project_images`
(project_id, url), `support_messages` (client_id, project_id, sender ∈ {`client`,`studio`}, body),
`admins` (user_id). Helpers: `is_admin()`, `handle_new_user()` trigger (auto-creates a `clients`
row on signup).

- **Clients** see only their own rows. **Admins** (rows in `admins`) can read/write everything.
- Studio replies must use `sender = 'studio'` (a check constraint rejects other values).
- Routes: `/portal/` (client), `/portal/admin/` (admin, `noindex`, no public link).
  On login, admins are auto-redirected from `/portal/` to `/portal/admin/`.
- Setup is run manually in the **Supabase SQL Editor**: `schema.sql` then `admin.sql`.
  Zed's admin user UID (`a1065e25-…`) is already inserted by `admin.sql`.

## Conventions & gotchas

- **Brand name vs wordmark:** the name is **`ZZDigital`** in `<title>`, meta, and JSON-LD
  (keeps the search entity consistent); the visible **nav wordmark** is **`ZZ Digital`** (with a space).
- **Never hand-edit `th/index.html`** — it's generated. Edit `index.html` (+ the `TH` dict) and rebuild.
- **Never put secrets in the repo/client code:** the Supabase **anon** key is fine (public);
  the **`service_role`** key and any AWS secret keys must never appear here.
- Every page uses a **dark/light theme** via `prefers-color-scheme` + `data-theme` +
  `localStorage["zz-theme"]`. Fonts are the system stack (no web fonts — keep it that way for speed).
- Portal/admin pages are `noindex` and have no public link (reachable by URL, then gated by auth).

## Design tokens (colors)

- Accent (violet): `#6d5efc` light / `#8b7dff` dark
- Mint: `#0fb894` light / `#2ee0b5` dark
- Brand gradient: violet → mint (`--grad`)
- Backgrounds: `#fbfaf8` light / `#0a0a0f` dark · Surface `#fff` / `#12121b`

## SEO

Canonical tags, `robots.txt`, `sitemap.xml` (10 URLs, hreflang alternates), complete OG/Twitter
tags + `og-image.png`, JSON-LD (`ProfessionalService`, `WebSite`, `FAQPage`, per-service `Service`
+ `BreadcrumbList`), reciprocal `hreflang`, and a Google Search Console **DNS TXT** verification
(record lives in Route 53). Details + backlog in `docs/SEO-PLAYBOOK.md`.

## Implementation status

- **Marketing site:** bilingual homepage + 4 service pages (web-design, logo-brand, hosting,
  local-seo); portfolio (ReviewSlip ✓, MDH ✓, Baanpong Lodge = placeholder gradient); pricing,
  FAQ, contact form (Web3Forms). Footer shows the Quickeasy Asia company registration.
- **SEO:** P0 + P1 done; per-service pages done (P2). GSC verify + sitemap submit is a manual step.
- **Portal:** Supabase auth with **sign-in and sign-up**, per-client projects, image-URL management,
  message threads; **admin screen** to manage clients/projects/statuses and reply; navbar **Log in**
  button; portal + admin carry the main-site nav links.
- **Considering:** migrating the portal DB from Supabase to self-hosted Postgres (needs a backend
  server; on its own branch).
