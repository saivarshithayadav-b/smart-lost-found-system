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
from dotenv import load_dotenv
from twilio.rest import Client
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from database import get_db_connection


# AI MATCHING PIPELINE
from matching.database_matching import match_lost_item


# FLASK APPLICATION
app = Flask(__name__)
load_dotenv()
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


# SEND SMS MATCH ALERT
def send_match_sms(
    phone_number,
    lost_item_name,
    found_item_name,
    final_score
):
    try:
        account_sid = os.getenv(
            "TWILIO_ACCOUNT_SID"
        )
        auth_token = os.getenv(
            "TWILIO_AUTH_TOKEN"
        )
        twilio_phone_number = os.getenv(
            "TWILIO_PHONE_NUMBER"
        )
        if (
            not account_sid
            or not auth_token
            or not twilio_phone_number
        ):
            print(
                "Twilio credentials are not configured."
            )
            return False
        if not phone_number:
            print(
                "User does not have a phone number."
            )
            return False
        client = Client(
            account_sid,
            auth_token
        )
        message = client.messages.create(
            body=(
                "Smart Lost & Found Alert: "
                f"A potential match was found for your lost item "
                f"'{lost_item_name}' with found item "
                f"'{found_item_name}'. "
                f"AI Match Score: {final_score}. "
                "Please log in to verify the match."
            ),
            from_=twilio_phone_number,
            to=phone_number
        )
        print(
            "SMS sent successfully. "
            f"Message SID: {message.sid}"
        )
        return True
    except Exception as e:
        print(
            "SMS sending error:",
            e
        )
        return False


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


# NORMALIZE PHONE NUMBER
def normalize_phone(phone):
    phone = phone.strip()
    if phone.startswith("0"):
        phone = "+91" + phone[1:]
    elif phone.startswith("91") and not phone.startswith("+"):
        phone = "+" + phone
    elif not phone.startswith("+"):
        phone = "+91" + phone
    return phone


# REGISTER
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"].strip()
        email = request.form["email"].strip()
        country_code = request.form["country_code"]
        phone_number = request.form["phone"].strip()
        password = request.form["password"]

        if not phone_number.isdigit() or len(phone_number) != 10:
            return "Please enter a valid 10-digit phone number.", 400

        phone = country_code + phone_number
        hashed_password = generate_password_hash(password)

        connection = get_db_connection()
        cursor = connection.cursor()

        try:
            cursor.execute(
                """
                INSERT INTO users (name, email, phone, password)
                VALUES (%s, %s, %s, %s)
                """,
                (name, email, phone, hashed_password)
            )
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            cursor.close()
            connection.close()

        return redirect(url_for("login"))

    return render_template("register.html")
# LOGIN
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        login_value = request.form["email"].strip()
        password = request.form["password"]

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        try:
            cursor.execute(
                """
                SELECT *
                FROM users
                WHERE email = %s OR phone = %s
                """,
                (login_value, login_value)
            )
            user = cursor.fetchone()
        finally:
            cursor.close()
            connection.close()

        if user:
            stored_password = user["password"]

            if stored_password.startswith(("scrypt:", "pbkdf2:")):
                password_valid = check_password_hash(
                    stored_password, password
                )
            else:
                password_valid = stored_password == password

            if password_valid:
                session["user_id"] = user["id"]
                session["name"] = user["name"]
                return redirect(url_for("home"))

        return "Invalid email/phone number or password"

    return render_template("login.html")

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

        # PRIVATE OWNERSHIP VERIFICATION DETAILS
        verification_0 = request.form.get(
            "verification_0"
        )
        verification_1 = request.form.get(
            "verification_1"
        )
        verification_2 = request.form.get(
            "verification_2"
        )
        verification_3 = request.form.get(
            "verification_3"
        )

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
                image_path,
                verification_0,
                verification_1,
                verification_2,
                verification_3
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
                image_path,
                verification_0,
                verification_1,
                verification_2,
                verification_3
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
        return redirect(url_for("login"))

    verification = request.form.get("verification")
    found_item_id = request.form.get("found_item_id")
    final_score = request.form.get("final_score")
    lost_item_id = session.get("lost_item_id")
    user_id = session.get("user_id")

    if verification not in ("confirmed", "rejected"):
        return "Invalid verification status", 400
    if not found_item_id:
        return "Found item ID is missing", 400
    if final_score is None or final_score == "":
        return "Final score is missing", 400
    if not lost_item_id:
        return "Lost item ID is missing", 400

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        # Fetch both parties and the item details for this potential match.
        cursor.execute(
            """
            SELECT
                li.id AS lost_id,
                li.user_id AS owner_id,
                li.item_name AS lost_item_name,
                fi.id AS found_id,
                fi.user_id AS finder_id,
                fi.item_name AS found_item_name,
                owner.phone AS owner_phone,
                finder.phone AS finder_phone
            FROM lost_items li
            JOIN found_items fi ON fi.id = %s
            JOIN users owner ON owner.id = li.user_id
            JOIN users finder ON finder.id = fi.user_id
            WHERE li.id = %s
            """,
            (found_item_id, lost_item_id)
        )
        parties = cursor.fetchone()

        if not parties:
            return "Lost or found item not found", 404

        owner_id = parties["owner_id"]
        finder_id = parties["finder_id"]

        if user_id not in (owner_id, finder_id):
            return "You are not allowed to verify this match", 403

        if owner_id == finder_id:
            return "You cannot verify a match between your own items", 400

        # The current user's approval is stored in the correct column.
        approval_column = (
            "owner_approval" if user_id == owner_id else "finder_approval"
        )
        approval_value = "accepted" if verification == "confirmed" else "rejected"

        # Find an existing verification row for this pair.
        cursor.execute(
            """
            SELECT id, verification_status, owner_approval, finder_approval
            FROM match_verifications
            WHERE lost_item_id = %s AND found_item_id = %s
            ORDER BY id DESC
            LIMIT 1
            """,
            (lost_item_id, found_item_id)
        )
        match = cursor.fetchone()

        if match and match["verification_status"] == "rejected":
            return "This match has already been rejected", 400

        already_fully_approved = bool(
            match
            and match["verification_status"] == "confirmed"
            and match["owner_approval"] == "accepted"
            and match["finder_approval"] == "accepted"
        )

        if not match:
            owner_approval = (
                approval_value if user_id == owner_id else "pending"
            )
            finder_approval = (
                approval_value if user_id == finder_id else "pending"
            )
            status = "rejected" if verification == "rejected" else "pending"

            cursor.execute(
                """
                INSERT INTO match_verifications
                (
                    lost_item_id,
                    found_item_id,
                    user_id,
                    final_score,
                    verification_status,
                    owner_approval,
                    finder_approval
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    lost_item_id,
                    found_item_id,
                    user_id,
                    final_score,
                    status,
                    owner_approval,
                    finder_approval
                )
            )
            match_id = cursor.lastrowid

            if verification == "rejected":
                connection.commit()
                return "Match rejected. Chat remains unavailable.", 200
        else:
            match_id = match["id"]
            if verification == "rejected":
                cursor.execute(
                    f"""
                    UPDATE match_verifications
                    SET {approval_column} = 'rejected',
                        verification_status = 'rejected'
                    WHERE id = %s
                    """,
                    (match_id,)
                )
                connection.commit()
                return "Match rejected. Chat remains unavailable.", 200

            cursor.execute(
                f"""
                UPDATE match_verifications
                SET {approval_column} = 'accepted'
                WHERE id = %s
                """,
                (match_id,)
            )

        # Read the saved approvals after this user's decision.
        cursor.execute(
            """
            SELECT owner_approval, finder_approval, verification_status
            FROM match_verifications
            WHERE id = %s
            """,
            (match_id,)
        )
        approvals = cursor.fetchone()

        both_accepted = (
            approvals["owner_approval"] == "accepted"
            and approvals["finder_approval"] == "accepted"
        )

        if both_accepted:
            cursor.execute(
                """
                UPDATE match_verifications
                SET verification_status = 'confirmed'
                WHERE id = %s
                """,
                (match_id,)
            )

            if not already_fully_approved:
                score_for_message = final_score

                # Notify both users only after both independently approve.
                owner_message = (
                    f"Match confirmed: your lost item "
                    f"'{parties['lost_item_name']}' matches the found item "
                    f"'{parties['found_item_name']}'. "
                    f"AI Match Score: {score_for_message}. "
                    "You may now continue through the app."
                )
                finder_message = (
                    f"Match confirmed: your found item "
                    f"'{parties['found_item_name']}' matches the lost item "
                    f"'{parties['lost_item_name']}'. "
                    f"AI Match Score: {score_for_message}. "
                    "You may now continue through the app."
                )

                cursor.execute(
                    """
                    INSERT INTO notifications
                    (
                        user_id, message,
                        related_lost_item_id, related_found_item_id
                    )
                    VALUES (%s, %s, %s, %s), (%s, %s, %s, %s)
                    """,
                    (
                        owner_id, owner_message, lost_item_id, found_item_id,
                        finder_id, finder_message, lost_item_id, found_item_id
                    )
                )

        connection.commit()

        if both_accepted and not already_fully_approved:
            # Send the SMS alerts after the database transaction is committed.
            send_match_sms(
                parties["owner_phone"],
                parties["lost_item_name"],
                parties["found_item_name"],
                final_score
            )
            send_match_sms(
                parties["finder_phone"],
                parties["lost_item_name"],
                parties["found_item_name"],
                final_score
            )
            return (
                "Both users accepted. The match is confirmed and SMS alerts "
                "were attempted for both users.",
                200
            )

        if both_accepted:
            return "Both users have already accepted this match.", 200

        return "Your approval has been saved. Waiting for the other user.", 200

    except Exception:
        connection.rollback()
        raise

    finally:
        cursor.close()
        connection.close()


# NOTIFICATIONS
@app.route("/notifications")
def notifications():
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
        SELECT *
        FROM notifications
        WHERE user_id = %s
        ORDER BY created_at DESC
        """,
        (session["user_id"],)
    )
    notifications = cursor.fetchall()
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
    cursor = connection.cursor(
        dictionary=True
    )

    # GET NOTIFICATION DETAILS
    cursor.execute(
        """
        SELECT
            id,
            related_lost_item_id,
            related_found_item_id
        FROM notifications
        WHERE id = %s
        AND user_id = %s
        """,
        (
            notification_id,
            session["user_id"]
        )
    )
    notification = cursor.fetchone()
    if not notification:
        cursor.close()
        connection.close()
        return "Notification not found", 404

    # MARK AS READ
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

    # IF THIS IS A MATCH NOTIFICATION
    if (
        notification["related_lost_item_id"]
        and notification["related_found_item_id"]
    ):
        session["lost_item_id"] = (
            notification["related_lost_item_id"]
        )
        return redirect(
            url_for(
                "notification_match",
                notification_id=notification_id
            )
        )

    # NORMAL NOTIFICATION
    return redirect(
        url_for("notifications")
    )


# NOTIFICATION MATCH DETAILS
@app.route("/notification-match/<int:notification_id>")
def notification_match(notification_id):
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
            n.id AS notification_id,
            n.message,
            n.related_lost_item_id,
            n.related_found_item_id,
            l.id AS lost_id,
            l.item_name AS lost_item_name,
            l.category AS lost_category,
            l.description AS lost_description,
            l.color AS lost_color,
            l.brand AS lost_brand,
            l.lost_date,
            l.location AS lost_location,
            l.image_path AS lost_image,
            f.id AS found_id,
            f.item_name AS found_item_name,
            f.category AS found_category,
            f.description AS found_description,
            f.color AS found_color,
            f.brand AS found_brand,
            f.found_date,
            f.location AS found_location,
            f.image_path AS found_image
        FROM notifications n
        LEFT JOIN lost_items l
            ON n.related_lost_item_id = l.id
        LEFT JOIN found_items f
            ON n.related_found_item_id = f.id
        WHERE n.id = %s
        AND n.user_id = %s
        """,
        (
            notification_id,
            session["user_id"]
        )
    )
    match = cursor.fetchone()
    cursor.close()
    connection.close()
    if not match:
        return "Match notification not found", 404

    # RENDER THE MATCH PAGE
    return render_template(
        "notification_match.html",
        match=match
    )


# REPORT FOUND ITEM
@app.route("/found-item", methods=["GET", "POST"])
def found_item():
    if "user_id" not in session:
        return redirect(
            url_for("login")
        )
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
        found_item_id = cursor.lastrowid
        cursor.close()
        connection.close()

        # ---------------------------------------------------------
        # CHECK NEW FOUND ITEM AGAINST EXISTING LOST ITEMS
        # ---------------------------------------------------------
        if (
            latitude is not None
            and longitude is not None
        ):
            connection = get_db_connection()
            cursor = connection.cursor(
                dictionary=True
            )
            cursor.execute(
                """
                SELECT *
                FROM lost_items
                WHERE user_id != %s
                AND latitude IS NOT NULL
                AND longitude IS NOT NULL
                """,
                (
                    session["user_id"],
                )
            )
            existing_lost_items = cursor.fetchall()
            cursor.close()
            connection.close()

            # Run the existing matching pipeline for
            # every existing lost item.
            for lost_item_data in existing_lost_items:
                try:
                    matching_results = match_lost_item(
                        lost_item_data,
                        radius_km=5
                    )
                    for result in matching_results:
                        if str(
                            result.get("found_item_id")
                        ) == str(found_item_id):
                            final_score = result.get(
                                "final_score",
                                0
                            )
                            message = (
                                f"Potential match found "
                                f"for your lost item "
                                f"'{lost_item_data['item_name']}' "
                                f"with found item "
                                f"'{item_name}'. "
                                f"AI Match Score: "
                                f"{final_score}"
                            )
                            connection = get_db_connection()
                            cursor = connection.cursor()
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
                                    lost_item_data["user_id"],
                                    message,
                                    lost_item_data["id"],
                                    found_item_id
                                )
                            )
                            connection.commit()
                            cursor.close()
                            connection.close()

                            # SEND SMS ALERT TO LOST ITEM OWNER
                            connection = get_db_connection()
                            cursor = connection.cursor(
                                dictionary=True
                            )
                            cursor.execute(
                                """
                                SELECT phone
                                FROM users
                                WHERE id = %s
                                """,
                                (
                                    lost_item_data["user_id"],
                                )
                            )
                            lost_item_owner = cursor.fetchone()
                            cursor.close()
                            connection.close()
                            if (
                                lost_item_owner
                                and lost_item_owner["phone"]
                            ):
                                send_match_sms(
                                    lost_item_owner["phone"],
                                    lost_item_data["item_name"],
                                    item_name,
                                    final_score
                                )
                except Exception as e:
                    print(
                        "Matching error:",
                        e
                    )
        return redirect(
            url_for("found_items")
        )
    return render_template(
        "found_item.html"
    )


# VIEW MY LOST ITEMS + SEARCH
@app.route("/lost-items")
def lost_items():
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
        return redirect(
            url_for("login")
        )
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
            item_id,
            session["user_id"]
        )
    )
    item = cursor.fetchone()
    if not item:
        cursor.close()
        connection.close()
        return "Lost item not found or unauthorized", 404
    cursor.execute(
        """
        DELETE FROM lost_items
        WHERE id = %s
        AND user_id = %s
        """,
        (
            item_id,
            session["user_id"]
        )
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
    return redirect(
        url_for("lost_items")
    )


# DELETE FOUND ITEM
@app.route("/delete-found-item/<int:item_id>", methods=["POST"])
def delete_found_item(item_id):
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
        SELECT image_path
        FROM found_items
        WHERE id = %s
        AND user_id = %s
        """,
        (
            item_id,
            session["user_id"]
        )
    )
    item = cursor.fetchone()
    if not item:
        cursor.close()
        connection.close()
        return "Found item not found or unauthorized", 404
    cursor.execute(
        """
        DELETE FROM found_items
        WHERE id = %s
        AND user_id = %s
        """,
        (
            item_id,
            session["user_id"]
        )
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
    return redirect(
        url_for("found_items")
    )


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
@app.route("/profile-settings", methods=["GET", "POST"])
def profile_settings():
    if "user_id" not in session:
        return redirect(url_for("login"))
    connection = get_db_connection()
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        phone = request.form["phone"]
        cursor = connection.cursor()
        cursor.execute(
            """
            UPDATE users
            SET
                name = %s,
                email = %s,
                phone = %s
            WHERE id = %s
            """,
            (
                name,
                email,
                phone,
                session["user_id"]
            )
        )
        connection.commit()
        cursor.close()
        connection.close()
        session["name"] = name
        return redirect(url_for("profile_settings"))
    cursor = connection.cursor(dictionary=True)
    cursor.execute(
        """
        SELECT
            id,
            name,
            email,
            phone
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