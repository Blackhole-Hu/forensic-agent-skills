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


def norm_path(path: str) -> tuple[str, ...]:
    normalized = path.replace("\\", "/")
    parts: list[str] = []
    for part in normalized.split("/"):
        if not part or part == ".":
            continue
        if part == "..":
            if not parts:
                return ("<escape>",)
            parts.pop()
        else:
            parts.append(part)
    return tuple(parts)


def path_is_within(candidate: str, root: str, recursive: bool, max_depth: int | None) -> bool:
    candidate_parts = norm_path(candidate)
    root_parts = norm_path(root)
    if "<escape>" in candidate_parts or candidate_parts[: len(root_parts)] != root_parts:
        return False
    depth = len(candidate_parts) - len(root_parts)
    if not recursive and depth != 0:
        return False
    return max_depth is None or depth <= max_depth


def validate_semantics(request: dict[str, Any], response: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    req = request.get("request", request)
    payload = req.get("payload", {})
    environment = payload.get("environment", {})
    mode = payload.get("access_mode")
    scope = payload.get("cluster_scope", {})
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

    response_payload = response.get("payload", response)
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

    for item in response_payload.get("vm_disk_map", []):
        key = (item.get("cluster_scope_id"), item.get("workload_id"))
        if key not in vm_map or item.get("object_type") != vm_map[key].get("object_type"):
            errors.append("vm_disk_map workload reference/type mismatch")
        storage_id = item.get("storage_id")
        if storage_id is not None and (key[0], storage_id) not in storage_targets:
            errors.append("vm_disk_map storage reference is outside scope")

    vm_disk_map = {
        (x.get("cluster_scope_id"), x.get("vm_disk_mapping_id")): x
        for x in response_payload.get("vm_disk_map", [])
    }
    storage_map = {
        (x.get("cluster_scope_id"), x.get("storage_id")): x
        for x in response_payload.get("storage_map", [])
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
    for key, layer_node in nodes.items():
        owner_node_id = layer_node.get("owner_node_id")
        if owner_node_id is not None and (key[0], owner_node_id) not in node_map:
            errors.append("Layer Node owner_node_id does not reference node_map")
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
        if (cluster_id, mapping.get("terminal_layer_node_id")) not in nodes:
            errors.append("vm_disk_map terminal_layer_node_id is missing")
        if any((cluster_id, ref) not in layer_edge_ids for ref in mapping.get("layer_edge_refs", [])):
            errors.append("vm_disk_map references a missing scoped Layer Edge")
    for snapshot in response_payload.get("snapshot_map", []):
        cluster_id = snapshot.get("cluster_scope_id")
        if any((cluster_id, ref) not in nodes for ref in snapshot.get("layer_node_refs", [])):
            errors.append("snapshot_map references a missing scoped Layer Node")
        if any((cluster_id, ref) not in layer_edge_ids for ref in snapshot.get("backing_edge_refs", [])):
            errors.append("snapshot_map references a missing scoped Layer Edge")

    actions: list[dict[str, Any]] = []
    collection_requests: list[dict[str, Any]] = []
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
        if request_value is not None:
            required_collection_fields = {"actions", "paths", "max_output_bytes", "reason"}
            if not required_collection_fields <= request_value.keys():
                errors.append("targeted_collection_request is not fully expanded")
            if not request_value.get("actions") or not request_value.get("reason"):
                errors.append("targeted_collection_request requires non-empty actions and reason")
            action_ids = [action.get("action_id") for action in request_value.get("actions", [])]
            if any(not action_id for action_id in action_ids) or len(action_ids) != len(set(action_ids)):
                errors.append("targeted collection action_id must be non-empty and unique")
            for action in request_value.get("actions", []):
                if not ACTION_FIELDS <= action.keys():
                    errors.append("targeted collection Action is not fully expanded")
            for path_record in request_value.get("paths", []):
                if path_record.get("action_id") not in action_ids:
                    errors.append("targeted collection path references an unknown Action")
            paths_by_action: dict[str, list[dict[str, Any]]] = {}
            for path_record in request_value.get("paths", []):
                paths_by_action.setdefault(path_record.get("action_id"), []).append(path_record)
            for action in request_value.get("actions", []):
                if action.get("action_type") in BOUND_PATH_ACTIONS:
                    path_records = paths_by_action.get(action.get("action_id"), [])
                    if len(path_records) != 1 or path_records[0].get("path") != action.get("source_path"):
                        errors.append("bounded Action lacks one matching targeted collection path record")
            collection_requests.append(request_value)
            actions.extend(request_value.get("actions", []))

    effective_limits = response_payload.get("effective_limits", {})
    for limit_name, limit in effective_limits.items():
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
    for request_value in collection_requests:
        request_limit = request_value.get("max_output_bytes")
        output_limit = required_action_limits["max_output_bytes"].get("value")
        if not isinstance(request_limit, int) or request_limit <= 0:
            errors.append("targeted collection max_output_bytes must be positive")
        elif isinstance(output_limit, int) and request_limit > output_limit:
            errors.append("targeted collection output exceeds effective limit")

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
    return errors


def minimal_case() -> tuple[dict[str, Any], dict[str, Any]]:
    route_step = "step-current"
    planner_step = "step-planner"
    request = {
        "request": {
            "context": {
                "current_step_id": route_step,
                "upstream_environment": {"plan_id": "plan-1"},
                "route_record": {
                    "route_plan": [
                        {"route_step_id": route_step, "skill": "cluster-virtualization-forensics", "status": "running"},
                        {"route_step_id": planner_step, "skill": "server-rebuild-planner", "status": "completed"},
                    ]
                },
            },
            "payload": {
                "access_mode": "live-cluster",
                "environment": {
                    "plan_id": "plan-1", "session_id": "session-1",
                    "connection_ids": ["conn-1"],
                },
                "cluster_scope": {
                    "allowed_cluster_targets": [{"cluster_scope_id": "cluster-1", "connection_id": "conn-1"}],
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
                },
            },
        }
    }
    response = {
        "ledger_events": [],
        "findings": [],
        "payload": {
            "vm_map": [{
                "cluster_scope_id": "cluster-1", "workload_id": "vm-1",
                "object_type": "vm", "platform": "pve-qemu",
            }],
            "vm_disk_map": [{
                "cluster_scope_id": "cluster-1", "workload_id": "vm-1",
                "object_type": "vm", "storage_id": "storage-1",
                "terminal_layer_node_id": "layer-vm",
            }],
            "layer_map": {
                "nodes": [{
                    "cluster_scope_id": "cluster-1", "layer_node_id": "layer-vm",
                    "node_type": "vm-disk", "owner_node_id": None,
                }],
                "edges": [],
            },
            "environment": {"plan_id": "plan-1"},
            "image_candidates": [],
            "blockers": [],
            "effective_limits": {
                "max_actions": {"value": 4, "status": "resolved", "basis": ["test policy"]},
                "max_output_bytes": {"value": 4096, "status": "resolved", "basis": ["test policy"]},
                "max_objects_per_action": {"value": 8, "status": "resolved", "basis": ["test policy"]},
            },
            "cross_domain_candidates": [{
                "skill": "server-rebuild-executor",
                "dependency_step_ids": [planner_step],
                "planner_authorization": {
                    "planner_step_id": planner_step, "plan_id": "plan-1", "plan_status": "ready",
                },
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
                    }]
                    , "paths": [{
                        "action_id": "copy-1", "path_role": "remote-config-source",
                        "path": "/etc/pve/storage.cfg",
                    }],
                    "max_output_bytes": 1024,
                    "reason": "test bounded collection",
                },
            }],
        },
    }
    return request, response


def run_self_tests() -> list[str]:
    failures: list[str] = []
    request, response = minimal_case()
    if validate_semantics(request, response):
        failures.append("valid semantic case was rejected")

    mutations = []
    offline = copy.deepcopy((request, response))
    offline[0]["request"]["payload"]["access_mode"] = "offline-node-image"
    mutations.append(("offline Session", *offline))
    null_live_connection = copy.deepcopy((request, response))
    null_live_connection[0]["request"]["payload"]["environment"]["connection_ids"] = [None]
    null_live_connection[0]["request"]["payload"]["cluster_scope"]["allowed_cluster_targets"][0]["connection_id"] = None
    null_live_connection[1]["payload"]["cross_domain_candidates"][0]["targeted_collection_request"]["actions"][0]["connection_id"] = None
    mutations.append(("null live connection", *null_live_connection))
    masked_cluster_target = copy.deepcopy((request, response))
    valid_target = masked_cluster_target[0]["request"]["payload"]["cluster_scope"]["allowed_cluster_targets"][0]
    masked_cluster_target[0]["request"]["payload"]["cluster_scope"]["allowed_cluster_targets"] = [
        {**valid_target, "connection_id": None}, valid_target,
    ]
    mutations.append(("duplicate Cluster target masks invalid connection", *masked_cluster_target))
    rootless_disk_set = copy.deepcopy((request, response))
    rootless_payload = rootless_disk_set[0]["request"]["payload"]
    rootless_payload["access_mode"] = "disk-set"
    rootless_payload["environment"].update({"session_id": None, "connection_ids": [], "root_artifact_refs": []})
    rootless_payload["cluster_scope"]["allowed_cluster_targets"][0]["connection_id"] = None
    rootless_payload["cluster_scope"]["disk_set_members"] = []
    rootless_disk_set[1]["payload"]["cross_domain_candidates"] = []
    mutations.append(("rootless empty disk-set", *rootless_disk_set))
    unregistered_package = copy.deepcopy((request, response))
    package_request = unregistered_package[0]["request"]
    package_request["material_info"] = {"artifact_refs": []}
    package_request["context"]["route_record"]["evidence_scope"] = "one artifact package"
    package_payload = package_request["payload"]
    package_payload["access_mode"] = "artifact-package"
    package_payload["environment"].update({
        "session_id": None, "connection_ids": [],
        "root_artifact_refs": ["artifact-unregistered"],
    })
    package_payload["cluster_scope"]["allowed_cluster_targets"][0]["connection_id"] = None
    package_payload["cluster_scope"]["allowed_paths"] = []
    unregistered_package[1]["payload"]["cross_domain_candidates"] = []
    mutations.append(("unregistered rootless artifact package", *unregistered_package))
    bad_disk = copy.deepcopy((request, response))
    bad_disk[1]["payload"]["cross_domain_candidates"][0]["targeted_collection_request"]["actions"][0].update(
        {"action_type": "mdraid-detail", "target_type": "disk", "target_ref": "unapproved", "allowed_path_scope_id": None}
    )
    mutations.append(("unapproved live disk", *bad_disk))
    bad_path = copy.deepcopy((request, response))
    bad_path[1]["payload"]["cross_domain_candidates"][0]["targeted_collection_request"]["actions"][0]["allowed_path_scope_id"] = "missing"
    mutations.append(("missing path scope", *bad_path))
    case_escape = copy.deepcopy((request, response))
    case_escape[1]["payload"]["cross_domain_candidates"][0]["targeted_collection_request"]["actions"][0]["source_path"] = "/ETC/PVE/storage.cfg"
    mutations.append(("case-changed path authorization", *case_escape))
    bad_workload = copy.deepcopy((request, response))
    bad_workload[1]["payload"]["vm_map"][0].update({"object_type": "container-template", "platform": "pve-qemu"})
    mutations.append(("invalid template platform", *bad_workload))
    bad_planner = copy.deepcopy((request, response))
    bad_planner[1]["payload"]["cross_domain_candidates"][0]["planner_authorization"]["plan_id"] = None
    mutations.append(("missing Planner plan", *bad_planner))
    mismatched_planner = copy.deepcopy((request, response))
    mismatched_planner[1]["payload"]["cross_domain_candidates"][0]["planner_authorization"]["plan_id"] = "other-plan"
    mutations.append(("mismatched Planner plan", *mismatched_planner))
    bad_image = copy.deepcopy((request, response))
    bad_image[1]["payload"]["image_candidates"] = [{
        "cluster_scope_id": "cluster-1", "candidate_id": "image-1", "object_type": "descriptor",
        "content_availability": "descriptor-only", "identity_status": "verified-descriptor",
        "large_artifact_status": "not-required", "analysis_readiness": "ready",
        "analysis_readiness_basis": ["invalid test candidate"], "backing_refs": [],
    }]
    mutations.append(("invalid image readiness", *bad_image))
    evidence_free_completed = copy.deepcopy((request, response))
    evidence_free_completed[1]["payload"]["image_candidates"] = [{
        "cluster_scope_id": "cluster-1", "candidate_id": "image-complete",
        "object_type": "full-image", "content_availability": "complete",
        "identity_status": "verified-content", "large_artifact_status": "completed",
        "analysis_readiness": "ready", "analysis_readiness_basis": ["complete content"],
        "backing_refs": [], "layer_node_refs": [], "artifact_refs": [],
        "ledger_event_refs": [],
    }]
    mutations.append(("completed large Artifact without workflow evidence", *evidence_free_completed))
    empty_collection = copy.deepcopy((request, response))
    collection = empty_collection[1]["payload"]["cross_domain_candidates"][0]["targeted_collection_request"]
    collection.update({"actions": [], "paths": [], "reason": ""})
    mutations.append(("empty targeted collection", *empty_collection))
    bad_log_window = copy.deepcopy((request, response))
    log_action = bad_log_window[1]["payload"]["cross_domain_candidates"][0]["targeted_collection_request"]["actions"][0]
    log_action.update({"action_type": "bounded-log-collection", "since": None, "until": None})
    mutations.append(("bounded log without time window", *bad_log_window))
    bad_layer = copy.deepcopy((request, response))
    bad_layer[1]["payload"]["layer_map"] = {
        "nodes": [
            {"cluster_scope_id": "cluster-1", "layer_node_id": "disk", "node_type": "physical-disk", "owner_node_id": None},
            {"cluster_scope_id": "cluster-1", "layer_node_id": "vg", "node_type": "lvm-vg", "owner_node_id": None},
        ],
        "edges": [{
            "cluster_scope_id": "cluster-1", "from_layer_node_id": "disk",
            "to_layer_node_id": "vg", "relation": "allocates",
        }],
    }
    mutations.append(("invalid Layer endpoint", *bad_layer))
    cyclic_layer = copy.deepcopy((request, response))
    cyclic_layer[1]["payload"]["layer_map"] = {
        "nodes": [
            {"cluster_scope_id": "cluster-1", "layer_node_id": "delta-a", "node_type": "snapshot-delta", "owner_node_id": None},
            {"cluster_scope_id": "cluster-1", "layer_node_id": "delta-b", "node_type": "snapshot-delta", "owner_node_id": None},
        ],
        "edges": [
            {"cluster_scope_id": "cluster-1", "from_layer_node_id": "delta-a", "to_layer_node_id": "delta-b", "relation": "delta-parent-of"},
            {"cluster_scope_id": "cluster-1", "from_layer_node_id": "delta-b", "to_layer_node_id": "delta-a", "relation": "delta-parent-of"},
        ],
    }
    mutations.append(("cyclic Layer parents", *cyclic_layer))
    skipped_negative = copy.deepcopy((request, response))
    skipped_negative[1]["ledger_events"] = [{
        "event_id": "led-skipped", "event_type": "state-transition",
        "status": "skipped", "stage": "Stage 6",
    }]
    skipped_negative[1]["findings"] = [{
        "category": "negative", "evidence_refs": ["led-skipped"],
    }]
    mutations.append(("negative Finding from skipped Stage", *skipped_negative))
    skipped_scope_bypass = copy.deepcopy((request, response))
    skipped_scope_bypass[1]["ledger_events"] = [
        {"event_id": "led-skipped", "event_type": "state-transition", "status": "skipped", "stage": "Stage 6"},
        {"event_id": "led-other", "event_type": "state-transition", "status": "completed", "stage": "Stage 9"},
    ]
    skipped_scope_bypass[1]["findings"] = [{"category": "negative", "evidence_refs": ["led-other"]}]
    mutations.append(("negative Finding bypasses skipped scope", *skipped_scope_bypass))
    bad_projection = copy.deepcopy((request, response))
    bad_projection[1]["payload"]["disk_map"] = [{
        "cluster_scope_id": "cluster-1", "disk_id": "disk-1",
        "owner_node_id": None, "layer_node_id": "missing-layer",
    }]
    mutations.append(("projection references missing Layer", *bad_projection))
    bad_timeline = copy.deepcopy((request, response))
    bad_timeline[1]["payload"]["timeline_candidates"] = [{
        "cluster_scope_id": "cluster-1", "candidate_id": "time-1",
        "source_artifact_id": "artifact-test", "ledger_event_refs": [], "basis": [],
    }]
    mutations.append(("Timeline candidate lacks evidence", *bad_timeline))
    unresolved_limit = copy.deepcopy((request, response))
    unresolved_limit[1]["payload"]["effective_limits"]["max_actions"] = {
        "value": None, "status": "unresolved", "basis": ["no approved source"],
    }
    mutations.append(("Action with unresolved limit", *unresolved_limit))

    for name, mutated_request, mutated_response in mutations:
        if not validate_semantics(mutated_request, mutated_response):
            failures.append(f"invalid semantic case accepted: {name}")
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
