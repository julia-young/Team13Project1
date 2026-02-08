"""
Auth helpers: login required check and password verification.

Used by routes to protect photo routes (upload, gallery, search, download)
and to verify login credentials against the database.
"""
#------------------------------- imports -------------------------------------#
from functools import wraps

from flask import redirect, session, url_for

#------------------------------- login_required -------------------------------#
def login_required(f):
    """
    Decorator: redirect to login if the user is not in session.

    Use on any route that should only be visible when logged in
    (e.g. upload, gallery, search, download).
    """
    @wraps(f)
    def wrapped(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return wrapped


