"""
AIRA — Workspace Service
File I/O operations with security for the workspace.
"""

import os
import re

from utils.security import is_safe_path
from utils.logger import get_logger

logger = get_logger("services.workspace")


class WorkspaceService:
    """Workspace file management service."""

    def __init__(self, workspace_root):
        self.root = os.path.abspath(workspace_root)
        os.makedirs(self.root, exist_ok=True)

    def get_tree(self, project_path=""):
        """Get file tree for a project directory."""
        base = os.path.join(self.root, project_path) if project_path else self.root
        if not is_safe_path(self.root, project_path) and project_path:
            return None, "Invalid path"

        if not os.path.exists(base):
            return [], None

        return self._build_tree(base), None

    def read_file(self, file_path):
        """Read a file's content."""
        full_path = os.path.join(self.root, file_path)
        logger.info(f"WORKSPACE_FILE_READ_REQUEST: path={file_path}, absolute={full_path}")
        
        if not is_safe_path(self.root, file_path):
            logger.error(f"WORKSPACE_FILE_READ_FAILURE: Invalid path {file_path}")
            return None, "Invalid path"

        if not os.path.isfile(full_path):
            logger.error(f"WORKSPACE_FILE_READ_FAILURE: File not found {file_path}")
            return None, "File not found"

        try:
            file_size = os.path.getsize(full_path)
            with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            
            logger.info(f"WORKSPACE_FILE_READ_SUCCESS: path={file_path}, size={file_size}, content_length={len(content)}")
            return {
                "path": file_path,
                "content": content,
                "size": file_size,
                "language": self._detect_language(file_path),
            }, None
        except Exception as e:
            logger.error(f"WORKSPACE_FILE_READ_FAILURE: exception={e}")
            return None, f"Could not read file: {str(e)}"

    def write_file(self, file_path, content):
        """Write content to a file."""
        full_path = os.path.join(self.root, file_path)
        if not is_safe_path(self.root, file_path):
            return None, "Invalid path"

        try:
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(content)
            logger.info(f"File saved: {file_path}")
            return {"path": file_path, "size": len(content.encode("utf-8"))}, None
        except Exception as e:
            logger.error(f"Write error: {e}")
            return None, f"Could not write file: {str(e)}"

    def create_file(self, file_path, is_directory=False, content=""):
        """Create a file or directory."""
        full_path = os.path.join(self.root, file_path)
        if not is_safe_path(self.root, file_path):
            return None, "Invalid path"

        if os.path.exists(full_path):
            return None, "Path already exists"

        try:
            if is_directory:
                os.makedirs(full_path, exist_ok=True)
            else:
                os.makedirs(os.path.dirname(full_path), exist_ok=True)
                with open(full_path, "w", encoding="utf-8") as f:
                    f.write(content)
            return {"path": file_path, "type": "directory" if is_directory else "file"}, None
        except Exception as e:
            logger.error(f"Create error: {e}")
            return None, f"Could not create: {str(e)}"

    def delete_file(self, file_path):
        """Delete a file or directory."""
        full_path = os.path.join(self.root, file_path)
        if not is_safe_path(self.root, file_path):
            return False, "Invalid path"

        if not os.path.exists(full_path):
            return False, "Path not found"

        try:
            if os.path.isdir(full_path):
                import shutil
                shutil.rmtree(full_path)
            else:
                os.remove(full_path)
            logger.info(f"Deleted: {file_path}")
            return True, None
        except Exception as e:
            return False, f"Could not delete: {str(e)}"

    def search_files(self, query, project_path=""):
        """Search across files for content matches."""
        base = os.path.join(self.root, project_path) if project_path else self.root
        results = []
        max_results = 100

        try:
            pattern = re.compile(re.escape(query), re.IGNORECASE)
        except re.error:
            return [], None

        skip_dirs = {".git", "node_modules", "__pycache__", ".venv", "venv"}
        skip_exts = {".pyc", ".pyo", ".exe", ".dll", ".so", ".bin", ".jpg", ".png", ".gif", ".ico"}

        for dirpath, dirnames, filenames in os.walk(base):
            # Skip non-essential directories
            dirnames[:] = [d for d in dirnames if d not in skip_dirs]

            for filename in filenames:
                if len(results) >= max_results:
                    break

                ext = os.path.splitext(filename)[1].lower()
                if ext in skip_exts:
                    continue

                full = os.path.join(dirpath, filename)
                rel = os.path.relpath(full, self.root)

                # Search filename
                if pattern.search(filename):
                    results.append({
                        "path": rel.replace("\\", "/"),
                        "type": "filename",
                        "matches": [],
                    })

                # Search content
                try:
                    with open(full, "r", encoding="utf-8", errors="replace") as f:
                        for i, line in enumerate(f, 1):
                            if pattern.search(line):
                                results.append({
                                    "path": rel.replace("\\", "/"),
                                    "type": "content",
                                    "line": i,
                                    "text": line.strip()[:200],
                                })
                                if len(results) >= max_results:
                                    break
                except (OSError, UnicodeDecodeError):
                    continue

        return results, None

    def _build_tree(self, path, prefix=""):
        """Build recursive file tree."""
        tree = []
        skip = {".git", "node_modules", "__pycache__", ".venv", "venv"}

        try:
            entries = sorted(os.listdir(path), key=lambda x: (not os.path.isdir(os.path.join(path, x)), x.lower()))
        except PermissionError:
            return tree

        for entry in entries:
            if entry in skip:
                continue
            full = os.path.join(path, entry)
            rel = os.path.join(prefix, entry) if prefix else entry

            if os.path.isdir(full):
                tree.append({
                    "name": entry,
                    "path": rel.replace("\\", "/"),
                    "type": "directory",
                    "children": self._build_tree(full, rel),
                })
            else:
                tree.append({
                    "name": entry,
                    "path": rel.replace("\\", "/"),
                    "type": "file",
                    "size": os.path.getsize(full),
                    "language": self._detect_language(entry),
                })
        return tree

    @staticmethod
    def _detect_language(filename):
        """Detect programming language from file extension."""
        ext_map = {
            ".py": "python", ".js": "javascript", ".jsx": "javascript",
            ".ts": "typescript", ".tsx": "typescript", ".java": "java",
            ".c": "c", ".cpp": "cpp", ".h": "c", ".hpp": "cpp",
            ".cs": "csharp", ".go": "go", ".rs": "rust", ".rb": "ruby",
            ".php": "php", ".swift": "swift", ".kt": "kotlin",
            ".scala": "scala", ".r": "r", ".sql": "sql",
            ".html": "html", ".css": "css", ".scss": "scss",
            ".json": "json", ".xml": "xml", ".yaml": "yaml", ".yml": "yaml",
            ".md": "markdown", ".sh": "shell", ".bash": "shell",
            ".dockerfile": "dockerfile", ".toml": "toml",
        }
        ext = os.path.splitext(filename)[1].lower()
        return ext_map.get(ext, "plaintext")
