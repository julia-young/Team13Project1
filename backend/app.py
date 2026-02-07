"""
Photo gallery Flask application — entry point.

Creates the app, loads config, and registers all routes from routes.py.
Keep this file small: no business logic here, only wiring.
"""
#------------------------------- imports -------------------------------#
from flask import Flask
from routes import app_routes


# ---------------------------------------------------------------------------
# Create the Flask app
# ---------------------------------------------------------------------------

app = Flask(__name__)

# Required for session (login). Use env var on EC2; dev default for local.
app.config["SECRET_KEY"] = "dev-secret-change-on-ec2"


# ---------------------------------------------------------------------------
# App routes: attach URL paths to handlers (login, upload, gallery, etc. in routes.py)
# ---------------------------------------------------------------------------

app_routes(app)


# ---------------------------------------------------------------------------
# Run the development server (python app.py)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    app.run(debug=True)
