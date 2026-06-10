"""
AIRA — Technology Stack Detector
Detects languages, frameworks, databases, build tools, and infrastructure.
"""

import os
import json
from collections import Counter
from utils.logger import get_logger

logger = get_logger("analyzer.tech")

LANGUAGE_EXTENSIONS = {
    ".py": "Python", ".js": "JavaScript", ".jsx": "JavaScript",
    ".ts": "TypeScript", ".tsx": "TypeScript", ".java": "Java",
    ".c": "C", ".cpp": "C++", ".h": "C/C++ Header", ".hpp": "C++ Header",
    ".cs": "C#", ".go": "Go", ".rs": "Rust", ".rb": "Ruby",
    ".php": "PHP", ".swift": "Swift", ".kt": "Kotlin",
    ".scala": "Scala", ".r": "R", ".sql": "SQL",
    ".html": "HTML", ".css": "CSS", ".scss": "SCSS",
    ".sh": "Shell", ".bash": "Shell",
    ".yaml": "YAML", ".yml": "YAML", ".json": "JSON",
    ".xml": "XML", ".toml": "TOML", ".md": "Markdown",
    ".vue": "Vue", ".svelte": "Svelte", ".dart": "Dart",
}

FRAMEWORK_INDICATORS = {
    # JS/TS Frameworks
    "react": {"files": [], "deps": ["react", "react-dom"]},
    "next.js": {"files": ["next.config.js", "next.config.mjs", "next.config.ts"], "deps": ["next"]},
    "vue": {"deps": ["vue"]},
    "angular": {"files": ["angular.json"], "deps": ["@angular/core"]},
    "svelte": {"deps": ["svelte"]},
    "express": {"deps": ["express"]},
    "nest.js": {"deps": ["@nestjs/core"]},

    # Python Frameworks
    "flask": {"deps": ["flask", "Flask"]},
    "django": {"files": ["manage.py"], "deps": ["django", "Django"]},
    "fastapi": {"deps": ["fastapi"]},
    "pytorch": {"deps": ["torch"]},
    "tensorflow": {"deps": ["tensorflow"]},

    # Other
    "spring boot": {"files": ["pom.xml"], "deps": ["spring-boot"]},
    "rails": {"files": ["Gemfile"], "deps": ["rails"]},
}

DATABASE_INDICATORS = {
    "MongoDB": {"deps": ["pymongo", "mongoose", "mongodb"], "files": []},
    "PostgreSQL": {"deps": ["psycopg2", "pg", "postgres"], "files": []},
    "MySQL": {"deps": ["mysql", "mysql2", "mysqlclient"], "files": []},
    "Redis": {"deps": ["redis", "ioredis"], "files": []},
    "SQLite": {"deps": ["sqlite3", "better-sqlite3"], "files": ["*.sqlite", "*.db"]},
}


class TechDetector:
    """Detects the complete technology stack of a project."""

    def __init__(self, project_path):
        self.root = project_path

    def detect(self):
        """Run full technology detection."""
        languages = self._detect_languages()
        primary = max(languages, key=languages.get) if languages else "Unknown"
        frameworks = self._detect_frameworks()
        databases = self._detect_databases()
        build_tools = self._detect_build_tools()
        infrastructure = self._detect_infrastructure()
        testing = self._detect_testing()

        return {
            "languages": languages,
            "primary_language": primary,
            "frameworks": frameworks,
            "databases": databases,
            "build_tools": build_tools,
            "infrastructure": infrastructure,
            "testing_frameworks": testing,
            "project_type": self._classify_project(languages, frameworks),
        }

    def _detect_languages(self):
        """Detect languages and LOC per language."""
        lang_loc = Counter()
        skip = {"node_modules", ".venv", "venv", ".git", "__pycache__", "dist", "build"}

        for dirpath, dirnames, filenames in os.walk(self.root):
            dirnames[:] = [d for d in dirnames if d not in skip]

            for f in filenames:
                ext = os.path.splitext(f)[1].lower()
                lang = LANGUAGE_EXTENSIONS.get(ext)
                if lang and lang not in {"JSON", "YAML", "TOML", "Markdown", "XML"}:
                    full = os.path.join(dirpath, f)
                    try:
                        with open(full, "r", encoding="utf-8", errors="replace") as fh:
                            loc = sum(1 for line in fh if line.strip())
                        lang_loc[lang] += loc
                    except Exception:
                        pass

        return dict(lang_loc.most_common(15))

    def _detect_frameworks(self):
        """Detect frameworks from dependency files and project structure."""
        detected = []
        all_deps = self._get_all_dependency_names()
        root_files = self._get_root_files()

        for framework, indicators in FRAMEWORK_INDICATORS.items():
            found = False
            # Check dependency names
            for dep in indicators.get("deps", []):
                if dep.lower() in all_deps:
                    found = True
                    break
            # Check indicator files
            for f in indicators.get("files", []):
                if f.lower() in root_files:
                    found = True
                    break

            if found:
                detected.append(framework)

        return detected

    def _detect_databases(self):
        """Detect database technologies."""
        detected = []
        all_deps = self._get_all_dependency_names()

        for db, indicators in DATABASE_INDICATORS.items():
            for dep in indicators.get("deps", []):
                if dep.lower() in all_deps:
                    detected.append(db)
                    break

        return detected

    def _detect_build_tools(self):
        """Detect build tools and bundlers."""
        tools = []
        root_files = self._get_root_files()

        tool_files = {
            "webpack": ["webpack.config.js", "webpack.config.ts"],
            "vite": ["vite.config.js", "vite.config.ts"],
            "rollup": ["rollup.config.js"],
            "esbuild": ["esbuild.config.js"],
            "maven": ["pom.xml"],
            "gradle": ["build.gradle", "build.gradle.kts"],
            "cargo": ["cargo.toml"],
            "make": ["makefile"],
            "cmake": ["cmakelists.txt"],
        }

        for tool, files in tool_files.items():
            if any(f in root_files for f in files):
                tools.append(tool)

        return tools

    def _detect_infrastructure(self):
        """Detect infrastructure and DevOps tools."""
        infra = []
        root_files = self._get_root_files()

        infra_files = {
            "Docker": ["dockerfile", "docker-compose.yml", "docker-compose.yaml", ".dockerignore"],
            "Kubernetes": ["k8s", "kubernetes", "deployment.yaml", "service.yaml"],
            "GitHub Actions": [".github"],
            "GitLab CI": [".gitlab-ci.yml"],
            "Terraform": ["main.tf", "terraform.tf"],
            "Nginx": ["nginx.conf"],
        }

        for tech, files in infra_files.items():
            if any(f in root_files for f in files):
                infra.append(tech)

        # Check .github directory exists
        if os.path.isdir(os.path.join(self.root, ".github", "workflows")):
            if "GitHub Actions" not in infra:
                infra.append("GitHub Actions")

        return infra

    def _detect_testing(self):
        """Detect testing frameworks."""
        testing = []
        all_deps = self._get_all_dependency_names()

        test_deps = {
            "Jest": ["jest"],
            "Pytest": ["pytest"],
            "JUnit": ["junit"],
            "Mocha": ["mocha"],
            "Vitest": ["vitest"],
            "Cypress": ["cypress"],
            "Playwright": ["playwright", "@playwright/test"],
        }

        for framework, deps in test_deps.items():
            for dep in deps:
                if dep.lower() in all_deps:
                    testing.append(framework)
                    break

        return testing

    def _get_all_dependency_names(self):
        """Get all dependency names across all manifest files."""
        deps = set()

        # package.json
        pkg_path = os.path.join(self.root, "package.json")
        if os.path.isfile(pkg_path):
            try:
                with open(pkg_path, "r") as f:
                    data = json.load(f)
                for key in ["dependencies", "devDependencies"]:
                    deps.update(k.lower() for k in data.get(key, {}).keys())
            except Exception:
                pass

        # requirements.txt
        req_path = os.path.join(self.root, "requirements.txt")
        if os.path.isfile(req_path):
            try:
                with open(req_path, "r") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#") and not line.startswith("-"):
                            pkg = line.split("==")[0].split(">=")[0].split("<=")[0].strip()
                            deps.add(pkg.lower())
            except Exception:
                pass

        return deps

    def _get_root_files(self):
        """Get lowercase root-level filenames."""
        try:
            return {f.lower() for f in os.listdir(self.root)}
        except PermissionError:
            return set()

    def _classify_project(self, languages, frameworks):
        """Classify overall project type."""
        if "next.js" in frameworks:
            return "Full-stack Next.js Application"
        if "react" in frameworks and any(f in frameworks for f in ["flask", "django", "express", "fastapi"]):
            return "Full-stack Web Application"
        if "react" in frameworks:
            return "React Frontend Application"
        if any(f in frameworks for f in ["flask", "django", "fastapi", "express", "nest.js"]):
            return "Backend API Service"
        if "Python" in languages and ("pytorch" in frameworks or "tensorflow" in frameworks):
            return "Machine Learning Project"
        if len(languages) == 1:
            return f"{list(languages.keys())[0]} Project"
        return "Multi-language Project"
