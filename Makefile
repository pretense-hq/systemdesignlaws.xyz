.PHONY: test serve ci ci-fast e2e

test:
	python3 -m unittest discover -s tests -v

serve:
	python3 -m http.server 8888

# Full CI pipeline locally - both jobs from .github/workflows/test.yml.
# Serves the repo and runs the browser suite against it, so the site is
# validated without depending on GitHub Actions or the live host.
ci:
	./scripts/ci_local.sh

# Same, minus the browser suite (no Playwright needed).
ci-fast:
	./scripts/ci_local.sh --no-e2e

# Browser suite only, against an already-running `make serve`.
e2e:
	NO_PROXY=127.0.0.1,localhost E2E_BASE_URL=http://127.0.0.1:8888 \
		python3 -m unittest tests.e2e_website_test -v
