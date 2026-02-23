.PHONY: reformat reformat-staged test

reformat:
	uv format

reformat-staged:
	git diff --cached --name-only -- '*.py' | xargs -r uv format --

test:
	uv run pytest tests/ -v
