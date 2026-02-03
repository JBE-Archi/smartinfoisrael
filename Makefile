.PHONY: generate validate build serve

generate:
	python3 scripts/generate_pages.py
	python3 scripts/generate_sitemap.py

validate:
	python3 scripts/validate_site.py

build: generate validate
	@echo "Build OK"

serve:
	python3 -m http.server 8000
