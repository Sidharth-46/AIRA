"""
AIRA — Git Routes
Blueprint for git operations.
"""

import os
import subprocess
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity

from models.project import Project
from utils.logger import get_logger

logger = get_logger("routes.git")

git_bp = Blueprint("git", __name__, url_prefix="/api/git")

def _get_project_path(project_id, user_id):
    if project_id and user_id:
        project = Project.find_by_id(project_id, user_id=user_id)
        if project and project.get("path"):
            return project["path"]
    return current_app.config.get("WORKSPACE_FOLDER", "./data/workspace")

def _run_git(cmd, cwd):
    try:
        result = subprocess.run(
            ["git"] + cmd,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        return result.stdout.strip(), result.stderr.strip(), result.returncode
    except Exception as e:
        return "", str(e), 1

@git_bp.route("/status", methods=["GET"])
@jwt_required()
def get_status():
    project_id = request.args.get("project")
    user_id = get_jwt_identity()
    cwd = _get_project_path(project_id, user_id)

    # Check if git repo
    if not os.path.isdir(os.path.join(cwd, ".git")):
        return jsonify({"is_git": False}), 200

    out, err, code = _run_git(["status", "--porcelain"], cwd)
    if code != 0:
        return jsonify({"error": err}), 400

    files = []
    if out:
        for line in out.split("\n"):
            if len(line) >= 3:
                status_xy = line[:2]
                path = line[3:]
                files.append({"status": status_xy, "path": path})

    out_branch, _, _ = _run_git(["branch", "--show-current"], cwd)

    return jsonify({
        "is_git": True,
        "branch": out_branch,
        "files": files
    }), 200

@git_bp.route("/stage", methods=["POST"])
@jwt_required()
def stage_files():
    data = request.get_json(silent=True) or {}
    project_id = data.get("project")
    paths = data.get("paths", [])
    user_id = get_jwt_identity()
    cwd = _get_project_path(project_id, user_id)

    if not paths:
        return jsonify({"error": "No paths provided"}), 400

    out, err, code = _run_git(["add"] + paths, cwd)
    if code != 0:
        return jsonify({"error": err}), 400

    return jsonify({"message": "Staged successfully"}), 200

@git_bp.route("/unstage", methods=["POST"])
@jwt_required()
def unstage_files():
    data = request.get_json(silent=True) or {}
    project_id = data.get("project")
    paths = data.get("paths", [])
    user_id = get_jwt_identity()
    cwd = _get_project_path(project_id, user_id)

    if not paths:
        return jsonify({"error": "No paths provided"}), 400

    out, err, code = _run_git(["restore", "--staged"] + paths, cwd)
    if code != 0:
        return jsonify({"error": err}), 400

    return jsonify({"message": "Unstaged successfully"}), 200

@git_bp.route("/commit", methods=["POST"])
@jwt_required()
def commit():
    data = request.get_json(silent=True) or {}
    project_id = data.get("project")
    message = data.get("message", "")
    user_id = get_jwt_identity()
    cwd = _get_project_path(project_id, user_id)

    if not message:
        return jsonify({"error": "Message required"}), 400

    out, err, code = _run_git(["commit", "-m", message], cwd)
    if code != 0:
        return jsonify({"error": err or out}), 400

    return jsonify({"message": "Committed successfully"}), 200

@git_bp.route("/push", methods=["POST"])
@jwt_required()
def push():
    data = request.get_json(silent=True) or {}
    project_id = data.get("project")
    user_id = get_jwt_identity()
    cwd = _get_project_path(project_id, user_id)

    out, err, code = _run_git(["push"], cwd)
    if code != 0:
        return jsonify({"error": err or out}), 400

    return jsonify({"message": "Pushed successfully"}), 200

@git_bp.route("/pull", methods=["POST"])
@jwt_required()
def pull():
    data = request.get_json(silent=True) or {}
    project_id = data.get("project")
    user_id = get_jwt_identity()
    cwd = _get_project_path(project_id, user_id)

    out, err, code = _run_git(["pull"], cwd)
    if code != 0:
        return jsonify({"error": err or out}), 400

    return jsonify({"message": "Pulled successfully"}), 200
