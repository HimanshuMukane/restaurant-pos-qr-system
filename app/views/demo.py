"""
Demo management endpoints — only active when DEMO_MODE=1.
POST /demo/reset   — wipes transactional data and re-seeds demo state.
                     Protected by DEMO_RESET_SECRET env var.
"""
import os
from functools import wraps
from flask import Blueprint, request, jsonify, current_app

bp = Blueprint("demo", __name__)


def _require_secret(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        secret = os.environ.get("DEMO_RESET_SECRET", "").strip()
        if not secret:
            return jsonify({"error": "DEMO_RESET_SECRET is not configured on this server"}), 500
        provided = (
            request.headers.get("Authorization", "").removeprefix("Bearer ").strip()
            or request.args.get("secret", "").strip()
        )
        if provided != secret:
            return jsonify({"error": "unauthorized"}), 401
        return f(*args, **kwargs)
    return decorated


@bp.post("/demo/reset")
@_require_secret
def demo_reset():
    if not current_app.config.get("DEMO_MODE"):
        return jsonify({"error": "not in demo mode"}), 403
    try:
        from utils.demo_seed import run_nightly_reset
        run_nightly_reset()
        return jsonify({"status": "ok", "message": "Demo reset successfully."})
    except Exception as exc:
        current_app.logger.exception("Demo reset failed")
        return jsonify({"error": str(exc)}), 500


@bp.post("/demo/full-reset")
@_require_secret
def demo_full_reset():
    """Full wipe + reseed — use this when you want a completely fresh state."""
    if not current_app.config.get("DEMO_MODE"):
        return jsonify({"error": "not in demo mode"}), 403
    try:
        from utils.demo_seed import run_seed
        run_seed()
        return jsonify({"status": "ok", "message": "Full demo reseed complete."})
    except Exception as exc:
        current_app.logger.exception("Demo full-reset failed")
        return jsonify({"error": str(exc)}), 500
