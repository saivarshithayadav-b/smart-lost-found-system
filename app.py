from flask import (
    Flask,
    render_template,
    request,
    session,
    redirect,
    url_for,
    send_from_directory
)

import os

from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash

from database import get_db_connection
# AI MATCHING PIPELINE
from matching.database_matching import match_lost_item
# FLASK APPLICATION
app = Flask(__name__)

app.secret_key = "lost-found-secret-key"
# IMAGE UPLOAD SETTINGS
UPLOAD_FOLDER = os.path.join(
    app.root_path,
    "uploads"
)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

ALLOWED_EXTENSIONS = {
    "png",
    "jpg",
    "jpeg",
    "gif"
}

def allowed_file(filename):

    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower()
        in ALLOWED_EXTENSIONS
    )
# SERVE UPLOADED IMAGES
@app.route("/uploads/<filename>")
def uploaded_file(filename):

    return send_from_directory(
        app.config["UPLOAD_FOLDER"],
        filename
    )
# HOME
@app.route("/")
def home():

    unread_count = 0

    if "user_id" in session:

        connection = get_db_connection()

        cursor = connection.cursor(
            dictionary=True
        )

        cursor.execute(
            """
            SELECT COUNT(*) AS unread_count
            FROM notifications
            WHERE user_id = %s
            AND is_read = FALSE
            """,
            (session["user_id"],)
        )

        result = cursor.fetchone()

        unread_count = result["unread_count"]

        cursor.close()
        connection.close()

    return render_template(
        "index.html",
        unread_count=unread_count
    )
# REGISTER
@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form["name"]

        email = request.form["email"]

        password = request.form["password"]

        hashed_password = generate_password_hash(
            password
        )

        connection = get_db_connection()

        cursor = connection.cursor()

        cursor.execute(
            """
            INSERT INTO users
            (name, email, password)
            VALUES (%s, %s, %s)
            """,
            (
                name,
                email,
                hashed_password
            )
        )

        connection.commit()

        cursor.close()
        connection.close()

        return redirect(
            url_for("login")
        )

    return render_template(
        "register.html"
    )
# LOGIN
@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]

        password = request.form["password"]

        connection = get_db_connection()

        cursor = connection.cursor(
            dictionary=True
        )

        cursor.execute(
            """
            SELECT *
            FROM users
            WHERE email = %s
            """,
            (email,)
        )

        user = cursor.fetchone()

        cursor.close()
        connection.close()

        if user and check_password_hash(
            user["password"],
            password
        ):

            session["user_id"] = user["id"]

            session["name"] = user["name"]

            return redirect(
                url_for("home")
            )

        return "Invalid email or password"

    return render_template(
        "login.html"
    )
# LOGOUT
@app.route("/logout")
def logout():

    session.clear()

    return redirect(
        url_for("home")
    )
# REPORT LOST ITEM
@app.route("/lost-item", methods=["GET", "POST"])
def lost_item():

    if "user_id" not in session:

        return redirect(
            url_for("login")
        )

    if request.method == "POST":
        # GET FORM DATA
        item_name = request.form["item_name"]

        category = request.form["category"]

        description = request.form["description"]

        color = request.form["color"]

        brand = request.form["brand"]

        lost_date = request.form["lost_date"] or None

        location = request.form["location"]

        latitude = request.form["latitude"] or None

        longitude = request.form["longitude"] or None
        # IMAGE UPLOAD
        image = request.files.get("image")

        image_path = None

        if (
            image
            and image.filename
            and allowed_file(image.filename)
        ):

            filename = secure_filename(
                image.filename
            )

            image.save(
                os.path.join(
                    app.config["UPLOAD_FOLDER"],
                    filename
                )
            )

            image_path = filename
        # DATABASE INSERT
        connection = get_db_connection()

        cursor = connection.cursor()

        cursor.execute(
            """
            INSERT INTO lost_items
            (
                user_id,
                item_name,
                category,
                description,
                color,
                brand,
                lost_date,
                location,
                latitude,
                longitude,
                image_path
            )
            VALUES
            (
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s
            )
            """,
            (
                session["user_id"],
                item_name,
                category,
                description,
                color,
                brand,
                lost_date,
                location,
                latitude,
                longitude,
                image_path
            )
        )

        connection.commit()

        lost_item_id = cursor.lastrowid

        cursor.close()
        connection.close()
        # GET COMPLETE LOST ITEM
        connection = get_db_connection()

        cursor = connection.cursor(
            dictionary=True
        )

        cursor.execute(
            """
            SELECT *
            FROM lost_items
            WHERE id = %s
            """,
            (lost_item_id,)
        )

        lost_item_data = cursor.fetchone()

        cursor.close()
        connection.close()
        # AI MATCHING
        matching_results = []

        if (
            lost_item_data
            and lost_item_data["latitude"] is not None
            and lost_item_data["longitude"] is not None
        ):

            matching_results = match_lost_item(
                lost_item_data,
                radius_km=5
            )
        # STORE RESULTS IN SESSION
        session["matching_results"] = matching_results

        session["lost_item_id"] = lost_item_id
        # REDIRECT TO MATCH RESULTS
        return redirect(
            url_for("match_results")
        )

    return render_template(
        "lost_item.html"
    )
# MATCH RESULTS
@app.route("/match-results")
def match_results():

    if "user_id" not in session:

        return redirect(
            url_for("login")
        )

    matching_results = session.get(
        "matching_results",
        []
    )

    lost_item_id = session.get(
        "lost_item_id"
    )
    # GET LOST ITEM IMAGE DIRECTLY FROM DATABASE
    lost_image = None

    if lost_item_id:

        connection = get_db_connection()

        cursor = connection.cursor(
            dictionary=True
        )

        cursor.execute(
            """
            SELECT image_path
            FROM lost_items
            WHERE id = %s
            AND user_id = %s
            """,
            (
                lost_item_id,
                session["user_id"]
            )
        )

        lost_item = cursor.fetchone()

        cursor.close()
        connection.close()

        if lost_item:

            lost_image = lost_item["image_path"]
    # GET FOUND ITEM IMAGES DIRECTLY FROM DATABASE
    for result in matching_results:

        result["lost_item_image"] = lost_image

        found_item_id = result.get(
            "found_item_id"
        )

        found_image = None

        if found_item_id:

            connection = get_db_connection()

            cursor = connection.cursor(
                dictionary=True
            )

            cursor.execute(
                """
                SELECT image_path
                FROM found_items
                WHERE id = %s
                """,
                (found_item_id,)
            )

            found_item = cursor.fetchone()

            cursor.close()
            connection.close()

            if found_item:

                found_image = found_item["image_path"]

        result["found_item_image"] = found_image
    # DISPLAY MATCH RESULTS
    return render_template(
        "match_results.html",
        matching_results=matching_results,
        lost_item_id=lost_item_id
    )
# VERIFY MATCH
@app.route("/verify-match", methods=["POST"])
def verify_match():

    if "user_id" not in session:

        return redirect(
            url_for("login")
        )
    # GET DATA FROM FORM
    verification = request.form.get(
        "verification"
    )

    found_item_id = request.form.get(
        "found_item_id"
    )

    final_score = request.form.get(
        "final_score"
    )

    lost_item_id = session.get(
        "lost_item_id"
    )

    user_id = session.get(
        "user_id"
    )
    # VALIDATE DATA
    if verification not in (
        "confirmed",
        "rejected"
    ):

        return "Invalid verification status", 400

    if not found_item_id:

        return "Found item ID is missing", 400

    if not final_score:

        return "Final score is missing", 400

    if not lost_item_id:

        return "Lost item ID is missing", 400
    # CONNECT TO DATABASE
    connection = get_db_connection()

    cursor = connection.cursor(
        dictionary=True
    )
    # GET FOUND ITEM OWNER
    cursor.execute(
        """
        SELECT
            user_id,
            item_name
        FROM found_items
        WHERE id = %s
        """,
        (found_item_id,)
    )

    found_item = cursor.fetchone()

    if not found_item:

        cursor.close()
        connection.close()

        return "Found item not found", 404

    found_item_owner_id = found_item["user_id"]

    found_item_name = found_item["item_name"]
    # SAVE VERIFICATION
    cursor.execute(
        """
        INSERT INTO match_verifications
        (
            lost_item_id,
            found_item_id,
            user_id,
            final_score,
            verification_status
        )
        VALUES
        (
            %s,
            %s,
            %s,
            %s,
            %s
        )
        """,
        (
            lost_item_id,
            found_item_id,
            user_id,
            final_score,
            verification
        )
    )
    # CREATE NOTIFICATION
    if verification == "confirmed":

        message = (
            f"Your found item '{found_item_name}' "
            f"has been confirmed as a match by the "
            f"lost item owner. "
            f"AI Match Score: {final_score}"
        )

        cursor.execute(
            """
            INSERT INTO notifications
            (
                user_id,
                message,
                related_lost_item_id,
                related_found_item_id
            )
            VALUES
            (
                %s,
                %s,
                %s,
                %s
            )
            """,
            (
                found_item_owner_id,
                message,
                lost_item_id,
                found_item_id
            )
        )
    # COMMIT
    connection.commit()

    cursor.close()
    connection.close()
    # CONFIRMED
    if verification == "confirmed":

        return f"""
        <!DOCTYPE html>

        <html>

        <head>

            <title>
                Match Confirmed
            </title>

        </head>

        <body>

            <h1>
                Match Confirmed
            </h1>

            <p>
                You confirmed that this is your item.
            </p>

            <p>
                <strong>
                    Lost Item ID:
                </strong>

                {lost_item_id}
            </p>

            <p>
                <strong>
                    Found Item ID:
                </strong>

                {found_item_id}
            </p>

            <p>
                <strong>
                    AI Match Score:
                </strong>

                {final_score}
            </p>

            <p>
                <strong>
                    Status:
                </strong>

                Confirmed
            </p>

            <p>
                A notification has been sent
                to the found item owner.
            </p>

            <br>

            <a href="/">
                Back to Home
            </a>

        </body>

        </html>
        """
    # REJECTED
    return f"""
    <!DOCTYPE html>

    <html>

    <head>

        <title>
            Match Rejected
        </title>

    </head>

    <body>

        <h1>
            Match Rejected
        </h1>

        <p>
            You rejected this potential match.
        </p>

        <p>
            <strong>
                Lost Item ID:
            </strong>

            {lost_item_id}
        </p>

        <p>
            <strong>
                Found Item ID:
            </strong>

            {found_item_id}
        </p>

        <p>
            <strong>
                AI Match Score:
            </strong>

            {final_score}
        </p>

        <p>
            <strong>
                Status:
            </strong>

            Rejected
        </p>

        <br>

        <a href="/">
            Back to Home
        </a>

    </body>

    </html>
    """
# NOTIFICATIONS
@app.route("/notifications")
def notifications():

    if "user_id" not in session:

        return redirect(
            url_for("login")
        )
    # GET CURRENT USER NOTIFICATIONS
    connection = get_db_connection()

    cursor = connection.cursor(
        dictionary=True
    )

    cursor.execute(
        """
        SELECT *
        FROM notifications
        WHERE user_id = %s
        ORDER BY created_at DESC
        """,
        (session["user_id"],)
    )

    notifications = cursor.fetchall()
    # GET UNREAD NOTIFICATION COUNT
    cursor.execute(
        """
        SELECT COUNT(*) AS unread_count
        FROM notifications
        WHERE user_id = %s
        AND is_read = FALSE
        """,
        (session["user_id"],)
    )

    unread_result = cursor.fetchone()

    unread_count = unread_result["unread_count"]

    cursor.close()
    connection.close()
    # DISPLAY NOTIFICATIONS
    return render_template(
        "notifications.html",
        notifications=notifications,
        unread_count=unread_count
    )
# MARK NOTIFICATION AS READ
@app.route("/notifications/read/<int:notification_id>")
def mark_notification_read(notification_id):

    if "user_id" not in session:

        return redirect(
            url_for("login")
        )

    connection = get_db_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        UPDATE notifications
        SET is_read = TRUE
        WHERE id = %s
        AND user_id = %s
        """,
        (
            notification_id,
            session["user_id"]
        )
    )

    connection.commit()

    cursor.close()
    connection.close()

    return redirect(
        url_for("notifications")
    )
# REPORT FOUND ITEM
@app.route("/found-item", methods=["GET", "POST"])
def found_item():

    if "user_id" not in session:

        return redirect(
            url_for("login")
        )

    if request.method == "POST":
        # GET FORM DATA
        item_name = request.form["item_name"]

        category = request.form["category"]

        description = request.form["description"]

        color = request.form["color"]

        brand = request.form["brand"]

        found_date = request.form["found_date"] or None

        location = request.form["location"]

        latitude = request.form["latitude"] or None

        longitude = request.form["longitude"] or None
        # IMAGE UPLOAD
        image = request.files.get("image")

        image_path = None

        if (
            image
            and image.filename
            and allowed_file(image.filename)
        ):

            filename = secure_filename(
                image.filename
            )

            image.save(
                os.path.join(
                    app.config["UPLOAD_FOLDER"],
                    filename
                )
            )

            image_path = filename
        # DATABASE INSERT
        connection = get_db_connection()

        cursor = connection.cursor()

        cursor.execute(
            """
            INSERT INTO found_items
            (
                user_id,
                item_name,
                category,
                description,
                color,
                brand,
                found_date,
                location,
                latitude,
                longitude,
                image_path
            )
            VALUES
            (
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s
            )
            """,
            (
                session["user_id"],
                item_name,
                category,
                description,
                color,
                brand,
                found_date,
                location,
                latitude,
                longitude,
                image_path
            )
        )

        connection.commit()

        cursor.close()
        connection.close()

        return redirect(
            url_for("found_items")
        )

    return render_template(
        "found_item.html"
    )
# VIEW MY LOST ITEMS + SEARCH
@app.route("/lost-items")
def lost_items():
    # LOGIN REQUIRED
    if "user_id" not in session:

        return redirect(
            url_for("login")
        )

    search = request.args.get(
        "search",
        ""
    ).strip()

    connection = get_db_connection()

    cursor = connection.cursor(
        dictionary=True
    )
    # SEARCH ONLY MY LOST ITEMS
    if search:

        search_value = f"%{search}%"

        cursor.execute(
            """
            SELECT
                lost_items.*,
                users.name

            FROM lost_items

            JOIN users
            ON lost_items.user_id = users.id

            WHERE
                lost_items.user_id = %s
                AND
                (
                    lost_items.item_name LIKE %s
                    OR lost_items.category LIKE %s
                    OR lost_items.description LIKE %s
                    OR lost_items.color LIKE %s
                    OR lost_items.brand LIKE %s
                    OR lost_items.location LIKE %s
                )

            ORDER BY
                lost_items.created_at DESC
            """,
            (
                session["user_id"],
                search_value,
                search_value,
                search_value,
                search_value,
                search_value,
                search_value
            )
        )
    # SHOW ONLY MY LOST ITEMS
    else:

        cursor.execute(
            """
            SELECT
                lost_items.*,
                users.name

            FROM lost_items

            JOIN users
            ON lost_items.user_id = users.id

            WHERE
                lost_items.user_id = %s

            ORDER BY
                lost_items.created_at DESC
            """,
            (
                session["user_id"],
            )
        )

    items = cursor.fetchall()

    cursor.close()

    connection.close()

    return render_template(
        "lost_items.html",
        items=items,
        search=search
    )
# VIEW MY FOUND ITEMS + SEARCH
@app.route("/found-items")
def found_items():
    # LOGIN REQUIRED
    if "user_id" not in session:

        return redirect(
            url_for("login")
        )

    search = request.args.get(
        "search",
        ""
    ).strip()

    connection = get_db_connection()

    cursor = connection.cursor(
        dictionary=True
    )
    # SEARCH ONLY MY FOUND ITEMS
    if search:

        search_value = f"%{search}%"

        cursor.execute(
            """
            SELECT
                found_items.*,
                users.name

            FROM found_items

            JOIN users
            ON found_items.user_id = users.id

            WHERE
                found_items.user_id = %s
                AND
                (
                    found_items.item_name LIKE %s
                    OR found_items.category LIKE %s
                    OR found_items.description LIKE %s
                    OR found_items.color LIKE %s
                    OR found_items.brand LIKE %s
                    OR found_items.location LIKE %s
                )

            ORDER BY
                found_items.created_at DESC
            """,
            (
                session["user_id"],
                search_value,
                search_value,
                search_value,
                search_value,
                search_value,
                search_value
            )
        )
    # SHOW ONLY MY FOUND ITEMS
    else:

        cursor.execute(
            """
            SELECT
                found_items.*,
                users.name

            FROM found_items

            JOIN users
            ON found_items.user_id = users.id

            WHERE
                found_items.user_id = %s

            ORDER BY
                found_items.created_at DESC
            """,
            (
                session["user_id"],
            )
        )

    items = cursor.fetchall()

    cursor.close()

    connection.close()

    return render_template(
        "found_items.html",
        items=items,
        search=search
    )
# DELETE LOST ITEM
@app.route("/delete-lost-item/<int:item_id>", methods=["POST"])
def delete_lost_item(item_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute(
        """
        SELECT image_path FROM lost_items
        WHERE id = %s AND user_id = %s
        """,
        (item_id, session["user_id"])
    )

    item = cursor.fetchone()

    if not item:
        cursor.close()
        connection.close()
        return "Lost item not found or unauthorized", 404

    cursor.execute(
        """
        DELETE FROM lost_items
        WHERE id = %s AND user_id = %s
        """,
        (item_id, session["user_id"])
    )
    connection.commit()
    cursor.close()
    connection.close()

    if item.get("image_path"):
        image_path = os.path.join(
            app.config["UPLOAD_FOLDER"],
            item["image_path"]
        )
        if os.path.isfile(image_path):
            os.remove(image_path)

    return redirect(url_for("lost_items"))
# DELETE FOUND ITEM
@app.route("/delete-found-item/<int:item_id>", methods=["POST"])
def delete_found_item(item_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute(
        """
        SELECT image_path FROM found_items
        WHERE id = %s AND user_id = %s
        """,
        (item_id, session["user_id"])
    )

    item = cursor.fetchone()

    if not item:
        cursor.close()
        connection.close()
        return "Found item not found or unauthorized", 404

    cursor.execute(
        """
        DELETE FROM found_items
        WHERE id = %s AND user_id = %s
        """,
        (item_id, session["user_id"])
    )
    connection.commit()
    cursor.close()
    connection.close()

    if item.get("image_path"):
        image_path = os.path.join(
            app.config["UPLOAD_FOLDER"],
            item["image_path"]
        )
        if os.path.isfile(image_path):
            os.remove(image_path)

    return redirect(url_for("found_items"))
# PROFILE
@app.route("/profile")
def profile():

    if "user_id" not in session:

        return redirect(
            url_for("login")
        )

    connection = get_db_connection()

    cursor = connection.cursor(
        dictionary=True
    )

    user_id = session["user_id"]
    # GET USER DETAILS
    cursor.execute(
        """
        SELECT
            id,
            name,
            email,
            created_at
        FROM users
        WHERE id = %s
        """,
        (user_id,)
    )

    user = cursor.fetchone()
    # GET MY LOST ITEMS
    cursor.execute(
        """
        SELECT *
        FROM lost_items
        WHERE user_id = %s
        ORDER BY created_at DESC
        """,
        (user_id,)
    )

    lost_items = cursor.fetchall()
    # GET MY FOUND ITEMS
    cursor.execute(
        """
        SELECT *
        FROM found_items
        WHERE user_id = %s
        ORDER BY created_at DESC
        """,
        (user_id,)
    )

    found_items = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template(
        "profile.html",
        user=user,
        lost_items=lost_items,
        found_items=found_items
    )
# SETTINGS
@app.route("/settings")
def settings():

    if "user_id" not in session:
        return redirect(
            url_for("login")
        )

    return render_template(
        "settings.html"
    )
# PROFILE SETTINGS
@app.route("/profile-settings")
def profile_settings():

    if "user_id" not in session:
        return redirect(
            url_for("login")
        )

    connection = get_db_connection()

    cursor = connection.cursor(
        dictionary=True
    )

    cursor.execute(
        """
        SELECT
            id,
            name,
            email
        FROM users
        WHERE id = %s
        """,
        (session["user_id"],)
    )

    user = cursor.fetchone()

    cursor.close()
    connection.close()

    return render_template(
        "profile_settings.html",
        user=user
    )
# ACCOUNT & SECURITY
@app.route("/account-settings")
def account_settings():

    if "user_id" not in session:
        return redirect(
            url_for("login")
        )

    return render_template(
        "account_settings.html"
    )
# PRIVACY
@app.route("/privacy")
def privacy():

    if "user_id" not in session:
        return redirect(
            url_for("login")
        )

    return render_template(
        "privacy.html"
    )
# HELP & SUPPORT
@app.route("/help-support")
def help_support():

    if "user_id" not in session:
        return redirect(
            url_for("login")
        )

    return render_template(
        "help_support.html"
    )
# ABOUT
@app.route("/about")
def about():

    if "user_id" not in session:
        return redirect(
            url_for("login")
        )

    return render_template(
        "about.html"
    )
# RUN APPLICATION
if __name__ == "__main__":

    app.run(
        debug=True,
        port=5001
    )