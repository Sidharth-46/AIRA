"""
AIRA — Chat Routes
Blueprint for chat CRUD and SSE message streaming.
"""

import json
from flask import Blueprint, request, jsonify, Response, stream_with_context
from flask_jwt_extended import jwt_required, get_jwt_identity

from services.chat_service import ChatService
from utils.validators import (
    validate_request,
    ChatCreateSchema,
    MessageSchema,
    ChatUpdateSchema,
)
from utils.logger import get_logger

logger = get_logger("routes.chat")

chat_bp = Blueprint("chat", __name__, url_prefix="/api/chats")


@chat_bp.route("", methods=["GET"])
@jwt_required()
def list_chats():
    """List user's chats with optional search and folder filter."""
    user_id = get_jwt_identity()
    search = request.args.get("search")
    folder = request.args.get("folder")
    page = request.args.get("page", 1, type=int)
    limit = request.args.get("limit", 50, type=int)

    result, error = ChatService.get_chats(
        user_id, search=search, folder=folder, page=page, limit=limit
    )
    if error:
        return jsonify({"error": error}), 500

    return jsonify(result), 200


@chat_bp.route("", methods=["POST"])
@jwt_required()
def create_chat():
    """Create a new chat."""
    user_id = get_jwt_identity()
    data, errors = validate_request(ChatCreateSchema, request.get_json(silent=True) or {})
    if errors:
        return jsonify({"error": "Validation failed", "details": errors}), 400

    chat, error = ChatService.create_chat(
        user_id, title=data.get("title", "New Chat"), folder=data.get("folder")
    )
    if error:
        return jsonify({"error": error}), 500

    return jsonify({"chat": chat}), 201


@chat_bp.route("/<chat_id>", methods=["GET"])
@jwt_required()
def get_chat(chat_id):
    """Get a chat with its messages."""
    user_id = get_jwt_identity()
    chat, error = ChatService.get_chat(chat_id, user_id)
    if error:
        return jsonify({"error": error}), 404

    return jsonify({"chat": chat}), 200


@chat_bp.route("/<chat_id>", methods=["PUT"])
@jwt_required()
def update_chat(chat_id):
    """Update a chat (title, folder, pinned)."""
    user_id = get_jwt_identity()
    data, errors = validate_request(ChatUpdateSchema, request.get_json(silent=True) or {})
    if errors:
        return jsonify({"error": "Validation failed", "details": errors}), 400

    chat, error = ChatService.update_chat(chat_id, user_id, data)
    if error:
        return jsonify({"error": error}), 404

    return jsonify({"chat": chat}), 200


@chat_bp.route("/<chat_id>", methods=["DELETE"])
@jwt_required()
def delete_chat(chat_id):
    """Delete a chat and all its messages."""
    user_id = get_jwt_identity()
    deleted, error = ChatService.delete_chat(chat_id, user_id)
    if error:
        return jsonify({"error": error}), 404

    return jsonify({"message": "Chat deleted"}), 200


@chat_bp.route("/<chat_id>/messages", methods=["POST"])
@jwt_required()
def send_message(chat_id):
    """Send a message and stream the AI response via SSE."""
    user_id = get_jwt_identity()
    data, errors = validate_request(MessageSchema, request.get_json(silent=True) or {})
    if errors:
        return jsonify({"error": "Validation failed", "details": errors}), 400

    generator, error = ChatService.send_message(chat_id, user_id, data["content"], data.get("workspace_context"))
    if error:
        return jsonify({"error": error}), 404

    def sse_stream():
        """Convert generator events to SSE format."""
        try:
            for event in generator:
                event_type = event.get("event", "message")
                event_data = event.get("data", "")
                yield f"event: {event_type}\ndata: {json.dumps(event_data)}\n\n"
        except GeneratorExit:
            logger.info(f"SSE stream closed by client for chat {chat_id}")
        except Exception as exc:
            error_msg = str(exc)
            logger.error(f"SSE stream error: {error_msg}")
            yield f"event: error\ndata: {json.dumps(error_msg)}\n\n"

    return Response(
        stream_with_context(sse_stream()),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # Nginx: disable buffering
            "Connection": "keep-alive",
        },
    )


@chat_bp.route("/folders", methods=["GET"])
@jwt_required()
def get_folders():
    """Get user's chat folders."""
    user_id = get_jwt_identity()
    folders = ChatService.get_folders(user_id)
    return jsonify({"folders": folders}), 200
