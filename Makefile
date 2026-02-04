.PHONY: generate validate build serve nav

generate:
	python3 scripts/generate_pages.py
	python3 scripts/generate_finance_hub.py
	python3 scripts/generate_sitemap.py

validate:
	python3 scripts/validate_site.py

build: generate validate
	@echo "Build OK"

nav:
	python3 scripts/generate_navigation_map.py

serve:
	python3 -m http.server 8000
