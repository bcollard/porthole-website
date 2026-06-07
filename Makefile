.DEFAULT_GOAL := help

# PREVIEW_PORT, not PORT — the parent `porthole` project sets PORT=8081 in
# its .envrc, which leaks via direnv into shells that cd in here.
PREVIEW_PORT ?= 8765

# Use /usr/bin/python3 explicitly — the plain `python3` on this box goes
# through a safe-chain shim that errors on /usr/local/certs/. See CLAUDE.md.
PYTHON ?= /usr/bin/python3

help: ## Show this help
	@grep -E '^[a-zA-Z0-9_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-18s\033[0m %s\n", $$1, $$2}'

preview: ## Serve the site locally (override with PREVIEW_PORT=...)
	@echo "→ http://localhost:$(PREVIEW_PORT)/"
	@$(PYTHON) -m http.server $(PREVIEW_PORT)

og-image: ## Re-rasterize assets/og-image.svg → assets/og-image.png
	rsvg-convert -w 1200 -h 630 assets/og-image.svg -o assets/og-image.png
	@echo "✓ wrote assets/og-image.png"

deploy-run: ## Trigger the GitHub Actions deploy workflow on main
	gh workflow run deploy-website.yaml --repo bcollard/porthole-website --ref main

bucket-head: ## curl -I the bucket origin (bypass the custom-domain edge cache)
	curl -sI https://storage.googleapis.com/porthole.runlocal.dev/index.html
