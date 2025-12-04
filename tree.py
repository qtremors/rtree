#!/usr/bin/env python3
"""
rtree.py

Generates a plain-text folder/file tree for a specified directory.
Can handle Git repositories (respecting .gitignore) and standard folders.

Behavioral Notes:
  - By default, generates a visual ASCII tree.
  - Automatically respects .gitignore rules (prioritizes `git check-ignore`).
  - Hides .git folder contents unless --raw is used.
  - Always shows the .gitignore file itself.
  - Supports colored output (Blue=Dir, Green=File, Yellow=Config).
  - Colors are automatically disabled when writing to a file.

Arguments:
  -r, --repo  : Target directory (absolute or relative).
                Defaults to current directory (.) if omitted.
  --depth     : Limit the recursion depth (e.g., --depth 2).
                Default is -1 (unlimited).
  --list      : Scan the current directory and list all detected git repositories.
  --flat      : Output a flat list of paths (pre-order traversal) instead of a tree.
  --raw       : "Raw" mode. Ignores .gitignore rules and includes full .git/ contents.
  --no-color  : Force disable colored output in the terminal.
  -o, --out   : Output file behavior:
                - [No value]: Auto-generate filename (e.g., 'folder_tree.txt').
                - [Filename]: Write output to the specific filename provided.
                - [Omitted] : Print to standard output (console).

Commands:

    # --- Basic Usage ---
    # Scan the current directory
    rtree
    python rtree.py

    # Scan a specific subdirectory
    rtree -r my-project
    python rtree.py -r my-project

    # Scan an absolute path
    rtree -r "C:/Projects/App"
    python rtree.py -r "C:/Projects/App"

    # --- Depth Control ---
    # Limit tree to 2 levels deep (great for large repos)
    rtree --depth 2
    python rtree.py --depth 2

    # Combine specific target with depth limit
    rtree -r src --depth 3
    python rtree.py -r src --depth 3

    # --- Output to File ---
    # Auto-name the output file (e.g., 'folder_tree.txt')
    rtree -o
    python rtree.py -o

    # Save to a specific filename
    rtree -o structure.txt
    python rtree.py -o structure.txt

    # Scan 'src' and save to 'src.txt'
    rtree -r src -o src.txt
    python rtree.py -r src -o src.txt

    # --- Flat List Mode ---
    # Output a flat list of file paths instead of a tree
    rtree --flat
    python rtree.py --flat

    # Save the flat list to a file
    rtree --flat -o list.txt
    python rtree.py --flat -o list.txt

    # --- Raw / Debug Mode ---
    # Ignore .gitignore rules (shows .git, venv, etc.)
    rtree --raw
    python rtree.py --raw

    # See top-level hidden files only
    rtree --raw --depth 1
    python rtree.py --raw --depth 1

    # Flat list of every file on disk (ignoring rules)
    rtree --raw --flat
    python rtree.py --raw --flat

    # --- Utilities ---
    # List all git repositories found in the current directory
    rtree --list
    python rtree.py --list

    # Force disable colored output in the terminal
    rtree --no-color
    python rtree.py --no-color
"""

from __future__ import annotations

import argparse
import fnmatch
import os
import itertools
import time
import subprocess
import sys
from typing import Dict, List, Optional, Set, Tuple


# =============================================================================
# ANSI Colors
# =============================================================================
class Colors:
    BLUE = "\033[94m"
    GREEN = "\033[92m"
    CYAN = "\033[96m"
    YELLOW = "\033[93m"
    RESET = "\033[0m"
    BOLD = "\033[1m"

    @staticmethod
    def style(text: str, color: str, enabled: bool = True) -> str:
        if not enabled:
            return text
        return f"{color}{text}{Colors.RESET}"


# =============================================================================
# Core Class
# =============================================================================


class RepoTreeVisualizer:
    def __init__(
        self,
        repo_path: str,
        raw_mode: bool = False,
        max_depth: int = -1,
        use_color: bool = True,
        callback=None,
    ):
        self.repo_path = os.path.abspath(repo_path)
        self.raw_mode = raw_mode
        self.max_depth = max_depth
        self.use_color = use_color
        self.callback = callback
        self.gitignore_patterns = self._read_gitignore()

        # Pre-compute ignored files logic
        self.ignored_set: Set[str] = set()
        if not self.raw_mode:
            self.ignored_set = self._compute_ignored_set()

    # -------------------------------------------------------------------------
    # Internal Helpers
    # -------------------------------------------------------------------------

    def _read_gitignore(self) -> List[str]:
        path = os.path.join(self.repo_path, ".gitignore")
        if not os.path.isfile(path):
            return []
        patterns = []
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    line = line.rstrip("\n")
                    if not line or line.lstrip().startswith("#"):
                        continue
                    patterns.append(line)
        except PermissionError:
            pass
        return patterns

    def _is_git_repo(self) -> bool:
        try:
            subprocess.run(
                ["git", "--version"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=3,
            )
            return os.path.isdir(os.path.join(self.repo_path, ".git"))
        except Exception:
            return False

    def _git_check_ignore(self, relpaths: List[str]) -> Set[str]:
        if not relpaths:
            return set()
        try:
            input_bytes = "\0".join(relpaths).encode("utf-8")
            proc = subprocess.run(
                ["git", "check-ignore", "--stdin", "-z"],
                input=input_bytes,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                cwd=self.repo_path,
                timeout=10,
            )
            if proc.returncode not in (0, 1) or not proc.stdout:
                return set()
            parts = [p.decode("utf-8") for p in proc.stdout.split(b"\0") if p]
            return set(parts)
        except Exception:
            return set()

    def _compile_simple_patterns(self) -> List[Tuple[str, bool, bool]]:
        compiled = []
        for raw in self.gitignore_patterns:
            p = raw.strip()
            if not p or p.startswith("#"):
                continue
            is_dir = p.endswith("/")
            if is_dir:
                p = p[:-1]
            anchored = p.startswith("/")
            if anchored:
                p = p[1:]
            p = p.replace("\\", "/")
            compiled.append((p, is_dir, anchored))
        return compiled

    def _simple_gitignore_match(
        self, relpath: str, compiled_patterns: List[Tuple[str, bool, bool]]
    ) -> bool:
        if not compiled_patterns:
            return False
        for pat, is_dir, anchored in compiled_patterns:
            if anchored:
                if fnmatch.fnmatch(relpath, pat) or fnmatch.fnmatch(relpath, pat + "/"):
                    return (
                        (relpath == pat or relpath.startswith(pat + "/"))
                        if is_dir
                        else True
                    )
            elif fnmatch.fnmatch(relpath, pat) or fnmatch.fnmatch(
                os.path.basename(relpath), pat
            ):
                return (
                    (relpath == pat or relpath.startswith(pat + "/"))
                    if is_dir
                    else True
                )
        return False

    def _collect_all_relpaths(
        self, prune_patterns: List[Tuple[str, bool, bool]] = None
    ) -> Tuple[List[str], Set[str]]:
        rels = []
        early_ignored = set()

        try:
            for dirpath, dirnames, filenames in os.walk(self.repo_path, topdown=True):
                if self.callback: self.callback()
                rel_dir = os.path.relpath(dirpath, self.repo_path)
                if rel_dir == ".":
                    rel_dir = ""
                else:
                    rel_dir = rel_dir.replace(os.sep, "/")
                    rels.append(rel_dir)

                if prune_patterns:
                    active_dirs = []
                    for d in dirnames:
                        path_to_check = (rel_dir + "/" + d) if rel_dir else d
                        if self._simple_gitignore_match(path_to_check, prune_patterns):
                            early_ignored.add(path_to_check)
                        else:
                            active_dirs.append(d)
                    dirnames[:] = active_dirs

                for f in filenames:
                    rels.append(
                        (rel_dir + "/" + f if rel_dir else f).replace(os.sep, "/")
                    )
        except PermissionError:
            pass
        return rels, early_ignored

    def _compute_ignored_set(self) -> Set[str]:
        compiled = self._compile_simple_patterns()

        all_rel, early_ignored = self._collect_all_relpaths(prune_patterns=compiled)

        ignored: Set[str] = {r for r in all_rel if r.startswith(".git/")}
        ignored.update(early_ignored)

        if self._is_git_repo():
            ig = self._git_check_ignore(all_rel)
            if ig:
                ignored.update(p.replace("\\", "/") for p in ig if p)
                ignored.discard(".gitignore")
        else:
            for r in all_rel:
                if r == ".gitignore" or r.startswith(".git/"):
                    continue
                if self._simple_gitignore_match(r, compiled):
                    ignored.add(r)

        return {x.rstrip("/") for x in ignored if x != ".git" and x != ".gitignore"}

        compiled = self._compile_simple_patterns()
        for r in all_rel:
            if r == ".gitignore" or r.startswith(".git/"):
                if r.startswith(".git/"):
                    ignored.add(r)
                continue
            if self._simple_gitignore_match(r, compiled):
                ignored.add(r)

        return {x.rstrip("/") for x in ignored if x != ".git" and x != ".gitignore"}

    # -------------------------------------------------------------------------
    # Tree Generation
    # -------------------------------------------------------------------------

    def get_ascii_tree(self) -> List[str]:
        def _build_tree_dict(root: str) -> Dict:
            tree: Dict[str, Dict] = {}
            root_abs = os.path.abspath(root)
            try:
                for dirpath, dirnames, filenames in os.walk(root_abs, topdown=True):
                    rel_dir = os.path.relpath(dirpath, root_abs)
                    rel_dir_norm = (
                        "" if rel_dir == "." else rel_dir.replace(os.sep, "/")
                    )

                    # Depth Check
                    current_depth = (
                        0 if not rel_dir_norm else rel_dir_norm.count("/") + 1
                    )
                    if self.max_depth > -1 and current_depth >= self.max_depth:
                        dirnames[:] = []  # Stop recursion
                        filenames[
                            :
                        ] = []  # Don't show files at max depth (optional preference)

                    parts = [] if rel_dir_norm == "" else rel_dir_norm.split("/")
                    node = tree
                    for p in parts:
                        node = node.setdefault(p, {})

                    # Filter Directories
                    keep_dirs = []
                    for d in sorted(dirnames):
                        if d == ".git" and not self.raw_mode:
                            node.setdefault(".git", {})
                            continue
                        rel = (rel_dir_norm + "/" + d) if rel_dir_norm else d
                        if not self.raw_mode and (
                            rel in self.ignored_set
                            or rel.rstrip("/") in self.ignored_set
                        ):
                            continue
                        keep_dirs.append(d)
                    dirnames[:] = keep_dirs

                    for d in dirnames:
                        node.setdefault(d, {})

                    # Filter Files
                    for f in sorted(filenames):
                        relf = (rel_dir_norm + "/" + f) if rel_dir_norm else f
                        if f == ".gitignore":
                            node.setdefault(f, {})
                            continue
                        if not self.raw_mode and (
                            relf in self.ignored_set
                            or relf.rstrip("/") in self.ignored_set
                        ):
                            continue
                        node.setdefault(f, {})
            except PermissionError:
                pass
            return tree

        def _render_ascii(node: Dict, prefix: str = "") -> List[str]:
            items = sorted(node.items(), key=lambda x: (len(x[1]) == 0, x[0].lower()))
            lines = []
            for idx, (name, child) in enumerate(items):
                is_last = idx == len(items) - 1
                connector = "└── " if is_last else "├── "

                # Color Logic
                if child or name == ".git":  # Directory
                    colored_name = Colors.style(name + "/", Colors.BLUE, self.use_color)
                elif name == ".gitignore":
                    colored_name = Colors.style(name, Colors.YELLOW, self.use_color)
                else:  # File
                    colored_name = Colors.style(name, Colors.GREEN, self.use_color)

                lines.append(prefix + connector + colored_name)

                if child:
                    extension = "    " if is_last else "│   "
                    lines.extend(_render_ascii(child, prefix + extension))
            return lines

        tree_dict = _build_tree_dict(self.repo_path)
        # Color the root header
        header = Colors.style(
            os.path.basename(self.repo_path) + "/",
            Colors.BLUE + Colors.BOLD,
            self.use_color,
        )
        return [header] + _render_ascii(tree_dict)

    def get_flat_list(self) -> List[str]:
        """Generates a pre-order flat list of paths."""
        lines = []
        root_abs = self.repo_path

        def _recurse(abs_path: str, rel_prefix: str, depth: int):
            if self.max_depth > -1 and depth > self.max_depth:
                return
            try:
                entries = sorted(os.listdir(abs_path))
            except PermissionError:
                return

            files = [e for e in entries if os.path.isfile(os.path.join(abs_path, e))]
            dirs = [e for e in entries if os.path.isdir(os.path.join(abs_path, e))]

            for f in files:
                rel = (rel_prefix + f) if rel_prefix else f
                if (
                    f != ".gitignore"
                    and not self.raw_mode
                    and (rel in self.ignored_set or rel.rstrip("/") in self.ignored_set)
                ):
                    continue
                lines.append(rel)

            for d in sorted(dirs):
                rel = (rel_prefix + d) if rel_prefix else d
                if rel == ".git" and not self.raw_mode:
                    lines.append(rel + "/")
                    continue
                if not self.raw_mode and (
                    rel in self.ignored_set or rel.rstrip("/") in self.ignored_set
                ):
                    continue
                lines.append(rel + "/")
                _recurse(os.path.join(abs_path, d), rel + "/", depth + 1)

        _recurse(root_abs, "", 0)
        return lines


# =============================================================================
# Main Execution
# =============================================================================


def auto_out_name(
    repo_name: str, ascii_mode: bool, flat_mode: bool, raw_mode: bool
) -> str:
    base = os.path.basename(os.path.abspath(repo_name))
    suffix = "flat_tree" if flat_mode else "tree"
    if not flat_mode and ascii_mode:
        suffix = "ascii_tree"
    if raw_mode:
        suffix += "_raw"
    return f"{base}_{suffix}.txt"


def main():
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    p.add_argument(
        "--repo",
        "-r",
        default=".",
        nargs="?",
        help="Target directory (absolute or relative). Defaults to current directory.",
    )
    p.add_argument("--out", "-o", nargs="?", const=True, help="Write output to file.")
    p.add_argument("--flat", action="store_true", help="Output flat list.")
    p.add_argument(
        "--raw", action="store_true", help="Include everything (ignore .gitignore)."
    )
    p.add_argument(
        "--depth",
        type=int,
        default=-1,
        help="Max recursion depth (default: unlimited).",
    )
    p.add_argument("--no-color", action="store_true", help="Disable colored output.")
    p.add_argument("--list", action="store_true", help="List available git repos.")

    args = p.parse_args()
    cwd = os.getcwd()

    if args.list:
        try:
            repos = [
                n
                for n in sorted(os.listdir(cwd))
                if os.path.isdir(os.path.join(cwd, n, ".git"))
            ]
            for r in repos:
                print(Colors.style(r, Colors.BLUE, not args.no_color))
            if not repos:
                print("No git repos found.")
        except Exception:
            pass
        return

    target_arg = args.repo
    repo_path = (
        target_arg if os.path.isabs(target_arg) else os.path.join(cwd, target_arg)
    )

    if not os.path.isdir(repo_path):
        print(f"Error: '{target_arg}' is not a valid directory.", file=sys.stderr)
        sys.exit(2)

    # Determine if we should use color
    out_arg = args.out
    writing_to_file = out_arg is not None
    use_color = not args.no_color and not writing_to_file

    # --- Spinner Setup ---
    spinner_active = not writing_to_file and sys.stdout.isatty()
    msg = f"rtree: scanning {repo_path}..."
    spinner = itertools.cycle(["|", "/", "-", "\\"])
    last_spin = 0

    def update_spinner():
        nonlocal last_spin
        if not spinner_active:
            return
        now = time.time()
        if now - last_spin > 0.1:
            sys.stdout.write(
                Colors.style(f"\r{msg} {next(spinner)}", Colors.CYAN, use_color)
            )
            sys.stdout.flush()
            last_spin = now

    if spinner_active:
        sys.stdout.write("\033[?25l") # Hide Cursor
        sys.stdout.write(Colors.style(msg, Colors.CYAN, use_color))
        sys.stdout.flush()

    try:
        # Pass the callback to the visualizer
        visualizer = RepoTreeVisualizer(
            repo_path, 
            raw_mode=bool(args.raw), 
            max_depth=args.depth, 
            use_color=use_color,
            callback=update_spinner
        )

        output_lines = (
            visualizer.get_flat_list() if args.flat else visualizer.get_ascii_tree()
        )
        
        # Clear spinner line
        if spinner_active:
            sys.stdout.write(f"\r{' ' * (len(msg) + 5)}\r")
            sys.stdout.flush()

        if writing_to_file:
            outname = (
                auto_out_name(repo_path, not args.flat, args.flat, args.raw)
                if out_arg is True
                else out_arg
            )
            try:
                with open(outname, "w", encoding="utf-8") as f:
                    f.write("\n".join(output_lines) + "\n")
                print(f"Output written to: {Colors.style(str(outname), Colors.GREEN)}")
            except Exception as e:
                print(f"Error writing to '{outname}': {e}", file=sys.stderr)
        else:
            print("\n".join(output_lines))

    finally:
        if spinner_active:
            sys.stdout.write("\033[?25h") # Show Cursor

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n" + Colors.style("⚠ Tree generation interrupted.", Colors.YELLOW))
        sys.exit(0)