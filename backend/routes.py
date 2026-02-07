"""
Route handlers for the photo gallery app.

All HTTP routes (login, upload, gallery, search, download) live here.
Each route uses db.py for database access; photo routes will also use S3.
"""
#------------------------------- imports -------------------------------------#
import db
from flask import redirect, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash


# ---------------------------------------------------------------------------
# Public routes (no login required)
# ---------------------------------------------------------------------------

def home():
    """Serve the home page. Logged in: greeting and Log out. Not logged in: Welcome with Sign up or Log in."""
    if session.get("user_id"):
        return f"Hello, {session.get('username', '')}! <a href='/logout'>Log out</a>"
    return "Welcome. First time? <a href='/signup'>Sign up</a>. Already have an account? <a href='/login'>Log in</a>."


def db_check():
    """
    Check that the app can connect to the RDS database.

    Uses db.get_conn() which reads DB_HOST, DB_USER, DB_PASS from env.
    - Success: returns "DB connection successful".
    - Failure: returns error message (e.g. missing env, timeout from local Mac).
    RDS is only reachable from EC2 (same VPC); local runs may timeout.
    """
    try:
        with db.get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
        return "DB connection successful."
    except Exception as e:
        return f"DB connection failed: {e}", 500


# ---------------------------------------------------------------------------
# Auth routes (login, logout)
# ---------------------------------------------------------------------------

def login():
    """
    GET: Show login form (username, password).
    POST: Check credentials with db.get_user_by_username and Werkzeug hash;
          on success set session["user_id"], session["username"] and redirect to home.
    """
    if request.method == "GET":
        # Simple HTML form; Person 4 can replace with a template later.
        return """
        <h1>Log in</h1>
        <p>Already have an account? Enter your credentials below.</p>
        <form method="post" action="/login">
            <label>Username: <input name="username" type="text" required></label><br>
            <label>Password: <input name="password" type="password" required></label><br>
            <button type="submit">Log in</button>
        </form>
        <p>Don't have an account? <a href="/signup">Sign up</a></p>
        """
    # POST: process form
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")
    if not username or not password:
        return "Username and password required.", 400
    user = db.get_user_by_username(username)
    if not user:
        return "Invalid username or password.", 401
    if not check_password_hash(user["password_hash"], password):
        return "Invalid username or password.", 401
    session["user_id"] = user["id"]
    session["username"] = user["username"]
    return redirect(url_for("home"))


def signup():
    """
    GET: Show sign-up form (username, password, email).
    POST: Hash password, db.create_user(...), redirect to login.
    """
    if request.method == "GET":
        return """
        <h1>Sign up</h1>
        <p>First time? Create an account below.</p>
        <form method="post" action="/signup">
            <label>Username: <input name="username" type="text" required></label><br>
            <label>Password: <input name="password" type="password" required></label><br>
            <label>Email: <input name="email" type="email"></label><br>
            <button type="submit">Sign up</button>
        </form>
        <p>Already have an account? <a href="/login">Log in</a></p>
        """
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")
    email = request.form.get("email", "").strip() or None
    if not username or not password:
        return "Username and password required.", 400
    if db.get_user_by_username(username):
        return "Username already taken.", 400
    password_hash = generate_password_hash(password)
    db.create_user(username, email, password_hash)
    return redirect(url_for("login"))


def logout():
    """Clear session and redirect to login."""
    session.clear()
    return redirect(url_for("login"))


# ---------------------------------------------------------------------------
# Photo routes (login required) — to be added later
# ---------------------------------------------------------------------------
# def upload(): ...
# def gallery(): ...
# def search(): ...
# def download(): ...


# ---------------------------------------------------------------------------
# App routes: attach URL paths to handlers (called from app.py)
# ---------------------------------------------------------------------------

def app_routes(app):
    """
    Attach route handlers from this file to the Flask app.

    Called from app.py after creating the app so that each URL path
    (e.g. "/", "/db-check") maps to the right function (home, db_check, etc.).
    """
    app.add_url_rule("/", "home", home)
    app.add_url_rule("/db-check", "db_check", db_check)
    app.add_url_rule("/login", "login", login, methods=["GET", "POST"])
    app.add_url_rule("/signup", "signup", signup, methods=["GET", "POST"])
    app.add_url_rule("/logout", "logout", logout)
    # Upload, gallery, search, download will be added here.
