#!/usr/bin/env python3
"""add_files_to_xcode.py — detect and add new source files to an Xcode project.

Usage:
    python3 scripts/add_files_to_xcode.py [--files F ...] [--target NAME]
                                          [--project PATH] [--dry-run]

Exit codes: 0 success · 1 project file not found · 2 invalid project
structure · 3 no files to add.
"""

from __future__ import annotations

import argparse
import random
import re
import shutil
import sys
from pathlib import Path

SOURCE_EXTS = {".swift", ".m", ".mm", ".c", ".cpp"}
RESOURCE_EXTS = {".storyboard", ".xib", ".xcassets", ".json", ".plist",
                 ".png", ".jpg", ".jpeg", ".strings", ".entitlements"}
SKIP_DIRS = {".git", ".build", "DerivedData", "Pods", "Carthage", ".swiftpm",
             "node_modules", "__pycache__"}

UUID_RE = re.compile(r"\b[0-9A-F]{24}\b")
SECTION_RE = {
    "build_file": re.compile(r"/\* Begin PBXBuildFile section \*/"),
    "file_ref": re.compile(r"/\* Begin PBXFileReference section \*/"),
}
INSERT_AFTER_RE = {
    "build_file": re.compile(r"/\* Begin PBXBuildFile section \*/\n"),
    "file_ref": re.compile(r"/\* Begin PBXFileReference section \*/\n"),
}


def new_uuid(used: set[str]) -> str:
    while True:
        u = "".join(random.choices("0123456789ABCDEF", k=24))
        if u not in used:
            used.add(u)
            return u


def file_kind(path: Path) -> str:
    ext = path.suffix.lower()
    if ext in SOURCE_EXTS:
        return "source"
    return "resource"


def last_known_file_type(path: Path) -> str:
    return {
        ".swift": "sourcecode.swift",
        ".m": "sourcecode.c.objc",
        ".mm": "sourcecode.cpp.objcpp",
        ".c": "sourcecode.c.c",
        ".cpp": "sourcecode.cpp.cpp",
        ".h": "sourcecode.c.h",
        ".storyboard": "file.storyboard",
        ".xib": "file.xib",
        ".xcassets": "folder.assetcatalog",
        ".json": "text.json",
        ".plist": "text.plist.xml",
        ".strings": "text.plist.strings",
        ".entitlements": "text.plist.entitlements",
    }.get(path.suffix.lower(), "text")


def find_project(start: Path) -> Path | None:
    for p in sorted(start.glob("*.xcodeproj")):
        candidate = p / "project.pbxproj"
        if candidate.exists():
            return candidate
    return None


def scan_untracked(project_file: Path, root: Path, body: str) -> list[Path]:
    referenced = {m.group(1) for m in re.finditer(r"path = ([^;]+);", body)}
    referenced_names = {Path(r.strip('"')).name for r in referenced}
    found: list[Path] = []
    for f in sorted(root.rglob("*")):
        if not f.is_file():
            continue
        if any(part in SKIP_DIRS or part.endswith(".xcodeproj") for part in f.parts):
            continue
        if f.suffix.lower() not in SOURCE_EXTS | RESOURCE_EXTS:
            continue
        if f.name in referenced_names:
            continue
        found.append(f)
    return found


def main() -> int:
    ap = argparse.ArgumentParser(description="Add new files to an Xcode project.")
    ap.add_argument("--files", nargs="*", default=None,
                    help="specific files to add (default: auto-scan)")
    ap.add_argument("--target", default=None, help="native target name (default: first)")
    ap.add_argument("--project", default=None, help="path to project.pbxproj or .xcodeproj")
    ap.add_argument("--dry-run", action="store_true", help="preview without writing")
    args = ap.parse_args()

    root = Path.cwd()
    if args.project:
        p = Path(args.project)
        project_file = p / "project.pbxproj" if p.suffix == ".xcodeproj" else p
    else:
        project_file = find_project(root)
    if project_file is None or not project_file.exists():
        print("error: project.pbxproj not found (use --project)", file=sys.stderr)
        return 1
    project_file = Path(project_file)

    body = project_file.read_text(encoding="utf-8")
    used_uuids = set(UUID_RE.findall(body))

    # --- locate target + its Sources phase ---------------------------------
    targets = re.findall(
        r"([0-9A-F]{24}) /\* ([^*]+) \*/ = \{\s*isa = PBXNativeTarget;", body)
    if not targets:
        print("error: no PBXNativeTarget found (invalid project structure)",
              file=sys.stderr)
        return 2
    target_uuid, target_name = next(
        ((u, n) for u, n in targets if n == args.target), targets[0])
    if args.target and target_name != args.target:
        print(f"error: target not found: {args.target}", file=sys.stderr)
        return 2

    phases_block = re.search(
        re.escape(target_uuid) + r" /\* [^*]+ \*/ = \{.*?buildPhases = \((.*?)\);",
        body, re.S)
    if not phases_block:
        print("error: cannot locate build phases (invalid project structure)",
              file=sys.stderr)
        return 2
    phase_uuids = UUID_RE.findall(phases_block.group(1))
    sources_phase = resources_phase = None
    for pu in phase_uuids:
        m = re.search(re.escape(pu) + r" /\* ([^*]+) \*/ = \{\s*isa = (PBX\w+?BuildPhase);", body)
        if not m:
            continue
        if m.group(2) == "PBXSourcesBuildPhase":
            sources_phase = (pu, m.group(1))
        elif m.group(2) == "PBXResourcesBuildPhase":
            resources_phase = (pu, m.group(1))

    # --- main group children (files appear at project root level) ----------
    main_group = re.search(r"mainGroup = ([0-9A-F]{24});", body)
    if not main_group:
        print("error: cannot locate mainGroup (invalid project structure)",
              file=sys.stderr)
        return 2
    main_group_uuid = main_group.group(1)

    # --- collect candidate files -------------------------------------------
    if args.files:
        files = [Path(f) for f in args.files]
        missing = [str(f) for f in files if not (root / f).exists()]
        if missing:
            print(f"error: file(s) not found: {', '.join(missing)}", file=sys.stderr)
            return 3
    else:
        files = scan_untracked(project_file, root, body)
    files = [f for f in files if f.name not in
             {Path(r.strip('"')).name for r in re.findall(r"path = ([^;]+);", body)}]
    if not files:
        print("no files to add")
        return 3

    # --- plan edits ---------------------------------------------------------
    build_entries: list[str] = []
    ref_entries: list[str] = []
    phase_adds: list[tuple[str, str, str]] = []  # (phase_uuid, build_uuid, name)
    group_adds: list[tuple[str, str]] = []       # (ref_uuid, name)
    plan: list[str] = []

    for f in files:
        rel = f if not f.is_absolute() else f.relative_to(root)
        kind = file_kind(rel)
        ref_uuid = new_uuid(used_uuids)
        name = rel.name
        ref_entries.append(
            f"\t\t{ref_uuid} /* {name} */ = {{isa = PBXFileReference; "
            f"lastKnownFileType = {last_known_file_type(rel)}; "
            f"path = {rel.as_posix()}; sourceTree = \"<group>\"; }};")
        group_adds.append((ref_uuid, name))
        if kind == "source" and sources_phase:
            build_uuid = new_uuid(used_uuids)
            build_entries.append(
                f"\t\t{build_uuid} /* {name} in Sources */ = {{isa = PBXBuildFile; "
                f"fileRef = {ref_uuid} /* {name} */; }};")
            phase_adds.append((sources_phase[0], build_uuid, f"{name} in Sources"))
            plan.append(f"  + {rel}  (Sources → {target_name})")
        else:
            if resources_phase:
                build_uuid = new_uuid(used_uuids)
                build_entries.append(
                    f"\t\t{build_uuid} /* {name} in Resources */ = {{isa = PBXBuildFile; "
                    f"fileRef = {ref_uuid} /* {name} */; }};")
                phase_adds.append((resources_phase[0], build_uuid, f"{name} in Resources"))
            plan.append(f"  + {rel}  (file reference only)")

    print(("DRY-RUN: would add" if args.dry_run else "Adding")
          + f" {len(files)} file(s) to target '{target_name}':")
    print("\n".join(plan))
    if args.dry_run:
        return 0

    # --- apply edits --------------------------------------------------------
    out = body
    out = INSERT_AFTER_RE["build_file"].sub(
        lambda m: m.group(0) + "\n".join(build_entries) + "\n", out, count=1) \
        if build_entries else out
    out = INSERT_AFTER_RE["file_ref"].sub(
        lambda m: m.group(0) + "\n".join(ref_entries) + "\n", out, count=1)

    for phase_uuid, build_uuid, label in phase_adds:
        out = re.sub(
            r"(" + phase_uuid + r" /\* [^*]+ \*/ = \{\s*isa = PBX\w+?BuildPhase;.*?files = \(\n)",
            lambda m: m.group(1) + f"\t\t\t\t{build_uuid} /* {label} */,\n",
            out, count=1, flags=re.S)

    out = re.sub(
        r"(" + main_group_uuid + r" /\* [^*]* \*/ = \{\s*isa = PBXGroup;.*?children = \(\n)",
        lambda m: m.group(1) + "".join(
            f"\t\t\t\t{u} /* {n} */,\n" for u, n in group_adds),
        out, count=1, flags=re.S)

    if out == body:
        print("error: failed to apply edits (invalid project structure)",
              file=sys.stderr)
        return 2

    backup = project_file.with_suffix(".pbxproj.bak")
    shutil.copy2(project_file, backup)
    project_file.write_text(out, encoding="utf-8")
    print(f"backup written: {backup.name}")
    print(f"done: {len(files)} file(s) added")
    return 0


if __name__ == "__main__":
    sys.exit(main())
