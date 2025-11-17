.PHONY: reformat reformat-staged

reformat:
	uv format

reformat-staged:
	git diff --cached --name-only -- '*.py' | xargs -r uv format --
