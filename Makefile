# Usage:
#   make release MODULE=go VERSION=0.1.0
#   make release MODULE=jvm VERSION=0.2.0
#   make release MODULE=python VERSION=0.2.0
#   make release MODULE=rust VERSION=0.1.0
#
# Steps:
#   1. Updates the version in the module's config file (except Go, which is tag-only)
#   2. Commits the version change
#   3. Creates and pushes a git tag: testcontainers-{MODULE}/v{VERSION}
#   4. The pushed tag triggers the GitHub Actions release workflow

MODULES := go jvm python rust

# Validation
ifndef MODULE
  $(error MODULE is required. Usage: make release MODULE=go VERSION=0.1.0)
endif
ifndef VERSION
  $(error VERSION is required. Usage: make release MODULE=go VERSION=0.1.0)
endif
ifeq ($(filter $(MODULE),$(MODULES)),)
  $(error MODULE must be one of: $(MODULES))
endif

TAG := testcontainers-$(MODULE)/v$(VERSION)

# Cross-platform sed in-place: macOS requires -i '', GNU/Linux requires -i
SED_INPLACE := sed -i$(shell sed --version >/dev/null 2>&1 || echo " ''")

.PHONY: release bump-version tag

release: bump-version tag
	@echo ""
	@echo "Released $(TAG)"
	@echo "GitHub Actions release workflow should now be triggered."

bump-version:
ifeq ($(MODULE),go)
	@echo "Go uses tag-based versioning, no file to update."
else ifeq ($(MODULE),jvm)
	@echo "Updating testcontainers-jvm/build.gradle to version $(VERSION)"
	@$(SED_INPLACE) "s/^version = '.*'/version = '$(VERSION)'/" testcontainers-jvm/build.gradle
	@git add testcontainers-jvm/build.gradle
	@git commit -m "chore(jvm): bump version to $(VERSION)"
else ifeq ($(MODULE),python)
	@echo "Updating testcontainers-python/pyproject.toml to version $(VERSION)"
	@$(SED_INPLACE) 's/^version = ".*"/version = "$(VERSION)"/' testcontainers-python/pyproject.toml
	@git add testcontainers-python/pyproject.toml
	@git commit -m "chore(python): bump version to $(VERSION)"
else ifeq ($(MODULE),rust)
	@echo "Updating testcontainers-rust/Cargo.toml to version $(VERSION)"
	@$(SED_INPLACE) '/^\[package\]/,/^\[/{s/^version = ".*"/version = "$(VERSION)"/}' testcontainers-rust/Cargo.toml
	@git add testcontainers-rust/Cargo.toml
	@git commit -m "chore(rust): bump version to $(VERSION)"
endif

tag:
	@echo "Creating tag $(TAG)"
	@git tag -a "$(TAG)" -m "Release $(TAG)"
	@echo "Pushing tag $(TAG)"
	@git push origin "$(TAG)"
