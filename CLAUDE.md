# porthole-website — porthole.runlocal.dev

Single-page marketing site for [porthole](https://github.com/bcollard/porthole),
the browser-based Kubernetes debug terminal. Hand-rolled HTML/CSS — no SSG,
no framework, no JS dependencies beyond a tiny theme toggle. Served as
static files from a GCS bucket.

Sibling sites at `klimax.runlocal.dev` and `claudestatus.runlocal.dev`
use the exact same pattern; treat them as siblings — any change here
should probably be considered there.

---

## Layout

```
.
├── index.html
├── styles.css
├── 404.html
├── robots.txt · sitemap.xml
├── assets/
│   ├── favicon.svg
│   ├── og-image.svg
│   └── og-image.png
├── cicd/
│   └── setup-gcp-wif.sh
└── .github/workflows/
    └── deploy-website.yaml
```

---

## Local preview

```bash
/usr/bin/python3 -m http.server 8765
# open http://localhost:8765/
```

**Don't use plain `python3`** — on this machine it's wrapped by a
`safe-chain.cjs` shim that fails with `EACCES` on `/usr/local/certs/`.
Same for any other `python3 -c …` invocation. Always go through
`/usr/bin/python3`.

---

## Regenerating the OG card

The card is composed entirely in `assets/og-image.svg` (no embedded
bitmaps) and rasterized with `rsvg-convert`:

```bash
rsvg-convert -w 1200 -h 630 assets/og-image.svg -o assets/og-image.png
```

Edit the SVG (text, gradient, layout) and re-run. Both files are
committed — the PNG is what crawlers fetch.

---

## Deploy pipeline

Push to `main` that touches anything outside `README.md`, `CLAUDE.md`,
`cicd/**`, and `.github/**` runs `.github/workflows/deploy-website.yaml`,
which:

1. Authenticates via Workload Identity Federation (no SA keys).
2. `gsutil rsync -r -d` the repo root into `gs://porthole.runlocal.dev`,
   excluding `.git/`, `.github/`, `cicd/`, `README.md`, `CLAUDE.md`,
   `.gitignore`, and **`gha-creds-*.json`** (see gotcha below).
3. `gsutil setmeta` to set short cache for HTML/CSS (10 min) and long
   cache for images (1 day).

For workflow-file or setup-script changes that need a deploy run:

```bash
gh workflow run deploy-website.yaml --repo bcollard/porthole-website --ref main
```

---

## ⚠ Deploy gotchas (already handled, don't reintroduce)

### 1. `google-github-actions/auth@v2` leaks a credential file

`auth@v2` writes its WIF `external_account` config to
`./gha-creds-<random>.json` in the runner working dir. If `gsutil rsync`
doesn't exclude it, **the file ends up in the public bucket**. The
credential's `credential_source.url` points back to a per-run GitHub
OIDC endpoint that dies with the job, so the exposure window is seconds —
but it's still terrible hygiene.

The current rsync exclude pattern (`-x`) catches `gha-creds-*.json`.
Keep it there. If you ever rewrite the workflow, preserve that
exclusion.

The sibling `klimax.runlocal.dev` and `claudestatus.runlocal.dev`
workflows have the same exclusion — match the pattern when touching them.

### 2. The custom IAM role needs `storage.objects.update` for `setmeta`

The shared custom role `claudecodebucketadmin` on GCP project
`personal-218506` is used by this site and the sibling ones. If you
re-run `cicd/setup-gcp-wif.sh` against a fresh project, make sure the
role includes `storage.objects.update` — without it, `gsutil setmeta`
silently 403s and HTML deploys serve GCS's default 1 h cache TTL,
making "deploy not propagating" debugging confusing.

### 3. The GCS edge cache lies about `Cache-Control` for ~1 h after first deploy

The `porthole.runlocal.dev` custom domain caches the first response
(default `max-age=3600`) before `setmeta` has had a chance to set a
shorter cache. After the first successful deploy with `setmeta` working,
the custom domain may still serve a stale HTML for up to an hour.
Verify against the bucket origin to bypass the cache:

```bash
curl -sI https://storage.googleapis.com/porthole.runlocal.dev/index.html
```

---

## One-time GCP setup

```bash
./cicd/setup-gcp-wif.sh
```

Idempotent. Reuses the WIF pool `gitops-pool` and OIDC provider
`gh-provider` that exist on the personal GCP project. Creates the
bucket, the service account, and binds WIF impersonation for
`bcollard/porthole-website`.
