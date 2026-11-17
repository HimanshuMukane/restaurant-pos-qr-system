from functools import wraps
from flask import abort, request, session, g
from flask_login import current_user
from utils.tenancy import set_current_tenant_id, get_current_tenant_id

def roles_required(*allowed_roles):
    def deco(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            if not current_user.is_authenticated:
                from flask_login import login_manager
                return login_manager.unauthorized()
            if current_user.role not in allowed_roles:
                abort(403)
            return fn(*args, **kwargs)
        return wrapper
    return deco

def register_before_request(app):
    @app.before_request
    def _setup_request_tenancy_and_session():
        session.permanent = False

        # Determine tenant_id
        tid = None
        # 1. From URL param: ?tenant= or ?tenant_id=
        tid = request.args.get("tenant") or request.args.get("tenant_id")

        # 2. From HTTP header
        if not tid:
            tid = request.headers.get("X-Tenant-ID")

        # 3. From authenticated user
        if not tid and current_user.is_authenticated and hasattr(current_user, "tenant_id"):
            tid = current_user.tenant_id

        # 4. From session
        if not tid and "tenant_id" in session:
            tid = session["tenant_id"]

        # 5. Fallback
        if not tid:
            tid = "default"

        tid = str(tid).strip()
        g.tenant_id = tid
        session["tenant_id"] = tid
        set_current_tenant_id(tid)

    @app.context_processor
    def inject_tenancy_context():
        tid = get_current_tenant_id()
        # Retrieve tenant metadata
        from utils.data.core import connect_db
        brand_name = "Restaurant POS & QR"
        currency_symbol = "$"
        try:
            with connect_db() as conn, conn.cursor() as cur:
                cur.execute("SELECT id, name, brand_name, currency_symbol FROM tenants WHERE id = %s", (tid,))
                row = cur.fetchone()
                if row:
                    brand_name = row.get("brand_name") or row.get("name") or brand_name
                    currency_symbol = row.get("currency_symbol") or currency_symbol
        except Exception:
            pass

        return {
            "current_tenant_id": tid,
            "brand_name": brand_name,
            "currency_symbol": currency_symbol
        }
