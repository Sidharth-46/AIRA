"""
AIRA — Workspace Routes
Blueprint for workspace file management.
"""

from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity

from services.workspace_service import WorkspaceService
from utils.validators import validate_request, FileCreateSchema
from utils.logger import get_logger
import json
from flask import Response, stream_with_context
from services.workspace_chat_service import WorkspaceChatService

logger = get_logger("routes.workspace")

workspace_bp = Blueprint("workspace", __name__, url_prefix="/api/workspace")


from models.project import Project

def _get_ws(project_id=None, user_id=None):
    """Get workspace service instance."""
    if project_id and user_id:
        project = Project.find_by_id(project_id, user_id=user_id)
        if project and project.get("path"):
            return WorkspaceService(project["path"])
            
    root = current_app.config.get("WORKSPACE_FOLDER", "./data/workspace")
    return WorkspaceService(root)


@workspace_bp.route("/tree", methods=["GET"])
@jwt_required()
def get_tree():
    """Get file tree for a project."""
    project_id = request.args.get("project", "")
    user_id = get_jwt_identity()
    
    project_name = None
    if project_id:
        project = Project.find_by_id(project_id, user_id=user_id)
        if project:
            project_name = project.get("name")

    ws = _get_ws(project_id, user_id)
    tree, error = ws.get_tree()
    if error:
        return jsonify({"error": error}), 400
    return jsonify({"tree": tree, "projectName": project_name}), 200


@workspace_bp.route("/file", methods=["GET"])
@jwt_required()
def read_file():
    """Read a file's content."""
    file_path = request.args.get("path")
    project_id = request.args.get("project")
    user_id = get_jwt_identity()
    
    if not file_path:
        return jsonify({"error": "Path parameter required"}), 400

    ws = _get_ws(project_id, user_id)
    result, error = ws.read_file(file_path)
    if error:
        return jsonify({"error": error}), 404

    return jsonify({"file": result}), 200


@workspace_bp.route("/file", methods=["PUT"])
@jwt_required()
def save_file():
    """Save file content."""
    data = request.get_json(silent=True) or {}
    file_path = data.get("path")
    content = data.get("content", "")
    project_id = data.get("project")
    user_id = get_jwt_identity()

    if not file_path:
        return jsonify({"error": "Path required"}), 400

    ws = _get_ws(project_id, user_id)
    result, error = ws.write_file(file_path, content)
    if error:
        return jsonify({"error": error}), 400

    return jsonify({"file": result}), 200


@workspace_bp.route("/file", methods=["POST"])
@jwt_required()
def create_file():
    """Create a new file or folder."""
    data, errors = validate_request(FileCreateSchema, request.get_json(silent=True) or {})
    if errors:
        return jsonify({"error": "Validation failed", "details": errors}), 400

    # We need project ID from body, assuming it might be in data dict if Schema allowed it. 
    # Let's extract it from raw JSON just in case Schema strips it.
    raw_data = request.get_json(silent=True) or {}
    project_id = raw_data.get("project")
    user_id = get_jwt_identity()

    ws = _get_ws(project_id, user_id)
    result, error = ws.create_file(
        data["path"], is_directory=data.get("is_directory", False), content=data.get("content", "")
    )
    if error:
        return jsonify({"error": error}), 400

    return jsonify({"file": result}), 201


@workspace_bp.route("/file", methods=["DELETE"])
@jwt_required()
def delete_file():
    """Delete a file or folder."""
    file_path = request.args.get("path")
    project_id = request.args.get("project")
    user_id = get_jwt_identity()
    
    if not file_path:
        return jsonify({"error": "Path parameter required"}), 400

    ws = _get_ws(project_id, user_id)
    deleted, error = ws.delete_file(file_path)
    if error:
        return jsonify({"error": error}), 404

    return jsonify({"message": "Deleted"}), 200


@workspace_bp.route("/search", methods=["GET"])
@jwt_required()
def search_files():
    """Search across files."""
    query = request.args.get("q")
    project_id = request.args.get("project", "")
    user_id = get_jwt_identity()

    if not query:
        return jsonify({"error": "Query parameter 'q' required"}), 400

    ws = _get_ws(project_id, user_id)
    # Since ws root is already the project, project_path=""
    results, error = ws.search_files(query, "")
    if error:
        return jsonify({"error": error}), 500

    return jsonify({"results": results, "count": len(results)}), 200


@workspace_bp.route("/chat/<project_id>", methods=["GET"])
@jwt_required()
def get_workspace_chat(project_id):
    """Get the workspace chat history for a project."""
    user_id = get_jwt_identity()
    chat, error = WorkspaceChatService.get_chat(project_id, user_id)
    if error:
        return jsonify({"error": error}), 404
    return jsonify({"chat": chat}), 200


@workspace_bp.route("/chat/<project_id>", methods=["DELETE"])
@jwt_required()
def clear_workspace_chat(project_id):
    """Clear the workspace chat history for a project."""
    user_id = get_jwt_identity()
    chat, error = WorkspaceChatService.clear_chat(project_id, user_id)
    if error:
        return jsonify({"error": error}), 404
    return jsonify({"message": "Workspace chat cleared", "chat": chat}), 200


@workspace_bp.route("/chat/<project_id>", methods=["POST"])
@jwt_required()
def send_workspace_message(project_id):
    """Send a message to the workspace chat and stream response via SSE."""
    user_id = get_jwt_identity()
    data = request.get_json(silent=True) or {}
    content = data.get("message")
    current_file = data.get("currentFile")
    
    if not content:
        return jsonify({"error": "Message content required"}), 400

    generator, error = WorkspaceChatService.send_message(
        project_id=project_id, 
        user_id=user_id, 
        content=content, 
        current_file=current_file
    )
    
    if error:
        return jsonify({"error": error}), 500

    def sse_stream():
        try:
            for event in generator:
                event_type = event.get("event", "message")
                event_data = event.get("data", "")
                yield f"event: {event_type}\ndata: {json.dumps(event_data)}\n\n"
        except GeneratorExit:
            logger.info(f"SSE stream closed by client for workspace chat {project_id}")
        except Exception as exc:
            logger.error(f"SSE stream error: {exc}")
            yield f"event: error\ndata: {json.dumps(str(exc))}\n\n"

    return Response(
        stream_with_context(sse_stream()),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )
