#!/usr/bin/env python3
"""Prepare reviewed native skill plugins; activation is an explicit host action."""

from __future__ import annotations

import argparse
from dataclasses import asdict
import json
import os
from pathlib import Path
import shutil
import tempfile

try:
    from .upstream_catalog import Catalog, UpstreamError, identifier, load_catalog
    from .upstream_sources import fingerprint_tree, stage_source, support_digest
except ImportError:
    from upstream_catalog import Catalog, UpstreamError, identifier, load_catalog
    from upstream_sources import fingerprint_tree, stage_source, support_digest


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def prepare(
    catalog: Catalog,
    destination: Path,
    *,
    source_ids: tuple[str, ...] = (),
    marketplace_name: str = "bible-reviewed-additions",
) -> dict[str, object]:
    """Build a new marketplace, retaining source paths and excluding host setup."""
    if not destination.is_absolute() or destination.exists() or destination.is_symlink():
        raise UpstreamError("destination must be a new absolute directory")
    identifier(marketplace_name, "marketplace name")
    if any(
        identity not in catalog.sources or catalog.sources[identity].installation != "native"
        for identity in source_ids
    ):
        raise UpstreamError("selected sources must be reviewed native providers")
    sources = [
        source
        for source in catalog.sources.values()
        if source.installation == "native" and (not source_ids or source.id in source_ids)
    ]
    if not sources:
        raise UpstreamError("catalog has no native sources")
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(tempfile.mkdtemp(prefix=".native-plugins-", dir=destination.parent))
    plugins: list[dict[str, object]] = []
    try:
        for source in sources:
            staged = stage_source(source, temporary / "staging" / source.id)
            skills = [skill for skill in catalog.skills.values() if skill.source == source.id]
            for skill in skills:
                if fingerprint_tree(staged / skill.path) != skill.tree_sha256:
                    raise UpstreamError(f"native tree digest mismatch: {skill.id}")
            provider = temporary / "providers" / source.id
            provider.mkdir(parents=True)
            for payload in source.support:
                if support_digest(staged / payload.path) != payload.sha256:
                    raise UpstreamError(f"native support digest mismatch: {source.id}")
            for root in (*source.skill_roots, *(payload.path for payload in source.support)):
                target = provider / root
                target.parent.mkdir(parents=True, exist_ok=True)
                if (staged / root).is_dir():
                    shutil.copytree(staged / root, target)
                else:
                    shutil.copy2(staged / root, target)
            for relative in (source.license_path, *(notice.path for notice in source.notices)):
                target = provider / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(staged / relative, target)
            name = "bible-" + source.id
            write_json(
                provider / ".codex-plugin/plugin.json",
                {
                    "name": name,
                    "version": "0.0.0-" + source.revision[:12],
                    "description": f"Reviewed original skills from {source.url}",
                    "skills": ["./" + skill.path for skill in skills],
                },
            )
            write_json(
                provider / "source-provenance.json",
                {"source": asdict(source), "skills": {s.id: s.tree_sha256 for s in skills}},
            )
            plugins.append(
                {
                    "name": name,
                    "source": {"source": "local", "path": "./providers/" + source.id},
                    "policy": {"installation": "AVAILABLE", "authentication": "ON_INSTALL"},
                    "category": "Developer Tools",
                }
            )
        shutil.rmtree(temporary / "staging")
        write_json(
            temporary / ".agents/plugins/marketplace.json",
            {
                "name": marketplace_name,
                "interface": {"displayName": "Bible reviewed skill additions"},
                "plugins": plugins,
            },
        )
        # Refuse a destination created while archives were being staged.
        if destination.exists() or destination.is_symlink():
            raise UpstreamError("destination appeared during preparation")
        os.rename(temporary, destination)
    finally:
        if temporary.exists():
            shutil.rmtree(temporary)
    return {"marketplace": str(destination), "plugins": [p["name"] for p in plugins]}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--destination", type=Path, required=True)
    parser.add_argument(
        "--source",
        action="append",
        default=[],
        help="Select a reviewed native source; repeat as needed (default: all)",
    )
    parser.add_argument(
        "--marketplace-name",
        default="bible-reviewed-additions",
        help="Host marketplace namespace; use a new name for a separate wave",
    )
    args = parser.parse_args()
    try:
        catalog = load_catalog(
            args.root / "config/upstream-skills.json", args.root / "skills/registry.yml"
        )
        result = prepare(
            catalog,
            args.destination,
            source_ids=tuple(args.source),
            marketplace_name=args.marketplace_name,
        )
    except (UpstreamError, OSError) as exc:
        parser.exit(1, f"native plugin preparation failed: {exc}\n")
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
