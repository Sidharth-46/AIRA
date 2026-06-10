"""
AIRA — Authentication Routes
Blueprint for signup, login, refresh, profile.
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    jwt_required,
    get_jwt_identity,
    get_jwt,
)

from services.auth_service import AuthService
from utils.validators import validate_request, SignupSchema, LoginSchema
from utils.logger import get_logger

logger = get_logger("routes.auth")

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")

# Store for revoked tokens (in production, use Redis)
_revoked_tokens = set()


@auth_bp.route("/signup", methods=["POST"])
def signup():
    """Register a new user."""
    data, errors = validate_request(SignupSchema, request.get_json(silent=True) or {})
    if errors:
        return jsonify({"error": "Validation failed", "details": errors}), 400

    user, error = AuthService.signup(data)
    if error:
        return jsonify({"error": error}), 409

    # Generate tokens
    access_token = create_access_token(identity=user["id"])
    refresh_token = create_refresh_token(identity=user["id"])

    return jsonify({
        "message": "Account created successfully",
        "user": user,
        "access_token": access_token,
        "refresh_token": refresh_token,
    }), 201


@auth_bp.route("/login", methods=["POST"])
def login():
    """Authenticate a user."""
    data, errors = validate_request(LoginSchema, request.get_json(silent=True) or {})
    if errors:
        return jsonify({"error": "Validation failed", "details": errors}), 400

    user, error = AuthService.login(data)
    if error:
        return jsonify({"error": error}), 401

    access_token = create_access_token(identity=user["id"])
    refresh_token = create_refresh_token(identity=user["id"])

    return jsonify({
        "message": "Login successful",
        "user": user,
        "access_token": access_token,
        "refresh_token": refresh_token,
    }), 200


@auth_bp.route("/refresh", methods=["POST"])
@jwt_required(refresh=True)
def refresh():
    """Refresh the access token."""
    identity = get_jwt_identity()
    access_token = create_access_token(identity=identity)

    return jsonify({
        "access_token": access_token,
    }), 200


@auth_bp.route("/me", methods=["GET"])
@jwt_required()
def get_profile():
    """Get current user profile."""
    user_id = get_jwt_identity()
    user, error = AuthService.get_profile(user_id)
    if error:
        return jsonify({"error": error}), 404

    return jsonify({"user": user}), 200


@auth_bp.route("/logout", methods=["POST"])
@jwt_required()
def logout():
    """Logout — revoke current token."""
    jti = get_jwt()["jti"]
    _revoked_tokens.add(jti)
    return jsonify({"message": "Logged out successfully"}), 200


def check_if_token_revoked(jwt_header, jwt_payload):
    """Callback to check if a JWT has been revoked."""
    jti = jwt_payload["jti"]
    return jti in _revoked_tokens
