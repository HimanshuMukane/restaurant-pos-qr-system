import os
from contextvars import ContextVar
from flask import request, session, g

_tenant_var = ContextVar("current_tenant_id", default="default")

def get_current_tenant_id():
    """
    Get the tenant_id in the current execution context.
    Order of lookup:
    1. Flask g.tenant_id if set
    2. URL query param ?tenant= or ?tenant_id=
    3. Session tenant_id
    4. HTTP header X-Tenant-ID
    5. ContextVar
    6. Environment variable DEFAULT_TENANT_ID or 'default'
    """
    try:
        if hasattr(g, "tenant_id") and g.tenant_id:
            return g.tenant_id
    except RuntimeError:
        pass

    try:
        # Check query string
        t = request.args.get("tenant") or request.args.get("tenant_id")
        if t:
            return t.strip()

        # Check request headers
        h = request.headers.get("X-Tenant-ID")
        if h:
            return h.strip()

        # Check session
        if "tenant_id" in session and session["tenant_id"]:
            return session["tenant_id"]
    except RuntimeError:
        pass

    # ContextVar fallback
    var_val = _tenant_var.get()
    if var_val:
        return var_val

    return os.getenv("DEFAULT_TENANT_ID", "default")


def set_current_tenant_id(tenant_id):
    _tenant_var.set(tenant_id)
    try:
        g.tenant_id = tenant_id
    except RuntimeError:
        pass
