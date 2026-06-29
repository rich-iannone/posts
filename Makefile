# Makefile for the Posit Open Source blog posts.
#
# Each post lives in its own directory as `<post>/index.qmd` and renders to
# `<post>/index.md` (the file Hugo publishes). Posts with executable `{python}`
# cells run against the `posts-blog` Jupyter kernel backed by ./.venv.
#
# Common usage:
#   make setup                 create .venv, install deps, register the kernel
#   make small-focused-tools     render a single post (by directory name)
#   make all                   re-render posts that ALREADY have an index.md
#   make list                  show each post and whether its .md is current
#   make clean                 remove Quarto caches (keeps the .md files)
#   make help                  list available targets (default)
#
# A bare `make` only prints help; it never renders. `make all` refreshes the
# posts that already have a rendered index.md and never creates a new one for a
# post that hasn't opted in. Use `make <post>` to render a post for the first time.

PYTHON   ?= python3.13
VENV     := .venv
VENV_PY  := $(VENV)/bin/python
KERNEL   := posts-blog
STAMP    := $(VENV)/.posts-stamp
RENDER   := scripts/render_post.py

QMD         := $(wildcard */index.qmd)
POSTS       := $(patsubst %/index.qmd,%,$(QMD))
EXISTING_MD := $(wildcard */index.md)

.DEFAULT_GOAL := help
.PHONY: all setup clean list help $(POSTS)

all: $(EXISTING_MD)  ## Re-render every post that already has an index.md

# Render one post's index.md from its index.qmd. The kernel/venv must exist
# first (order-only prereq: required present, but its timestamp won't force a
# needless re-render).
%/index.md: %/index.qmd | $(STAMP)
	$(VENV_PY) $(RENDER) "$*"

# Convenience: `make <post-dir>` renders that post (creating index.md if needed).
$(POSTS): %: %/index.md

setup: $(STAMP)  ## Create the venv, install requirements, register the kernel

$(STAMP): requirements.txt
	test -d $(VENV) || $(PYTHON) -m venv $(VENV)
	$(VENV_PY) -m pip install --upgrade pip
	$(VENV_PY) -m pip install -r requirements.txt
	$(VENV_PY) -m ipykernel install --user --name $(KERNEL) \
		--display-name "Posts blog ($(VENV))"
	touch $(STAMP)

list:  ## Show each post and whether its .md is up to date
	@for q in $(QMD); do \
		d=$$(dirname $$q); m=$$d/index.md; \
		if [ ! -f $$m ]; then st="no .md (run: make $$d)"; \
		elif [ $$q -nt $$m ]; then st="OUT OF DATE"; \
		else st="up to date"; fi; \
		printf "  %-28s %s\n" "$$d" "$$st"; \
	done

clean:  ## Remove Quarto caches and freeze dirs (keeps the rendered .md files)
	find . -type d -name .quarto -prune -exec rm -rf {} +
	find . -type d -name '*_files' -prune -exec rm -rf {} +

help:  ## List available targets
	@awk 'BEGIN{FS=":.*## "} /^[a-zA-Z0-9_.\/%-]+:.*## /{printf "  \033[1m%-10s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST) | sort
