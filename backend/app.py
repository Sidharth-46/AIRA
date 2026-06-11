"""
AIRA — Autonomous Intelligent Reasoning Agent
Flask Application Factory

Think. Reason. Build.
"""

import os
from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_socketio import SocketIO

from config import get_config
from utils.logger import setup_logger, get_logger

# Initialize SocketIO globally
socketio = SocketIO(
    cors_allowed_origins="*", 
    async_mode="gevent",
    logger=True,
    engineio_logger=True
)

def create_app():
    """Create and configure the Flask application."""
    app = Flask(__name__)

    # Load configuration
    config = get_config()
    app.config.from_object(config)

    # Ensure data directories exist
    for folder in [
        app.config.get("UPLOAD_FOLDER", "./data/uploads"),
        app.config.get("WORKSPACE_FOLDER", "./data/workspace"),
        app.config.get("CHROMADB_PATH", "./data/embeddings"),
        os.path.dirname(app.config.get("LOG_FILE", "./logs/aira.log")),
    ]:
        os.makedirs(folder, exist_ok=True)

    # Initialize logging
    logger = setup_logger(app)
    app_logger = get_logger("app")

    # Initialize CORS
    CORS(
        app,
        resources={r"/api/*": {"origins": app.config.get("CORS_ORIGINS", ["*"])}},
        supports_credentials=True,
    )

    # Initialize SocketIO
    socketio.init_app(app)

    # Initialize JWT
    jwt = JWTManager(app)

    # Token revocation check
    @jwt.token_in_blocklist_loader
    def check_token_revoked(jwt_header, jwt_payload):
        from routes.auth import check_if_token_revoked
        return check_if_token_revoked(jwt_header, jwt_payload)

    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return jsonify({"error": "Token has expired", "code": "token_expired"}), 401

    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return jsonify({"error": "Invalid token", "code": "invalid_token"}), 401

    @jwt.unauthorized_loader
    def missing_token_callback(error):
        return jsonify({"error": "Authorization required", "code": "missing_token"}), 401

    # Initialize rate limiter
    limiter = Limiter(
        app=app,
        key_func=get_remote_address,
        default_limits=[app.config.get("RATELIMIT_DEFAULT", "100/hour")],
        storage_uri=app.config.get("RATELIMIT_STORAGE_URL", "memory://"),
    )

    # Security headers middleware
    @app.after_request
    def add_security_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "SAMEORIGIN"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        return response

    # Initialize database
    with app.app_context():
        try:
            from services.database import init_db
            init_db(app)
        except Exception as e:
            app_logger.warning(f"MongoDB connection deferred: {e}")

    # Register blueprints
    from routes.auth import auth_bp
    from routes.chat import chat_bp
    from routes.projects import projects_bp
    from routes.workspace import workspace_bp
    from routes.dashboard import dashboard_bp
    from routes.models import models_bp
    from routes.documents import documents_bp
    from routes.terminal import TerminalNamespace
    from routes.git import git_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(chat_bp)
    app.register_blueprint(projects_bp)
    app.register_blueprint(workspace_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(models_bp)
    app.register_blueprint(documents_bp)
    app.register_blueprint(git_bp)

    socketio.on_namespace(TerminalNamespace('/ws/terminal'))

    # Health check endpoint
    @app.route("/api/health", methods=["GET"])
    def health():
        """System health check."""
        health_data = {
            "status": "healthy",
            "service": "AIRA — Autonomous Intelligent Reasoning Agent",
            "version": "1.0.0",
        }

        # Check MongoDB
        try:
            from services.database import health_check as db_health
            db_ok, db_info = db_health()
            health_data["mongodb"] = {"connected": db_ok}
        except Exception:
            health_data["mongodb"] = {"connected": False}

        # Check Ollama
        try:
            from services.ollama_service import OllamaService
            ollama_status = OllamaService.get_status()
            health_data["ollama"] = ollama_status.get("ollama", {"connected": False})
        except Exception:
            health_data["ollama"] = {"connected": False}

        return jsonify(health_data), 200

    # Global error handlers
    @app.errorhandler(400)
    def bad_request(e):
        return jsonify({"error": "Bad request", "message": str(e)}), 400

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": "Not found"}), 404

    @app.errorhandler(405)
    def method_not_allowed(e):
        return jsonify({"error": "Method not allowed"}), 405

    @app.errorhandler(413)
    def payload_too_large(e):
        return jsonify({"error": "File too large"}), 413

    @app.errorhandler(429)
    def rate_limit_exceeded(e):
        return jsonify({"error": "Rate limit exceeded. Please try again later."}), 429

    @app.errorhandler(500)
    def internal_error(e):
        app_logger.error(f"Internal server error: {e}")
        return jsonify({"error": "Internal server error"}), 500

    app_logger.info("=" * 50)
    app_logger.info("  AIRA — Autonomous Intelligent Reasoning Agent")
    app_logger.info("  Think. Reason. Build.")
    app_logger.info(f"  Environment: {app.config.get('FLASK_ENV', 'development')}")
    app_logger.info("=" * 50)

    return app


if __name__ == "__main__":
    app = create_app()
    socketio.run(
        app,
        host="0.0.0.0",
        port=5000,
        debug=app.config.get("DEBUG", True),
    )
