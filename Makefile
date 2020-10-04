all: src/index.js

run: all
	python3 app.py

fake: all
	FAKE_ROBOT=1 python3 app.py

src/index.js: src/index.ts
	tsc src/index.ts