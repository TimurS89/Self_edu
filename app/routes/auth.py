import hmac

from flask import Blueprint, current_app, redirect, render_template_string, request, session, url_for

auth_bp = Blueprint("auth", __name__)

LOGIN_TEMPLATE = """
<!DOCTYPE html>
<html><head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Self Edu - Login</title>
<style>
  body { font-family: -apple-system, system-ui, sans-serif; display: flex;
         justify-content: center; align-items: center; min-height: 100vh;
         margin: 0; background: #0f172a; color: #e2e8f0; }
  .login { text-align: center; padding: 2rem; }
  h1 { font-size: 1.5rem; margin-bottom: 1.5rem; }
  input { padding: 0.75rem 1rem; font-size: 1rem; border: 1px solid #334155;
          border-radius: 8px; background: #1e293b; color: #e2e8f0; width: 200px; }
  button { padding: 0.75rem 1.5rem; font-size: 1rem; border: none;
           border-radius: 8px; background: #3b82f6; color: white; cursor: pointer;
           margin-top: 1rem; display: block; width: 100%; }
  .error { color: #f87171; margin-top: 0.5rem; font-size: 0.875rem; }
</style>
</head><body>
<div class="login">
  <h1>Self Edu</h1>
  <form method="POST">
    <input type="password" name="token" placeholder="Enter token" autofocus>
    <button type="submit">Enter</button>
    {% if error %}<p class="error">{{ error }}</p>{% endif %}
  </form>
</div>
</body></html>
"""


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if not current_app.config.get("APP_TOKEN"):
        session["authenticated"] = True
        return redirect(url_for("dashboard.index"))

    if request.method == "POST":
        if hmac.compare_digest(request.form.get("token", ""), current_app.config["APP_TOKEN"]):
            session["authenticated"] = True
            return redirect(url_for("dashboard.index"))
        return render_template_string(LOGIN_TEMPLATE, error="Invalid token")

    return render_template_string(LOGIN_TEMPLATE, error=None)


@auth_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth.login"))
