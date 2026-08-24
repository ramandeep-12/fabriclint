RULES = {
    "FL001": {
        "severity": "HIGH",
        "description": "Possible hard-coded credential.",
        "category": "Notebook",
    },
    "FL002": {
        "severity": "MEDIUM",
        "description": "Hard-coded GUID or Fabric identifier.",
        "category": "Notebook",
    },
    "FL003": {
        "severity": "MEDIUM",
        "description": "Driver-side data collection.",
        "category": "Notebook",
    },
    "FL004": {
        "severity": "MEDIUM",
        "description": "Single-partition Spark operation.",
        "category": "Notebook",
    },
    "FL005": {
        "severity": "MEDIUM",
        "description": "Full overwrite operation.",
        "category": "Notebook",
    },

    "FL100": {
        "severity": "HIGH",
        "description": "Missing Fabric system metadata.",
        "category": "Platform",
    },
    "FL101": {
        "severity": "HIGH",
        "description": "Mixed Fabric metadata formats.",
        "category": "Platform",
    },
    "FL102": {
        "severity": "HIGH",
        "description": "Incomplete legacy metadata pair.",
        "category": "Platform",
    },
    "FL103": {
        "severity": "HIGH",
        "description": "Invalid .platform JSON.",
        "category": "Platform",
    },
    "FL104": {
        "severity": "HIGH",
        "description": "Unsupported platform metadata version.",
        "category": "Platform",
    },
    "FL105": {
        "severity": "LOW",
        "description": "Missing platform schema.",
        "category": "Platform",
    },
    "FL106": {
        "severity": "HIGH",
        "description": "Missing platform config.",
        "category": "Platform",
    },
    "FL107": {
        "severity": "HIGH",
        "description": "Invalid or missing logicalId.",
        "category": "Platform",
    },
    "FL108": {
        "severity": "HIGH",
        "description": "Missing platform metadata.",
        "category": "Platform",
    },
    "FL109": {
        "severity": "HIGH",
        "description": "Missing Fabric item type.",
        "category": "Platform",
    },
    "FL110": {
        "severity": "HIGH",
        "description": "Missing Fabric display name.",
        "category": "Platform",
    },
    "FL111": {
        "severity": "HIGH",
        "description": "Metadata type does not match item type.",
        "category": "Platform",
    },

    "FL200": {
        "severity": "HIGH",
        "description": "Missing pipeline-content.json.",
        "category": "Pipeline",
    },
    "FL201": {
        "severity": "HIGH",
        "description": "Invalid pipeline JSON.",
        "category": "Pipeline",
    },
    "FL202": {
        "severity": "MEDIUM",
        "description": "Pipeline contains no activities.",
        "category": "Pipeline",
    },
    "FL203": {
        "severity": "MEDIUM",
        "description": "Hard-coded identifier in pipeline.",
        "category": "Pipeline",
    },
    "FL204": {
        "severity": "MEDIUM",
        "description": "Execution activity has no explicit retry.",
        "category": "Pipeline",
    },
    "FL205": {
        "severity": "HIGH",
        "description": "Broken activity dependency.",
        "category": "Pipeline",
    },
    "FL206": {
        "severity": "HIGH",
        "description": "Duplicate activity name.",
        "category": "Pipeline",
    },
}