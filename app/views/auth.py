from flask import Blueprint, render_template, request, redirect, url_for, flash, make_response, session
from flask_login import login_user, logout_user, login_required
import bcrypt
from utils import auth
from flask import current_app
from utils.tenancy import set_current_tenant_id

bp = Blueprint("auth", __name__)

@bp.route("/login", methods=["GET", "POST"])
def login():
    tenant_param = (request.args.get("tenant") or request.args.get("tenant_id") or "").strip()
    if tenant_param:
        session["tenant_id"] = tenant_param
        set_current_tenant_id(tenant_param)

    if request.method == "POST":
        username = (request.form.get("username") or "").strip().lower()
        password = request.form.get("password") or ""
        form_tenant = (request.form.get("tenant_id") or "").strip()
        if form_tenant:
            session["tenant_id"] = form_tenant
            set_current_tenant_id(form_tenant)

        current_tenant = session.get("tenant_id", "default")
        row = auth.get_user_by_username(current_app.config["DATABASE_URL"], username, tenant_id=current_tenant)
        if not row and current_app.config.get("DEMO_MODE"):
            demo_alias = auth.get_demo_alias(username)
            if demo_alias:
                role_row = auth.get_active_user_by_role(current_app.config["DATABASE_URL"], demo_alias["role"], tenant_id=current_tenant)
                live_password = ((role_row or {}).get("demo_password_plain") or demo_alias["password"] or "")
                if role_row and password == live_password:
                    row = dict(role_row)
                    row["display_username"] = username
                    row["display_full_name"] = demo_alias["label"].rstrip("s")
                    row["demo_alias"] = username
                elif role_row and password != live_password:
                    row = None
                else:
                    flash(f"demo {demo_alias['role']} account unavailable", "error")
                    return render_template("login.html"), 503
        if not row:
            flash("User not found or invalid tenant", "error")
            return render_template("login.html"), 401
        if not row["is_active"]:
            flash("Account disabled", "error")
            return render_template("login.html"), 403
        is_demo_alias = bool(getattr(row, "get", None) and row.get("demo_alias"))
        if is_demo_alias or bcrypt.checkpw(password.encode("utf-8"), row["password_hash"].encode("utf-8")):
            user_obj = auth.User(row)
            session["tenant_id"] = user_obj.tenant_id
            set_current_tenant_id(user_obj.tenant_id)
            login_user(user_obj)
            nxt = request.args.get("next")
            return redirect(nxt or url_for("dashboard.dashboard"))
        else:
            flash("Password incorrect", "error")
            return render_template("login.html"), 401
    return render_template("login.html")

@bp.route("/logout", methods=["POST", "GET"])
@login_required
def logout():
    logout_user()
    from flask import session
    session.clear()
    resp = make_response(redirect(url_for("auth.login")))
    resp.set_cookie("session", "", expires=0)
    return resp
