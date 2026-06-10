"""
AIRA — Workspace Context Builder
Builds repository-aware context strings for the agent orchestrator.
Enforces limits, discovers relevant files, and caches summaries.
"""

import os
import re
import time
import hashlib
from utils.logger import get_logger
from models.project import Project
from services.workspace_service import WorkspaceService
from flask import current_app

logger = get_logger("services.workspace_context")

MAX_FILES = 10
MAX_CHARS = 20000
MAX_READ_SIZE = 1024 * 1024  # 1MB
CACHE_TTL = 900  # 15 minutes

IGNORE_DIRS = {".git", "node_modules", "dist", "build", "venv", ".venv", "__pycache__"}
METADATA_FILES = {"package.json", "requirements.txt", "docker-compose.yml", "readme.md", "pyproject.toml", "cargo.toml"}


class WorkspaceContextBuilder:
    """Intelligent context builder for workspaces."""

    _cache = {}  # { project_id: { "summary": ..., "architecture": ..., "hash": ..., "lastIndexed": ... } }

    @classmethod
    def extract_keywords(cls, prompt: str) -> list:
        """Extract important keywords from prompt for smart file discovery."""
        # Simple extraction: words >= 3 chars, ignoring common stop words
        stop_words = {"this", "that", "there", "what", "where", "when", "why", "how", "the", "and", "for", "with", "bug", "fix", "error"}
        words = re.findall(r'\b[a-zA-Z]{3,}\b', prompt.lower())
        return list(set(w for w in words if w not in stop_words))

    @classmethod
    def generate_fingerprint(cls, workspace_service: WorkspaceService, project_path: str) -> str:
        """Generate a fast hash of the project state to detect changes."""
        base = os.path.join(workspace_service.root, project_path) if project_path else workspace_service.root
        
        file_count = 0
        names = []
        mod_times = []
        
        if not os.path.exists(base):
            return ""

        for dirpath, dirnames, filenames in os.walk(base):
            dirnames[:] = [d for d in dirnames if d not in IGNORE_DIRS]
            for f in filenames:
                full_path = os.path.join(dirpath, f)
                try:
                    mtime = os.path.getmtime(full_path)
                    file_count += 1
                    names.append(f)
                    mod_times.append(str(mtime))
                except OSError:
                    continue

        raw = f"{file_count}_{''.join(sorted(names))}_{''.join(mod_times)}"
        return hashlib.md5(raw.encode('utf-8')).hexdigest()

    @classmethod
    def get_context(cls, project_id: str, current_file: str, prompt: str) -> str:
        """
        Build or retrieve the workspace context.
        Returns a formatted string for injection.
        """
        if not project_id:
            return ""

        project = Project.find_by_id(project_id)
        if not project:
            return ""

        workspace_root = current_app.config.get("WORKSPACE_ROOT", "/app/workspace")
        workspace_service = WorkspaceService(workspace_root)
        project_path = project.get("path", "")
        
        logger.info("WORKSPACE_RELEVANCE_SCAN started")

        fingerprint = cls.generate_fingerprint(workspace_service, project_path)
        now = time.time()
        
        cached = cls._cache.get(project_id)
        if cached:
            if cached["hash"] != fingerprint:
                logger.info(f"WORKSPACE_CONTEXT_INVALIDATED: Project {project_id} changed.")
            elif (now - cached["lastIndexed"]) > CACHE_TTL:
                logger.info(f"WORKSPACE_CONTEXT_INVALIDATED: Project {project_id} cache expired.")
            else:
                logger.info("WORKSPACE_CONTEXT_CACHE_HIT")
                return cls._format_context(project, current_file, cached["files"], cached["summary"])
                
        logger.info("WORKSPACE_CONTEXT_CACHE_MISS")
        logger.info("WORKSPACE_CONTEXT_BUILD started")

        # 1. Gather all files
        base = os.path.join(workspace_service.root, project_path) if project_path else workspace_service.root
        all_files = []
        if os.path.exists(base):
            for dirpath, dirnames, filenames in os.walk(base):
                dirnames[:] = [d for d in dirnames if d not in IGNORE_DIRS]
                for f in filenames:
                    rel_path = os.path.relpath(os.path.join(dirpath, f), base).replace("\\", "/")
                    all_files.append(rel_path)

        # 2. Extract keywords and find related files
        keywords = cls.extract_keywords(prompt)
        related_files = []
        for kw in keywords:
            for f in all_files:
                if kw in f.lower() and f not in related_files:
                    related_files.append(f)
        
        if related_files:
            logger.info(f"WORKSPACE_RELATED_FILES_FOUND: {related_files}")

        # 3. Prioritize files
        selected_paths = []
        
        def add_file(f):
            if f and f in all_files and f not in selected_paths and len(selected_paths) < MAX_FILES:
                selected_paths.append(f)

        # Priority 1: Active File
        add_file(current_file)
        
        # Priority 2/3: Discovered / Related
        for rf in related_files:
            add_file(rf)
            
        # Priority 4: Metadata
        for meta in METADATA_FILES:
            for f in all_files:
                if f.lower().endswith(meta):
                    add_file(f)

        logger.info(f"WORKSPACE_CONTEXT_SELECTED_FILES: {selected_paths}")

        # 4. Read files securely adhering to limits
        file_contents = {}
        total_chars = 0
        total_bytes = 0
        
        for path in selected_paths:
            full_path = os.path.join(base, path)
            try:
                size = os.path.getsize(full_path)
                if total_bytes + size > MAX_READ_SIZE:
                    continue
                    
                with open(full_path, "r", encoding="utf-8", errors="ignore") as file_obj:
                    content = file_obj.read()
                    
                if total_chars + len(content) > MAX_CHARS:
                    # Truncate content
                    allowed = MAX_CHARS - total_chars
                    content = content[:allowed] + "\n\n...[TRUNCATED DUE TO SIZE LIMIT]..."
                    
                file_contents[path] = content
                total_chars += len(content)
                total_bytes += size
                
                if total_chars >= MAX_CHARS:
                    break
            except Exception as e:
                logger.warning(f"Failed to read {path}: {e}")

        # 5. Build Summary
        summary = f"Project contains {len(all_files)} files.\n"
        if project.get("analysis"):
            summary += f"Architecture: {project['analysis'].get('architecture', 'Unknown')}\n"
        
        # Save to Cache
        cls._cache[project_id] = {
            "summary": summary,
            "files": file_contents,
            "hash": fingerprint,
            "lastIndexed": now
        }
        
        logger.info("WORKSPACE_CONTEXT_REBUILT")

        return cls._format_context(project, current_file, file_contents, summary)

    @classmethod
    def _format_context(cls, project, current_file, file_contents, summary) -> str:
        """Format the block for injection."""
        lines = []
        lines.append(f"ACTIVE PROJECT: {project.get('name', 'Unknown')}")
        if current_file:
            lines.append(f"ACTIVE FILE: {current_file}")
            
        related = [f for f in file_contents.keys() if f != current_file]
        if related:
            lines.append("RELATED FILES:")
            for rf in related:
                lines.append(f"- {rf}")
                
        lines.append("\nPROJECT SUMMARY:")
        lines.append(summary)
        
        lines.append("\n--- FILE CONTENTS ---")
        for path, content in file_contents.items():
            lines.append(f"\n// File: {path}")
            lines.append(content)
            
        return "\n".join(lines)
