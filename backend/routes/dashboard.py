"""
AIRA — Dashboard Routes
Blueprint for user statistics and activity.
"""

from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from services.dashboard_service import DashboardService
from utils.logger import get_logger

logger = get_logger("routes.dashboard")

dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/api/dashboard")


@dashboard_bp.route("/stats", methods=["GET"])
@jwt_required()
def get_stats():
    """Get user dashboard statistics."""
    user_id = get_jwt_identity()
    stats = DashboardService.get_stats(user_id)
    return jsonify({"stats": stats}), 200


@dashboard_bp.route("/activity", methods=["GET"])
@jwt_required()
def get_activity():
    """Get recent user activity."""
    user_id = get_jwt_identity()
    activity = DashboardService.get_activity(user_id)
    return jsonify({"activity": activity}), 200


@dashboard_bp.route("/usage", methods=["GET"])
@jwt_required()
def get_usage():
    """Get usage chart data."""
    user_id = get_jwt_identity()
    chart = DashboardService.get_usage_chart(user_id)
    return jsonify({"usage": chart}), 200
