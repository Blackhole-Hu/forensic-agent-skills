#!/usr/bin/env python3
"""Phase 2 contract schema validation script.

Validates all JSON schemas, test fixtures, and semantic constraints.
Uses referencing.Registry for portable $ref resolution and FormatChecker
for date-time validation.

Usage: python scripts/validate_contracts.py
"""

import json
import sys
from pathlib import Path

from jsonschema import Draft7Validator, FormatChecker
from referencing import Registry, Resource

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

# Stage name mapping for rebuild-status
STAGE_NAME_MAP = {
    0: "plan-validation-preflight",
    1: "workspace-source-preservation",
    2: "artifact-preparation",
    3: "runtime-configuration",
    4: "network-configuration",
    5: "runtime-launch-stabilization",
    6: "service-discovery-connection-handoff",
}


def load_schemas():
    """Load all schemas and return as dict keyed by $id."""
    schemas = {}
    for name in SCHEMA_FILES:
        path = TEMPLATES / name
        with open(path, "r", encoding="utf-8") as f:
            schema = json.load(f)
        uri = schema.get("$id", name)
        schemas[uri] = schema
        schemas[name] = schema
    return schemas


def build_registry(schemas):
    """Build a referencing Registry from loaded schemas."""
    def retrieve(uri: str):
        if uri in schemas:
            return Resource.from_contents(schemas[uri])
        raise Exception(f"Unknown schema: {uri}")

    registry = Registry(retrieve=retrieve)
    return registry


def check_schema_meta(schemas):
    """Verify each schema is valid Draft-07."""
    errors = []
    for name in SCHEMA_FILES:
        schema = schemas[name]
        try:
            Draft7Validator.check_schema(schema)
        except Exception as e:
            errors.append(f"FAIL check_schema {name}: {e}")
    return errors


def validate_fixtures(schemas, registry):
    """Validate valid and invalid fixtures against their schemas."""
    errors = []
    successes = []
    format_checker = FormatChecker()

    for fixture_dir, expect_valid in [
        (TESTS / "valid", True),
        (TESTS / "invalid", False),
    ]:
        if not fixture_dir.exists():
            continue
        for fixture_file in sorted(fixture_dir.glob("*.json")):
            with open(fixture_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Determine schema from filename prefix
            schema_name = None
            for sn in SCHEMA_FILES:
                prefix = sn.replace(".schema.json", "").replace("-", "_")
                if fixture_file.stem.startswith(prefix):
                    schema_name = sn
                    break
            if not schema_name:
                prefix = fixture_file.stem.split("_")[0]
                for sn in SCHEMA_FILES:
                    if sn.startswith(prefix):
                        schema_name = sn
                        break
            if not schema_name:
                errors.append(f"SKIP {fixture_file.name}: cannot determine schema")
                continue

            schema = schemas[schema_name]
            validator = Draft7Validator(
                schema, registry=registry, format_checker=format_checker
            )
            validation_errors = list(validator.iter_errors(data))

            if expect_valid:
                if validation_errors:
                    for ve in validation_errors:
                        errors.append(
                            f"FAIL valid {fixture_file.name} vs {schema_name}: {ve.message}"
                        )
                else:
                    successes.append(f"PASS {fixture_file.name} (valid)")
            else:
                if validation_errors:
                    successes.append(
                        f"PASS {fixture_file.name} (correctly rejected)"
                    )
                else:
                    errors.append(
                        f"FAIL invalid {fixture_file.name} vs {schema_name}: should be rejected"
                    )

    return errors, successes


def check_schema_fixture_coverage():
    """Verify every schema has at least one valid and one invalid fixture."""
    errors = []
    for name in SCHEMA_FILES:
        prefix = name.replace(".schema.json", "").replace("-", "_")
        valid_fixtures = list((TESTS / "valid").glob(f"{prefix}*.json"))
        invalid_fixtures = list((TESTS / "invalid").glob(f"{prefix}*.json"))
        if not valid_fixtures:
            errors.append(f"COVERAGE: {name} has no valid fixture")
        if not invalid_fixtures:
            errors.append(f"COVERAGE: {name} has no invalid fixture")
    return errors


def check_stage_completeness():
    """Check rebuild-status fixtures have stages 0-6 with correct names."""
    errors = []
    for fixture_file in sorted((TESTS / "valid").glob("rebuild*.json")):
        with open(fixture_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        stages = data.get("stages", [])
        stage_nums = [s["stage"] for s in stages]

        # Unique
        if len(stage_nums) != len(set(stage_nums)):
            errors.append(f"FAIL {fixture_file.name}: duplicate stage numbers")
        # Complete 0-6
        if set(stage_nums) != set(range(7)):
            errors.append(
                f"FAIL {fixture_file.name}: stages must cover 0-6, got {sorted(stage_nums)}"
            )
        # Name mapping
        for s in stages:
            expected = STAGE_NAME_MAP.get(s["stage"])
            if expected and s["name"] != expected:
                errors.append(
                    f"FAIL {fixture_file.name}: stage {s['stage']} name should be '{expected}', got '{s['name']}'"
                )
        # Completed stages should have evidence
        for s in stages:
            if s["status"] == "completed" and not s.get("evidence_event_ids"):
                errors.append(
                    f"FAIL {fixture_file.name}: stage {s['stage']} completed but no evidence_event_ids"
                )
    return errors


def check_route_semantics():
    """Check route record semantic constraints."""
    errors = []
    for fixture_file in sorted((TESTS / "valid").glob("route*.json")):
        with open(fixture_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        route_id = data.get("route_id", "")
        max_hops = data.get("routing_policy", {}).get("max_hops", 16)
        step_ids = {s["route_step_id"] for s in data.get("route_plan", [])}

        # Step ID uniqueness
        if len(step_ids) != len(data.get("route_plan", [])):
            errors.append(f"FAIL {fixture_file.name}: duplicate route_step_id")

        # Dependency references exist
        for step in data.get("route_plan", []):
            for dep in step.get("dependency_step_ids", []):
                if dep not in step_ids:
                    errors.append(
                        f"FAIL {fixture_file.name}: step {step['route_step_id']} depends on non-existent {dep}"
                    )

        # Handoff checks
        for h in data.get("handoffs", []):
            if h.get("route_id") != route_id:
                errors.append(
                    f"FAIL {fixture_file.name}: handoff route_id mismatch"
                )
            if h.get("from_step_id") not in step_ids:
                errors.append(
                    f"FAIL {fixture_file.name}: handoff from_step_id not in route_plan"
                )
            if h.get("to_step_id") not in step_ids:
                errors.append(
                    f"FAIL {fixture_file.name}: handoff to_step_id not in route_plan"
                )
            if h.get("hop_count", 0) > max_hops:
                errors.append(
                    f"FAIL {fixture_file.name}: hop_count {h['hop_count']} > max_hops {max_hops}"
                )
    return errors


def main():
    print("=" * 60)
    print("Phase 2 Contract Schema Validation")
    print("=" * 60)

    schemas = load_schemas()
    registry = build_registry(schemas)

    all_errors = []
    all_successes = []

    # 1. Schema meta-validation
    print(f"\n[1] Schema meta-validation ({len(SCHEMA_FILES)} schemas)")
    meta_errors = check_schema_meta(schemas)
    all_errors.extend(meta_errors)
    if meta_errors:
        for e in meta_errors:
            print(f"  {e}")
    else:
        print(f"  PASS all {len(SCHEMA_FILES)} schemas valid Draft-07")

    # 2. Fixture validation
    print("\n[2] Fixture validation")
    fixture_errors, fixture_successes = validate_fixtures(schemas, registry)
    all_errors.extend(fixture_errors)
    all_successes.extend(fixture_successes)
    for s in fixture_successes:
        print(f"  {s}")
    for e in fixture_errors:
        print(f"  {e}")

    # 3. Coverage
    print("\n[3] Schema fixture coverage")
    coverage_errors = check_schema_fixture_coverage()
    all_errors.extend(coverage_errors)
    if coverage_errors:
        for e in coverage_errors:
            print(f"  {e}")
    else:
        print(f"  PASS all {len(SCHEMA_FILES)} schemas have valid+invalid fixtures")

    # 4. Stage completeness
    print("\n[4] Rebuild Status stage completeness")
    stage_errors = check_stage_completeness()
    all_errors.extend(stage_errors)
    if stage_errors:
        for e in stage_errors:
            print(f"  {e}")
    else:
        print("  PASS stages 0-6 unique with correct names and evidence")

    # 5. Route semantics
    print("\n[5] Route semantic checks")
    route_errors = check_route_semantics()
    all_errors.extend(route_errors)
    if route_errors:
        for e in route_errors:
            print(f"  {e}")
    else:
        print("  PASS step IDs unique, dependencies exist, handoffs consistent")

    # Summary
    print("\n" + "=" * 60)
    print(f"Results: {len(all_successes)} PASS, {len(all_errors)} FAIL")
    print(f"Schemas: {len(SCHEMA_FILES)}")
    valid_count = len(list((TESTS / "valid").glob("*.json")))
    invalid_count = len(list((TESTS / "invalid").glob("*.json")))
    print(f"Fixtures: {valid_count} valid, {invalid_count} invalid")
    print("=" * 60)

    if all_errors:
        print("\nFAILED")
        sys.exit(1)
    else:
        print("\nALL CHECKS PASSED")
        sys.exit(0)


if __name__ == "__main__":
    main()
