from flask import Blueprint
from flask_login import login_required
import subprocess
from ..authz import roles_required

bp = Blueprint("system", __name__)

@bp.post("/_shutdown_browser")
@login_required
@roles_required("admin")
def shutdown_browser():
    # Optional: restrict
    # if not current_user.has_role("admin"):
    #     abort(403)

    cmds = [
        ["pkill", "-f", "chromium-browser"],
        ["pkill", "-f", "chromium"],
        ["pkill", "-f", "chrome"],
        ["pkill", "-f", "firefox"],
    ]
    for cmd in cmds:
        try:
            subprocess.Popen(cmd)
        except Exception:
            pass

    return ("", 204)
