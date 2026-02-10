"""
Route handlers for the photo gallery app.

All HTTP routes (login, upload, gallery, search, download) live here.
Each route uses db.py for database access; photo routes will also use S3.
"""
#------------------------------- imports -------------------------------------#
import os
import time

import boto3
import db
from flask import redirect, request, Response, session, url_for, render_template
from werkzeug.security import check_password_hash, generate_password_hash
from auth import login_required





# ---------------------------------------------------------------------------
# Public routes (no login required)
# ---------------------------------------------------------------------------

def home():
    """Serve the home page. Logged in: greeting and Log out. Not logged in: Welcome with Sign up or Log in."""
    bucket = os.environ.get("S3_BUCKET", "assignment-1-images")
    if session.get("user_id"):
        photos = db.list_photos(session["user_id"])
        # pass S3_BUCKET so the template can build the image URLs
        return render_template("index.html", photos=photos, S3_BUCKET=bucket)
    return render_template("home.html")


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
    # GET: creating account
    if request.method == "GET":
        msg = "Account created. Please log in." if request.args.get("created") else ""
        # This line connects to your new login.html!
        return render_template("login.html", message=msg)
    # POST: process form
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")
    user = db.get_user_by_username(username)


    if user and check_password_hash(user["password_hash"], password):
        session["user_id"] = user["id"]
        session["username"] = user["username"]
        return redirect(url_for("home"))
    return render_template("login.html", error="Invalid credentials.")
    
    # if not username or not password:
    #     return "Username and password required.", 400
    # user = db.get_user_by_username(username)
    # if not user:
    #     return "Invalid username or password.", 401
    # if not check_password_hash(user["password_hash"], password):
    #     return "Invalid username or password.", 401
    # session["user_id"] = user["id"]
    # session["username"] = user["username"]
    # return redirect(url_for("home"))




def signup():
    """
    GET: Show sign-up form (username, password, email).
    POST: Hash password, db.create_user(...), redirect to login.
    """

    if request.method == "GET":
        return render_template("signup.html")
    
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")
    if db.get_user_by_username(username):
        return render_template("signup.html", error="Username taken.")
        
    db.create_user(username, None, generate_password_hash(password))
    return redirect(url_for("login", created=1))

    # if request.method == "GET":
    #     return """
    #     <h1>Sign up</h1>
    #     <p>First time? Create an account below.</p>
    #     <form method="post" action="/signup">
    #         <label>Username: <input name="username" type="text" required></label><br>
    #         <label>Password: <input name="password" type="password" required></label><br>
    #         <label>Email: <input name="email" type="email"></label><br>
    #         <button type="submit">Sign up</button>
    #     </form>
    #     <p>Already have an account? <a href="/login">Log in</a></p>
    #     """
    # username = request.form.get("username", "").strip()
    # password = request.form.get("password", "")
    # email = request.form.get("email", "").strip() or None
    # if not username or not password:
    #     return "Username and password required.", 400
    # if db.get_user_by_username(username):
    #     return "Username already taken.", 400
    # password_hash = generate_password_hash(password)
    # db.create_user(username, email, password_hash)
    # return redirect(url_for("login", created=1))


def logout():
    """Clear session and redirect to login."""
    session.clear()
    return redirect(url_for("login"))


# ---------------------------------------------------------------------------
# Photo routes (login required)
# ---------------------------------------------------------------------------

@login_required
def upload():
    """
    GET: Show upload form (file, optional title).
    POST: Upload file to S3, save row with db.add_photo, redirect to home.
    """

    if request.method == "GET":
        return render_template("form.html")
        
    photo = request.files.get("photo")
    if not photo or photo.filename == "":
        return "No file selected.", 400

    user_id = session["user_id"]
    title = request.form.get("title", "").strip() or None
    original_name = photo.filename
    safe_name = os.path.basename(original_name).replace(" ", "_")
    bucket = os.environ.get("S3_BUCKET", "assignment-1-images")
    key = f"{user_id}/{int(time.time())}_{photo.filename.replace(' ', '_')}"


    # user_id = session["user_id"]
    # title = request.form.get("title", "").strip() or None
    # original_name = photo.filename
    # safe_name = os.path.basename(original_name).replace(" ", "_")
    # bucket = os.environ.get("S3_BUCKET", "assignment-1-images")
    # key = f"{user_id}/{int(time.time())}_{safe_name}"
    # content_type = photo.content_type or "application/octet-stream"
    # body = photo.read()
    # size_bytes = len(body)

    try:
        s3 = boto3.client("s3", region_name=os.environ.get("AWS_REGION", "us-east-2"))
        s3.put_object(Bucket=bucket, Key=key, Body=photo.read(), ContentType=photo.content_type)
        db.add_photo(user_id, bucket, key, photo.filename, title=title)
    except Exception as e:
        return f"Upload failed: {e}", 500

    return redirect(url_for("home"))
    



    
    # if request.method == "GET":
    #     return """
    #     <h1>Upload a photo</h1>
    #     <form method="post" action="/upload" enctype="multipart/form-data">
    #         <label>Photo: <input type="file" name="photo" accept="image/*" required></label><br>
    #         <label>Title (optional): <input type="text" name="title"></label><br>
    #         <button type="submit">Upload</button>
    #     </form>
    #     <p><a href="/">Home</a></p>
    #     """
    # photo = request.files.get("photo")
    # if not photo or photo.filename == "":
    #     return "No file selected.", 400

    # user_id = session["user_id"]
    # title = request.form.get("title", "").strip() or None
    # original_name = photo.filename
    # safe_name = os.path.basename(original_name).replace(" ", "_")
    # bucket = os.environ.get("S3_BUCKET", "assignment-1-images")
    # key = f"{user_id}/{int(time.time())}_{safe_name}"
    # content_type = photo.content_type or "application/octet-stream"
    # body = photo.read()
    # size_bytes = len(body)

    # try:
    #     s3 = boto3.client("s3", region_name=os.environ.get("AWS_REGION", "us-east-2"))
    #     s3.put_object(Bucket=bucket, Key=key, Body=body, ContentType=content_type)
    #     db.add_photo(
    #         user_id, bucket, key, original_name,
    #         title=title, description=None, tags=None,
    #         content_type=content_type, size_bytes=size_bytes,
    #     )
    # except Exception as e:
    #     return f"Upload failed: {e}", 500

    # return redirect(url_for("home"))


@login_required
def gallery():
    """List the current user's photos with download links."""

    bucket = os.environ.get("S3_BUCKET", "assignment-1-images")
    photos = db.list_photos(session["user_id"])
    return render_template("index.html", photos=photos, S3_BUCKET=bucket)

    # user_id = session["user_id"]
    # photos = db.list_photos(user_id)
    # if not photos:
    #     return """
    #     <h1>Gallery</h1>
    #     <p>No photos yet. <a href="/upload">Upload</a> one.</p>
    #     <p><a href="/">Home</a></p>
    #     """
    # lines = ["<h1>Gallery</h1>", "<ul>"]
    # for p in photos:
    #     title = p.get("title") or p.get("original_name", "Photo")
    #     lines.append(f'<li>{title} — <a href="/download/{p["id"]}">Download</a></li>')
    # lines.append("</ul>")
    # lines.append('<p><a href="/upload">Upload</a> | <a href="/search">Search</a> | <a href="/">Home</a></p>')
    # return "\n".join(lines)


@login_required
def search():
    """Search photos by title, description, or tags; show results with download links."""

    user_id = session["user_id"]
    # Change 'q' to 'query' to match your HTML input name
    q = request.args.get("query", "").strip() 
    bucket = os.environ.get("S3_BUCKET", "assignment-1-images")
    photos = db.search_photos(user_id, q=q) if q else []
    # Ensure query=q is passed so the "Showing search results for..." text works
    return render_template("search.html", photos=photos, query=q, S3_BUCKET=bucket)




    # user_id = session["user_id"]
    # q = request.args.get("q", "").strip()
    # bucket = os.environ.get("S3_BUCKET", "assignment-1-images")
    # photos = db.search_photos(user_id, q=q) if q else []
    # return render_template("search.html", photos=photos, query=q, S3_BUCKET=bucket)



    

    # user_id = session["user_id"]
    # q = request.args.get("q", "").strip() or request.form.get("q", "").strip()
    # if not q:
    #     return """
    #     <h1>Search</h1>
    #     <form method="get" action="/search">
    #         <label>Search: <input type="text" name="q" placeholder="title, description, or tags"></label>
    #         <button type="submit">Search</button>
    #     </form>
    #     <p><a href="/gallery">Gallery</a> | <a href="/">Home</a></p>
    #     """
    # photos = db.search_photos(user_id, q=q)
    # if not photos:
    #     return f"""
    #     <h1>Search</h1>
    #     <p>No results for &quot;{q}&quot;.</p>
    #     <p><a href="/search">Search again</a> | <a href="/gallery">Gallery</a> | <a href="/">Home</a></p>
    #     """
    # lines = [f"<h1>Search results for &quot;{q}&quot;</h1>", "<ul>"]
    # for p in photos:
    #     title = p.get("title") or p.get("original_name", "Photo")
    #     lines.append(f'<li>{title} — <a href="/download/{p["id"]}">Download</a></li>')
    # lines.append("</ul>")
    # lines.append('<p><a href="/search">Search again</a> | <a href="/gallery">Gallery</a> | <a href="/">Home</a></p>')
    # return "\n".join(lines)


@login_required
def download(photo_id):
    """Stream the photo from S3 so the user can download it."""

    user_id = session["user_id"]
    photo = db.get_photo(photo_id, user_id)
    if not photo: return "Not found.", 404
    
    s3 = boto3.client("s3", region_name=os.environ.get("AWS_REGION", "us-east-2"))
    obj = s3.get_object(Bucket=photo["s3_bucket"], Key=photo["s3_key"])
    return Response(obj["Body"].read(), content_type=photo.get("content_type"),
                    headers={"Content-Disposition": f"attachment; filename={photo['original_name']}"})
    # user_id = session["user_id"]
    # photo = db.get_photo(photo_id, user_id)
    # if not photo:
    #     return "Photo not found.", 404
    # bucket = photo["s3_bucket"]
    # key = photo["s3_key"]
    # content_type = photo.get("content_type") or "application/octet-stream"
    # filename = photo.get("original_name") or "photo"
    # try:
    #     s3 = boto3.client("s3", region_name=os.environ.get("AWS_REGION", "us-east-2"))
    #     obj = s3.get_object(Bucket=bucket, Key=key)
    #     body = obj["Body"].read()
    # except Exception as e:
    #     return f"Download failed: {e}", 500
    # resp = Response(body, content_type=content_type)
    # resp.headers["Content-Disposition"] = f'attachment; filename="{filename}"'
    # return resp


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
    app.add_url_rule("/upload", "upload", upload, methods=["GET", "POST"])
    app.add_url_rule("/gallery", "gallery", gallery)
    app.add_url_rule("/search", "search", search, methods=["GET", "POST"])
    app.add_url_rule("/download/<int:photo_id>", "download", download)
    