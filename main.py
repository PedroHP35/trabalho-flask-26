import os
from functools import wraps
from flask import Flask, request, jsonify, render_template, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
import database

app = Flask(__name__)


app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key")

API_KEY = os.environ.get("API_KEY", "chave-padrao-dev")


def require_api_key(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        key = request.headers.get("X-API-Key")
        if key != API_KEY:
            return jsonify({"error": "Unauthorized"}), 401
        return f(*args, **kwargs)
    return decorated

def login_required(f):
 
    @wraps(f)
    def decorated(*args, **kwargs):
        if "username" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated


@app.route("/login", methods=["GET", "POST"])
def login():
    """
    GET  → exibe o template de login
    POST → valida credenciais e inicia sessão
    """
    if "username" in session:
        return redirect(url_for("dashboard"))  

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        user = database.get_user_by_username(username)

        if user and check_password_hash(user["password_hash"], password):
            session["username"] = username  
            return redirect(url_for("dashboard"))

        flash("Usuário ou senha incorretos.", "error")

    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        confirm  = request.form.get("confirm", "")

        if not username or not password:
            flash("Preencha todos os campos.", "error")
        elif len(password) < 6:
            flash("A senha deve ter pelo menos 6 caracteres.", "error")
        elif password != confirm:
            flash("As senhas não coincidem.", "error")
        else:
            hashed = generate_password_hash(password)
            success = database.create_user(username, hashed)

            if success:
                flash("Conta criada! Faça login.", "success")
                return redirect(url_for("login"))
            else:
                flash("Este nome de usuário já existe.", "error")

    return render_template("register.html")


@app.route("/dashboard")
@login_required
def dashboard():
    """Exibe todos os registros formatados via Jinja2."""
    values = database.get_all_values()
    return render_template("dashboard.html", values=values, username=session["username"])


@app.route("/dashboard/add", methods=["POST"])
@login_required
def dashboard_add():
    value = request.form.get("value", "").strip()
    if value:
        database.insert_value(value)
        flash("Registro adicionado com sucesso.", "success")
    else:
        flash("O valor não pode ser vazio.", "error")
    return redirect(url_for("dashboard"))


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))



@app.route("/api/data", methods=["GET"])
@require_api_key
def api_get():
    return jsonify(database.get_all_values()), 200


@app.route("/api/data", methods=["POST"])
@require_api_key
def api_post():
    body = request.get_json(silent=True)
    if not body or "data" not in body:
        return jsonify({"error": "Campo 'data' ausente no corpo JSON"}), 400

    value = body["data"]
    if not isinstance(value, str) or not value.strip():
        return jsonify({"error": "'data' deve ser uma string não vazia"}), 422

    new_id = database.insert_value(value.strip())
    return jsonify({"message": "Valor adicionado", "id": new_id}), 201



@app.route("/")
def index():
    return redirect(url_for("login"))



database.create_tables()

if __name__ == "__main__":
    debug_mode = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
    app.run(host="0.0.0.0", port=5000, debug=debug_mode)
