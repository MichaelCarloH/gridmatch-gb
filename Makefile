PYTHON ?= python

.PHONY: install demo-data train backtest notebooks api web test

install:
	$(PYTHON) -m pip install -e ".[dev]"
	npm install

demo-data:
	$(PYTHON) scripts/build_demo_dataset.py

train:
	$(PYTHON) scripts/train_models.py

backtest:
	$(PYTHON) scripts/run_backtest.py

notebooks:
	$(PYTHON) scripts/execute_notebooks.py

api:
	uvicorn api.index:app --reload

web:
	npm run dev

test:
	$(PYTHON) -m pytest
	npm run lint
	npm run build
