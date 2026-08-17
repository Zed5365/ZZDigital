# SEO Playbook — ZZDigital (zzdigitaldesign.com)

A portable, execution-ready SEO plan. Fill in the **Project Profile**, then work the
phases in order. Every task lists **what / why / how (with a Claude Code prompt) /
done-when** so it can be handed to an agent or a human.

> **How to reuse across projects**
> 1. Copy this file into the new repo.
> 2. Fill in **§0 Project Profile** — that's the only per-site input most tasks need.
> 3. Run phases **1 → 9** in order. Phases 1–3 + 6 are universal; 4 (i18n) and
>    5 (local) are conditional — skip if the profile says they don't apply.
> 4. Use **Appendix A** snippets as starting templates (they read values from the Profile).
> 5. Keep **§10 Governance** running forever.
> 6. Anything marked _[stack]_ has hosting-specific notes in **Appendix C**.

---

## 0. Project Profile (ZZDigital)

| Field | Value |
|---|---|
| Primary domain | `zzdigitaldesign.com` |
| Canonical host | **apex** (`zzdigitaldesign.com`) — 301 `www` → apex. *(Neither serves over HTTPS yet; site is currently only live at the S3 website endpoint — see Phase 1.1 / Appendix C.)* |
| Primary language | `en` |
| Additional locales | `th` (Thai) — **currently a client-side JS toggle only; not indexable per-language** |
| Target countries | Thailand (primary; Chiang Mai focus) + international ("working worldwide") |
| Business type | Local service business — one-person digital studio (web design / branding) |
| Physical location? | Service-area business based in **Chiang Mai** (no walk-in storefront) → do a scoped Phase 5 (GBP as service-area business, `LocalBusiness`/`ProfessionalService` schema with `areaServed`) |
| Hosting / stack | Static single-file `index.html` in S3 bucket `zzdigitaldesign.com`, region `ap-southeast-1`. **S3 static-website hosting, HTTP only, no CDN yet.** Images from separate public bucket `zzdigital-website-images` (us-east-1) |
| Rendering | Static HTML — **English is in the raw HTML** (indexes fine); Thai is swapped in by client-side JS (not indexed) |
| Primary conversions | Contact-form submit (Web3Forms → `info@zzdigital.awsapps.com`), phone/LINE call (`+66 83 9696 555`) |
| Key pages / templates | **Single page** (Home) with sections: Services, Work, Process, Pricing, Testimonials, FAQ, Contact |
| Top competitors | _TBD — other Chiang Mai / Thailand web-design studios & freelancers (fill from Phase 7 research)_ |
| Seed keywords | `web design Chiang Mai`, `website design Thailand`, `รับทำเว็บไซต์เชียงใหม่`, `ออกแบบเว็บไซต์`, `logo design Chiang Mai`, `restaurant website Thailand`, `small business website Thailand`, `ทำเว็บไซต์ร้านอาหาร` — _validate & expand in Phase 7_ |
| Analytics tool | none-yet |
| Search Console verified? | **In progress** — domain-property DNS TXT record added in Route 53 and resolving publicly; awaiting the "Verify" click + sitemap submit (Phase 9.1) |

**Rendering matters most.** ZZDigital's English content is server-rendered static HTML, so
English indexes fine. **Thai only appears after JS runs** (a client-side language toggle that
auto-selects Thai for Thai browsers), so Google indexes little or no Thai. Phase 4 fixes this.

---

## 1. Technical Foundations — Crawlability & Indexation

Goal: search engines can find, crawl, render, and index the right URLs — and nothing else.

- [ ] **1.1 Canonical host + HTTPS**
  - _Why:_ `http/https` and `www/apex` variants split ranking signals and can dupe-index.
  - _How:_ Serve HTTPS only; 301-redirect all variants to the one canonical host in §0. _[stack]_
  - _Done when:_ `curl -I` on every variant returns `301` to the canonical `https://` origin, which returns `200`.
  - _ZZDigital status:_ ❌ **Not started — highest priority.** Site is only reachable at the HTTP S3 website endpoint; `https://zzdigitaldesign.com` doesn't serve at all. Needs CloudFront + ACM cert + Route 53 alias.

- [ ] **1.2 `robots.txt`**
  - _Why:_ Controls crawling and advertises the sitemap.
  - _How:_ Publish at `/robots.txt` (Appendix A.1). Never block CSS/JS. Ensure **staging** hosts disallow all.
  - _Done when:_ `https://DOMAIN/robots.txt` returns 200 and references the sitemap.
  - _ZZDigital status:_ ❌ Not in bucket.

- [ ] **1.3 XML sitemap**
  - _Why:_ Gives crawlers a clean list of canonical URLs + last-modified dates.
  - _How:_ Generate `/sitemap.xml` (Appendix A.2) with only indexable 200-status canonical URLs. Regenerate on build/deploy. Add a per-locale/hreflang sitemap if multilingual.
  - _Done when:_ Validates, lists every important URL, submitted in Search Console (9.1).
  - _ZZDigital status:_ ❌ Not in bucket. Trivial today (one page); grows once Thai + service pages exist.

- [ ] **1.4 Canonical tags**
  - _Why:_ Declares the preferred URL for each page; kills duplicate-content ambiguity.
  - _How:_ Self-referencing `<link rel="canonical" href="https://DOMAIN/path">` on every page (absolute URL).
  - _Done when:_ Every page has exactly one canonical pointing at its own clean URL.
  - _ZZDigital status:_ ❌ Missing from `index.html`.

- [ ] **1.5 Indexation control**
  - _Why:_ Thin/utility pages shouldn't be indexed; staging must never be.
  - _How:_ `<meta name="robots" content="noindex,follow">` on those; password/`noindex` all non-prod environments. _[stack]_
  - _Done when:_ `site:DOMAIN` in Google shows only intended pages (after crawl).
  - _ZZDigital status:_ ✅ Single intended page; no utility pages to suppress. (Watch the S3 endpoint URL doesn't get indexed alongside the domain — the canonical + redirect in 1.1/1.4 handle that.)

- [ ] **1.6 Rendering / content-in-HTML** _(critical for SPA)_
  - _Why:_ If primary content requires JS, indexing is unreliable and slow.
  - _How:_ Prefer static HTML or SSR/SSG so the initial HTML response already contains headings, copy, and links. Verify with "View Source" (not DevTools).
  - _Done when:_ `curl -s https://DOMAIN/ | grep "<your headline text>"` finds the copy in raw HTML.
  - _ZZDigital status:_ ✅ for English (raw HTML). ⚠️ Thai is JS-only — see Phase 4.

- [ ] **1.7 Clean URLs & 404s**
  - _Why:_ Readable, stable URLs; real 404s (not soft-200s) for missing pages.
  - _How:_ Lowercase, hyphenated, no query cruft; return a real `404` status + helpful 404 page. _[stack]_
  - _Done when:_ A random missing path returns HTTP 404.
  - _ZZDigital status:_ ⚠️ S3 website hosting currently returns `index.html` (200) as the error document for unknown paths — a soft-200. Add a real 404 document once more pages exist.

- [ ] **1.8 Redirect hygiene**
  - _Why:_ Preserve equity when URLs change; avoid chains/loops.
  - _How:_ Maintain a redirect map; use single-hop 301s. Never bulk-redirect to the homepage.
  - _Done when:_ No redirect chains > 1 hop; old URLs 301 to closest equivalent.
  - _ZZDigital status:_ N/A yet (no legacy URLs). Set up cleanly with 1.1.

---

## 2. On-Page SEO

Goal: each page targets one intent and communicates it clearly to users and crawlers.

- [ ] **2.1 Title tags** — Unique per page, ~50–60 chars, primary keyword first, brand last: `Primary Keyword — Brand`.
- [ ] **2.2 Meta descriptions** — Unique, ~140–160 chars, compelling, includes the query + a reason to click.
- [ ] **2.3 Heading hierarchy** — Exactly one `<h1>` matching page intent; logical `<h2>/<h3>` outline.
- [ ] **2.4 Semantic HTML** — `<header> <nav> <main> <article> <section> <footer>`; one `<main>`.
- [ ] **2.5 Keyword mapping** — One primary + a few secondary keywords per URL; no cannibalization.
- [ ] **2.6 Internal linking** — Descriptive anchor text; every important page reachable within ~3 clicks.
- [ ] **2.7 Images** — Descriptive filenames, meaningful `alt`, explicit `width`/`height`, WebP/AVIF, lazy-load below the fold.
- [ ] **2.8 Descriptive links** — No "click here"; anchor text says the destination.
- _Done when:_ Every template has unique title/description, one H1, a clean heading outline, and no orphan pages.
- _ZZDigital status:_ ✅ Title/description present; ✅ one H1 ("Small studio. Serious websites."); ✅ semantic sections + in-page anchor nav. ⚠️ **Title/description keyword targeting is brand-led, not search-led** — rework toward "web design Chiang Mai / Thailand". ⚠️ ReviewSlip image lacks `width`/`height` and isn't WebP (2.7).

---

## 3. Structured Data (schema.org JSON-LD)

Goal: eligibility for rich results and clearer entity understanding. Use JSON-LD in `<head>`.

- [ ] **3.1 Organization** or **LocalBusiness** (use `LocalBusiness`/`ProfessionalService` — Chiang Mai service-area business; Appendix A.4).
- [ ] **3.2 WebSite** (+ `SearchAction` only if you add site search).
- [ ] **3.3 BreadcrumbList** on non-home pages (once they exist).
- [ ] **3.4 Type-specific**: `FAQPage` (the site already has an FAQ section — easy win), `Service` per offering, `Review`/`AggregateRating` only if genuine.
- _Done when:_ Passes the **Rich Results Test** and Search Console "Enhancements" shows no errors.
- _ZZDigital status:_ ❌ None present. Quick wins: `ProfessionalService` + `WebSite` + `FAQPage` (built from the existing FAQ copy).

---

## 4. International / Multilingual SEO

Goal: each language is separately crawlable, indexable, and served to the right users.

- [ ] **4.1 Distinct URLs per language** — `/` (or `/en/`) & `/th/`. **The client-side toggle that swaps text at one URL is not indexable per-language — replace it with real URLs.**
- [ ] **4.2 `hreflang` annotations** — Reciprocal tags across the language cluster + `x-default` (Appendix A.5).
- [ ] **4.3 `lang` attribute** — `<html lang="th">` matches the served language.
- [ ] **4.4 Localized metadata & content** — Translate titles, descriptions, headings, alt text, and structured data — not just body copy. The existing draft Thai should be proofread before it's indexed.
- [ ] **4.5 One canonical per language** — Each locale URL self-canonicalizes.
- _Done when:_ Each language has its own URL returning translated content in raw HTML, with valid reciprocal hreflang, and both appear under `site:DOMAIN`.
- _ZZDigital status:_ ⚠️ **Biggest content-visibility gap.** All Thai (`TH = {…}` dictionary in `index.html`) is applied by JS at one URL. Pre-render a static `/th/index.html` from that dictionary at build time; keep English at `/`; add reciprocal hreflang. The `<html lang>` already flips correctly client-side — make it correct server-side per URL too.

---

## 5. Local SEO  _(service-area business — Chiang Mai)_

- [ ] **5.1 Google Business Profile** — Create as a **service-area business** (hide address, set Chiang Mai + service area); complete categories (Web designer / Website designer), photos, hours, services; keep active.
- [ ] **5.2 NAP consistency** — Identical Name/Phone (and email) on the site (`LocalBusiness` schema + footer) and every external listing. *(No public street address — that's fine for a service-area business.)*
- [ ] **5.3 `LocalBusiness` schema** — With `areaServed`, `telephone`, `email`, `priceRange`, `sameAs` (Appendix A.4; drop `streetAddress` if not public).
- [ ] **5.4 Citations & directories** — Consistent listings in relevant Thai/creative directories.
- [ ] **5.5 Localized landing pages** — A page targeting "web design Chiang Mai" / "รับทำเว็บไซต์เชียงใหม่" with genuine local content.
- [ ] **5.6 Reviews** — Ask clients; respond to all. (Never fabricate reviews — the current testimonials should be real & attributable before adding `Review` schema.)
- _Done when:_ GBP verified, NAP identical everywhere, LocalBusiness schema validates.

---

## 6. Performance & Core Web Vitals

Goal: fast, stable pages. Targets (75th percentile, mobile): **LCP ≤ 2.5s · INP ≤ 200ms · CLS ≤ 0.1**.

- [ ] **6.1 Images** — Right-sized, WebP/AVIF, `width`/`height` set (prevents CLS), `loading="lazy"` off-screen, `fetchpriority="high"` on the LCP image.
- [ ] **6.2 Fonts** — `font-display: swap`; self-host/subset; avoid layout shift. *(ZZDigital uses a system font stack — no web-font penalty. Keep it that way.)*
- [ ] **6.3 CSS/JS** — Minify; defer non-critical JS; remove unused CSS. *(Currently one self-contained file with inline CSS/JS — fine at this size; minify on a build step if it grows.)*
- [ ] **6.4 Caching & compression** — Long-lived immutable caching for hashed assets, short for HTML; Brotli/gzip; serve via CDN. _[stack]_
- [ ] **6.5 Preload critical assets** — LCP image / hero font.
- [ ] **6.6 Reduce third-party JS** — Only Web3Forms is called (on submit). Keep third-party JS minimal.
- _Measure:_ PageSpeed Insights, Lighthouse, CrUX. _Done when:_ All three CWV "Good" on mobile.
- _ZZDigital status:_ ⚠️ Likely good overall (no web fonts, small inline bundle). Two fixes: (a) S3 website hosting has **no CDN/compression** — CloudFront (1.1) adds Brotli + edge caching; (b) the ReviewSlip PNG (~270 KB) has no `width`/`height` and isn't WebP — set dimensions + convert.

---

## 7. Content Strategy & E-E-A-T

Goal: cover the topics your audience searches, credibly.

- [ ] **7.1 Keyword & intent research** — Build clusters by intent. Tools: Search Console queries (once live), autocomplete, "People also ask", competitor gap. Record in the Profile's keyword table.
- [ ] **7.2 Page/keyword map** — One primary intent per URL; a page per core service (Website, Logo & brand, Hosting, Local SEO) and per key term.
- [ ] **7.3 Content calendar** — Prioritize by value × winnability; publish on a cadence (e.g. short case studies of ReviewSlip / Baanpong Lodge / MDH).
- [ ] **7.4 On-page depth** — Answer the query fully; add media; strong intro that states the answer.
- [ ] **7.5 E-E-A-T signals** — Clear About/Contact, real client work & named testimonials, HTTPS, no intrusive interstitials.
- [ ] **7.6 Refresh cadence** — Update/prune stale pages quarterly.
- _Done when:_ Every core service has a dedicated page; a content backlog exists.
- _ZZDigital status:_ ⚠️ Single page competing for many terms at once. Real portfolio work (ReviewSlip, Baanpong Lodge, MDH) is strong E-E-A-T raw material — turn each into a case-study page.

---

## 8. Off-Page / Authority

- [ ] **8.1 Backlinks** — Earn via useful content, client/partner site credits ("site by ZZDigital" footer links on delivered sites), directories. Avoid paid link schemes / PBNs.
- [ ] **8.2 Business & social profiles** — Complete, consistent, linked with `sameAs` in schema.
- [ ] **8.3 Unlinked mentions** — Reclaim by requesting a link.
- [ ] **8.4 Internal authority flow** — Link from strong pages to priority pages.
- _Done when:_ A prioritized outreach list exists; referring-domain count trends up.
- _ZZDigital status:_ 🟢 Easy lever available — a discreet "Website by ZZDigital →" credit on each client site (ReviewSlip, Baanpong Lodge, MDH, etc.) earns relevant, natural backlinks.

---

## 9. Measurement & Analytics

- [ ] **9.1 Google Search Console** — Verify (DNS or file), submit sitemap, monitor Coverage/Indexing, Enhancements, CWV, query performance. **Do this first — it's the ground truth.**
- [ ] **9.2 Analytics** — Install GA4, or a privacy-friendly option (Plausible/Umami/Cloudflare Web Analytics) — good where PDPA/GDPR & consent simplicity matter.
- [ ] **9.3 Conversion tracking** — Track contact-form submit + phone/LINE clicks as events/goals.
- [ ] **9.4 Rank & visibility tracking** — Track priority keywords (Search Console or a rank tracker).
- [ ] **9.5 Bing Webmaster Tools** — Optional; cheap extra coverage.
- [ ] **9.6 Reporting cadence** — Monthly: impressions, clicks, avg position, top pages/queries, conversions, CWV, index coverage.
- _Done when:_ GSC + analytics + conversion tracking live and a monthly report template exists.
- _ZZDigital status:_ ⚠️ GSC domain-property TXT is live in Route 53 — **click "Verify" in Search Console, then submit the sitemap once 1.3 ships.** No analytics yet (9.2) — Cloudflare Web Analytics or Plausible recommended (PDPA-friendly).

---

## 10. Governance (ongoing)

- **Monthly:** GSC coverage/errors, CWV, top movers, broken links, new content shipped.
- **Quarterly:** content refresh/prune, backlink review, competitor gap, schema still valid.
- **On every deploy (regression guard):** titles/descriptions present & unique, one H1, canonical present, sitemap regenerated, no accidental `noindex`, no staging leak, Lighthouse SEO ≥ 95.
- **On URL changes:** add 301s, update sitemap + internal links.

---

## Priority tiers (ZZDigital)

| Tier | Items | Rationale |
|---|---|---|
| **P0 — Foundation** | 1.1 HTTPS + domain (CloudFront/ACM/Route 53), 1.2 robots, 1.3 sitemap, 1.4 canonical, 9.1 finish GSC verify + submit sitemap | The site isn't even reachable at `zzdigitaldesign.com` yet, and nothing's indexable/measurable without these. |
| **P1 — Core visibility** | 2.x title/description keyword rework, 3.1–3.2 + FAQPage schema, complete OG/Twitter tags, 4.x Thai `/th/` pages + hreflang, 6.x CloudFront + image fixes | Drives rankings & CTR and unlocks the entire Thai audience. |
| **P2 — Growth** | 7.x per-service/case-study pages, 5.x GBP + local, 8.x "built by" backlinks, 9.2 analytics | Compounds over months. |

---

# Appendix A — Copy-paste templates

Replace `DOMAIN` = `zzdigitaldesign.com`, `Brand` = `ZZDigital`, and business details with Profile values.

### A.1 `robots.txt`
```
User-agent: *
Allow: /

Sitemap: https://zzdigitaldesign.com/sitemap.xml
```
Staging/non-prod hosts (incl. the raw S3 endpoint if it stays reachable) must instead serve:
```
User-agent: *
Disallow: /
```

### A.2 `sitemap.xml`
```xml
<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>https://zzdigitaldesign.com/</loc>
    <lastmod>2026-08-17</lastmod>
  </url>
  <!-- add https://zzdigitaldesign.com/th/ once the Thai page exists -->
</urlset>
```

### A.3 `<head>` template (single-locale)
```html
<title>Web Design in Chiang Mai &amp; Thailand — ZZDigital</title>
<meta name="description" content="Fast, hand-built websites, logos and hosting for restaurants, resorts and local businesses in Chiang Mai and across Thailand. From ฿3,000." />
<link rel="canonical" href="https://zzdigitaldesign.com/" />
<meta name="robots" content="index,follow" />

<!-- Open Graph -->
<meta property="og:type" content="website" />
<meta property="og:title" content="Web Design in Chiang Mai & Thailand — ZZDigital" />
<meta property="og:description" content="Fast, hand-built websites and logos. Launch in two weeks." />
<meta property="og:url" content="https://zzdigitaldesign.com/" />
<meta property="og:image" content="https://zzdigitaldesign.com/og-image.jpg" /> <!-- 1200×630 -->
<meta property="og:locale" content="en_US" />
<meta property="og:locale:alternate" content="th_TH" />

<!-- Twitter/X -->
<meta name="twitter:card" content="summary_large_image" />
<meta name="twitter:title" content="Web Design in Chiang Mai & Thailand — ZZDigital" />
<meta name="twitter:description" content="Fast, hand-built websites and logos. Launch in two weeks." />
<meta name="twitter:image" content="https://zzdigitaldesign.com/og-image.jpg" />
```
*(Favicon already present as an inline SVG data-URI — keep it.)*

### A.4 `ProfessionalService` / `LocalBusiness` JSON-LD (service-area, no public street address)
```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "ProfessionalService",
  "name": "ZZDigital",
  "url": "https://zzdigitaldesign.com/",
  "image": "https://zzdigitaldesign.com/og-image.jpg",
  "description": "One-person digital studio in Chiang Mai building fast, hand-built websites, logos and hosting for local businesses.",
  "telephone": "+66-83-9696-555",
  "email": "info@zzdigital.awsapps.com",
  "priceRange": "฿฿",
  "areaServed": [
    { "@type": "City", "name": "Chiang Mai" },
    { "@type": "Country", "name": "Thailand" }
  ],
  "address": { "@type": "PostalAddress", "addressLocality": "Chiang Mai", "addressCountry": "TH" },
  "sameAs": [
    "https://github.com/Zed5365/ZZDigital"
    /* add Facebook / LINE / Instagram / LinkedIn as they exist */
  ]
}
</script>
```
Add a `WebSite` node and a `FAQPage` node (built from the existing FAQ section) as separate JSON-LD blocks.

### A.5 `hreflang` cluster (put on BOTH the English and Thai pages)
```html
<link rel="alternate" hreflang="en" href="https://zzdigitaldesign.com/" />
<link rel="alternate" hreflang="th" href="https://zzdigitaldesign.com/th/" />
<link rel="alternate" hreflang="x-default" href="https://zzdigitaldesign.com/" />
```

---

# Appendix B — Claude Code automation

Per-phase prompts you can paste into Claude Code on this repo:

- **Audit:** "Audit `index.html` against `docs/SEO-PLAYBOOK.md` §1–§3 and §6. For each checklist item report PASS/FAIL with file:line evidence, then a prioritized fix list (P0/P1/P2)."
- **Head/meta:** "Apply the Appendix A.3 `<head>` block, filling title/description/canonical/OG from the page's real content. List assumptions."
- **Schema:** "Generate `ProfessionalService` + `WebSite` + `FAQPage` JSON-LD (Appendix A.4) from the real business details and the existing FAQ copy; inject into `<head>`; validate the JSON."
- **Sitemap/robots:** "Generate `robots.txt` and `sitemap.xml` for the current route list; wire regeneration into the deploy step; add `--content-type` on upload."
- **CWV:** "Add `width`/`height` to the ReviewSlip image, convert it to WebP, and set `fetchpriority` appropriately; show before/after."
- **i18n:** "Pre-render a static `/th/index.html` from the `TH` dictionary in `index.html`, keep English at `/`, add reciprocal hreflang (Appendix A.5), and set `<html lang>` per file."

**CI regression guard (§10):** add a step (GitHub Action) that runs Lighthouse CI (assert SEO ≥ 95) and a link checker on every PR; fail on a missing canonical, duplicate/blank title, or an unexpected `noindex`.

---

# Appendix C — This project (ZZDigital) applied

**Stack:** static single-file `index.html` in S3 bucket `zzdigitaldesign.com`, region
`ap-southeast-1`, served today via **S3 static-website hosting over HTTP only (no CDN)**.
Homepage renders at the S3 website endpoint; the apex domain does not serve yet. Single page,
bilingual EN/TH via a **client-side** toggle (auto-selects Thai for Thai-language browsers).
Images from a separate public bucket `zzdigital-website-images` (us-east-1). Contact form via
Web3Forms → `info@zzdigital.awsapps.com`. DNS in Route 53 (hosted zone `Z00211972T0UGXJIDKRSH`).

### Current-state audit
| Item | Status | Note |
|---|---|---|
| HTTPS + custom domain | ❌ | **Site only loads at the HTTP S3 website endpoint.** `https://zzdigitaldesign.com` doesn't serve — no CloudFront/ACM/DNS alias yet. Top priority. |
| Title + meta description | ✅ / ⚠️ | Present & reasonable, but **brand-led, not keyword-led** — rework toward "web design Chiang Mai / Thailand". |
| One H1, semantic sections | ✅ | `header/nav/main/section/footer`, single H1, in-page anchor nav. Good structure. |
| `robots.txt` | ❌ | Not in bucket. |
| `sitemap.xml` | ❌ | Not in bucket. |
| Canonical tag | ❌ | Missing from `index.html`. |
| Open Graph | ⚠️ | Partial — `og:title/description/type` present; **missing `og:url`, `og:image` (1200×630), `og:locale`.** |
| Twitter cards | ❌ | Missing — poor link previews. |
| JSON-LD structured data | ❌ | No `ProfessionalService`/`Organization`/`WebSite`; FAQ not marked up as `FAQPage`. |
| Favicon | ✅ | Inline SVG data-URI favicon present. |
| Thai SEO | ⚠️ | **Biggest content gap:** TH exists only as a JS text-swap at one URL → Google indexes English only. |
| Core Web Vitals | ⚠️ | Likely good (system fonts, small inline bundle). But **no CDN/compression** (S3-only) and the ReviewSlip PNG (~270 KB) lacks `width`/`height` + isn't WebP. |
| Search Console | ⚠️ | Domain-property DNS TXT added & resolving; **needs the "Verify" click + sitemap submit.** |
| Analytics | ❌ | None installed. |

### Prioritized backlog for ZZDigital
- **P0**
  1. **Stand up HTTPS at the real domain:** CloudFront distribution in front of the bucket, ACM cert for `zzdigitaldesign.com` + `www` (**cert must be in `us-east-1` for CloudFront**, even though the bucket is `ap-southeast-1`), Route 53 alias A/AAAA for apex + www. Choose **apex** canonical; 301 `www`→apex and `http`→`https` via a CloudFront Function.
  2. Add self-referencing `<link rel="canonical" href="https://zzdigitaldesign.com/">` to `index.html`.
  3. Add `robots.txt` + `sitemap.xml` to the bucket with correct content-types (see stack notes). **Exclude `docs/` and `*.md` from the deploy so this playbook never ships.**
  4. Finish **Google Search Console** (TXT already live) → click Verify → submit the sitemap.
- **P1**
  5. Complete OG tags (`og:url`, `og:image`, `og:locale`) + add Twitter card tags; create a 1200×630 OG image.
  6. Add `ProfessionalService` + `WebSite` + `FAQPage` JSON-LD (Chiang Mai; `areaServed` Thailand + worldwide; phone `+66 83 9696 555`; email `info@zzdigital.awsapps.com`; `sameAs` socials).
  7. **Fix Thai SEO:** pre-render a static `/th/index.html` from the existing `TH` dictionary, keep English at `/`, add reciprocal hreflang. Proofread the draft Thai before it's indexed.
  8. Rework title/description/H-tags toward researched keywords; ReviewSlip image → add `width`/`height` + WebP.
- **P2**
  9. Expand beyond one page: a page per service (Website, Logo & brand, Hosting, Local SEO) and per key term ("รับทำเว็บไซต์เชียงใหม่", "web design Chiang Mai"); case-study pages for ReviewSlip / Baanpong Lodge / MDH.
  10. Create a **Google Business Profile** (service-area business, Chiang Mai) + local citations.
  11. Add privacy-friendly analytics (Cloudflare Web Analytics / Plausible) + track contact-form submit & LINE/phone clicks as conversions.
  12. Add a discreet "Website by ZZDigital →" credit on delivered client sites for natural backlinks.

### ZZDigital stack notes _[stack]_
- **robots/sitemap upload:** `aws s3 cp robots.txt s3://zzdigitaldesign.com/ --content-type text/plain` and `aws s3 cp sitemap.xml s3://zzdigitaldesign.com/ --content-type application/xml`.
- **HTTPS/canonical:** needs CloudFront + ACM (**cert in `us-east-1`**) + Route 53 alias. Canonical-host + http→https redirect via a **CloudFront Function** (viewer-request). Point CloudFront at the S3 **website endpoint** (not the REST endpoint) so index/error-document routing still works, or migrate to OAC + a routing function.
- **Caching:** `index.html` already carries `Cache-Control: no-cache, must-revalidate`; give hashed/static assets long-lived immutable caching once CloudFront is in place. Invalidate `/*` (or just `/index.html`) on deploy.
- **Deploy hygiene:** the current deploy is `aws s3 sync . s3://zzdigitaldesign.com --exclude ".git/*" --exclude ".gitignore"`. **Add `--exclude "docs/*"` and `--exclude "*.md"`** so this playbook and future docs never reach the public bucket. Also clean up the leftover 2024 `css/`, `images/`, `js/`, `uploadToS3.bat` objects still in the bucket.
- **Images:** served from public bucket `zzdigital-website-images` (us-east-1). Consider serving them through the same CloudFront for HTTPS + edge caching, and use no-space, lowercase, WebP filenames.
- **Security headers** (SEO-adjacent trust): add a CloudFront Response Headers Policy (HSTS, X-Content-Type-Options, Referrer-Policy) once CloudFront exists.

---

_Last updated: 2026-08-17._
