"""
AIRA — Project Service
Handles project upload, extraction, and analysis orchestration.
"""

import os
import shutil
import zipfile

from models.project import Project
from utils.security import validate_zip_contents, is_safe_path
from utils.logger import get_logger

logger = get_logger("services.project")


class ProjectService:
    """Project service layer."""

    @staticmethod
    def upload_project(user_id, file, upload_folder):
        """Upload and extract a ZIP project."""
        if not file or not file.filename:
            return None, "No file provided"

        if not file.filename.endswith(".zip"):
            return None, "Only ZIP files are accepted"

        # Create project directory
        project_name = os.path.splitext(file.filename)[0]
        project_dir = os.path.join(upload_folder, str(user_id), project_name)
        os.makedirs(project_dir, exist_ok=True)

        # Save ZIP temporarily
        zip_path = os.path.join(upload_folder, str(user_id), file.filename)
        os.makedirs(os.path.dirname(zip_path), exist_ok=True)
        file.save(zip_path)

        try:
            # Validate and extract
            with zipfile.ZipFile(zip_path, "r") as zip_ref:
                is_safe, message = validate_zip_contents(zip_ref)
                if not is_safe:
                    os.remove(zip_path)
                    return None, f"Unsafe ZIP: {message}"

                zip_ref.extractall(project_dir)

            # Clean up ZIP
            os.remove(zip_path)

            # Build file tree
            structure = ProjectService._build_tree(project_dir)
            files_count = ProjectService._count_files(project_dir)
            total_size = ProjectService._get_size(project_dir)

            # Save to database
            project = Project.create(
                user_id=user_id,
                name=project_name,
                project_type="uploaded",
                path=project_dir,
                structure=structure,
            )

            Project.update_analysis(
                project["id"],
                analysis=None,
                files_count=files_count,
                total_size=total_size,
            )

            project["files_count"] = files_count
            project["total_size"] = total_size

            logger.info(f"Project uploaded: {project_name} ({files_count} files)")
            return project, None

        except zipfile.BadZipFile:
            if os.path.exists(zip_path):
                os.remove(zip_path)
            return None, "Invalid ZIP file"
        except Exception as e:
            logger.error(f"Upload error: {e}")
            if os.path.exists(zip_path):
                os.remove(zip_path)
            return None, f"Upload failed: {str(e)}"

    @staticmethod
    def get_projects(user_id, page=1, limit=20):
        """Get user's projects."""
        projects, total = Project.find_by_user(user_id, page=page, limit=limit)
        return {
            "projects": projects,
            "total": total,
            "page": page,
            "limit": limit,
        }, None

    @staticmethod
    def get_project(project_id, user_id):
        """Get a project by ID."""
        project = Project.find_by_id(project_id, user_id=user_id)
        if not project:
            return None, "Project not found"
        return project, None

    @staticmethod
    def delete_project(project_id, user_id):
        """Delete a project and its files."""
        project = Project.find_by_id(project_id, user_id=user_id)
        if not project:
            return False, "Project not found"

        # Delete files
        if project.get("path") and os.path.exists(project["path"]):
            shutil.rmtree(project["path"], ignore_errors=True)

        from models.workspace_chat import WorkspaceChat
        WorkspaceChat.delete_by_project(project_id, user_id)

        Project.delete(project_id, user_id)
        logger.info(f"Project deleted: {project_id}")
        return True, None

    @staticmethod
    def analyze_project(project_id, user_id):
        """Trigger analysis on a project."""
        project = Project.find_by_id(project_id, user_id=user_id)
        if not project:
            return None, "Project not found"

        if not project.get("path") or not os.path.exists(project["path"]):
            return None, "Project files not found"

        Project.update_status(project_id, "processing")

        try:
            from services.repository_service import RepositoryService
            analysis = RepositoryService.analyze(project["path"])

            Project.update_analysis(
                project_id,
                analysis=analysis,
                languages=analysis.get("languages", []),
                files_count=analysis.get("files_count", 0),
                total_size=analysis.get("total_size", 0),
            )

            project["analysis"] = analysis
            return project, None
        except ImportError:
            # Repository analyzer not yet available
            basic_analysis = {
                "structure": ProjectService._build_tree(project["path"]),
                "files_count": ProjectService._count_files(project["path"]),
                "total_size": ProjectService._get_size(project["path"]),
                "status": "basic_analysis",
            }
            Project.update_analysis(project_id, analysis=basic_analysis)
            project["analysis"] = basic_analysis
            return project, None

    @staticmethod
    def _build_tree(path, prefix=""):
        """Build a file tree structure recursively."""
        tree = []
        try:
            entries = sorted(os.listdir(path))
        except PermissionError:
            return tree

        # Filter out hidden files and common non-essential dirs
        skip = {".git", "node_modules", "__pycache__", ".venv", "venv", ".idea", ".vscode"}

        for entry in entries:
            if entry in skip:
                continue

            full_path = os.path.join(path, entry)
            rel_path = os.path.join(prefix, entry) if prefix else entry

            if os.path.isdir(full_path):
                tree.append({
                    "name": entry,
                    "path": rel_path,
                    "type": "directory",
                    "children": ProjectService._build_tree(full_path, rel_path),
                })
            else:
                try:
                    size = os.path.getsize(full_path)
                except OSError:
                    size = 0
                tree.append({
                    "name": entry,
                    "path": rel_path,
                    "type": "file",
                    "size": size,
                })

        return tree

    @staticmethod
    def _count_files(path):
        """Count total files in directory."""
        count = 0
        for _, _, files in os.walk(path):
            count += len(files)
        return count

    @staticmethod
    def _get_size(path):
        """Get total directory size in bytes."""
        total = 0
        for dirpath, _, filenames in os.walk(path):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                try:
                    total += os.path.getsize(fp)
                except OSError:
                    pass
        return total
