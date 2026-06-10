"""
AIRA — Project Routes
Blueprint for project upload, listing, and analysis.
"""

import os
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity

from services.project_service import ProjectService
from utils.logger import get_logger

logger = get_logger("routes.projects")

projects_bp = Blueprint("projects", __name__, url_prefix="/api/projects")


@projects_bp.route("/upload", methods=["POST"])
@jwt_required()
def upload_project():
    """Upload a ZIP project."""
    user_id = get_jwt_identity()

    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files["file"]
    upload_folder = current_app.config.get("UPLOAD_FOLDER", "./data/uploads")

    project, error = ProjectService.upload_project(user_id, file, upload_folder)
    if error:
        return jsonify({"error": error}), 400

    return jsonify({"project": project}), 201


@projects_bp.route("", methods=["GET"])
@jwt_required()
def list_projects():
    """List user's projects."""
    user_id = get_jwt_identity()
    page = request.args.get("page", 1, type=int)
    limit = request.args.get("limit", 20, type=int)

    result, error = ProjectService.get_projects(user_id, page=page, limit=limit)
    if error:
        return jsonify({"error": error}), 500

    return jsonify(result), 200


@projects_bp.route("/<project_id>", methods=["GET"])
@jwt_required()
def get_project(project_id):
    """Get a project with its analysis."""
    user_id = get_jwt_identity()
    project, error = ProjectService.get_project(project_id, user_id)
    if error:
        return jsonify({"error": error}), 404

    return jsonify({"project": project}), 200


@projects_bp.route("/<project_id>", methods=["DELETE"])
@jwt_required()
def delete_project(project_id):
    """Delete a project."""
    user_id = get_jwt_identity()
    deleted, error = ProjectService.delete_project(project_id, user_id)
    if error:
        return jsonify({"error": error}), 404

    return jsonify({"message": "Project deleted"}), 200


@projects_bp.route("/<project_id>/analyze", methods=["POST"])
@jwt_required()
def analyze_project(project_id):
    """Trigger analysis on a project."""
    user_id = get_jwt_identity()
    project, error = ProjectService.analyze_project(project_id, user_id)
    if error:
        return jsonify({"error": error}), 400

    return jsonify({"project": project}), 200
