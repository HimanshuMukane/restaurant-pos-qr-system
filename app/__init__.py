import os
from flask import Flask
from flask_login import LoginManager, current_user
from dotenv import load_dotenv, find_dotenv
from .config import DevConfig
from .filters import register_filters
from .authz import register_before_request
from .socketbus import init_socketio, socketio
load_dotenv(find_dotenv(filename=".env", usecwd=True), override=True)
import time


login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.login_message_category = "info"

def _ensure_demo_user_passwords(app):
    if not app.config.get("DEMO_MODE"):
        return
    try:
        from utils.data.core import connect_db
        with connect_db() as conn, conn.cursor() as c:
            for group in app.config.get("DEMO_USERS") or []:
                for entry in group.get("entries") or []:
                    role = (entry.get("role") or "").strip().lower()
                    password = entry.get("password") or ""
                    if not role or not password:
                        continue
                    c.execute(
                        """
                        UPDATE users
                        SET demo_password_plain = COALESCE(NULLIF(demo_password_plain, ''), %s)
                        WHERE role = %s AND is_active = 1
                        """,
                        (password, role),
                    )
            conn.commit()
    except Exception:
        app.logger.exception("Failed to ensure demo password mirrors")


def create_app(config_object=DevConfig):
    app = Flask(__name__, static_folder="../static", template_folder="../templates")
    app.config.from_object(config_object)

    app.jinja_env.globals.update(ASSET_VER=os.getenv("ASSET_VER", str(int(time.time()))))


    if not app.config.get("DATABASE_URL"):
        raise RuntimeError("DATABASE_URL is not set. Put it in your .env")

    _ensure_demo_user_passwords(app)

    login_manager.init_app(app)
    init_socketio(app)
    register_filters(app)
    register_before_request(app)

    from utils import auth

    @login_manager.user_loader
    def load_user(user_id):
        row = auth.get_user_by_id(app.config["DATABASE_URL"], user_id)
        return auth.User(row) if row else None

    from .views.dashboard import bp as dashboard_bp
    from .views.sessions import bp as sessions_bp
    from .views.orders import bp as orders_bp
    from .views.billing import bp as billing_bp
    from .views.analytics import bp as analytics_bp
    from .views.reservations import bp as reservations_bp
    from .views.menu import bp as menu_bp
    from .views.misc import bp as misc_bp
    from .views.auth import bp as auth_bp
    from .views.layouts import bp as layouts_bp
    from .views.split import bp as split_bp
    from .views.table import bp as table_bp
    from .views.print import bp as print_bp
    from .views.takeaway import bp as takeaway_bp
    from .views.admin import bp as admin_bp
    from .views.qr_public import bp as qr_public_bp
    from .views.api_reservations import bp as api_reservations_bp
    from .views.system import bp as system_bp
    from .views.printers import bp as printers_bp
    from .views.demo import bp as demo_bp

    app.register_blueprint(dashboard_bp)
    app.register_blueprint(sessions_bp)
    app.register_blueprint(orders_bp)
    app.register_blueprint(billing_bp)
    app.register_blueprint(analytics_bp)
    app.register_blueprint(reservations_bp)
    app.register_blueprint(menu_bp)
    app.register_blueprint(misc_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(layouts_bp)
    app.register_blueprint(split_bp)
    app.register_blueprint(table_bp)
    app.register_blueprint(print_bp)
    app.register_blueprint(takeaway_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(qr_public_bp)
    app.register_blueprint(api_reservations_bp)
    app.register_blueprint(system_bp)
    app.register_blueprint(printers_bp)
    app.register_blueprint(demo_bp)


    app.config["QR_TOKEN"] = os.getenv("QR_SHARED_SECRET", "")

    @app.context_processor
    def inject_flags_cp():
        try:
            if not getattr(current_user, "is_authenticated", False):
                return {"is_admin": False}

            # prefer explicit checker
            has_admin_method = False
            if hasattr(current_user, "has_role") and callable(current_user.has_role):
                try:
                    has_admin_method = bool(current_user.has_role("admin"))
                except Exception:
                    has_admin_method = False

            # normalize roles from many possible shapes
            roles_raw = (
                getattr(current_user, "role", None) or
                getattr(current_user, "roles", None)   # sometimes a list/tuple or objects
            )
            roles_norm = set()
            if isinstance(roles_raw, (list, tuple, set)):
                for r in roles_raw:
                    name = getattr(r, "name", r)
                    if name:
                        roles_norm.add(str(name).strip().lower())
            elif roles_raw is not None:
                for p in str(roles_raw).replace(",", " ").split():
                    if p.strip():
                        roles_norm.add(p.strip().lower())

            # only accept a REAL bool for flag_ok (avoid "False"/"0" becoming True)
            flag_val = getattr(current_user, "is_admin", False)
            flag_ok = (flag_val is True)

            return {"is_admin": bool(has_admin_method or ("admin" in roles_norm) or flag_ok)}
        except Exception:
            return {"is_admin": False}

    from utils.config_store import get_app_config

    @app.context_processor
    def inject_pos_config():
        try:
            return {"pos_config": get_app_config()}
        except Exception:
            return {"pos_config": {}}

    @app.context_processor
    def inject_demo_config():
        demo_users = app.config.get("DEMO_USERS") or []
        if app.config.get("DEMO_MODE"):
            try:
                demo_users = auth.build_demo_users(app.config["DATABASE_URL"], demo_users)
            except Exception:
                demo_users = app.config.get("DEMO_USERS") or []
        return {
            "demo_mode": bool(app.config.get("DEMO_MODE")),
            "demo_users": demo_users,
        }


    # ---------- legacy endpoint aliases (must run BEFORE return app) ----------
    def _alias_endpoint(app, new_endpoint: str, old_endpoint: str):
        for rule in app.url_map.iter_rules():
            if rule.endpoint == old_endpoint:
                view_func = app.view_functions[old_endpoint]
                if new_endpoint not in app.view_functions:
                    app.add_url_rule(
                        rule.rule,
                        endpoint=new_endpoint,
                        view_func=view_func,
                        methods=sorted((rule.methods or set()) - {"HEAD", "OPTIONS"})
                    )
                return

    legacy_map = {
        "dashboard": "dashboard.dashboard",
        "view_table": "sessions.view_table",
        "view_session": "sessions.view_session",
        "merge_table": "sessions.merge_table",
        "move_table": "sessions.move_table",
        "menu_admin": "menu.menu_admin",
        "cancel_table": "sessions.cancel_table",
        "add_order": "orders.add_order",
        "print_preview": "billing.print_preview",
        "close_bill": "billing.close_bill",
        "print_final_receipt": "billing.print_final_receipt",
        "api/analytics/overview": "analytics.analytics_overview",
        "analytics_overview": "analytics.analytics_overview",
        "analytics_payments_mix": "analytics.analytics_payments_mix",
        "analytics_top_items": "analytics.analytics_top_items",
        "analytics_by_hour": "analytics.analytics_by_hour",
        "analytics_ops": "analytics.analytics_ops",
        "analytics_reservations": "analytics.analytics_reservations",
        "assign_table": "reservations.assign_table",
        "add_reservation": "reservations.add_reservation",
        "api_list_preorder": "reservations.api_list_preorder",
        "api_add_preorder": "reservations.api_add_preorder",
        "api_del_preorder": "reservations.api_del_preorder",
        "api_get_menu": "menu.api_get_menu",
        "api_patch_item": "menu.api_patch_item",
        "api_patch_dish": "menu.api_patch_dish",
        "api_add_item": "menu.api_add_item",
        "serve_menu": "misc.serve_menu",
        "session_qr_page": "misc.session_qr_page",
        "session_qr_png": "misc.session_qr_png",
        "qr_generate": "misc.qr_generate",
        "kitchen_preview": "misc.kitchen_preview",
        "print_order_stub": "misc.print_order_stub",
        "login": "auth.login",
        "analytics_page": "analytics.analytics_page",
        "transactions_page": "billing.transactions_page",
        "qr_ticket": "misc.qr_ticket",
        "logout": "auth.logout",
        "kitchen_void_preview": "misc.kitchen_void_preview",
        "print_qr_direct": "misc.print_qr_direct",
    }
    for alias, target in legacy_map.items():
        _alias_endpoint(app, alias, target)
    # -------------------------------------------------------------------------

    return app
