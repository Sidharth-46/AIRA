"""
AIRA — Dependency Analyzer
Parses dependency files, maps import relationships, detects issues.
"""

import os
import json
import re
from utils.logger import get_logger

logger = get_logger("analyzer.dependencies")


class DependencyAnalyzer:
    """Analyzes project dependencies and import relationships."""

    DEPENDENCY_FILES = {
        "package.json": "npm",
        "package-lock.json": "npm_lock",
        "requirements.txt": "pip",
        "Pipfile": "pipenv",
        "pyproject.toml": "pyproject",
        "pom.xml": "maven",
        "build.gradle": "gradle",
        "Cargo.toml": "cargo",
        "go.mod": "go",
        "Gemfile": "bundler",
        "composer.json": "composer",
    }

    def __init__(self, project_path):
        self.root = project_path

    def analyze(self):
        """Full dependency analysis."""
        return {
            "dependency_files": self._find_dependency_files(),
            "packages": self._parse_all_dependencies(),
            "import_graph": self._build_import_graph(),
            "circular_deps": self._detect_circular_deps(),
        }

    def _find_dependency_files(self):
        """Find all dependency manifest files."""
        found = []
        for dirpath, _, filenames in os.walk(self.root):
            # Skip deep nesting and vendored code
            rel = os.path.relpath(dirpath, self.root)
            if any(skip in rel for skip in ["node_modules", ".venv", "venv", ".git"]):
                continue

            for f in filenames:
                if f in self.DEPENDENCY_FILES:
                    path = os.path.relpath(os.path.join(dirpath, f), self.root)
                    found.append({
                        "file": path.replace("\\", "/"),
                        "type": self.DEPENDENCY_FILES[f],
                    })
        return found

    def _parse_all_dependencies(self):
        """Parse all dependency files."""
        all_deps = {}
        dep_files = self._find_dependency_files()

        for df in dep_files:
            file_path = os.path.join(self.root, df["file"])
            dep_type = df["type"]

            try:
                if dep_type == "npm":
                    all_deps[df["file"]] = self._parse_package_json(file_path)
                elif dep_type == "pip":
                    all_deps[df["file"]] = self._parse_requirements_txt(file_path)
                elif dep_type == "pyproject":
                    all_deps[df["file"]] = self._parse_pyproject_toml(file_path)
                elif dep_type == "go":
                    all_deps[df["file"]] = self._parse_go_mod(file_path)
            except Exception as e:
                logger.warning(f"Failed to parse {df['file']}: {e}")
                all_deps[df["file"]] = {"error": str(e)}

        return all_deps

    def _parse_package_json(self, path):
        """Parse npm package.json."""
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        return {
            "name": data.get("name", "unknown"),
            "version": data.get("version", "0.0.0"),
            "dependencies": data.get("dependencies", {}),
            "devDependencies": data.get("devDependencies", {}),
            "total": len(data.get("dependencies", {})) + len(data.get("devDependencies", {})),
        }

    def _parse_requirements_txt(self, path):
        """Parse Python requirements.txt."""
        deps = {}
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or line.startswith("-"):
                    continue
                # Parse package==version, package>=version, etc.
                match = re.match(r"^([a-zA-Z0-9_-]+)\s*([><=!~]+\s*[\d.]+)?", line)
                if match:
                    name = match.group(1)
                    version = match.group(2).strip() if match.group(2) else "*"
                    deps[name] = version

        return {"dependencies": deps, "total": len(deps)}

    def _parse_pyproject_toml(self, path):
        """Parse pyproject.toml (basic parsing)."""
        deps = {}
        in_deps = False

        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line == "[project.dependencies]" or line == "dependencies = [":
                    in_deps = True
                    continue
                if in_deps and line.startswith("["):
                    break
                if in_deps and line.startswith('"'):
                    pkg = line.strip('",').split(">=")[0].split("==")[0].strip()
                    if pkg:
                        deps[pkg] = "*"

        return {"dependencies": deps, "total": len(deps)}

    def _parse_go_mod(self, path):
        """Parse go.mod."""
        deps = {}
        with open(path, "r", encoding="utf-8") as f:
            in_require = False
            for line in f:
                line = line.strip()
                if line.startswith("require ("):
                    in_require = True
                    continue
                if in_require and line == ")":
                    break
                if in_require:
                    parts = line.split()
                    if len(parts) >= 2:
                        deps[parts[0]] = parts[1]

        return {"dependencies": deps, "total": len(deps)}

    def _build_import_graph(self):
        """Build a file-to-file import graph (Python and JS/TS)."""
        graph = {"nodes": [], "edges": []}
        files_map = {}

        # Collect source files
        for dirpath, _, filenames in os.walk(self.root):
            rel = os.path.relpath(dirpath, self.root)
            if any(skip in rel for skip in ["node_modules", ".venv", "venv", ".git", "__pycache__"]):
                continue

            for f in filenames:
                ext = os.path.splitext(f)[1]
                if ext in {".py", ".js", ".jsx", ".ts", ".tsx"}:
                    full = os.path.join(dirpath, f)
                    rel_path = os.path.relpath(full, self.root).replace("\\", "/")
                    files_map[rel_path] = full
                    graph["nodes"].append(rel_path)

        # Parse imports (limit to avoid long processing)
        if len(files_map) > 500:
            graph["note"] = "Import graph limited to first 500 files"
            files_to_process = dict(list(files_map.items())[:500])
        else:
            files_to_process = files_map

        for rel_path, full_path in files_to_process.items():
            try:
                with open(full_path, "r", encoding="utf-8", errors="replace") as f:
                    content = f.read()

                imports = self._extract_imports(content, rel_path)
                for imp in imports:
                    if imp in files_map:
                        graph["edges"].append({"from": rel_path, "to": imp})
            except Exception:
                continue

        return graph

    def _extract_imports(self, content, source_file):
        """Extract import references from source code."""
        imports = []
        ext = os.path.splitext(source_file)[1]
        source_dir = os.path.dirname(source_file)

        if ext == ".py":
            # Python: from x.y import z, import x.y
            for match in re.finditer(r"(?:from|import)\s+([\w.]+)", content):
                module = match.group(1).replace(".", "/") + ".py"
                imports.append(module)

        elif ext in {".js", ".jsx", ".ts", ".tsx"}:
            # JS/TS: import ... from './path', require('./path')
            for match in re.finditer(r"(?:import|require)\s*\(?\s*['\"]([./][^'\"]+)['\"]", content):
                path = match.group(1)
                if path.startswith("./") or path.startswith("../"):
                    resolved = os.path.normpath(os.path.join(source_dir, path)).replace("\\", "/")
                    # Try common extensions
                    for candidate_ext in ["", ".js", ".jsx", ".ts", ".tsx", "/index.js", "/index.ts"]:
                        candidate = resolved + candidate_ext
                        imports.append(candidate)

        return imports

    def _detect_circular_deps(self):
        """Detect circular dependencies in the import graph."""
        graph = {}
        import_graph = self._build_import_graph()

        for edge in import_graph.get("edges", []):
            src = edge["from"]
            dst = edge["to"]
            if src not in graph:
                graph[src] = []
            graph[src].append(dst)

        # Simple DFS cycle detection
        cycles = []
        visited = set()
        rec_stack = set()

        def dfs(node, path):
            if len(cycles) >= 10:  # Limit cycles found
                return
            visited.add(node)
            rec_stack.add(node)
            path.append(node)

            for neighbor in graph.get(node, []):
                if neighbor in rec_stack:
                    cycle_start = path.index(neighbor) if neighbor in path else -1
                    if cycle_start >= 0:
                        cycles.append(path[cycle_start:] + [neighbor])
                elif neighbor not in visited:
                    dfs(neighbor, path[:])

            rec_stack.discard(node)

        for node in graph:
            if node not in visited:
                dfs(node, [])

        return cycles[:10]  # Max 10 cycles
