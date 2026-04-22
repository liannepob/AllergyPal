from cs50 import SQL
from flask import Flask, render_template, request, redirect, session, url_for, flash
from flask_session import Session
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import date, datetime
from helpers import login_required
from services.auth_tokens import generate_token
from services.auth_tokens import verify_token
from services.email import send_reset_email
import hashlib
import os
import requests
from dotenv import load_dotenv
load_dotenv()
import logging
logging.getLogger("urllib3").setLevel(logging.WARNING)


app = Flask(__name__)
app.secret_key = "dev"

# Configure sessions
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Connect to database
db = SQL("sqlite:///allergy.db")
# redirects users to the homepage
@app.route("/")
def index():
    return render_template("index.html")

# Authentication Routes: Register, Log-in, Log-out, Forgot-Password
@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")
        age = request.form.get("age")
        hometown = request.form.get("hometown")
        food_pref = request.form.get("food_pref")

        # checks the name and email to make sure they exist
        if not name or not email or not password or not username:
            return "missing field(s)"

        # checks if the password matches the confirmation
        if password != confirmation:
            return ("passwords do not match")

        # Check if username exists
        rows = db.execute("SELECT * FROM users WHERE username = ?", username)
        if len(rows) != 0:
            return ("username already exists")

        # Check if email already exists
        rows = db.execute("SELECT * FROM users WHERE email = ?", email)
        if len(rows) != 0:
            return ("email already exists please provide a different one or log in.")

        # Gets the current date and time to update users table
        created_at = date.today().isoformat()

        # Hash password and insert into DB
        hashed_pass = generate_password_hash(password, method="pbkdf2:sha256")        
        db.execute("INSERT INTO users(name, email, username, hash, age, hometown, food_pref, created_at) VALUES(?,?,?,?,?,?,?,?)", name, email, username, hashed_pass, age, hometown, food_pref, created_at)

        # Log in user
        userID = db.execute("SELECT id FROM users WHERE username = ?", username)[0]["id"]
        session["user_id"] = userID

        return redirect("/")
    else:
        return render_template("register.html")

# Login route for users
@app.route("/login", methods=["GET", "POST"])
def login():
    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Query database for username
        rows = db.execute(
            "SELECT * FROM users WHERE username = ?", request.form.get("username")
        )

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(
            rows[0]["hash"], request.form.get("password")
        ):
            return("invalid username and/or password")

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")

# Logout route for users
@app.route("/logout")
def logout():
    """Logs the user out"""
    session.clear()
    # Redirect user to login form
    return redirect("/")

# profile section for users info and the way to update it
@app.route("/profile", methods=["GET"])
@login_required
def profile():
    current = session["user_id"]

    # gets a dictionary for users profile for view all but hash
    users = db.execute(
        "SELECT name, username, age, food_pref, hometown, email, created_at FROM users WHERE id = ?",
        current
    )

    # gets a dictionary for the allergies and severity of user allergies
    # joined the allergy_id from user_allergies with the id from allergies tables
    allergens = db.execute(
        """SELECT allergies.id, allergies.name, user_allergies.severity
        FROM user_allergies
        JOIN allergies
        ON user_allergies.allergy_id = allergies.id
        WHERE user_allergies.user_id = ?""",
        current
    )

    er_contact = db.execute(
        """
        SELECT id, contact_name, phone, relationship, age
        FROM emergency_contacts
        WHERE user_id = ?
        """,
        current
    )

    # checks users table to make sure all tables are full/have status
    if len(users) != 1:
        return "Error: User not found"
       # makes sure the user actually has status
    row = users[0]
    # gets the user's data for the profile page
    return render_template(
        "profile.html",
        name = row["name"],
        age = row["age"],
        username = row["username"],
        food_pref = row["food_pref"],
        hometown = row["hometown"],
        email = row["email"],
        created_at = row["created_at"],
        allergens = allergens,
        er_contact = er_contact
        )

@app.route("/edit_profile", methods=["GET", "POST"])
@login_required
def edit_profile():
    current = session["user_id"]

    if request.method == "POST":
        # Get updated form values
        name = request.form.get("name")
        age = request.form.get("age")
        hometown = request.form.get("hometown")
        food_pref = request.form.get("food_pref")

        if not name or not age or not hometown:
            flash("Name, age, and hometown are required.")
            return redirect(url_for("edit_profile"))

        # Update the user in the database
        db.execute("UPDATE users SET name = ?, age = ?, hometown = ?, food_pref = ? WHERE id = ?",
                    name, age, hometown, food_pref, current)

        return redirect(url_for("profile"))

    else:
        # GET: fetch current user info to prefill the form
        user = db.execute("SELECT name, age, hometown, food_pref FROM users WHERE id = ?", current)[0]

        return render_template(
            "edit_profile.html",
            name=user["name"],
            age=user["age"],
            hometown=user["hometown"],
            food_pref=user["food_pref"]
        )

# form for users to add their allergies, and a post section so it updates the allergies.db
@app.route("/add_allergy", methods=["GET", "POST"])
@login_required
def add_allergy():

    current = session["user_id"]

    # checks if the form is submitted via POST then gets all the info from the form
    if request.method == "GET":
        return render_template("add_allergy.html")

    # POST method
    if request.method == "POST":
        allergen_name = request.form.get("allergen")
        category = request.form.get("category")
        severity = request.form.get("severity")

        # case conditionals that verify submission and case
        if not allergen_name or not category or not severity:
            return "missing field(s)"
        strip_allergen = allergen_name.strip()
        allergen = strip_allergen.lower()
        if not allergen:
            return "missing field(s)"
        # category
        strip_category = category.strip()
        category = strip_category.lower()
        if not category:
            return "missing field(s)"
        # severity
        strip_severity = severity.strip()
        severity = strip_severity.lower()
        if not severity:
            return "missing field(s)"

        # gets the allergy_ids based on the allergen in the database
        a_check = db.execute("SELECT id FROM allergies WHERE name = ?", allergen)

        # will check if the list is empty, and will create a new allergen or will update
        if not a_check:
            db.execute("INSERT INTO allergies(name, category) VALUES(?,?)",
                allergen, category)
            # then will re-check the allergen_id from the updated table
            allergen_id= db.execute("SELECT id FROM allergies WHERE name = ?", allergen)[0]["id"]
        else:
            allergen_id = a_check[0]["id"]

        # checks if user has allergy already
        existing = db.execute("SELECT 1 FROM user_allergies WHERE user_id = ? AND allergy_id = ?",
            current, allergen_id)
        if existing:
            # update severity (and you could also update notes later)
            db.execute("UPDATE user_allergies SET severity = ? WHERE user_id = ? AND allergy_id = ?",
                severity, current, allergen_id)
            flash("Allergy updated successfully")
            return redirect(url_for("profile"))
        else:
            # first time logging this allergy for this user
            db.execute("INSERT INTO user_allergies(user_id, allergy_id, severity) VALUES(?,?,?)",
                current, allergen_id, severity)
            flash("Allergy added successfully")
            return redirect(url_for("profile"))

    return redirect(url_for("profile"))

@app.route("/delete_allergy", methods=["POST"])
@login_required
def delete_allergy():
    current = session["user_id"]

    allergen = request.form.get("allergy_id")

    # confirms the value of the deletion form
    if not allergen:
        return "missing allergy for deletion"

    db.execute("DELETE FROM user_allergies WHERE user_id = ? AND allergy_id = ?",
               current, allergen)

    flash("Allergy deleted successfully.")
    return redirect(url_for("profile"))

@app.route("/er_contacts", methods=["GET", "POST"])
@login_required
def er_contacts():
    current = session["user_id"]

    # strip/lower to avoid repeats in db
    if request.method == "POST":

        n = request.form.get("name")
        nu = request.form.get("number")

        if not n or not nu:
            return "missing field(s)"

        name = n.strip()
        number = nu.strip()

        # non required forms
        age = int(request.form.get("age")) if request.form.get("age") else None
        relation = request.form.get("relationship") if request.form.get("relationship") else None
        email = request.form.get("email").strip().lower() if request.form.get("email") else None
        address = request.form.get("address").strip().lower() if request.form.get("address") else None
        notes = request.form.get("notes") if request.form.get("notes") else None

        db.execute("""
                   INSERT INTO emergency_contacts
                   (user_id, contact_name, phone, email, address, age, relationship, notes)
                    VALUES(?, ?, ?, ?, ?, ?, ?, ?)""",
                   current, name, number, email, address, age, relation, notes)

        flash("Emergency contact added Successfully.")

    else:
        contacts = db.execute("SELECT * FROM emergency_contacts WHERE user_id = ?", current)
        return render_template("er_contacts.html", contacts=contacts)

    return redirect(url_for("er_contacts"))

# creates a route to delete an er_contact
@app.route("/delete_er_contact", methods=["POST"])
@login_required
def delete_er_contact():
    current = session["user_id"]

    contact = request.form.get("contact_id")

    # confirms the value of the deletion form
    if not contact:
        return "missing emergency contact for deletion"

    db.execute("DELETE FROM emergency_contacts WHERE id = ? AND user_id = ?",
               contact, current)

    flash("Emergency contact deleted successfully.")
    return redirect(url_for("profile"))

# route to show a emergency card to someone else
@app.route("/emergency", methods=["GET"])
@login_required
def emergency():
    current = session["user_id"]
    # should display user's contact info, their allergies, and their er contacts
    # user's information
    user_info = db.execute(
        """SELECT name, age, hometown
        FROM users
        WHERE id = ?""",
        current)
    # user's allergies
    allergies = db.execute(
        """SELECT name, severity
        FROM user_allergies
        JOIN allergies
        ON user_allergies.allergy_id = allergies.id
        WHERE user_allergies.user_id = ?""",
        current)
    # user's emergency contacts
    contacts = db.execute(
        """SELECT contact_name, phone, email, address, age, relationship, notes
        FROM emergency_contacts
        WHERE user_id = ?""",
        current)

    return render_template(
        "emergency.html",
        user_info = user_info,
        allergies = allergies,
        contacts = contacts,
    )

# Add restaurant: check if exists, insert restaurant into db
@app.route("/add_restaurant", methods=["POST","GET"])
@login_required
def add_restaurant():
    current = session["user_id"]
    # needs to check if restaurant exists: refer to add_allergy

    if request.method == "POST":

        r = request.form.get("restaurant")
        a = request.form.get("address")
        s = request.form.get("status")
        notes = request.form.get("notes") if request.form.get("notes") else None

        # required forms: restaurant name, address, status
        if not r or not a or not s:
            return "missing field(s)"
        else:
            restaurant = r.strip().lower()
            address = a.strip().lower()
            status = s.strip().lower()
        
        # check if the restaurant exists in the db
        rest_check = db.execute("SELECT id FROM restaurants WHERE name = ? AND address = ?", restaurant, address)
        
        if not rest_check:
            db.execute("INSERT INTO restaurants(name, address) VALUES(?, ?)",
                restaurant, address)
            rest_id = db.execute("SELECT id FROM restaurants WHERE name = ? AND address = ?",
                restaurant, address)[0]["id"]
        else:
            rest_id = rest_check[0]["id"]        
        
        # updating/insert restaurants into the saved table
        saved_rest = db.execute(
            """SELECT 1 FROM saved_restaurants WHERE user_id = ? AND restaurant_id = ?""",
            current, rest_id)

        if not saved_rest:
            db.execute(
                """INSERT INTO saved_restaurants(user_id, restaurant_id, status, notes, created_at)
            VALUES(?,?,?,?,?)""",
            current, rest_id, status, notes, date.today().isoformat()
            )
            flash("Added restaurant details successfully!")
            return redirect(url_for("add_restaurant"))
        else:
            db.execute(
            """UPDATE saved_restaurants
                SET status = ?, notes = ?
                WHERE user_id = ? AND restaurant_id = ?""",
                status, notes, current, rest_id
            )
            flash("Updated restaurant details successfully!")
            return redirect(url_for("add_restaurant"))
    else:
        return render_template("add_restaurant.html")

# Restaurant route to get information of restaurants
@app.route("/restaurant", methods=["GET"])
@login_required
def restaurant():
    current = session["user_id"]

    rests = db.execute(
        """SELECT restaurants.name, restaurants.address, saved_restaurants.status, saved_restaurants.notes, saved_restaurants.restaurant_id
        FROM saved_restaurants
        JOIN restaurants
        ON saved_restaurants.restaurant_id = restaurants.id
        WHERE saved_restaurants.user_id = ?""",
        current
    )

    # sends all the restaurant info into the html
    return render_template(
        "restaurants.html",
        restaurants = rests
    )


# Restaurant route to get information of restaurants
@app.route("/delete_restaurant", methods=["POST"])
@login_required
def delete_restaurant():
    current = session["user_id"]

    # get the info from rest.html
    rest = request.form.get("restaurant_id")

    # confirms the value of the deletion form
    if not rest:
        return "missing restaurant for deletion"

    db.execute("DELETE FROM saved_restaurants WHERE restaurant_id = ? AND user_id = ?",
               rest, current)

    flash("Restaurant deleted successfully.")
    return redirect(url_for("restaurant"))

@app.route("/search_restaurants", methods=["GET", "POST"])
@login_required
def search_restaurants():
    current = session["user_id"]

    if request.method == "POST":
        l = request.form.get("location")
        r = request.form.get("radius")
        lat = request.form.get("lat")
        lng = request.form.get("lng")

        if not l and not lat and not lng:
            return "please enter a location or provide your current location"

        if not r:
            return "missing field"

        location = l.strip().lower() if l else ""
        radius = r

        api_key = os.environ.get("GOOGLE_PLACES_API_KEY")
        url = "https://maps.googleapis.com/maps/api/place/textsearch/json"

        if lat and lng:
            params = {
            "location": f"{lat},{lng}",
            "radius": radius,
            "type": "restaurant",
            "key": api_key
            }

        else:
            params = {
            "query": location + " restaurants",
            "radius": radius,
            "type": "restaurant",
            "key": api_key
            }

        response = requests.get(url, params=params)
        data = response.json()
        results = data.get("results", [])

        return render_template("search_restaurants.html", results=results)

    else:
        return render_template("search_restaurants.html")

@app.route("/forgot_password", methods=["GET", "POST"])
def forgot_password():

    if request.method == "POST":
        email = request.form.get("email")
        check_email = db.execute("""SELECT id, email FROM users WHERE email = ?""", email)

        if not check_email:
            return redirect(url_for("forgot_password"))


        info = check_email[0]
        reset = generate_token(db, info["id"])
        reset_link = url_for('reset_password', token=reset, _external=True)
        send_email = send_reset_email(info["email"], reset_link)
        flash("Password reset email sent! Check your inbox.")
        return redirect(url_for("login"))
    
    else:
        return render_template("forgot_password.html")  # correct

@app.route("/reset/<token>", methods=["GET", "POST"])
def reset_pass(token):
    
    if request.method == "POST":
        new_pass = request.form.get("new_password")

        confirm = request.form.get("confirm")

        if new_pass != confirm:
            return "Passwords do not match, try again please."

        user_id = verify_token(db, token)

        if user_id is None:
            flash("Invalid or expired link")
            return redirect(url_for("forgot_password"))

        hashed_pass = generate_password_hash(new_pass, method="pbkdf2:sha256")  

        db.execute("""UPDATE users
                        SET hash = ?
                        WHERE id = ?""",
                         hashed_pass, user_id)

        now = datetime.now()

        token_hash = hashlib.sha256(token.encode()).hexdigest()
        db.execute("""UPDATE password_resets SET used_at = ? WHERE token_hash = ?""", now, token_hash)
        flash("Password Successfully Reset!")
        return redirect(url_for("login"))
        
    else:
        return render_template("reset_pass.html")


