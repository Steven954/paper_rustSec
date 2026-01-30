#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import shutil
import sys
from pathlib import Path


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")


def insert_after_line(lines: list[str], match_fn, new_lines: list[str]) -> bool:
    for i, line in enumerate(lines):
        if match_fn(line):
            lines[i + 1 : i + 1] = new_lines
            return True
    return False


def ensure_safedrop_module(rust_src: Path, safedrop_src: Path) -> None:
    src_dir = safedrop_src / "safedrop_check"
    if not src_dir.is_dir():
        raise FileNotFoundError(f"Missing safedrop_check module: {src_dir}")

    dst_dir = rust_src / "compiler" / "rustc_mir_transform" / "src" / "safedrop_check"
    dst_dir.mkdir(parents=True, exist_ok=True)
    shutil.copytree(src_dir, dst_dir, dirs_exist_ok=True)


def patch_query_mod(rust_src: Path) -> None:
    path = rust_src / "compiler" / "rustc_middle" / "src" / "query" / "mod.rs"
    text = read_text(path)
    if "safedrop_check" in text:
        return

    lines = text.splitlines()
    for i, line in enumerate(lines):
        if "query trigger_delay_span_bug" in line:
            indent = re.match(r"\s*", line).group(0)
            for j in range(i + 1, len(lines)):
                if lines[j].strip() == "}":
                    insert_lines = [
                        f"{indent}query safedrop_check(_: DefId) -> () {{",
                        f"{indent}    desc {{ \"check safedrop bugs in rustc mir\" }}",
                        f"{indent}}}",
                    ]
                    lines[j + 1 : j + 1] = insert_lines
                    write_text(path, "\n".join(lines) + "\n")
                    return
            break

    raise RuntimeError("Failed to insert safedrop_check query in rustc_middle/src/query/mod.rs")


def patch_passes(rust_src: Path) -> None:
    path = rust_src / "compiler" / "rustc_interface" / "src" / "passes.rs"
    text = read_text(path)
    if "safedrop_check" in text:
        return

    lines = text.splitlines()
    for i, line in enumerate(lines):
        if "layout_test::test_layout" in line:
            indent = re.match(r"\s*", line).group(0)
            insert_lines = [
                f"{indent}sess.time(\"safedrop_check\", || {{",
                f"{indent}    tcx.hir().par_body_owners(|def_id| tcx.ensure().safedrop_check(def_id));",
                f"{indent}}});",
            ]
            lines[i + 1 : i + 1] = insert_lines
            write_text(path, "\n".join(lines) + "\n")
            return

    raise RuntimeError("Failed to insert safedrop_check call in rustc_interface/src/passes.rs")


def patch_mir_transform_lib(rust_src: Path) -> None:
    path = rust_src / "compiler" / "rustc_mir_transform" / "src" / "lib.rs"
    text = read_text(path)
    lines = text.splitlines()
    changed = False

    if "pub mod safedrop_check;" not in text:
        insert_targets = [
            "mod required_consts;",
            "mod remove_zsts;",
            "mod remove_unneeded_drops;",
        ]
        inserted = False
        for target in insert_targets:
            for i, line in enumerate(lines):
                if line.strip() == target:
                    indent = re.match(r"\s*", line).group(0)
                    lines[i + 1 : i + 1] = [f"{indent}pub mod safedrop_check;"]
                    inserted = True
                    changed = True
                    break
            if inserted:
                break

        if not inserted:
            raise RuntimeError("Failed to insert safedrop_check module declaration")

    if "use safedrop_check::" not in text:
        inserted = False
        for i, line in enumerate(lines):
            if "use rustc_span" in line:
                indent = re.match(r"\s*", line).group(0)
                lines[i + 1 : i + 1] = [f"{indent}use safedrop_check::{{SafeDropGraph, FuncMap}};"]
                inserted = True
                changed = True
                break
        if not inserted:
            raise RuntimeError("Failed to insert safedrop_check use statement")

    if "safedrop_check," not in text:
        inserted = False
        for i, line in enumerate(lines):
            if re.search(r"\bis_mir_available\b", line):
                indent = re.match(r"\s*", line).group(0)
                lines[i + 1 : i + 1] = [f"{indent}safedrop_check,"]
                inserted = True
                changed = True
                break
        if not inserted:
            raise RuntimeError("Failed to insert safedrop_check provider entry")

    if "fn safedrop_check<" not in text:
        func = """
fn safedrop_check<'tcx>(tcx: TyCtxt<'tcx>, def_id: DefId) -> () {
    if let Some(_other) = tcx.hir().body_const_context(def_id.expect_local()) {
        return;
    }
    if tcx.is_mir_available(def_id) {
        let body = tcx.optimized_mir(def_id);
        let mut func_map = FuncMap::new();
        let mut safedrop_graph = SafeDropGraph::new(&body, tcx, def_id);
        safedrop_graph.solve_scc();
        safedrop_graph.safedrop_check(0, tcx, &mut func_map);
        if safedrop_graph.visit_times <= 10000 {
            safedrop_graph.output_warning();
        } else {
            println!(\"over_visited: {:?}\", def_id);
        }
    }
}
"""
        lines.append(func.strip("\n"))
        changed = True

    if changed:
        write_text(path, "\n".join(lines) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser(description="Apply SafeDrop patch to rustc source.")
    parser.add_argument("--rust-src", required=True, help="Path to rust-lang/rust source checkout")
    parser.add_argument("--safedrop-src", required=True, help="Path to SafeDrop repo")
    args = parser.parse_args()

    rust_src = Path(args.rust_src).resolve()
    safedrop_src = Path(args.safedrop_src).resolve()

    if not rust_src.is_dir():
        print(f"Rust source directory not found: {rust_src}", file=sys.stderr)
        return 2
    if not safedrop_src.is_dir():
        print(f"SafeDrop source directory not found: {safedrop_src}", file=sys.stderr)
        return 2

    ensure_safedrop_module(rust_src, safedrop_src)
    patch_query_mod(rust_src)
    patch_passes(rust_src)
    patch_mir_transform_lib(rust_src)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
