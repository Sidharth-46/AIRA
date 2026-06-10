import os
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required

from services.document_service import DocumentService
from utils.logger import get_logger

logger = get_logger("routes.documents")
documents_bp = Blueprint("documents", __name__, url_prefix="/api/documents")

@documents_bp.route("/index/project/<project_id>", methods=["POST"])
@jwt_required()
def index_project(project_id):
    """
    Index an entire project repository.
    """
    workspace_dir = current_app.config.get("WORKSPACE_FOLDER")
    project_dir = os.path.join(workspace_dir, project_id)
    
    if not os.path.exists(project_dir):
        return jsonify({"error": "Project directory not found"}), 404
        
    chunks = DocumentService.index_project(project_id, project_dir)
    return jsonify({"message": f"Successfully indexed {chunks} chunks", "chunks": chunks}), 200

@documents_bp.route("/search/<project_id>", methods=["POST"])
@jwt_required()
def search_documents(project_id):
    """
    Semantic search over indexed project documents.
    """
    data = request.json
    if not data or not data.get("query"):
        return jsonify({"error": "Query is required"}), 400
        
    query = data.get("query")
    top_k = data.get("top_k", 5)
    
    results = DocumentService.search_documents(project_id, query, top_k)
    return jsonify({"results": results}), 200

@documents_bp.route("/upload/<project_id>", methods=["POST"])
@jwt_required()
def upload_document(project_id):
    """
    Upload and index a single document.
    """
    if "file" not in request.files:
        return jsonify({"error": "No file part"}), 400
        
    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400
        
    uploads_dir = current_app.config.get("UPLOAD_FOLDER")
    os.makedirs(uploads_dir, exist_ok=True)
    
    file_path = os.path.join(uploads_dir, file.filename)
    file.save(file_path)
    
    chunks = DocumentService.index_document(project_id, file_path, file.filename)
    
    # Optionally clean up the file after indexing if we don't need the raw file
    # os.remove(file_path)
    
    return jsonify({
        "message": "File indexed successfully",
        "filename": file.filename,
        "chunks": chunks
    }), 200
