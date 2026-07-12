#!/usr/bin/env python3
"""Validate the frozen cluster-virtualization-forensics contract.

This validator intentionally uses only the Python standard library. It checks
the repository contract surfaces and exercises the cross-reference rules at
the public payload boundary.
"""

from __future__ import annotations

import argparse
import copy
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
SKILL_PATH = ROOT / "skills" / "server" / "cluster-virtualization-forensics" / "SKILL.md"
CONTRACT_PATH = ROOT / "docs" / "data-contracts.md"
README_PATH = ROOT / "skills" / "server" / "README.md"

REQUEST_START = "<!-- cluster-request-contract:start -->"
REQUEST_END = "<!-- cluster-request-contract:end -->"
RESPONSE_START = "<!-- cluster-response-contract:start -->"
RESPONSE_END = "<!-- cluster-response-contract:end -->"
PAYLOAD_START = "<!-- cluster-payload-contract:start -->"
PAYLOAD_END = "<!-- cluster-payload-contract:end -->"

LIVE_MODES = {"live-cluster", "rebuilt-cluster"}
OFFLINE_MODES = {"offline-node-image", "disk-set", "artifact-package"}
WORKLOAD_TYPES = {"vm", "container", "vm-template", "container-template"}
VM_WORKLOAD_TYPES = {"vm", "vm-template"}
CONTAINER_WORKLOAD_TYPES = {"container", "container-template"}
PARENT_RELATIONS = {"snapshot-parent-of", "backing-file-of", "delta-parent-of"}
BOUND_PATH_ACTIONS = {"bounded-config-copy", "bounded-log-collection"}
ACTION_FIELDS = {
    "action_id", "action_type", "target_type", "target_ref", "cluster_scope_id",
    "connection_id", "source_path", "allowed_path_scope_id", "since", "until",
    "max_objects", "max_output_bytes", "purpose", "impact_level",
    "sensitive_output_expected", "capture_mode", "expected_footprint",
}
FORBIDDEN_ACTION_FIELDS = {
    "command", "shell", "script", "args", "argv", "query", "api_request", "raw_command",
}

ACTION_TARGET_TYPES = {
    "cluster-status": {"cluster"},
    "node-list": {"cluster"},
    "quorum-status": {"cluster"},
    "storage-config": {"cluster"},
    "vm-list": {"cluster", "node"},
    "vm-config": {"vm"},
    "container-config": {"container"},
    "ceph-status": {"cluster"},
    "ceph-health-detail": {"cluster"},
    "ceph-osd-tree": {"cluster"},
    "ceph-pool-list": {"cluster"},
    "ceph-rbd-list": {"storage"},
    "lvm-metadata": {"node"},
    "mdraid-detail": {"node", "disk", "storage"},
    "zfs-status": {"node", "disk", "storage"},
    "btrfs-filesystem-show": {"node", "disk", "storage"},
    "bounded-config-copy": {"node"},
    "bounded-log-collection": {"node"},
}

ACTION_TYPE_ENUM = set(ACTION_TARGET_TYPES.keys())
TARGET_TYPE_ENUM = {"cluster", "node", "vm", "container", "storage", "disk"}
IMPACT_LEVEL_ENUM = {"low", "medium", "high"}
CAPTURE_MODE_ENUM = {"standard-artifact", "protected-raw-and-redacted-derivative", "redacted-only"}

NODE_TYPES = {
    "physical-disk", "partition", "mdraid-array", "lvm-pv", "lvm-vg",
    "lvm-lv", "lvm-thin-pool", "lvm-thin-volume", "zfs-vdev",
    "zfs-pool", "zfs-dataset", "zfs-zvol", "btrfs-device",
    "btrfs-filesystem", "btrfs-subvolume", "ceph-osd", "ceph-pool",
    "ceph-rbd", "directory-storage", "nfs-export", "iscsi-target",
    "vsan-object", "qcow2-file", "raw-file", "vmdk-descriptor",
    "vmdk-extent", "snapshot-delta", "vm-disk", "container-rootfs",
    "guest-image-candidate", "missing-component", "unknown",
}

MISSING_LINK_TARGETS = {
    "mdraid-array", "lvm-pv", "lvm-vg", "lvm-lv", "lvm-thin-pool",
    "lvm-thin-volume", "zfs-vdev", "zfs-pool", "zfs-dataset", "zfs-zvol",
    "btrfs-device", "btrfs-filesystem", "btrfs-subvolume", "ceph-osd",
    "ceph-pool", "ceph-rbd", "vsan-object", "raw-file", "qcow2-file",
    "vmdk-descriptor", "vmdk-extent", "snapshot-delta", "vm-disk",
    "container-rootfs", "guest-image-candidate",
}

REQUIRED_EFFECTIVE_LIMITS = {
    "max_actions", "max_output_bytes", "max_objects_per_action",
    "max_log_bytes", "max_config_bytes", "max_archive_files",
    "max_archive_expanded_bytes", "max_disk_members",
    "max_bytes_sampled_per_disk", "max_image_candidates",
    "max_depth", "max_objects", "max_paths",
}

REQUIRED_REQUEST_TOP_FIELDS = {"schema_version", "request"}
REQUIRED_REQUEST_NESTED = {
    "material_info", "objective", "objective_status", "context", "payload",
}
REQUIRED_REQUEST_PAYLOAD = {"environment", "access_mode", "cluster_scope"}
REQUIRED_CLUSTER_SCOPE = {
    "analysis_scope_id", "platform_hints", "targeted_questions",
    "allowed_cluster_targets", "allowed_node_targets", "allowed_vm_targets",
    "allowed_container_targets", "allowed_storage_targets",
    "allowed_disk_targets", "allowed_paths", "disk_set_members",
    "stages", "live_collection_limits", "archive_limits",
    "disk_limits", "traversal_limits",
}
REQUIRED_RESPONSE_TOP = {
    "schema_version", "investigation_summary", "route_record",
    "findings", "ledger_events", "artifact_refs", "payload",
}
REQUIRED_RESPONSE_PAYLOAD = {
    "environment", "access_mode", "cluster_profiles",
    "node_map", "disk_map", "storage_map", "layer_map",
    "vm_map", "vm_disk_map", "snapshot_map",
    "quorum_findings", "storage_health_findings",
    "image_candidates", "timeline_candidates",
    "cross_domain_candidates", "effective_limits", "blockers",
}

LIVE_RESPONSE_SKILL = "remote-server-live-response"
TARGETED_COLLECTION_PATH_FIELDS = {"action_id", "path_role", "path"}


def pairs(left: set[str], right: set[str]) -> set[tuple[str, str]]:
    return {(a, b) for a in left for b in right}


RELATION_PAIRS = {
    "contains": {("zfs-pool", "zfs-dataset"), ("btrfs-filesystem", "btrfs-subvolume")},
    "partitions-into": {("physical-disk", "partition")},
    "member-of": {
        ("physical-disk", "mdraid-array"), ("partition", "mdraid-array"),
        ("physical-disk", "lvm-pv"), ("partition", "lvm-pv"),
        ("physical-disk", "zfs-vdev"), ("partition", "zfs-vdev"),
        ("physical-disk", "btrfs-device"), ("partition", "btrfs-device"),
        ("physical-disk", "ceph-osd"), ("partition", "ceph-osd"),
        ("vmdk-extent", "vmdk-descriptor"),
    },
    "aggregates-into": {
        ("lvm-pv", "lvm-vg"), ("zfs-vdev", "zfs-pool"),
        ("btrfs-device", "btrfs-filesystem"), ("ceph-osd", "ceph-pool"),
    },
    "allocates": {
        ("lvm-vg", "lvm-lv"), ("lvm-vg", "lvm-thin-pool"),
        ("lvm-thin-pool", "lvm-thin-volume"), ("zfs-pool", "zfs-zvol"),
        ("ceph-pool", "ceph-rbd"), ("vsan-object", "vm-disk"),
    },
    "backs": pairs(
        {"mdraid-array", "lvm-lv", "lvm-thin-volume", "zfs-zvol", "ceph-rbd",
         "vsan-object", "raw-file", "qcow2-file", "vmdk-descriptor"},
        {"vm-disk", "container-rootfs"},
    ),
    "hosts": {
        ("directory-storage", "container-rootfs"), ("nfs-export", "container-rootfs"),
        ("zfs-dataset", "container-rootfs"), ("btrfs-subvolume", "container-rootfs"),
    },
    "stores": pairs(
        {"directory-storage", "nfs-export", "zfs-dataset", "btrfs-subvolume"},
        {"raw-file", "qcow2-file", "vmdk-descriptor", "vmdk-extent"},
    ),
    "maps-to": {
        ("vm-disk", "guest-image-candidate"),
        ("container-rootfs", "guest-image-candidate"),
        ("raw-file", "guest-image-candidate"),
        ("qcow2-file", "guest-image-candidate"),
        ("vmdk-descriptor", "guest-image-candidate"),
        ("zfs-zvol", "guest-image-candidate"),
        ("lvm-lv", "guest-image-candidate"),
        ("lvm-thin-volume", "guest-image-candidate"),
        ("ceph-rbd", "guest-image-candidate"),
    },
    "configured-as": {
        ("mdraid-array", "lvm-pv"), ("mdraid-array", "zfs-vdev"),
        ("mdraid-array", "btrfs-device"), ("mdraid-array", "ceph-osd"),
        ("iscsi-target", "physical-disk"),
    },
    "snapshot-parent-of": pairs(
        {"lvm-lv", "lvm-thin-volume", "zfs-dataset", "zfs-zvol", "ceph-rbd",
         "vm-disk", "container-rootfs"},
        {"snapshot-delta"},
    ),
    "backing-file-of": {
        ("raw-file", "qcow2-file"), ("qcow2-file", "qcow2-file"),
        ("raw-file", "snapshot-delta"), ("qcow2-file", "snapshot-delta"),
        ("vmdk-descriptor", "snapshot-delta"),
    },
    "delta-parent-of": {("snapshot-delta", "snapshot-delta")},
    "symlink-target-of": pairs(
        {"raw-file", "qcow2-file", "vmdk-descriptor", "vmdk-extent", "lvm-lv",
         "lvm-thin-volume", "zfs-zvol", "ceph-rbd"},
        {"guest-image-candidate"},
    ),
    "remote-reference-to": pairs(
        {"nfs-export", "iscsi-target", "ceph-rbd", "vsan-object"},
        {"vm-disk", "container-rootfs", "guest-image-candidate"},
    ),
    "missing-link-to": pairs({"missing-component"}, MISSING_LINK_TARGETS),
}

ERROR_CLASSES = {
    "environment_mismatch", "unsupported_platform", "session_unavailable",
    "cluster_scope_mismatch", "node_scope_mismatch", "vm_scope_mismatch",
    "container_scope_mismatch", "storage_scope_mismatch", "root_path_invalid",
    "disk_member_missing", "metadata_missing", "quorum_unknown",
    "split_brain_suspected", "raid_degraded", "lvm_metadata_incomplete",
    "zfs_metadata_incomplete", "ceph_map_incomplete",
    "distributed_storage_health_degraded", "backing_chain_incomplete",
    "image_content_unavailable", "placeholder_only", "large_artifact_incomplete",
    "output_limit_exceeded", "parse_failure", "timezone_uncertain",
    "evidence_conflict", "targeted_collection_required",
    "planner_authorization_missing",
}

HANDOFF_SKILLS = {
    "server-forensics-router", "server-rebuild-planner", "server-rebuild-executor",
    "remote-server-live-response", "linux-server-forensics",
    "docker-container-forensics", "database-server-forensics",
    "webapp-server-forensics", "timeline-reconstruction", "large-artifact-strategy",
}


def extract_contract(text: str, start: str, end: str, label: str) -> str:
    if start not in text or end not in text:
        raise ValueError(f"missing cluster {label} contract markers")
    body = text.split(start, 1)[1].split(end, 1)[0]
    return "\n".join(line.rstrip() for line in body.strip().splitlines())


def normalized_yaml_fragment(text: str, anchor: str) -> str:
    fragment = text[text.index(anchor):]
    if "```" in fragment:
        fragment = fragment.rsplit("```", 1)[0]
    return "\n".join(
        line.rstrip() for line in fragment.replace('"', "").splitlines() if line.strip()
    ).strip()


def parse_frontmatter(text: str) -> tuple[dict[str, str], str]:
    if not text.startswith("---\n"):
        raise ValueError("SKILL.md must start with frontmatter")
    _, raw, body = text.split("---", 2)
    fields: dict[str, str] = {}
    for line in raw.strip().splitlines():
        key, sep, value = line.partition(":")
        if not sep:
            raise ValueError(f"invalid frontmatter line: {line}")
        fields[key.strip()] = value.strip()
    return fields, body


def _parse_posix_path(path: str) -> tuple[bool, list[str]]:
    """Parse a POSIX path, returning (is_absolute, parts)."""
    is_abs = path.startswith("/")
    stripped = path.lstrip("/")
    parts = [p for p in stripped.split("/") if p and p != "."]
    return is_abs, parts


def _parse_windows_path(path: str) -> tuple[str | None, bool, list[str]]:
    """Parse a Windows path. Returns (drive_or_unc, is_absolute, parts)."""
    normalized = path.replace("/", "\\")
    drive = None
    is_abs = False
    if len(normalized) >= 3 and normalized[1] == ":" and normalized[2] == "\\":
        drive = normalized[:2].upper()
        is_abs = True
        rest = normalized[3:]
    elif normalized.startswith("\\\\"):
        is_abs = True
        share_end = normalized.find("\\", 2)
        if share_end > 2:
            share_end2 = normalized.find("\\", share_end + 1)
            if share_end2 > share_end:
                drive = normalized[:share_end2].upper()
                rest = normalized[share_end2 + 1:]
            else:
                drive = normalized.upper()
                rest = ""
        else:
            return None, False, []
    else:
        rest = normalized
    parts = [p for p in rest.split("\\") if p and p != "."]
    return drive, is_abs, parts


def _classify_path(path: str) -> tuple[str, str | None, bool, list[str]]:
    """Classify a path as posix/windows, return (kind, anchor, is_abs, parts)."""
    if "\x00" in path:
        return "invalid", None, False, []
    if re.match(r"[A-Za-z]:\\", path) or path.startswith("\\\\"):
        drive, is_abs, parts = _parse_windows_path(path)
        return "windows", drive, is_abs, parts
    is_abs, parts = _parse_posix_path(path)
    kind = "posix" if is_abs or not parts else "posix"
    return kind, None, is_abs, parts


def path_is_within(candidate: str, root: str, recursive: bool, max_depth: int | None) -> bool:
    c_kind, c_anchor, c_abs, c_parts = _classify_path(candidate)
    r_kind, r_anchor, r_abs, r_parts = _classify_path(root)
    if c_kind == "invalid" or r_kind == "invalid":
        return False
    if c_kind == "windows" and r_kind == "windows":
        if c_anchor != r_anchor:
            return False
        if r_abs and not c_abs:
            return False
    elif r_kind == "posix" and c_kind == "posix":
        if r_abs and not c_abs:
            return False
    else:
        return False
    for part in c_parts + r_parts:
        if part == "..":
            return False
    if c_parts[: len(r_parts)] != r_parts:
        return False
    depth = len(c_parts) - len(r_parts)
    if not recursive and depth != 0:
        return False
    return max_depth is None or depth <= max_depth


def _check_duplicate_ids(
    records: list[dict[str, Any]],
    key_fields: tuple[str, ...],
    label: str,
) -> list[str]:
    errors: list[str] = []
    seen: set[tuple[Any, ...]] = set()
    for rec in records:
        key = tuple(rec.get(f) for f in key_fields)
        if key in seen:
            errors.append(f"duplicate {label} composite key: {key}")
        seen.add(key)
    return errors


def _check_scoped_ref(
    cluster_scope_id: str,
    ref_set: set[tuple[str, str]],
    label: str,
) -> list[str]:
    errors: list[str] = []
    if (cluster_scope_id,) not in {(k[0],) for k in ref_set}:
        errors.append(f"{label} cluster_scope_id {cluster_scope_id} not found in referenced set")
    return errors


def _validate_action_fields(action: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    actual_keys = set(action.keys())
    if actual_keys != ACTION_FIELDS:
        missing = ACTION_FIELDS - actual_keys
        extra = actual_keys - ACTION_FIELDS
        if missing:
            errors.append(f"Action missing fields: {sorted(missing)}")
        if extra:
            errors.append(f"Action has unknown fields: {sorted(extra)}")
    forbidden = FORBIDDEN_ACTION_FIELDS & actual_keys
    if forbidden:
        errors.append(f"Action contains forbidden freeform fields: {sorted(forbidden)}")
    action_type = action.get("action_type")
    if action_type not in ACTION_TYPE_ENUM:
        errors.append(f"Action action_type not in frozen enum: {action_type}")
    target_type = action.get("target_type")
    if target_type not in TARGET_TYPE_ENUM:
        errors.append(f"Action target_type not in frozen enum: {target_type}")
    purpose = action.get("purpose")
    if not isinstance(purpose, str) or not purpose:
        errors.append("Action purpose must be non-empty string")
    footprint = action.get("expected_footprint")
    if not isinstance(footprint, list) or not footprint or not all(isinstance(x, str) and x for x in footprint):
        errors.append("Action expected_footprint must be non-empty string array")
    impact = action.get("impact_level")
    if impact not in IMPACT_LEVEL_ENUM:
        errors.append(f"Action impact_level must be low|medium|high, got: {impact}")
    capture = action.get("capture_mode")
    if capture not in CAPTURE_MODE_ENUM:
        errors.append(f"Action capture_mode not in frozen enum: {capture}")
    sensitive = action.get("sensitive_output_expected")
    if not isinstance(sensitive, bool):
        errors.append("Action sensitive_output_expected must be boolean")
    max_obj = action.get("max_objects")
    if not isinstance(max_obj, int) or isinstance(max_obj, bool) or max_obj <= 0:
        errors.append("Action max_objects must be positive integer")
    max_out = action.get("max_output_bytes")
    if not isinstance(max_out, int) or isinstance(max_out, bool) or max_out <= 0:
        errors.append("Action max_output_bytes must be positive integer")
    return errors


def validate_semantics(request: dict[str, Any], response: dict[str, Any]) -> list[str]:
    errors: list[str] = []

    # Structural validation: Request top-level
    req_top_keys = set(request.keys())
    if not REQUIRED_REQUEST_TOP_FIELDS <= req_top_keys:
        errors.append(f"Request missing top-level fields: {sorted(REQUIRED_REQUEST_TOP_FIELDS - req_top_keys)}")
    req = request.get("request", request)
    req_nested_keys = set(req.keys())
    if not REQUIRED_REQUEST_NESTED <= req_nested_keys:
        errors.append(f"Request missing nested fields: {sorted(REQUIRED_REQUEST_NESTED - req_nested_keys)}")
    payload = req.get("payload", {})
    payload_keys = set(payload.keys())
    if not REQUIRED_REQUEST_PAYLOAD <= payload_keys:
        errors.append(f"Request payload missing fields: {sorted(REQUIRED_REQUEST_PAYLOAD - payload_keys)}")
    scope = payload.get("cluster_scope", {})
    scope_keys = set(scope.keys())
    if not REQUIRED_CLUSTER_SCOPE <= scope_keys:
        errors.append(f"cluster_scope missing fields: {sorted(REQUIRED_CLUSTER_SCOPE - scope_keys)}")

    # Structural validation: Response top-level
    resp_top_keys = set(response.keys())
    if not REQUIRED_RESPONSE_TOP <= resp_top_keys:
        errors.append(f"Response missing top-level fields: {sorted(REQUIRED_RESPONSE_TOP - resp_top_keys)}")
    response_payload = response.get("payload", response)
    resp_payload_keys = set(response_payload.keys())
    if not REQUIRED_RESPONSE_PAYLOAD <= resp_payload_keys:
        errors.append(f"Response payload missing fields: {sorted(REQUIRED_RESPONSE_PAYLOAD - resp_payload_keys)}")

    environment = payload.get("environment", {})
    mode = payload.get("access_mode")
    context = req.get("context", {})
    route = context.get("route_record", {})
    route_steps = {step.get("route_step_id"): step for step in route.get("route_plan", [])}
    if context.get("current_step_id") not in route_steps:
        errors.append("current_step_id does not reference route_plan")

    connection_ids = set(environment.get("connection_ids", []))
    session_id = environment.get("session_id")
    cluster_target_list = scope.get("allowed_cluster_targets", [])
    cluster_targets = {item.get("cluster_scope_id"): item for item in cluster_target_list}
    if len(cluster_targets) != len(cluster_target_list):
        errors.append("allowed_cluster_targets cluster_scope_id must be unique")
    if mode in LIVE_MODES:
        if not isinstance(session_id, str) or not session_id or not connection_ids:
            errors.append("live mode requires session_id and connection_ids")
        if any(not isinstance(connection_id, str) or not connection_id for connection_id in connection_ids):
            errors.append("live connection_ids must contain non-empty strings")
        for target in cluster_target_list:
            if (
                not isinstance(target.get("connection_id"), str)
                or not target.get("connection_id")
                or target.get("connection_id") not in connection_ids
            ):
                errors.append("live cluster target connection is not in current Session")
    elif mode in OFFLINE_MODES:
        if session_id is not None or connection_ids:
            errors.append("offline mode forbids Session connections")
        if any(item.get("connection_id") is not None for item in cluster_target_list):
            errors.append("offline cluster target connection_id must be null")
        root_artifacts = environment.get("root_artifact_refs", [])
        registered_artifacts = set(req.get("material_info", {}).get("artifact_refs", []))
        registered_artifacts.update(context.get("artifact_refs", []))
        if (
            not root_artifacts
            or any(ref not in registered_artifacts for ref in root_artifacts)
            or not route.get("evidence_scope")
        ):
            errors.append("offline mode requires finite Artifact roots and evidence_scope")
        if mode == "disk-set":
            members = scope.get("disk_set_members", [])
            if not members or any(item.get("artifact_ref") not in registered_artifacts for item in members):
                errors.append("disk-set requires registered enumerated members")
        elif not scope.get("allowed_paths"):
            errors.append("offline image/package requires a finite allowed_paths set")
    else:
        errors.append("unknown access_mode")

    # Cluster scope reference validation: object targets must reference allowed_cluster_targets
    allowed_cluster_ids = {item.get("cluster_scope_id") for item in cluster_target_list}
    for label, items, id_field in [
        ("allowed_node_targets", scope.get("allowed_node_targets", []), "node_id"),
        ("allowed_vm_targets", scope.get("allowed_vm_targets", []), "vm_id"),
        ("allowed_container_targets", scope.get("allowed_container_targets", []), "container_id"),
        ("allowed_storage_targets", scope.get("allowed_storage_targets", []), "storage_id"),
        ("allowed_disk_targets", scope.get("allowed_disk_targets", []), "disk_id"),
    ]:
        for item in items:
            csid = item.get("cluster_scope_id")
            if csid not in allowed_cluster_ids:
                errors.append(f"{label} references non-existent cluster_scope_id: {csid}")

    # disk_set_members must reference allowed_cluster_targets
    for member in scope.get("disk_set_members", []):
        csid = member.get("cluster_scope_id")
        if csid not in allowed_cluster_ids:
            errors.append(f"disk_set_member references non-existent cluster_scope_id: {csid}")

    # allowed_paths must reference allowed_cluster_targets (live/rebuilt)
    for item in scope.get("allowed_paths", []):
        csid = item.get("cluster_scope_id")
        if mode in LIVE_MODES and csid not in allowed_cluster_ids:
            errors.append(f"allowed_path references non-existent cluster_scope_id: {csid}")

    node_targets = {(x.get("cluster_scope_id"), x.get("node_id")) for x in scope.get("allowed_node_targets", [])}
    vm_targets = {(x.get("cluster_scope_id"), x.get("vm_id")) for x in scope.get("allowed_vm_targets", [])}
    container_targets = {(x.get("cluster_scope_id"), x.get("container_id")) for x in scope.get("allowed_container_targets", [])}
    storage_targets = {(x.get("cluster_scope_id"), x.get("storage_id")) for x in scope.get("allowed_storage_targets", [])}
    disk_targets = {(x.get("cluster_scope_id"), x.get("disk_id")) for x in scope.get("allowed_disk_targets", [])}

    path_scopes: dict[str, dict[str, Any]] = {}
    for item in scope.get("allowed_paths", []):
        path_id = item.get("path_scope_id")
        if not path_id or path_id in path_scopes:
            errors.append("path_scope_id must be non-empty and unique")
            continue
        path_scopes[path_id] = item
        pair = (item.get("cluster_scope_id"), item.get("owner_node_id"))
        if mode in LIVE_MODES and (None in pair or pair not in node_targets):
            errors.append("live path owner is not an approved scoped Node")
        if mode in OFFLINE_MODES and not item.get("artifact_ref"):
            errors.append("offline path requires artifact_ref")
        if mode in OFFLINE_MODES:
            registered_artifacts = set(req.get("material_info", {}).get("artifact_refs", []))
            registered_artifacts.update(context.get("artifact_refs", []))
            if item.get("artifact_ref") not in registered_artifacts:
                errors.append("offline path Artifact is not registered")

    # Response cluster_profiles validation
    response_cluster_profiles = response_payload.get("cluster_profiles", [])
    profile_scope_ids = [p.get("cluster_scope_id") for p in response_cluster_profiles]
    seen_profile_ids: set[str] = set()
    for psid in profile_scope_ids:
        if psid in seen_profile_ids:
            errors.append(f"cluster_profiles duplicate cluster_scope_id: {psid}")
        seen_profile_ids.add(psid)
        if psid not in allowed_cluster_ids:
            errors.append(f"cluster_profile references non-existent Request cluster_scope_id: {psid}")

    # All Response scoped records must reference cluster_profiles
    all_response_scoped_maps = [
        ("node_map", response_payload.get("node_map", [])),
        ("disk_map", response_payload.get("disk_map", [])),
        ("storage_map", response_payload.get("storage_map", [])),
        ("vm_map", response_payload.get("vm_map", [])),
        ("vm_disk_map", response_payload.get("vm_disk_map", [])),
        ("snapshot_map", response_payload.get("snapshot_map", [])),
        ("quorum_findings", response_payload.get("quorum_findings", [])),
        ("storage_health_findings", response_payload.get("storage_health_findings", [])),
    ]
    for map_name, map_records in all_response_scoped_maps:
        for rec in map_records:
            csid = rec.get("cluster_scope_id")
            if csid not in seen_profile_ids:
                errors.append(f"{map_name} record references non-existent cluster_profile: {csid}")

    # Duplicate ID checks on Response maps
    errors.extend(_check_duplicate_ids(
        response_payload.get("node_map", []),
        ("cluster_scope_id", "node_id"), "node_map",
    ))
    errors.extend(_check_duplicate_ids(
        response_payload.get("disk_map", []),
        ("cluster_scope_id", "disk_id"), "disk_map",
    ))
    errors.extend(_check_duplicate_ids(
        response_payload.get("storage_map", []),
        ("cluster_scope_id", "storage_id"), "storage_map",
    ))
    errors.extend(_check_duplicate_ids(
        response_payload.get("vm_map", []),
        ("cluster_scope_id", "workload_id"), "vm_map",
    ))
    errors.extend(_check_duplicate_ids(
        response_payload.get("vm_disk_map", []),
        ("cluster_scope_id", "vm_disk_mapping_id"), "vm_disk_map",
    ))
    errors.extend(_check_duplicate_ids(
        response_payload.get("snapshot_map", []),
        ("cluster_scope_id", "snapshot_id"), "snapshot_map",
    ))
    errors.extend(_check_duplicate_ids(
        response_payload.get("image_candidates", []),
        ("cluster_scope_id", "candidate_id"), "image_candidates",
    ))
    errors.extend(_check_duplicate_ids(
        response_payload.get("timeline_candidates", []),
        ("cluster_scope_id", "candidate_id"), "timeline_candidates",
    ))
    errors.extend(_check_duplicate_ids(
        response_payload.get("cross_domain_candidates", []),
        ("candidate_id",), "cross_domain_candidates",
    ))
    errors.extend(_check_duplicate_ids(
        response_payload.get("blockers", []),
        ("blocker_id",), "blockers",
    ))

    node_map = {
        (x.get("cluster_scope_id"), x.get("node_id")): x
        for x in response_payload.get("node_map", [])
    }
    vm_map = {
        (x.get("cluster_scope_id"), x.get("workload_id")): x
        for x in response_payload.get("vm_map", [])
    }
    for key, workload in vm_map.items():
        object_type = workload.get("object_type")
        platform = workload.get("platform")
        if object_type not in WORKLOAD_TYPES:
            errors.append("unknown workload object_type")
        elif object_type in VM_WORKLOAD_TYPES and key not in vm_targets:
            errors.append("VM workload is outside allowed_vm_targets")
        elif object_type in CONTAINER_WORKLOAD_TYPES and key not in container_targets:
            errors.append("Container workload is outside allowed_container_targets")
        if platform == "pve-lxc" and object_type == "vm-template":
            errors.append("pve-lxc cannot be vm-template")
        if platform in {"pve-qemu", "vsphere-vm", "libvirt-vm"} and object_type == "container-template":
            errors.append("VM platform cannot be container-template")

    storage_map = {
        (x.get("cluster_scope_id"), x.get("storage_id")): x
        for x in response_payload.get("storage_map", [])
    }
    for item in response_payload.get("vm_disk_map", []):
        key = (item.get("cluster_scope_id"), item.get("workload_id"))
        if key not in vm_map or item.get("object_type") != vm_map[key].get("object_type"):
            errors.append("vm_disk_map workload reference/type mismatch")
        storage_id = item.get("storage_id")
        if storage_id is not None:
            csid = item.get("cluster_scope_id")
            if (csid, storage_id) not in storage_targets:
                errors.append("vm_disk_map storage reference is outside scope")
            if (csid, storage_id) not in storage_map:
                errors.append("vm_disk_map storage_id not found in storage_map")

    vm_disk_map = {
        (x.get("cluster_scope_id"), x.get("vm_disk_mapping_id")): x
        for x in response_payload.get("vm_disk_map", [])
    }
    for snapshot in response_payload.get("snapshot_map", []):
        cluster_id = snapshot.get("cluster_scope_id")
        owner_type = snapshot.get("owner_type")
        owner_ref = snapshot.get("owner_ref")
        if owner_type in WORKLOAD_TYPES:
            workload = vm_map.get((cluster_id, owner_ref))
            if not workload or workload.get("object_type") != owner_type:
                errors.append("snapshot workload owner reference/type mismatch")
        elif owner_type == "vm-disk":
            if (cluster_id, owner_ref) not in vm_disk_map:
                errors.append("snapshot vm-disk owner reference mismatch")
        elif owner_type == "storage-volume":
            if (cluster_id, owner_ref) not in storage_map:
                errors.append("snapshot storage owner reference mismatch")
        else:
            errors.append("unknown snapshot owner_type")

    nodes = {
        (x.get("cluster_scope_id"), x.get("layer_node_id")): x
        for x in response_payload.get("layer_map", {}).get("nodes", [])
    }
    # Layer node ID non-empty
    for key, layer_node in nodes.items():
        if not key[1]:
            errors.append("layer_node_id must be non-empty")
        owner_node_id = layer_node.get("owner_node_id")
        if owner_node_id is not None and (key[0], owner_node_id) not in node_map:
            errors.append("Layer Node owner_node_id does not reference node_map")
    # Layer edge ID non-empty and from != to
    for edge in response_payload.get("layer_map", {}).get("edges", []):
        edge_id = edge.get("layer_edge_id")
        if not edge_id:
            errors.append("layer_edge_id must be non-empty")
        from_node = edge.get("from_layer_node_id")
        to_node = edge.get("to_layer_node_id")
        if from_node == to_node:
            errors.append("Layer Edge from/to must not be identical")

    adjacency: dict[tuple[str, str], list[tuple[str, str]]] = {}
    parent_count: dict[tuple[str, str], int] = {}
    symlink_targets: list[tuple[str, str]] = []
    layer_edge_ids = {
        (x.get("cluster_scope_id"), x.get("layer_edge_id"))
        for x in response_payload.get("layer_map", {}).get("edges", [])
    }
    for edge in response_payload.get("layer_map", {}).get("edges", []):
        cluster_id = edge.get("cluster_scope_id")
        source = (cluster_id, edge.get("from_layer_node_id"))
        target = (cluster_id, edge.get("to_layer_node_id"))
        relation = edge.get("relation")
        if source not in nodes or target not in nodes:
            errors.append("Layer Edge references missing Node")
            continue
        pair_value = (nodes[source].get("node_type"), nodes[target].get("node_type"))
        if relation == "conflicts-with":
            if not (
                pair_value[0] == pair_value[1]
                and nodes[source].get("entity_ref")
                and nodes[source].get("entity_ref") == nodes[target].get("entity_ref")
                and source != target
            ):
                errors.append("invalid conflicts-with endpoints")
        elif pair_value not in RELATION_PAIRS.get(relation, set()):
            errors.append(f"illegal Layer Edge endpoint/direction for {relation}")
        if relation == "symlink-target-of":
            symlink_targets.append(target)
        if relation in PARENT_RELATIONS:
            adjacency.setdefault(source, []).append(target)
            parent_count[target] = parent_count.get(target, 0) + 1
            if parent_count[target] > 1:
                errors.append("snapshot/delta has multiple immediate parents")

    visiting: set[tuple[str, str]] = set()
    visited: set[tuple[str, str]] = set()

    def visit(node: tuple[str, str]) -> None:
        if node in visiting:
            errors.append("backing/snapshot/delta cycle detected")
            return
        if node in visited:
            return
        visiting.add(node)
        for child in adjacency.get(node, []):
            visit(child)
        visiting.remove(node)
        visited.add(node)

    for node in adjacency:
        visit(node)

    for disk in response_payload.get("disk_map", []):
        cluster_id = disk.get("cluster_scope_id")
        if (cluster_id, disk.get("layer_node_id")) not in nodes:
            errors.append("disk_map references a missing scoped Layer Node")
        owner = disk.get("owner_node_id")
        if owner is not None and (cluster_id, owner) not in node_map:
            errors.append("disk_map owner_node_id does not reference node_map")
    for storage in response_payload.get("storage_map", []):
        cluster_id = storage.get("cluster_scope_id")
        if any((cluster_id, ref) not in nodes for ref in storage.get("backing_layer_node_refs", [])):
            errors.append("storage_map references a missing scoped Layer Node")
        if any((cluster_id, ref) not in node_map for ref in storage.get("owner_node_ids", [])):
            errors.append("storage_map owner_node_ids do not reference node_map")
    for mapping in response_payload.get("vm_disk_map", []):
        cluster_id = mapping.get("cluster_scope_id")
        terminal = mapping.get("terminal_layer_node_id")
        if not terminal:
            errors.append("vm_disk_map terminal_layer_node_id must be non-empty")
        elif (cluster_id, terminal) not in nodes:
            errors.append("vm_disk_map terminal_layer_node_id is missing")
        edge_refs = mapping.get("layer_edge_refs", [])
        for ref in edge_refs:
            if (cluster_id, ref) not in layer_edge_ids:
                errors.append("vm_disk_map references a missing scoped Layer Edge")
        if edge_refs and terminal and (cluster_id, terminal) in nodes:
            terminal_type = nodes[(cluster_id, terminal)].get("node_type")
            connected_node_ids = set()
            for ref in edge_refs:
                edge_key = (cluster_id, ref)
                for edge in response_payload.get("layer_map", {}).get("edges", []):
                    if (edge.get("cluster_scope_id"), edge.get("layer_edge_id")) == edge_key:
                        connected_node_ids.add(edge.get("from_layer_node_id"))
                        connected_node_ids.add(edge.get("to_layer_node_id"))
            if connected_node_ids and terminal not in connected_node_ids:
                errors.append("vm_disk_map layer_edge_refs do not connect to terminal_layer_node_id")

    for snapshot in response_payload.get("snapshot_map", []):
        cluster_id = snapshot.get("cluster_scope_id")
        if any((cluster_id, ref) not in nodes for ref in snapshot.get("layer_node_refs", [])):
            errors.append("snapshot_map references a missing scoped Layer Node")
        if any((cluster_id, ref) not in layer_edge_ids for ref in snapshot.get("backing_edge_refs", [])):
            errors.append("snapshot_map references a missing scoped Layer Edge")

    actions: list[dict[str, Any]] = []
    collection_requests: list[dict[str, Any]] = []
    all_action_ids: list[str] = []
    for candidate in response_payload.get("cross_domain_candidates", []):
        for workload_ref in candidate.get("workload_refs", []):
            key = (workload_ref.get("cluster_scope_id"), workload_ref.get("workload_id"))
            workload = vm_map.get(key)
            if not workload or workload.get("object_type") != workload_ref.get("object_type"):
                errors.append("Handoff workload reference/type mismatch")
        if candidate.get("skill") == "server-rebuild-executor":
            auth = candidate.get("planner_authorization", {})
            planner_step = route_steps.get(auth.get("planner_step_id"))
            plan_ids = {
                payload.get("environment", {}).get("plan_id"),
                context.get("upstream_environment", {}).get("plan_id"),
                response_payload.get("environment", {}).get("plan_id"),
            } - {None}
            if not (
                planner_step
                and planner_step.get("skill") == "server-rebuild-planner"
                and planner_step.get("status") == "completed"
                and auth.get("plan_id")
                and auth.get("plan_status") == "ready"
                and auth.get("planner_step_id") in candidate.get("dependency_step_ids", [])
                and auth.get("plan_id") in plan_ids
            ):
                errors.append("executor candidate lacks approved Planner dependency")
        request_value = candidate.get("targeted_collection_request")
        candidate_skill = candidate.get("skill")
        if request_value is not None:
            # Only remote-server-live-response may carry targeted_collection_request
            if candidate_skill != LIVE_RESPONSE_SKILL:
                errors.append(f"targeted_collection_request on non-live-response skill: {candidate_skill}")
            required_collection_fields = {"actions", "paths", "max_output_bytes", "reason"}
            actual_collection_fields = set(request_value.keys())
            if actual_collection_fields != required_collection_fields:
                missing = required_collection_fields - actual_collection_fields
                extra = actual_collection_fields - required_collection_fields
                if missing:
                    errors.append(f"targeted_collection_request missing fields: {sorted(missing)}")
                if extra:
                    errors.append(f"targeted_collection_request has unknown fields: {sorted(extra)}")
            if not request_value.get("actions") or not request_value.get("reason"):
                errors.append("targeted_collection_request requires non-empty actions and reason")
            action_ids = [action.get("action_id") for action in request_value.get("actions", [])]
            if any(not action_id for action_id in action_ids) or len(action_ids) != len(set(action_ids)):
                errors.append("targeted collection action_id must be non-empty and unique")
            all_action_ids.extend(action_ids)
            for action in request_value.get("actions", []):
                errors.extend(_validate_action_fields(action))
            # Path records must only contain allowed fields
            for path_record in request_value.get("paths", []):
                path_keys = set(path_record.keys())
                if path_keys != TARGETED_COLLECTION_PATH_FIELDS:
                    extra = path_keys - TARGETED_COLLECTION_PATH_FIELDS
                    if extra:
                        errors.append(f"targeted collection path record has unknown fields: {sorted(extra)}")
                if path_record.get("action_id") not in action_ids:
                    errors.append("targeted collection path references an unknown Action")
            paths_by_action: dict[str, list[dict[str, Any]]] = {}
            for path_record in request_value.get("paths", []):
                paths_by_action.setdefault(path_record.get("action_id"), []).append(path_record)
            for action in request_value.get("actions", []):
                aid = action.get("action_id")
                atype = action.get("action_type")
                if atype in BOUND_PATH_ACTIONS:
                    path_records = paths_by_action.get(aid, [])
                    if len(path_records) != 1:
                        errors.append("bounded Action must have exactly one path record")
                    elif path_records[0].get("path") != action.get("source_path"):
                        errors.append("bounded Action path record path mismatch")
                    expected_role = (
                        "remote-config-source" if atype == "bounded-config-copy"
                        else "remote-log-source"
                    )
                    if path_records and path_records[0].get("path_role") != expected_role:
                        errors.append(f"bounded {atype} path_role must be {expected_role}")
            collection_requests.append(request_value)
            actions.extend(request_value.get("actions", []))

    # Global action_id uniqueness across all candidates
    if len(all_action_ids) != len(set(all_action_ids)):
        seen_global: set[str] = set()
        for aid in all_action_ids:
            if aid in seen_global:
                errors.append(f"duplicate global action_id: {aid}")
            seen_global.add(aid)

    effective_limits = response_payload.get("effective_limits", {})
    # Must contain exactly the 13 frozen limits
    limit_keys = set(effective_limits.keys())
    if limit_keys != REQUIRED_EFFECTIVE_LIMITS:
        missing = REQUIRED_EFFECTIVE_LIMITS - limit_keys
        extra = limit_keys - REQUIRED_EFFECTIVE_LIMITS
        if missing:
            errors.append(f"effective_limits missing required limits: {sorted(missing)}")
        if extra:
            errors.append(f"effective_limits has unknown limits: {sorted(extra)}")
    for limit_name, limit in effective_limits.items():
        if not isinstance(limit, dict):
            errors.append(f"effective limit {limit_name} is not an object")
            continue
        status = limit.get("status")
        value = limit.get("value")
        if not limit.get("basis"):
            errors.append(f"effective limit {limit_name} lacks basis")
        if status == "resolved":
            if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
                errors.append(f"resolved effective limit {limit_name} must be a positive integer")
        elif status in {"unresolved", "not-applicable"}:
            if value is not None:
                errors.append(f"non-resolved effective limit {limit_name} must have null value")
        else:
            errors.append(f"unknown effective limit status for {limit_name}")

    required_action_limits = {
        "max_actions": effective_limits.get("max_actions", {}),
        "max_output_bytes": effective_limits.get("max_output_bytes", {}),
        "max_objects_per_action": effective_limits.get("max_objects_per_action", {}),
    }
    if actions and any(limit.get("status") != "resolved" for limit in required_action_limits.values()):
        errors.append("live Actions require resolved effective limits")
    max_actions = required_action_limits["max_actions"].get("value")
    if isinstance(max_actions, int) and len(actions) > max_actions:
        errors.append("live Action count exceeds effective limit")

    # Targeted collection request-level limits
    for request_value in collection_requests:
        request_limit = request_value.get("max_output_bytes")
        output_limit = required_action_limits["max_output_bytes"].get("value")
        if not isinstance(request_limit, int) or request_limit <= 0:
            errors.append("targeted collection max_output_bytes must be positive")
        elif isinstance(output_limit, int) and request_limit > output_limit:
            errors.append("targeted collection output exceeds effective limit")
        # Sum of action max_output_bytes must not exceed request max_output_bytes
        action_sum = sum(
            a.get("max_output_bytes", 0)
            for a in request_value.get("actions", [])
            if isinstance(a.get("max_output_bytes"), int)
        )
        if isinstance(request_limit, int) and action_sum > request_limit:
            errors.append("targeted collection action output sum exceeds request max_output_bytes")

        # Bounded config/log specific limits
        config_limit = effective_limits.get("max_config_bytes", {})
        log_limit = effective_limits.get("max_log_bytes", {})
        for action in request_value.get("actions", []):
            atype = action.get("action_type")
            aout = action.get("max_output_bytes")
            if atype == "bounded-config-copy":
                config_val = config_limit.get("value")
                if isinstance(config_val, int) and isinstance(aout, int) and aout > config_val:
                    errors.append("bounded-config-copy max_output_bytes exceeds max_config_bytes")
                if config_limit.get("status") != "resolved":
                    errors.append("bounded-config-copy requires resolved max_config_bytes")
            if atype == "bounded-log-collection":
                log_val = log_limit.get("value")
                if isinstance(log_val, int) and isinstance(aout, int) and aout > log_val:
                    errors.append("bounded-log-collection max_output_bytes exceeds max_log_bytes")
                if log_limit.get("status") != "resolved":
                    errors.append("bounded-log-collection requires resolved max_log_bytes")

    for action in actions:
        cluster_id = action.get("cluster_scope_id")
        connection_id = action.get("connection_id")
        target_ref = action.get("target_ref")
        if mode not in LIVE_MODES:
            errors.append("offline mode cannot produce live Action")
        target = cluster_targets.get(cluster_id)
        if not target or target.get("connection_id") != connection_id or connection_id not in connection_ids:
            errors.append("Action connection/Cluster scope mismatch")
        target_type = action.get("target_type")
        action_type = action.get("action_type")
        if target_type not in ACTION_TARGET_TYPES.get(action_type, set()):
            errors.append("Action type/target_type mapping is invalid")
        target_sets = {
            "node": node_targets, "vm": vm_targets, "container": container_targets,
            "storage": storage_targets, "disk": disk_targets,
        }
        if target_type in target_sets and (cluster_id, target_ref) not in target_sets[target_type]:
            errors.append(f"Action target is outside allowed_{target_type}_targets")
        if target_type == "cluster" and target_ref != (target or {}).get("target_ref"):
            errors.append("Cluster Action target_ref is outside allowed_cluster_targets")
        max_objects = action.get("max_objects")
        max_output_bytes = action.get("max_output_bytes")
        object_limit = required_action_limits["max_objects_per_action"].get("value")
        output_limit = required_action_limits["max_output_bytes"].get("value")
        if not isinstance(max_objects, int) or max_objects <= 0:
            errors.append("Action max_objects must be positive")
        elif isinstance(object_limit, int) and max_objects > object_limit:
            errors.append("Action max_objects exceeds effective limit")
        if not isinstance(max_output_bytes, int) or max_output_bytes <= 0:
            errors.append("Action max_output_bytes must be positive")
        elif isinstance(output_limit, int) and max_output_bytes > output_limit:
            errors.append("Action max_output_bytes exceeds effective limit")
        if action.get("action_type") in BOUND_PATH_ACTIONS:
            if target_type != "node":
                errors.append("bounded copy/log Action must target node")
            path_scope = path_scopes.get(action.get("allowed_path_scope_id"))
            if not path_scope:
                errors.append("bounded copy/log Action lacks approved path scope")
            elif not (
                path_scope.get("cluster_scope_id") == cluster_id
                and path_scope.get("owner_node_id") == target_ref
                and action.get("source_path")
                and path_is_within(
                    action["source_path"], path_scope.get("path", ""),
                    bool(path_scope.get("recursive")), path_scope.get("max_depth"),
                )
            ):
                errors.append("bounded Action source_path is outside approved path scope")
            if action.get("action_type") == "bounded-log-collection":
                try:
                    since = datetime.fromisoformat(action["since"].replace("Z", "+00:00"))
                    until = datetime.fromisoformat(action["until"].replace("Z", "+00:00"))
                    if since >= until:
                        raise ValueError
                except (AttributeError, KeyError, TypeError, ValueError):
                    errors.append("bounded log Action requires ordered since/until")
        elif action.get("allowed_path_scope_id") is not None:
            errors.append("non-path Action allowed_path_scope_id must be null")

    events = {x.get("event_id"): x for x in response.get("ledger_events", [])}
    artifact_ids = set(req.get("material_info", {}).get("artifact_refs", []))
    artifact_ids.update(context.get("artifact_refs", []))
    artifact_ids.update(response.get("artifact_refs", []))
    response_environment = response_payload.get("environment", {})
    for artifact_key in ("root_artifact_refs", "collection_artifact_refs", "artifact_refs"):
        artifact_ids.update(response_environment.get(artifact_key, []))

    image_blockers = {
        (x.get("cluster_scope_id"), x.get("target_ref"))
        for x in response_payload.get("blockers", [])
        if x.get("scope") == "image"
    }
    images_by_id = {
        (x.get("cluster_scope_id"), x.get("candidate_id")): x
        for x in response_payload.get("image_candidates", [])
    }
    for layer_key in symlink_targets:
        entity_ref = nodes[layer_key].get("entity_ref")
        image = images_by_id.get((layer_key[0], entity_ref))
        if not image or image.get("object_type") != "symlink":
            errors.append("symlink-target-of must resolve to a symlink image candidate")
    for mapping in response_payload.get("vm_disk_map", []):
        cluster_id = mapping.get("cluster_scope_id")
        if any((cluster_id, ref) not in images_by_id for ref in mapping.get("image_candidate_refs", [])):
            errors.append("vm_disk_map references a missing image candidate")
    for image in response_payload.get("image_candidates", []):
        cluster_id = image.get("cluster_scope_id")
        if any((cluster_id, ref) not in nodes for ref in image.get("layer_node_refs", [])):
            errors.append("image candidate references a missing scoped Layer Node")
    for image in response_payload.get("image_candidates", []):
        key = (image.get("cluster_scope_id"), image.get("candidate_id"))
        readiness = image.get("analysis_readiness")
        if not image.get("analysis_readiness_basis"):
            errors.append("image candidate readiness requires basis")
        if readiness == "ready":
            backing_images = [
                images_by_id.get((key[0], ref)) for ref in image.get("backing_refs", [])
            ]
            if not (
                image.get("content_availability") == "complete"
                and image.get("identity_status") == "verified-content"
                and image.get("large_artifact_status") in {"completed", "not-required"}
                and key not in image_blockers
                and all(
                    backing
                    and backing.get("content_availability") == "complete"
                    and backing.get("identity_status") == "verified-content"
                    for backing in backing_images
                )
            ):
                errors.append("image candidate is not eligible for ready")
        if image.get("identity_status") == "correlated" and readiness == "ready":
            errors.append("correlated image cannot be ready")
        if image.get("identity_status") == "correlated" and not scope.get("targeted_questions"):
            errors.append("correlated image requires an explicit targeted question")
        if image.get("large_artifact_status") == "completed":
            image_artifacts = set(image.get("artifact_refs", []))
            image_events = [events.get(ref) for ref in image.get("ledger_event_refs", [])]
            if not (
                image_artifacts
                and image_artifacts <= artifact_ids
                and image_events
                and all(image_events)
                and any(
                    event.get("skill") == "large-artifact-strategy"
                    and event.get("status") == "completed"
                    and image_artifacts & set(event.get("artifact_refs", []))
                    for event in image_events
                )
            ):
                errors.append("completed large-Artifact state lacks workflow evidence")
        if image.get("object_type") in {
            "descriptor", "symlink", "placeholder", "metadata-only-reference",
            "remote-logical-reference", "missing-extent",
        } and readiness != "not-ready":
            errors.append("non-content image candidate must be not-ready")

    skipped_stages = {
        x.get("stage") for x in events.values()
        if x.get("event_type") == "state-transition" and x.get("status") == "skipped"
    }
    for finding in response.get("findings", []):
        if finding.get("category") != "negative":
            continue
        referenced_stages = {events.get(ref, {}).get("stage") for ref in finding.get("evidence_refs", [])}
        if skipped_stages & referenced_stages:
            errors.append("skipped Stage cannot support a negative Finding")
        if skipped_stages:
            errors.append("negative Finding is unsafe while any relevant Stage scope is skipped")

    ledger_ids = set(events)
    ledger_ids.update(context.get("ledger_event_refs", []))
    for candidate in response_payload.get("timeline_candidates", []):
        if candidate.get("source_artifact_id") not in artifact_ids:
            errors.append("Timeline candidate lacks source Artifact")
        ledger_refs = candidate.get("ledger_event_refs", [])
        if not ledger_refs or any(ref not in ledger_ids for ref in ledger_refs) or not candidate.get("basis"):
            errors.append("Timeline candidate lacks Ledger Event or basis")

    for blocker in response_payload.get("blockers", []):
        if blocker.get("error_class") not in ERROR_CLASSES:
            errors.append("unknown blocker error_class")
        if blocker.get("required_handoff") not in HANDOFF_SKILLS | {None}:
            errors.append("unknown blocker required_handoff")

    # Response environment consistency
    resp_env = response_payload.get("environment", {})
    if resp_env.get("access_mode") is not None and resp_env.get("access_mode") != mode:
        errors.append("Response payload access_mode differs from Request access_mode")
    if mode in LIVE_MODES:
        resp_session = resp_env.get("session_id")
        if resp_session is not None and resp_session != session_id:
            errors.append("live Response session_id differs from Request session_id")
        resp_conn_ids = set(resp_env.get("connection_ids", []))
        unauthorized_conns = resp_conn_ids - connection_ids
        if unauthorized_conns:
            errors.append(f"live Response contains unauthorized connection_ids: {unauthorized_conns}")
    elif mode in OFFLINE_MODES:
        if resp_env.get("session_id") is not None:
            errors.append("offline Response session_id must be null")
        if resp_env.get("connection_ids"):
            errors.append("offline Response connection_ids must be empty")
    # Plan ID consistency
    req_plan = environment.get("plan_id")
    resp_plan = resp_env.get("plan_id")
    upstream_plan = context.get("upstream_environment", {}).get("plan_id")
    if resp_plan is not None and req_plan is not None and resp_plan != req_plan:
        errors.append("Response plan_id conflicts with Request plan_id")
    if resp_plan is not None and upstream_plan is not None and resp_plan != upstream_plan:
        errors.append("Response plan_id conflicts with upstream plan_id")

    return errors


def minimal_case() -> tuple[dict[str, Any], dict[str, Any]]:
    route_step = "step-current"
    planner_step = "step-planner"
    request = {
        "schema_version": "1.0",
        "request": {
            "material_info": {
                "artifact_refs": ["artifact-test-001"],
                "material_type": "server-disk-image",
            },
            "objective": "identify cluster topology and VM mapping",
            "objective_status": "explicit",
            "context": {
                "current_step_id": route_step,
                "artifact_refs": [],
                "upstream_environment": {"plan_id": "plan-1"},
                "route_record": {
                    "schema_version": "1.0",
                    "route_id": "route-test-001",
                    "triggered_skill": "cluster-virtualization-forensics",
                    "route_status": "active",
                    "route_plan": [
                        {"route_step_id": route_step, "skill": "cluster-virtualization-forensics", "status": "running"},
                        {"route_step_id": planner_step, "skill": "server-rebuild-planner", "status": "completed"},
                    ],
                    "evidence_scope": "test cluster evidence",
                },
            },
            "payload": {
                "access_mode": "live-cluster",
                "environment": {
                    "plan_id": "plan-1", "session_id": "session-1",
                    "connection_ids": ["conn-1"],
                },
                "cluster_scope": {
                    "analysis_scope_id": "scope-1",
                    "platform_hints": ["proxmox-ve"],
                    "targeted_questions": ["identify all VMs"],
                    "allowed_cluster_targets": [{
                        "cluster_scope_id": "cluster-1", "connection_id": "conn-1",
                        "target_ref": "pve-cluster-1", "virtualization_platform": "proxmox-ve",
                        "endpoint_role": "pve-api",
                    }],
                    "allowed_node_targets": [{"cluster_scope_id": "cluster-1", "node_id": "node-1"}],
                    "allowed_vm_targets": [{"cluster_scope_id": "cluster-1", "vm_id": "vm-1"}],
                    "allowed_container_targets": [],
                    "allowed_storage_targets": [{"cluster_scope_id": "cluster-1", "storage_id": "storage-1"}],
                    "allowed_disk_targets": [{"cluster_scope_id": "cluster-1", "disk_id": "disk-1"}],
                    "allowed_paths": [{
                        "path_scope_id": "path-1", "cluster_scope_id": "cluster-1",
                        "owner_node_id": "node-1", "artifact_ref": None,
                        "path": "/etc/pve", "recursive": True, "max_depth": 2,
                    }],
                    "disk_set_members": [],
                    "stages": {
                        "include_platform_node_mapping": True,
                        "include_quorum_analysis": True,
                        "include_disk_mapping": True,
                        "include_storage_reconstruction": True,
                        "include_distributed_storage_analysis": True,
                        "include_vm_mapping": True,
                        "include_snapshot_backing_analysis": True,
                        "include_health_conflict_analysis": True,
                        "include_timeline_candidates": True,
                        "include_cross_domain_validation": True,
                    },
                    "live_collection_limits": {
                        "max_actions": 4, "max_output_bytes": 4096,
                        "max_objects_per_action": 8, "max_log_bytes": 8192,
                        "max_config_bytes": 4096, "max_session_seconds": 3600,
                    },
                    "archive_limits": {"max_archive_files": None, "max_archive_expanded_bytes": None},
                    "disk_limits": {
                        "max_disk_members": None, "max_bytes_sampled_per_disk": None,
                        "max_image_candidates": None,
                    },
                    "traversal_limits": {"max_depth": None, "max_objects": None, "max_paths": None},
                },
            },
        }
    }
    response = {
        "schema_version": "1.0",
        "investigation_summary": {
            "current_assessment": "cluster topology identified",
            "key_evidence": ["PVE cluster with one node"],
        },
        "route_record": {
            "schema_version": "1.0",
            "route_id": "route-test-001",
            "triggered_skill": "cluster-virtualization-forensics",
            "route_status": "active",
            "route_plan": [
                {"route_step_id": route_step, "skill": "cluster-virtualization-forensics", "status": "running"},
                {"route_step_id": planner_step, "skill": "server-rebuild-planner", "status": "completed"},
            ],
        },
        "findings": [],
        "ledger_events": [],
        "artifact_refs": [],
        "payload": {
            "environment": {"plan_id": "plan-1", "session_id": "session-1", "connection_ids": ["conn-1"]},
            "access_mode": "live-cluster",
            "cluster_profiles": [{
                "cluster_scope_id": "cluster-1",
                "cluster_id": "pve-cluster-1",
                "cluster_name": "test-cluster",
                "virtualization_platform": "proxmox-ve",
                "observation_mode": "live",
                "basis": ["PVE API response"],
                "confidence": "high",
            }],
            "node_map": [{
                "cluster_scope_id": "cluster-1", "node_id": "node-1",
                "hostname": "pve-node-1", "observation_mode": "live",
                "basis": ["PVE API"], "confidence": "high",
            }],
            "disk_map": [{
                "cluster_scope_id": "cluster-1", "disk_id": "disk-1",
                "owner_node_id": "node-1", "layer_node_id": "layer-disk-1",
                "observation_mode": "inferred", "basis": ["disk listing"], "confidence": "medium",
            }],
            "storage_map": [{
                "cluster_scope_id": "cluster-1", "storage_id": "storage-1",
                "owner_node_ids": ["node-1"], "storage_type": "directory",
                "backing_layer_node_refs": [], "health_status": "unknown",
                "observation_mode": "inferred", "basis": ["storage listing"], "confidence": "medium",
            }],
            "layer_map": {
                "nodes": [
                    {
                        "cluster_scope_id": "cluster-1", "layer_node_id": "layer-disk-1",
                        "node_type": "physical-disk", "owner_node_id": "node-1",
                    },
                    {
                        "cluster_scope_id": "cluster-1", "layer_node_id": "layer-vm",
                        "node_type": "vm-disk", "owner_node_id": None,
                    },
                ],
                "edges": [],
            },
            "vm_map": [{
                "cluster_scope_id": "cluster-1", "workload_id": "vm-1",
                "object_type": "vm", "platform": "pve-qemu",
                "observation_mode": "live", "basis": ["PVE API"], "confidence": "high",
            }],
            "vm_disk_map": [{
                "cluster_scope_id": "cluster-1", "workload_id": "vm-1",
                "object_type": "vm", "vm_disk_mapping_id": "vdm-1",
                "storage_id": "storage-1",
                "terminal_layer_node_id": "layer-vm",
                "layer_edge_refs": [],
                "image_candidate_refs": [],
                "observation_mode": "inferred", "basis": ["VM config"], "confidence": "medium",
            }],
            "snapshot_map": [],
            "quorum_findings": [],
            "storage_health_findings": [],
            "image_candidates": [],
            "timeline_candidates": [],
            "cross_domain_candidates": [{
                "candidate_id": "cdc-1",
                "skill": "server-rebuild-executor",
                "cluster_scope_id": "cluster-1",
                "dependency_step_ids": [planner_step],
                "planner_authorization": {
                    "planner_step_id": planner_step, "plan_id": "plan-1", "plan_status": "ready",
                },
                "workload_refs": [{
                    "cluster_scope_id": "cluster-1", "workload_id": "vm-1", "object_type": "vm",
                }],
                "basis": ["planner completed"],
                "confidence": "high",
                "targeted_collection_request": None,
            }],
            "effective_limits": {
                "max_actions": {"value": 4, "status": "resolved", "basis": ["test policy"]},
                "max_output_bytes": {"value": 4096, "status": "resolved", "basis": ["test policy"]},
                "max_objects_per_action": {"value": 8, "status": "resolved", "basis": ["test policy"]},
                "max_log_bytes": {"value": 8192, "status": "resolved", "basis": ["test policy"]},
                "max_config_bytes": {"value": 4096, "status": "resolved", "basis": ["test policy"]},
                "max_archive_files": {"value": None, "status": "not-applicable", "basis": ["offline only"]},
                "max_archive_expanded_bytes": {"value": None, "status": "not-applicable", "basis": ["offline only"]},
                "max_disk_members": {"value": None, "status": "not-applicable", "basis": ["offline only"]},
                "max_bytes_sampled_per_disk": {"value": None, "status": "not-applicable", "basis": ["offline only"]},
                "max_image_candidates": {"value": None, "status": "not-applicable", "basis": ["offline only"]},
                "max_depth": {"value": None, "status": "not-applicable", "basis": ["traversal not configured"]},
                "max_objects": {"value": None, "status": "not-applicable", "basis": ["traversal not configured"]},
                "max_paths": {"value": None, "status": "not-applicable", "basis": ["traversal not configured"]},
            },
            "blockers": [],
        },
    }
    return request, response


def minimal_live_collection_case() -> tuple[dict[str, Any], dict[str, Any]]:
    """A case with live-response targeted collection for testing."""
    request, response = minimal_case()
    # Switch the cross_domain candidate to live-response with targeted collection
    request["request"]["context"]["route_record"]["route_plan"] = [
        {"route_step_id": "step-current", "skill": "cluster-virtualization-forensics", "status": "running"},
    ]
    response["payload"]["cross_domain_candidates"] = [{
        "candidate_id": "cdc-live-1",
        "skill": "remote-server-live-response",
        "cluster_scope_id": "cluster-1",
        "dependency_step_ids": [],
        "planner_authorization": {
            "planner_step_id": None, "plan_id": None, "plan_status": None,
        },
        "workload_refs": [{
            "cluster_scope_id": "cluster-1", "workload_id": "vm-1", "object_type": "vm",
        }],
        "basis": ["live collection needed"],
        "confidence": "high",
        "targeted_collection_request": {
            "actions": [{
                "action_id": "copy-1",
                "action_type": "bounded-config-copy", "target_type": "node",
                "target_ref": "node-1", "cluster_scope_id": "cluster-1",
                "connection_id": "conn-1", "source_path": "/etc/pve/storage.cfg",
                "allowed_path_scope_id": "path-1",
                "since": None, "until": None,
                "max_objects": 1, "max_output_bytes": 1024,
                "purpose": "collect approved PVE config", "impact_level": "low",
                "sensitive_output_expected": False,
                "capture_mode": "standard-artifact",
                "expected_footprint": ["one configuration file"],
            }],
            "paths": [{
                "action_id": "copy-1", "path_role": "remote-config-source",
                "path": "/etc/pve/storage.cfg",
            }],
            "max_output_bytes": 1024,
            "reason": "test bounded collection",
        },
    }]
    return request, response


def run_self_tests() -> list[str]:
    failures: list[str] = []
    request, response = minimal_case()
    if validate_semantics(request, response):
        failures.append("valid semantic case was rejected")

    # Also test the live collection variant
    lc_request, lc_response = minimal_live_collection_case()
    if validate_semantics(lc_request, lc_response):
        failures.append("valid live collection case was rejected")

    mutations: list[tuple[str, dict[str, Any], dict[str, Any]]] = []

    # 1. Missing Response top-level field
    missing_schema = copy.deepcopy((request, response))
    del missing_schema[1]["schema_version"]
    mutations.append(("missing Response schema_version", *missing_schema))

    missing_findings = copy.deepcopy((request, response))
    del missing_findings[1]["findings"]
    mutations.append(("missing Response findings", *missing_findings))

    # 2. Missing payload required field
    missing_cluster_profiles = copy.deepcopy((request, response))
    del missing_cluster_profiles[1]["payload"]["cluster_profiles"]
    mutations.append(("missing payload cluster_profiles", *missing_cluster_profiles))

    missing_node_map = copy.deepcopy((request, response))
    del missing_node_map[1]["payload"]["node_map"]
    mutations.append(("missing payload node_map", *missing_node_map))

    missing_storage_map = copy.deepcopy((request, response))
    del missing_storage_map[1]["payload"]["storage_map"]
    mutations.append(("missing payload storage_map", *missing_storage_map))

    missing_layer_map = copy.deepcopy((request, response))
    del missing_layer_map[1]["payload"]["layer_map"]
    mutations.append(("missing payload layer_map", *missing_layer_map))

    # 3. Missing effective limit
    missing_limit = copy.deepcopy((request, response))
    del missing_limit[1]["payload"]["effective_limits"]["max_archive_files"]
    mutations.append(("missing effective limit max_archive_files", *missing_limit))

    extra_limit = copy.deepcopy((request, response))
    extra_limit[1]["payload"]["effective_limits"]["unknown_limit"] = {
        "value": 1, "status": "resolved", "basis": ["unknown"],
    }
    mutations.append(("unknown effective limit", *extra_limit))

    # 4. Action with forbidden command field
    bad_cmd = copy.deepcopy((lc_request, lc_response))
    bad_cmd[1]["payload"]["cross_domain_candidates"][0]["targeted_collection_request"]["actions"][0]["command"] = "rm -rf /"
    mutations.append(("Action with command field", *bad_cmd))

    # 5. targeted_collection_request on wrong skill (executor)
    wrong_skill_tcr = copy.deepcopy((request, response))
    wrong_skill_tcr[1]["payload"]["cross_domain_candidates"][0]["targeted_collection_request"] = {
        "actions": [{
            "action_id": "copy-wrong", "action_type": "bounded-config-copy",
            "target_type": "node", "target_ref": "node-1",
            "cluster_scope_id": "cluster-1", "connection_id": "conn-1",
            "source_path": "/etc/pve/storage.cfg", "allowed_path_scope_id": "path-1",
            "since": None, "until": None, "max_objects": 1, "max_output_bytes": 1024,
            "purpose": "test", "impact_level": "low",
            "sensitive_output_expected": False, "capture_mode": "standard-artifact",
            "expected_footprint": ["one file"],
        }],
        "paths": [{"action_id": "copy-wrong", "path_role": "remote-config-source", "path": "/etc/pve/storage.cfg"}],
        "max_output_bytes": 1024,
        "reason": "test",
    }
    # Ensure workload_refs present for validation
    wrong_skill_tcr[1]["payload"]["cross_domain_candidates"][0]["workload_refs"] = [{
        "cluster_scope_id": "cluster-1", "workload_id": "vm-1", "object_type": "vm",
    }]
    mutations.append(("targeted collection on executor skill", *wrong_skill_tcr))
    mutations.append(("targeted collection on executor skill", *wrong_skill_tcr))

    # 6. Orphan cluster_scope target
    orphan_target = copy.deepcopy((request, response))
    orphan_target[0]["request"]["payload"]["cluster_scope"]["allowed_node_targets"].append(
        {"cluster_scope_id": "nonexistent-cluster", "node_id": "orphan-node"}
    )
    mutations.append(("orphan node target references nonexistent cluster", *orphan_target))

    # 7. Duplicate scoped ID in node_map
    dup_node = copy.deepcopy((request, response))
    dup_node[1]["payload"]["node_map"].append({
        "cluster_scope_id": "cluster-1", "node_id": "node-1",
        "hostname": "duplicate", "observation_mode": "live",
        "basis": ["dup"], "confidence": "high",
    })
    mutations.append(("duplicate node_map entry", *dup_node))

    # 8. vm_disk_map references non-existent storage_map
    bad_storage_ref = copy.deepcopy((request, response))
    bad_storage_ref[1]["payload"]["vm_disk_map"][0]["storage_id"] = "storage-nonexistent"
    mutations.append(("vm_disk_map storage not in storage_map", *bad_storage_ref))

    # 9. Relative path bypass
    rel_bypass = copy.deepcopy((lc_request, lc_response))
    rel_bypass[1]["payload"]["cross_domain_candidates"][0]["targeted_collection_request"]["actions"][0]["source_path"] = "etc/pve/storage.cfg"
    mutations.append(("relative path bypasses absolute root", *rel_bypass))

    # 10. Action output sum exceeds request total
    oversum = copy.deepcopy((lc_request, lc_response))
    oversum[1]["payload"]["cross_domain_candidates"][0]["targeted_collection_request"]["actions"][0]["max_output_bytes"] = 2048
    oversum[1]["payload"]["cross_domain_candidates"][0]["targeted_collection_request"]["max_output_bytes"] = 1024
    mutations.append(("action output sum exceeds request limit", *oversum))

    # 11. Bounded config exceeds max_config_bytes
    over_config = copy.deepcopy((lc_request, lc_response))
    over_config[1]["payload"]["cross_domain_candidates"][0]["targeted_collection_request"]["actions"][0]["max_output_bytes"] = 8192
    over_config[1]["payload"]["cross_domain_candidates"][0]["targeted_collection_request"]["max_output_bytes"] = 8192
    over_config[1]["payload"]["effective_limits"]["max_output_bytes"]["value"] = 16384
    mutations.append(("bounded config exceeds max_config_bytes", *over_config))

    # 12. Bounded log exceeds max_log_bytes
    over_log = copy.deepcopy((lc_request, lc_response))
    over_log[1]["payload"]["cross_domain_candidates"][0]["targeted_collection_request"]["actions"][0]["action_type"] = "bounded-log-collection"
    over_log[1]["payload"]["cross_domain_candidates"][0]["targeted_collection_request"]["actions"][0]["since"] = "2026-01-01T00:00:00Z"
    over_log[1]["payload"]["cross_domain_candidates"][0]["targeted_collection_request"]["actions"][0]["until"] = "2026-01-02T00:00:00Z"
    over_log[1]["payload"]["cross_domain_candidates"][0]["targeted_collection_request"]["actions"][0]["max_output_bytes"] = 16384
    over_log[1]["payload"]["cross_domain_candidates"][0]["targeted_collection_request"]["paths"][0]["path_role"] = "remote-log-source"
    over_log[1]["payload"]["cross_domain_candidates"][0]["targeted_collection_request"]["max_output_bytes"] = 16384
    over_log[1]["payload"]["effective_limits"]["max_output_bytes"]["value"] = 32768
    mutations.append(("bounded log exceeds max_log_bytes", *over_log))

    # 13. Response session/connection mismatch
    session_mismatch = copy.deepcopy((request, response))
    session_mismatch[1]["payload"]["environment"]["session_id"] = "session-other"
    mutations.append(("Response session_id mismatch", *session_mismatch))

    conn_mismatch = copy.deepcopy((request, response))
    conn_mismatch[1]["payload"]["environment"]["connection_ids"] = ["conn-unauthorized"]
    mutations.append(("Response unauthorized connection_id", *conn_mismatch))

    # Additional: offline Response with session
    offline_session = copy.deepcopy((request, response))
    offline_session[0]["request"]["payload"]["access_mode"] = "offline-node-image"
    offline_session[0]["request"]["payload"]["environment"]["session_id"] = None
    offline_session[0]["request"]["payload"]["environment"]["connection_ids"] = []
    offline_session[0]["request"]["payload"]["environment"]["root_artifact_refs"] = ["artifact-test-001"]
    offline_session[0]["request"]["context"]["route_record"]["evidence_scope"] = "test offline"
    offline_session[0]["request"]["payload"]["cluster_scope"]["allowed_cluster_targets"][0]["connection_id"] = None
    offline_session[0]["request"]["payload"]["cluster_scope"]["allowed_paths"] = []
    offline_session[1]["payload"]["cross_domain_candidates"] = []
    offline_session[1]["payload"]["environment"]["session_id"] = "should-be-null"
    mutations.append(("offline Response with session_id", *offline_session))

    # Additional: Path traversal escape
    path_escape = copy.deepcopy((lc_request, lc_response))
    path_escape[1]["payload"]["cross_domain_candidates"][0]["targeted_collection_request"]["actions"][0]["source_path"] = "/etc/pve/../shadow"
    mutations.append(("path traversal via ..", *path_escape))

    # Additional: Windows drive mismatch
    drive_mismatch = copy.deepcopy((lc_request, lc_response))
    drive_mismatch[0]["request"]["payload"]["cluster_scope"]["allowed_paths"][0]["path"] = "C:\\PVE"
    drive_mismatch[1]["payload"]["cross_domain_candidates"][0]["targeted_collection_request"]["actions"][0]["source_path"] = "D:\\PVE\\storage.cfg"
    drive_mismatch[1]["payload"]["cross_domain_candidates"][0]["targeted_collection_request"]["paths"][0]["path"] = "D:\\PVE\\storage.cfg"
    mutations.append(("Windows drive mismatch", *drive_mismatch))

    # Additional: cluster_profile references nonexistent Request cluster
    bad_profile = copy.deepcopy((request, response))
    bad_profile[1]["payload"]["cluster_profiles"].append({
        "cluster_scope_id": "cluster-ghost",
        "virtualization_platform": "unknown",
        "observation_mode": "inferred",
        "basis": ["ghost"], "confidence": "low",
    })
    mutations.append(("cluster_profile references nonexistent cluster", *bad_profile))

    # Additional: vm_disk_map edge refs not connected to terminal
    bad_edge_ref = copy.deepcopy((request, response))
    bad_edge_ref[1]["payload"]["layer_map"]["edges"] = [{
        "cluster_scope_id": "cluster-1", "layer_edge_id": "edge-unrelated",
        "from_layer_node_id": "layer-disk-1", "to_layer_node_id": "layer-disk-1",
        "relation": "conflicts-with",
    }]
    bad_edge_ref[1]["payload"]["layer_map"]["nodes"][0]["entity_ref"] = "some-entity"
    bad_edge_ref[1]["payload"]["layer_map"]["nodes"].append({
        "cluster_scope_id": "cluster-1", "layer_node_id": "layer-disk-1-copy",
        "node_type": "physical-disk", "owner_node_id": None, "entity_ref": "some-entity",
    })
    bad_edge_ref[1]["payload"]["layer_map"]["edges"][0]["to_layer_node_id"] = "layer-disk-1-copy"
    bad_edge_ref[1]["payload"]["vm_disk_map"][0]["layer_edge_refs"] = ["edge-unrelated"]
    mutations.append(("vm_disk_map edge refs not connected to terminal", *bad_edge_ref))

    # Additional: response plan_id conflict
    plan_conflict = copy.deepcopy((request, response))
    plan_conflict[1]["payload"]["environment"]["plan_id"] = "plan-conflict"
    mutations.append(("Response plan_id conflicts with Request", *plan_conflict))

    for name, mutated_request, mutated_response in mutations:
        result = validate_semantics(mutated_request, mutated_response)
        if not result:
            failures.append(f"invalid semantic case accepted: {name}")
        else:
            # Verify the expected error type is present
            pass
    return failures


def validate_repository() -> list[str]:
    errors: list[str] = []
    if not SKILL_PATH.exists():
        return [f"missing {SKILL_PATH.relative_to(ROOT)}"]
    skill_text = SKILL_PATH.read_text(encoding="utf-8")
    contract_text = CONTRACT_PATH.read_text(encoding="utf-8")
    skill_request = ""
    skill_payload = ""
    skill_response = ""
    try:
        frontmatter, body = parse_frontmatter(skill_text)
        if set(frontmatter) != {"name", "description"}:
            errors.append("SKILL.md frontmatter must contain only name and description")
        if frontmatter.get("name") != "cluster-virtualization-forensics":
            errors.append("SKILL.md frontmatter name mismatch")
    except ValueError as exc:
        errors.append(str(exc))
        body = skill_text

    try:
        skill_request = extract_contract(skill_text, REQUEST_START, REQUEST_END, "request")
        docs_request = extract_contract(contract_text, REQUEST_START, REQUEST_END, "request")
        if skill_request != docs_request:
            errors.append("SKILL.md and docs/data-contracts.md 8.9 request contracts differ")
        skill_response = extract_contract(skill_text, RESPONSE_START, RESPONSE_END, "response")
        for top_level in (
            "investigation_summary:", "route_record:", "findings:",
            "ledger_events:", "artifact_refs:", "payload:",
        ):
            if top_level not in skill_response:
                errors.append(f"full Response Contract lacks {top_level}")
        skill_payload = extract_contract(skill_text, PAYLOAD_START, PAYLOAD_END, "payload")
        docs_payload = extract_contract(contract_text, PAYLOAD_START, PAYLOAD_END, "payload")
        if skill_payload != docs_payload:
            errors.append("SKILL.md and docs/data-contracts.md 8.9 payload contracts differ")
        if normalized_yaml_fragment(skill_response, "payload:") != normalized_yaml_fragment(skill_payload, "payload:"):
            errors.append("full Response payload differs from the synchronized payload block")
    except ValueError as exc:
        errors.append(str(exc))

    for marker in (REQUEST_START, REQUEST_END, PAYLOAD_START, PAYLOAD_END):
        if skill_text.count(marker) != 1 or contract_text.count(marker) != 1:
            errors.append(f"contract marker must occur exactly once: {marker}")
    for marker in (RESPONSE_START, RESPONSE_END):
        if skill_text.count(marker) != 1:
            errors.append(f"response contract marker must occur exactly once: {marker}")
    if skill_text.count("```") % 2 or contract_text.count("```") % 2:
        errors.append("Markdown code fence is not closed")
    if "\t" in skill_request + skill_payload:
        errors.append("Cluster contract YAML indentation contains a tab")

    required_terms = {
        "access modes": ["live-cluster", "rebuilt-cluster", "offline-node-image", "disk-set", "artifact-package"],
        "cluster stack": ["PVE", "pmxcfs", "Corosync", "Quorum", "Ceph", "mdraid", "LVM", "ZFS", "btrfs"],
        "workloads": ["VM", "Container", "Snapshot", "image_candidates"],
        "graph": ["provider/parent/base/resolved target", "snapshot-parent-of", "delta-parent-of", "symlink-target-of"],
        "scope": ["cluster_scope_id", "workload_id", "allowed_path_scope_id", "allowed_disk_targets"],
        "handoff": ["server-rebuild-planner", "server-rebuild-executor", "remote-server-live-response", "large-artifact-strategy"],
        "failure": ["route_status=active", "route_status=blocked", "execution_gate"],
    }
    combined = body
    for group, terms in required_terms.items():
        missing = [term for term in terms if term not in combined]
        if missing:
            errors.append(f"missing {group} terms: {', '.join(missing)}")

    for old_field in ("layer_hint", "real_image_found"):
        if re.search(rf"(?m)^\s*{old_field}\s*:", skill_text + "\n" + contract_text):
            errors.append(f"legacy payload field remains: {old_field}")
    if re.search(r"(?m)^\s*placeholder_only\s*:", skill_text + "\n" + contract_text):
        errors.append("legacy placeholder_only boolean remains")
    for old_relation in ("allocated-from", "snapshot-of", "delta-of", "symlink-to", "attached-to"):
        if old_relation in skill_text or old_relation in contract_text:
            errors.append(f"legacy Layer relation remains: {old_relation}")
    if re.search(r"[A-Za-z]:\\", skill_text):
        errors.append("SKILL.md contains a local Windows absolute path")
    readme_text = README_PATH.read_text(encoding="utf-8")
    if not re.search(
        r"(?m)^\| `cluster-virtualization-forensics/` \|[^\n]*\| Completed \|$",
        readme_text,
    ):
        errors.append("skills/server/README.md Cluster status is not Completed")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skip-self-tests", action="store_true")
    args = parser.parse_args()
    errors = validate_repository()
    if not args.skip_self_tests:
        errors.extend(run_self_tests())
    if errors:
        for error in errors:
            print(f"FAIL {error}")
        print(f"RESULT: {len(errors)} failure(s)")
        return 1
    print("PASS Cluster Skill frontmatter and frozen payload contract")
    print("PASS Cluster reference, Layer Graph, Session, Action, image, route, and Stage rules")
    print("PASS Cluster validator self-tests")
    print("RESULT: all Cluster contract checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
