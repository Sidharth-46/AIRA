"""
AIRA — Complexity Analyzer
LOC, file counts, cyclomatic complexity, duplication detection, hotspots.
"""

import os
import hashlib
from collections import Counter, defaultdict
from utils.logger import get_logger

logger = get_logger("analyzer.complexity")

SKIP_DIRS = {"node_modules", ".venv", "venv", ".git", "__pycache__", "dist", "build", ".next", "target"}
SKIP_EXTS = {".pyc", ".pyo", ".exe", ".dll", ".so", ".bin", ".class",
             ".jpg", ".jpeg", ".png", ".gif", ".ico", ".svg", ".bmp",
             ".woff", ".woff2", ".ttf", ".eot", ".mp4", ".mp3",
             ".zip", ".tar", ".gz", ".pdf", ".lock"}

CODE_EXTS = {".py", ".js", ".jsx", ".ts", ".tsx", ".java", ".c", ".cpp",
             ".h", ".hpp", ".cs", ".go", ".rs", ".rb", ".php", ".swift",
             ".kt", ".scala", ".vue", ".svelte", ".dart"}


class ComplexityAnalyzer:
    """Analyzes code complexity metrics."""

    def __init__(self, project_path):
        self.root = project_path

    def analyze(self):
        """Run full complexity analysis."""
        file_stats = self._collect_file_stats()
        loc_by_lang = self._loc_by_language(file_stats)
        hotspots = self._find_hotspots(file_stats)
        duplication = self._detect_duplication(file_stats)

        total_files = len(file_stats)
        total_loc = sum(f["loc"] for f in file_stats)
        total_size = sum(f["size"] for f in file_stats)
        code_files = [f for f in file_stats if f["ext"] in CODE_EXTS]
        avg_file_size = total_loc // max(len(code_files), 1)

        return {
            "total_files": total_files,
            "total_loc": total_loc,
            "total_size": total_size,
            "code_files_count": len(code_files),
            "average_file_loc": avg_file_size,
            "loc_by_language": loc_by_lang,
            "largest_files": hotspots[:15],
            "file_type_distribution": self._type_distribution(file_stats),
            "duplication": duplication,
            "complexity_rating": self._rate_complexity(total_loc, len(code_files)),
        }

    def _collect_file_stats(self):
        """Collect statistics for all files."""
        stats = []

        for dirpath, dirnames, filenames in os.walk(self.root):
            dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]

            for fname in filenames:
                ext = os.path.splitext(fname)[1].lower()
                if ext in SKIP_EXTS:
                    continue

                full_path = os.path.join(dirpath, fname)
                rel_path = os.path.relpath(full_path, self.root).replace("\\", "/")

                try:
                    size = os.path.getsize(full_path)
                    if size > 5 * 1024 * 1024:  # Skip files > 5MB
                        continue

                    loc = 0
                    blank = 0
                    comment = 0

                    with open(full_path, "r", encoding="utf-8", errors="replace") as f:
                        for line in f:
                            stripped = line.strip()
                            if not stripped:
                                blank += 1
                            elif stripped.startswith("#") or stripped.startswith("//") or stripped.startswith("*"):
                                comment += 1
                            else:
                                loc += 1

                    stats.append({
                        "path": rel_path,
                        "name": fname,
                        "ext": ext,
                        "size": size,
                        "loc": loc,
                        "blank": blank,
                        "comment": comment,
                        "total_lines": loc + blank + comment,
                    })
                except Exception:
                    continue

        return stats

    def _loc_by_language(self, file_stats):
        """Aggregate LOC by programming language."""
        from repository_analyzer.tech_detector import LANGUAGE_EXTENSIONS
        lang_loc = Counter()

        for f in file_stats:
            lang = LANGUAGE_EXTENSIONS.get(f["ext"])
            if lang and lang not in {"JSON", "YAML", "TOML", "Markdown", "XML"}:
                lang_loc[lang] += f["loc"]

        return dict(lang_loc.most_common(15))

    def _find_hotspots(self, file_stats):
        """Find largest/most complex files."""
        code_files = [f for f in file_stats if f["ext"] in CODE_EXTS]
        code_files.sort(key=lambda x: x["loc"], reverse=True)

        return [
            {"path": f["path"], "loc": f["loc"], "size": f["size"]}
            for f in code_files[:15]
        ]

    def _detect_duplication(self, file_stats):
        """Detect code duplication using hash-based approach."""
        chunk_hashes = defaultdict(list)
        code_files = [f for f in file_stats if f["ext"] in CODE_EXTS and f["loc"] > 5]

        for f in code_files[:200]:  # Limit to 200 files for performance
            full_path = os.path.join(self.root, f["path"])
            try:
                with open(full_path, "r", encoding="utf-8", errors="replace") as fh:
                    lines = [l.strip() for l in fh if l.strip()]

                # Check 5-line chunks for duplicates
                chunk_size = 5
                for i in range(len(lines) - chunk_size):
                    chunk = "\n".join(lines[i:i + chunk_size])
                    if len(chunk) > 50:  # Skip trivial chunks
                        chunk_hash = hashlib.md5(chunk.encode()).hexdigest()
                        chunk_hashes[chunk_hash].append({
                            "file": f["path"],
                            "line": i + 1,
                        })
            except Exception:
                continue

        # Find duplicated chunks
        duplicates = []
        for _, locations in chunk_hashes.items():
            if len(locations) > 1 and len(locations) <= 10:
                # Deduplicate same-file hits
                unique_files = set(loc["file"] for loc in locations)
                if len(unique_files) > 1:
                    duplicates.append({
                        "locations": locations[:5],
                        "count": len(locations),
                    })

        return {
            "duplicate_chunks": len(duplicates),
            "details": duplicates[:20],
        }

    def _type_distribution(self, file_stats):
        """Get file count by extension."""
        ext_counts = Counter(f["ext"] for f in file_stats)
        return dict(ext_counts.most_common(20))

    def _rate_complexity(self, total_loc, code_files):
        """Rate overall project complexity."""
        if total_loc < 1000:
            return {"level": "small", "label": "Small Project", "description": "Under 1K LOC — straightforward codebase."}
        elif total_loc < 10000:
            return {"level": "medium", "label": "Medium Project", "description": "1K-10K LOC — moderate complexity."}
        elif total_loc < 100000:
            return {"level": "large", "label": "Large Project", "description": "10K-100K LOC — significant codebase."}
        else:
            return {"level": "enterprise", "label": "Enterprise Project", "description": "100K+ LOC — enterprise-scale complexity."}
