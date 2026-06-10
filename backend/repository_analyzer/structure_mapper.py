"""
AIRA — Structure Mapper
Project structure analysis, architecture detection, entry point identification.
"""

import os
from utils.logger import get_logger

logger = get_logger("analyzer.structure")

SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv", "env",
             ".idea", ".vscode", ".next", "dist", "build", "target",
             ".tox", ".mypy_cache", ".pytest_cache", "coverage", ".nyc_output"}

ENTRY_POINTS = {
    "main.py", "app.py", "index.py", "server.py", "manage.py", "wsgi.py",
    "index.js", "app.js", "server.js", "main.js", "index.ts", "app.ts",
    "main.go", "main.rs", "Main.java", "Program.cs", "main.c", "main.cpp",
}

ARCHITECTURE_PATTERNS = {
    "mvc": {"controllers", "models", "views"},
    "mvvm": {"models", "viewmodels", "views"},
    "layered": {"routes", "services", "models", "controllers"},
    "microservices": {"services", "gateway", "api-gateway"},
    "monorepo": {"packages", "apps", "libs"},
    "hexagonal": {"domain", "ports", "adapters"},
}

DIR_PURPOSES = {
    "src": "source code",
    "lib": "library code",
    "tests": "test files", "test": "test files", "__tests__": "test files",
    "docs": "documentation", "doc": "documentation",
    "config": "configuration", "configs": "configuration",
    "scripts": "scripts/automation",
    "public": "static/public assets",
    "assets": "media/static assets",
    "static": "static files",
    "templates": "templates",
    "migrations": "database migrations",
    "fixtures": "test fixtures",
    "utils": "utilities", "helpers": "helper functions",
    "middleware": "middleware",
    "hooks": "React hooks",
    "components": "UI components",
    "pages": "page components",
    "api": "API endpoints",
    "routes": "route handlers",
    "services": "service layer",
    "models": "data models",
    "types": "type definitions",
}


class StructureMapper:
    """Analyzes project directory structure and architecture."""

    def __init__(self, project_path):
        self.root = project_path

    def analyze(self):
        """Full structure analysis."""
        tree = self._build_tree(self.root)
        top_dirs = self._get_top_level_dirs()
        entry_points = self._find_entry_points()
        architecture = self._detect_architecture(top_dirs)
        dir_classification = self._classify_directories(top_dirs)
        project_type = self._detect_project_type()

        return {
            "tree": tree,
            "top_level_directories": top_dirs,
            "entry_points": entry_points,
            "architecture": architecture,
            "directory_purposes": dir_classification,
            "project_type": project_type,
        }

    def _build_tree(self, path, prefix="", depth=0, max_depth=5):
        """Build recursive file tree."""
        if depth > max_depth:
            return []

        tree = []
        try:
            entries = sorted(os.listdir(path))
        except PermissionError:
            return tree

        for entry in entries:
            if entry in SKIP_DIRS or entry.startswith("."):
                continue

            full = os.path.join(path, entry)
            rel = os.path.join(prefix, entry) if prefix else entry

            if os.path.isdir(full):
                children = self._build_tree(full, rel, depth + 1, max_depth)
                tree.append({
                    "name": entry, "path": rel.replace("\\", "/"),
                    "type": "directory", "children": children,
                })
            else:
                tree.append({
                    "name": entry, "path": rel.replace("\\", "/"),
                    "type": "file", "size": os.path.getsize(full),
                })
        return tree

    def _get_top_level_dirs(self):
        """Get top-level directory names."""
        dirs = []
        try:
            for entry in os.listdir(self.root):
                full = os.path.join(self.root, entry)
                if os.path.isdir(full) and entry not in SKIP_DIRS and not entry.startswith("."):
                    dirs.append(entry)
        except PermissionError:
            pass
        return dirs

    def _find_entry_points(self):
        """Find project entry point files."""
        found = []
        for dirpath, _, filenames in os.walk(self.root):
            for skip in SKIP_DIRS:
                if skip in dirpath:
                    break
            else:
                for f in filenames:
                    if f in ENTRY_POINTS:
                        rel = os.path.relpath(os.path.join(dirpath, f), self.root)
                        found.append(rel.replace("\\", "/"))
        return found

    def _detect_architecture(self, top_dirs):
        """Detect architectural pattern from directory structure."""
        dir_set = set(d.lower() for d in top_dirs)

        # Also check one level deeper (src/controllers, etc.)
        for d in top_dirs:
            sub_path = os.path.join(self.root, d)
            if os.path.isdir(sub_path):
                try:
                    for sub in os.listdir(sub_path):
                        if os.path.isdir(os.path.join(sub_path, sub)):
                            dir_set.add(sub.lower())
                except PermissionError:
                    pass

        best_match = "standard"
        best_score = 0
        for pattern, required_dirs in ARCHITECTURE_PATTERNS.items():
            overlap = len(dir_set & required_dirs)
            if overlap > best_score:
                best_score = overlap
                best_match = pattern

        return best_match if best_score >= 2 else "standard"

    def _classify_directories(self, dirs):
        """Classify directories by purpose."""
        classified = {}
        for d in dirs:
            purpose = DIR_PURPOSES.get(d.lower(), "project code")
            classified[d] = purpose
        return classified

    def _detect_project_type(self):
        """Detect project type from files and structure."""
        root_files = set()
        try:
            root_files = {f.lower() for f in os.listdir(self.root) if os.path.isfile(os.path.join(self.root, f))}
        except PermissionError:
            pass

        if "package.json" in root_files:
            if any(f in root_files for f in ["next.config.js", "next.config.mjs", "next.config.ts"]):
                return "Next.js Application"
            if "vite.config.js" in root_files or "vite.config.ts" in root_files:
                return "Vite Application"
            return "Node.js Application"

        if "requirements.txt" in root_files or "pyproject.toml" in root_files or "setup.py" in root_files:
            if "manage.py" in root_files:
                return "Django Application"
            if "app.py" in root_files:
                return "Flask Application"
            return "Python Application"

        if "go.mod" in root_files:
            return "Go Application"
        if "cargo.toml" in root_files:
            return "Rust Application"
        if "pom.xml" in root_files:
            return "Java Maven Application"
        if "build.gradle" in root_files:
            return "Java Gradle Application"

        return "Generic Project"
