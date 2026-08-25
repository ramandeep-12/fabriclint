# FabricLint

FabricLint is a static analysis and pre-deployment quality tool for Microsoft Fabric projects.

It scans Fabric Git repositories and detects potential issues in notebooks, pipeline definitions, and Fabric metadata before changes are merged or deployed.

## Why FabricLint?

Fabric projects can contain hard-coded IDs, risky Spark operations, invalid metadata, broken pipeline dependencies, and other issues that may only appear later during deployment.

FabricLint helps catch these problems earlier.

Typical workflow:

```text
Microsoft Fabric
      ↓
Git repository
      ↓
FabricLint
      ↓
Pull Request / CI
      ↓
PASS → Merge / Deploy
FAIL → Fix issue
```

## Installation

Install from source:

```bash
git clone https://github.com/ramandeep-12/fabriclint.git
cd fabriclint

python -m pip install -e ".[dev]"
```

Verify:

```bash
fabriclint --help
```

## Usage

Scan a Fabric project:

```bash
fabriclint scan .
```

Scan with JSON output:

```bash
fabriclint scan . --format json
```

Fail CI when a HIGH severity issue is found:

```bash
fabriclint scan . --fail-on high
```

Discover Fabric items:

```bash
fabriclint items .
```

Validate Fabric item metadata:

```bash
fabriclint items . --validate
```

View all supported rules:

```bash
fabriclint rules
```

## Current Checks

### Notebook

| Rule | Severity | Check |
|---|---|---|
| FL001 | HIGH | Hard-coded credentials |
| FL002 | MEDIUM | Hard-coded GUIDs |
| FL003 | MEDIUM | `.collect()` / `.toPandas()` |
| FL004 | MEDIUM | `.coalesce(1)` / `.repartition(1)` |
| FL005 | MEDIUM | Full overwrite |

### Fabric Metadata

FabricLint validates `.platform` metadata, including:

- missing metadata
- invalid JSON
- unsupported version
- invalid `logicalId`
- missing item type or display name
- item type mismatch

Rules: `FL100`–`FL111`

### Data Pipelines

| Rule | Severity | Check |
|---|---|---|
| FL200 | HIGH | Missing `pipeline-content.json` |
| FL201 | HIGH | Invalid pipeline JSON |
| FL202 | MEDIUM | Empty pipeline |
| FL203 | MEDIUM | Hard-coded identifier |
| FL204 | MEDIUM | Retry policy review |
| FL205 | HIGH | Broken activity dependency |
| FL206 | HIGH | Duplicate activity name |

FabricLint also scans supported nested pipeline activities such as `ForEach`, `Until`, `IfCondition`, and `Switch`.

## Configuration

Create a `.fabriclint.toml` file:

```toml
[tool.fabriclint]

ignore = []

exclude = [
    ".venv/**",
    "build/**",
    "dist/**"
]

[tool.fabriclint.rules.FL203]
severity = "HIGH"

[tool.fabriclint.rules.FL204]
enabled = false
```

Rules can be disabled or their severity can be changed based on team requirements.

Inline notebook suppression is also supported:

```python
rows = df.collect()  # fabriclint: ignore FL003
```

## CI/CD

FabricLint can be used as a pull-request quality gate.

Example GitHub Actions step:

```yaml
- name: Install FabricLint
  run: pip install -e .

- name: Run FabricLint
  run: fabriclint scan . --fail-on high
```

If a HIGH issue is detected, FabricLint returns a failing exit code and the CI check fails.

## Development

Install development dependencies:

```bash
python -m pip install -e ".[dev]"
```

Run tests:

```bash
pytest -v
```

The project currently has automated tests covering CLI behavior, configuration, notebook scanning, Fabric metadata, item discovery, and pipeline validation.

## Roadmap

Planned improvements include:

- Additional Fabric item support
- Semantic Model validation
- More pipeline and notebook rules
- Cross-item dependency analysis
- Fabric REST API workspace scanning
- Azure DevOps integration
- AI-assisted explanations and remediation

## Disclaimer

FabricLint is an independent open-source project and is not affiliated with or officially maintained by Microsoft.

## License

See the `LICENSE` file for license information.

---

**FabricLint — catch Microsoft Fabric project issues before deployment.**