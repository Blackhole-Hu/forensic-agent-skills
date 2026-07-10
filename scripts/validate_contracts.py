#!/usr/bin/env python3
"""Phase 2 contract schema validation script.

Validates all JSON schemas and test fixtures without external dependencies
beyond jsonschema (already available in the environment).

Usage: python scripts/validate_contracts.py
"""

import json
import sys
from pathlib import Path
from jsonschema import Draft7Validator, ValidationError

ROOT = Path(__file__).resolve().parent.parent
TEMPLATES = ROOT / "templates"
TESTS = ROOT / "tests" / "contracts"

SCHEMA_FILES = [
    "ledger-event.schema.json",
    "route-record.schema.json",
    "request-envelope.schema.json",
    "response-envelope.schema.json",
    "timeline-event.schema.json",
    "rebuild-status.schema.json",
    "artifact-record.schema.json",
    "finding-record.schema.json",
    "recovery-policy.schema.json",
]


def load_schemas():
    """Load all schemas and build a registry for $ref resolution."""
    schemas = {}
    for name in SCHEMA_FILES:
        path = TEMPLATES / name
        with open(path, "r", encoding="utf-8") as f:
            schema = json.load(f)
        schemas[schema.get("$id", name)] = schema
        schemas[name] = schema  # also register by filename
    return schemas


def make_resolver(schemas):
    """Create a custom ref resolver that uses our schema registry."""
    from jsonschema import RefResolver
    store = {}
    for uri, schema in schemas.items():
        store[uri] = schema
    return RefResolver("", store)


def check_schema_meta(schemas, resolver):
    """Verify each schema is valid Draft-07."""
    errors = []
    for name in SCHEMA_FILES:
        path = TEMPLATES / name
        with open(path, "r", encoding="utf-8") as f:
            schema = json.load(f)
        schema_id = schema.get("$id", name)
        try:
            Draft7Validator.check_schema(schema)
        except Exception as e:
            errors.append(f"FAIL check_schema {name}: {e}")
    return errors


def validate_fixtures(schemas, resolver):
    """Validate valid and invalid fixtures against their schemas."""
    errors = []
    successes = []

    for fixture_dir, expect_valid in [
        (TESTS / "valid", True),
        (TESTS / "invalid", False),
    ]:
        if not fixture_dir.exists():
            continue
        for fixture_file in sorted(fixture_dir.glob("*.json")):
            with open(fixture_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Determine which schema to use from filename prefix
            schema_name = None
            for sn in SCHEMA_FILES:
                prefix = sn.replace(".schema.json", "").replace("-", "_")
                if fixture_file.stem.startswith(prefix) or fixture_file.stem.startswith(sn.split(".")[0]):
                    schema_name = sn
                    break
            if not schema_name:
                # Try matching by prefix before first underscore or dot
                prefix = fixture_file.stem.split("_")[0].split(".")[0]
                for sn in SCHEMA_FILES:
                    if sn.startswith(prefix):
                        schema_name = sn
                        break
            if not schema_name:
                errors.append(f"SKIP {fixture_file.name}: cannot determine schema")
                continue

            schema = schemas[schema_name]
            validator = Draft7Validator(schema, resolver=resolver)
            validation_errors = list(validator.iter_errors(data))

            if expect_valid:
                if validation_errors:
                    for ve in validation_errors:
                        errors.append(f"FAIL valid fixture {fixture_file.name} against {schema_name}: {ve.message}")
                else:
                    successes.append(f"PASS {fixture_file.name} (valid)")
            else:
                if validation_errors:
                    successes.append(f"PASS {fixture_file.name} (correctly rejected)")
                else:
                    errors.append(f"FAIL invalid fixture {fixture_file.name} against {schema_name}: should have been rejected")

    return errors, successes


def check_stage_completeness(schemas, resolver):
    """Check that rebuild-status test fixtures have stages 0-6 unique."""
    errors = []
    rebuild_schema = schemas["rebuild-status.schema.json"]
    validator = Draft7Validator(rebuild_schema, resolver=resolver)

    for fixture_file in sorted((TESTS / "valid").glob("rebuild*.json")):
        with open(fixture_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        stages = data.get("stages", [])
        stage_nums = [s["stage"] for s in stages]
        if len(stage_nums) != len(set(stage_nums)):
            errors.append(f"FAIL {fixture_file.name}: duplicate stage numbers")
        if set(stage_nums) != set(range(7)):
            errors.append(f"FAIL {fixture_file.name}: stages must cover 0-6, got {sorted(stage_nums)}")
    return errors


def check_route_hop_limits(schemas, resolver):
    """Check hop_count <= max_hops in route fixtures."""
    errors = []
    route_schema = schemas["route-record.schema.json"]
    validator = Draft7Validator(route_schema, resolver=resolver)

    for fixture_file in sorted((TESTS / "valid").glob("route*.json")):
        with open(fixture_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        max_hops = data.get("routing_policy", {}).get("max_hops", 16)
        for handoff in data.get("handoffs", []):
            if handoff.get("hop_count", 0) > max_hops:
                errors.append(f"FAIL {fixture_file.name}: hop_count {handoff['hop_count']} > max_hops {max_hops}")
    return errors


def main():
    print("=" * 60)
    print("Phase 2 Contract Schema Validation")
    print("=" * 60)

    schemas = load_schemas()
    resolver = make_resolver(schemas)

    all_errors = []
    all_successes = []

    # 1. Schema meta-validation
    print("\n[1] Schema meta-validation (Draft-07 check_schema)")
    meta_errors = check_schema_meta(schemas, resolver)
    if meta_errors:
        all_errors.extend(meta_errors)
        for e in meta_errors:
            print(f"  {e}")
    else:
        print(f"  PASS all {len(SCHEMA_FILES)} schemas are valid Draft-07")

    # 2. Fixture validation
    print("\n[2] Fixture validation")
    fixture_errors, fixture_successes = validate_fixtures(schemas, resolver)
    all_errors.extend(fixture_errors)
    all_successes.extend(fixture_successes)
    for s in fixture_successes:
        print(f"  {s}")
    for e in fixture_errors:
        print(f"  {e}")

    # 3. Stage completeness
    print("\n[3] Rebuild Status stage completeness")
    stage_errors = check_stage_completeness(schemas, resolver)
    all_errors.extend(stage_errors)
    if stage_errors:
        for e in stage_errors:
            print(f"  {e}")
    else:
        print("  PASS all rebuild fixtures have stages 0-6 unique")

    # 4. Route hop limits
    print("\n[4] Route hop limits")
    hop_errors = check_route_hop_limits(schemas, resolver)
    all_errors.extend(hop_errors)
    if hop_errors:
        for e in hop_errors:
            print(f"  {e}")
    else:
        print("  PASS all route fixtures respect max_hops")

    # Summary
    print("\n" + "=" * 60)
    print(f"Results: {len(all_successes)} PASS, {len(all_errors)} FAIL")
    print("=" * 60)

    if all_errors:
        print("\nFAILED")
        sys.exit(1)
    else:
        print("\nALL CHECKS PASSED")
        sys.exit(0)


if __name__ == "__main__":
    main()
