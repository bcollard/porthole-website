# porthole-website — porthole.runlocal.dev

Single-page marketing site for [porthole](https://github.com/bcollard/porthole),
a browser-based Kubernetes debug terminal. Hand-rolled HTML/CSS — no SSG, no
framework, no JS dependencies beyond a tiny theme toggle. Served as static
files from a GCS bucket.

Sibling sites live at `klimax.runlocal.dev` and `claudestatus.runlocal.dev`
under the same pattern.

---

## Layout

```
.
├── index.html                 # the page
├── styles.css                 # all styles; porthole-blue palette, light/dark/auto
├── 404.html
├── robots.txt · sitemap.xml
├── assets/
│   ├── favicon.svg            # porthole ring + dot motif
│   ├── og-image.svg           # editable source for the OG card (1200×630)
│   └── og-image.png           # rendered card the crawlers fetch
├── cicd/
│   └── setup-gcp-wif.sh       # one-time GCP setup (idempotent)
└── .github/workflows/
    └── deploy-website.yaml
```

---

## Local preview

```bash
/usr/bin/python3 -m http.server 8765
# open http://localhost:8765/
```

---

## Regenerating the OG card

```bash
rsvg-convert -w 1200 -h 630 assets/og-image.svg -o assets/og-image.png
```

Edit the SVG (text, gradient, layout) and re-run. Both files are committed —
the PNG is what crawlers fetch.

---

## Deploy pipeline

Push to `main` that touches anything outside `README.md`, `CLAUDE.md`,
`cicd/**`, and `.github/**` runs `.github/workflows/deploy-website.yaml`,
which:

1. Authenticates via Workload Identity Federation (no SA keys).
2. `gsutil rsync -r -d` the repo root into `gs://porthole.runlocal.dev`,
   excluding `.git/`, `.github/`, `cicd/`, `README.md`, `CLAUDE.md`,
   `.gitignore`, and **`gha-creds-*.json`** (see CLAUDE.md gotchas).
3. `gsutil setmeta` to set short cache for HTML/CSS (10 min) and long cache
   for images (1 day).

For workflow-file or setup-script changes that need a deploy run, use:

```bash
gh workflow run deploy-website.yaml --repo bcollard/porthole-website --ref main
```

---

## One-time GCP setup

```bash
./cicd/setup-gcp-wif.sh
```

Idempotent. Reuses the WIF pool `gitops-pool` and OIDC provider `gh-provider`
that already exist on the personal GCP project. Creates the bucket, the
service account, and binds WIF impersonation for `bcollard/porthole-website`.
