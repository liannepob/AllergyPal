# creates a login function to be used in all routes
# automatically checks if the user is logged in and if not, redirects them to log in before viewing
from functools import wraps
from flask import session, redirect

def login_required(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return wrapped
