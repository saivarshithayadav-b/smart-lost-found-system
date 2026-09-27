from flask import Flask, render_template, request, session, redirect, url_for, send_from_directory
import os
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from database import get_db_connection


app = Flask(__name__)

app.secret_key = "lost-found-secret-key"


# =========================================================
# IMAGE UPLOAD SETTINGS
# =========================================================

UPLOAD_FOLDER = os.path.join(app.root_path, "uploads")

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}


def allowed_file(filename):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS
    )


# =========================================================
# SERVE UPLOADED IMAGES
# =========================================================

@app.route("/uploads/<filename>")
def uploaded_file(filename):

    return send_from_directory(
        app.config["UPLOAD_FOLDER"],
        filename
    )


# =========================================================
# HOME
# =========================================================

@app.route("/")
def home():

    return render_template("index.html")


# =========================================================
# REGISTER
# =========================================================

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]

        hashed_password = generate_password_hash(password)

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

        return redirect(url_for("login"))

    return render_template("register.html")


# =========================================================
# LOGIN
# =========================================================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

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

            return redirect(url_for("home"))

        return "Invalid email or password"

    return render_template("login.html")


# =========================================================
# LOGOUT
# =========================================================

@app.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("home"))


# =========================================================
# REPORT LOST ITEM
# =========================================================

@app.route("/lost-item", methods=["GET", "POST"])
def lost_item():

    if "user_id" not in session:

        return redirect(url_for("login"))

    if request.method == "POST":

        item_name = request.form["item_name"]

        category = request.form["category"]

        description = request.form["description"]

        color = request.form["color"]

        brand = request.form["brand"]

        lost_date = request.form["lost_date"] or None

        location = request.form["location"]

        latitude = request.form["latitude"] or None

        longitude = request.form["longitude"] or None


        # -------------------------------------------------
        # IMAGE UPLOAD
        # -------------------------------------------------

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


        # -------------------------------------------------
        # DATABASE INSERT
        # -------------------------------------------------

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

        cursor.close()
        connection.close()

        return redirect(
            url_for("lost_items")
        )

    return render_template(
        "lost_item.html"
    )


# =========================================================
# REPORT FOUND ITEM
# =========================================================

@app.route("/found-item", methods=["GET", "POST"])
def found_item():

    if "user_id" not in session:

        return redirect(url_for("login"))

    if request.method == "POST":

        item_name = request.form["item_name"]

        category = request.form["category"]

        description = request.form["description"]

        color = request.form["color"]

        brand = request.form["brand"]

        found_date = request.form["found_date"] or None

        location = request.form["location"]

        latitude = request.form["latitude"] or None

        longitude = request.form["longitude"] or None


        # -------------------------------------------------
        # IMAGE UPLOAD
        # -------------------------------------------------

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


        # -------------------------------------------------
        # DATABASE INSERT
        # -------------------------------------------------

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


# =========================================================
# VIEW LOST ITEMS + SEARCH
# =========================================================

@app.route("/lost-items")
def lost_items():

    search = request.args.get(
        "search",
        ""
    ).strip()

    connection = get_db_connection()

    cursor = connection.cursor(
        dictionary=True
    )


    # -----------------------------------------------------
    # SEARCH
    # -----------------------------------------------------

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
                lost_items.item_name LIKE %s
                OR lost_items.category LIKE %s
                OR lost_items.description LIKE %s
                OR lost_items.color LIKE %s
                OR lost_items.brand LIKE %s
                OR lost_items.location LIKE %s

            ORDER BY
                lost_items.created_at DESC
            """,
            (
                search_value,
                search_value,
                search_value,
                search_value,
                search_value,
                search_value
            )
        )


    # -----------------------------------------------------
    # SHOW ALL ITEMS
    # -----------------------------------------------------

    else:

        cursor.execute(
            """
            SELECT
                lost_items.*,
                users.name

            FROM lost_items

            JOIN users
            ON lost_items.user_id = users.id

            ORDER BY
                lost_items.created_at DESC
            """
        )


    items = cursor.fetchall()

    cursor.close()

    connection.close()


    return render_template(
        "lost_items.html",
        items=items,
        search=search
    )


# =========================================================
# VIEW FOUND ITEMS + SEARCH
# =========================================================

@app.route("/found-items")
def found_items():

    search = request.args.get(
        "search",
        ""
    ).strip()

    connection = get_db_connection()

    cursor = connection.cursor(
        dictionary=True
    )


    # -----------------------------------------------------
    # SEARCH
    # -----------------------------------------------------

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
                found_items.item_name LIKE %s
                OR found_items.category LIKE %s
                OR found_items.description LIKE %s
                OR found_items.color LIKE %s
                OR found_items.brand LIKE %s
                OR found_items.location LIKE %s

            ORDER BY
                found_items.created_at DESC
            """,
            (
                search_value,
                search_value,
                search_value,
                search_value,
                search_value,
                search_value
            )
        )


    # -----------------------------------------------------
    # SHOW ALL ITEMS
    # -----------------------------------------------------

    else:

        cursor.execute(
            """
            SELECT
                found_items.*,
                users.name

            FROM found_items

            JOIN users
            ON found_items.user_id = users.id

            ORDER BY
                found_items.created_at DESC
            """
        )


    items = cursor.fetchall()

    cursor.close()

    connection.close()


    return render_template(
        "found_items.html",
        items=items,
        search=search
    )


# =========================================================
# RUN APPLICATION
# =========================================================

if __name__ == "__main__":

    app.run(
        debug=True,
        port=5001
    )