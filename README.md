# FabricLint

Static analysis and quality checks for Microsoft Fabric projects.

## Current capabilities

FabricLint scans Fabric `notebook-content.py` files and detects:

- Possible hard-coded credentials
- Hard-coded GUIDs and Fabric identifiers
- Spark `collect()` and `toPandas()` operations
- Single-partition operations
- Full overwrite operations

## Development installation

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
## JSON output

FabricLint can produce machine-readable JSON for CI/CD integrations:

```bash
fabriclint scan examples/broken-project --format json

## CI quality gates

FabricLint can return a non-zero exit code when findings reach a
configured severity threshold.

```bash
fabriclint scan . --fail-on high
