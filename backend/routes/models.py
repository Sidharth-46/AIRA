"""
AIRA — Model Management Routes
Blueprint for Ollama model listing, switching, and health.
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from utils.validators import validate_request, ModelSwitchSchema
from utils.logger import get_logger

logger = get_logger("routes.models")

models_bp = Blueprint("models", __name__, url_prefix="/api/models")


@models_bp.route("", methods=["GET"])
@jwt_required()
def list_models():
    """List available Ollama models."""
    try:
        from services.ollama_service import OllamaService
        models = OllamaService.list_models()
        return jsonify({"models": models}), 200
    except Exception as e:
        logger.error(f"Error listing models: {e}")
        return jsonify({"models": [], "error": "Could not connect to Ollama"}), 200


@models_bp.route("/active", methods=["GET"])
@jwt_required()
def get_active_model():
    """Get the currently active model."""
    try:
        from services.ollama_service import OllamaService
        model = OllamaService.get_active_model()
        return jsonify({"model": model}), 200
    except Exception as e:
        return jsonify({"model": None, "error": str(e)}), 200


@models_bp.route("/active", methods=["PUT"])
@jwt_required()
def switch_model():
    """Switch the active model."""
    data, errors = validate_request(ModelSwitchSchema, request.get_json(silent=True) or {})
    if errors:
        return jsonify({"error": "Validation failed", "details": errors}), 400

    try:
        from services.ollama_service import OllamaService
        result = OllamaService.switch_model(data["model"])
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@models_bp.route("/status", methods=["GET"])
@jwt_required()
def get_status():
    """Get Ollama server status and hardware info."""
    try:
        from services.ollama_service import OllamaService
        status = OllamaService.get_status()
        return jsonify(status), 200
    except Exception as e:
        return jsonify({
            "ollama": {"connected": False, "error": str(e)},
            "hardware": {},
        }), 200

@models_bp.route("/diagnostics", methods=["GET"])
@jwt_required()
def get_diagnostics():
    """Get dynamic model resolution diagnostics."""
    try:
        from services.ollama_service import OllamaService
        diagnostics = OllamaService.get_diagnostics()
        return jsonify(diagnostics), 200
    except Exception as e:
        logger.error(f"Diagnostics error: {e}")
        return jsonify({
            "ollama_running": False,
            "status": "error",
            "error": str(e)
        }), 500

@models_bp.route("/router-status", methods=["GET"])
@jwt_required()
def get_router_status():
    """Get dynamic model router diagnostics and cache status."""
    try:
        from services.model_router import get_model_router
        router = get_model_router()
        status = router.get_diagnostics()
        return jsonify(status), 200
    except Exception as e:
        logger.error(f"Router diagnostics error: {e}")
        return jsonify({"router_status": "error", "error": str(e)}), 500
