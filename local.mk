# ── Repo-local targets ───────────────────────────────────────────────────────
# Named here so `help` lists them and the ghost/help gates see them.
LOCAL_TARGETS = changelog-check

# `changelog-check` is not a standard.mk target -- standard.mk only cites
# doppler's as the worked example of a gate whose execution home is `lint`.
# This is that shape, not a private copy of something upstream.
#
# It exists because six commits landed between v0.3.10 and the 0.3.11 release
# branch with no CHANGELOG entry between them, and nothing noticed (#20). The
# discipline it enforces is the one this repo's own `release-branch` help text
# already assumes: "edit CHANGELOG.md ([Unreleased] -> [x.y.z])".
#
# The tag scan is the dangerous half. `actions/checkout` fetches no tags by
# default, so `git tag --list` is EMPTY in CI and every per-tag assertion below
# would pass over nothing. An empty result set and a clean one are
# indistinguishable unless something asserts the set was populated -- so this
# refuses to report success on zero tags rather than reading silence as green.
# ci.yml's lint job fetches tags for exactly this reason.
changelog-check: ## Every release tag has a CHANGELOG section; work in flight has [Unreleased]
	@set -e; \
	 tags="$$(git tag --list 'v*' --sort=v:refname)"; \
	 if [ -z "$$tags" ]; then \
	     echo "ERROR: changelog-check found NO tags."; \
	     echo "  The scan found nothing, so it did not run, so it has not passed."; \
	     echo "  A shallow checkout without tags is the usual cause:"; \
	     echo "  give the job 'fetch-depth: 0' or 'fetch-tags: true'."; \
	     exit 1; \
	 fi; \
	 allow="$$(sed 's/#.*//' .changelog-allow | tr -d '[:blank:]' | grep .)"; \
	 n=0; missing=""; stale=""; \
	 for t in $$tags; do \
	     n=$$((n+1)); v="$${t#v}"; \
	     if grep -q "^## \[$$v\]" CHANGELOG.md; then \
	         echo "$$allow" | grep -qx "$$t" && stale="$$stale $$t"; \
	     else \
	         echo "$$allow" | grep -qx "$$t" || missing="$$missing $$t"; \
	     fi; \
	 done; \
	 if [ -n "$$missing" ]; then \
	     echo "ERROR: released tags with no CHANGELOG section:$$missing"; \
	     echo "  release.yml extracts notes by that exact heading, so a missing"; \
	     echo "  one publishes the NEXT section's bullets under this version."; \
	     exit 1; \
	 fi; \
	 if [ -n "$$stale" ]; then \
	     echo "ERROR: .changelog-allow lists tag(s) that now HAVE a section:$$stale"; \
	     echo "  The ratchet may only shrink -- remove them from the file."; \
	     exit 1; \
	 fi; \
	 last="$$(git tag --list 'v*' --sort=-v:refname | head -1)"; \
	 ahead="$$(git rev-list "$$last..HEAD" --count 2>/dev/null || echo 0)"; \
	 ver="$$(grep '^version = ' pyproject.toml | sed 's/.*"\(.*\)".*/\1/')"; \
	 if [ "$$ahead" -gt 0 ] \
	    && ! grep -q '^## \[Unreleased\]' CHANGELOG.md \
	    && ! { [ "v$$ver" != "$$last" ] && grep -q "^## \[$$ver\]" CHANGELOG.md; }; then \
	     echo "ERROR: $$ahead commit(s) since $$last and no CHANGELOG entry."; \
	     echo "  Add a '## [Unreleased]' section and record them there;"; \
	     echo "  'make release-branch' promotes it to the version heading."; \
	     exit 1; \
	 fi; \
	 echo "changelog-check: $$n tag(s) checked, $$(echo "$$allow" | grep -c .) ratcheted; $$ahead commit(s) since $$last"

# Spliced onto lint, which is what gives it an execution home: CI runs
# `make lint`, and gates-home-check walks DOWN from the CI targets to find it.
lint: changelog-check
