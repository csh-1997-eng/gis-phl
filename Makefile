KERNEL_NAME ?= gis-phl
KERNEL_DISPLAY ?= Python (gis-phl)

.PHONY: sync lock kernel kernel-remove lab test

sync:
	uv sync --all-groups

lock:
	uv lock

kernel:
	uv run python -m ipykernel install --user --name "$(KERNEL_NAME)" --display-name "$(KERNEL_DISPLAY)"

kernel-remove:
	jupyter kernelspec uninstall -y "$(KERNEL_NAME)"

lab:
	uv run jupyter lab

test:
	uv run pytest -q
