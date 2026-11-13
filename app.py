from flask import (
    Flask,
    render_template,
    request,
    session,
    redirect,
    url_for,
    send_from_directory,
    jsonify
)
import os
import smtplib
from email.message import EmailMessage
from uuid import uuid4
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
app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev-only-change-this-secret")
if app.secret_key == "dev-only-change-this-secret":
    print("WARNING: Set FLASK_SECRET_KEY in your .env before production use.")


# IMAGE UPLOAD SETTINGS
UPLOAD_FOLDER = os.path.join(
    app.root_path,
    "uploads"
)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
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
    final_score,
    recipient_name=None,
    other_person_name=None,
    recipient_role="owner"
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
        phone_number = normalize_phone(str(phone_number))
        if not phone_number or len(phone_number) < 8:
            print("User phone number is invalid; SMS skipped.")
            return False
        client = Client(
            account_sid,
            auth_token
        )
        greeting = f"Hi {recipient_name}! " if recipient_name else "Hi! "
        other_name = other_person_name or "Another user"
        if recipient_role == "finder":
            sms_body = (
                f"{greeting}{other_name} has reported losing an item "
                f"('{lost_item_name}') that may match your found item "
                f"('{found_item_name}'). AI Match Score: {final_score}%. "
                "Please log in to Smart Lost & Found to review and verify "
                "the potential match. This is not yet confirmed."
            )
        else:
            sms_body = (
                f"{greeting}{other_name} has reported finding an item "
                f"('{found_item_name}') that may match your lost item "
                f"('{lost_item_name}'). AI Match Score: {final_score}%. "
                "Please log in to Smart Lost & Found to review and verify "
                "the potential match. This is not yet confirmed."
            )

        message = client.messages.create(
            body=sms_body,
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


# BUILD ONE CONSISTENT MATCH MESSAGE FOR ALL CHANNELS
def build_match_message(lost_item_name, found_item_name, final_score,
                        recipient_name=None, other_person_name=None,
                        recipient_role="owner"):
    greeting = f"Hi {recipient_name}! " if recipient_name else "Hi! "
    other_name = other_person_name or "Another user"
    if recipient_role == "finder":
        return (
            f"{greeting}{other_name} has reported losing an item "
            f"('{lost_item_name}') that may match your found item "
            f"('{found_item_name}'). AI Match Score: {final_score}%. "
            "Please log in to Smart Lost & Found to review and verify "
            "the potential match. This is not yet confirmed."
        )
    return (
        f"{greeting}{other_name} has reported finding an item "
        f"('{found_item_name}') that may match your lost item "
        f"('{lost_item_name}'). AI Match Score: {final_score}%. "
        "Please log in to Smart Lost & Found to review and verify "
        "the potential match. This is not yet confirmed."
    )


def send_match_email(email_address, lost_item_name, found_item_name,
                     final_score, recipient_name=None,
                     other_person_name=None, recipient_role="owner"):
    """Send an email if SMTP settings are configured; otherwise skip safely."""
    host = os.getenv("SMTP_HOST")
    username = os.getenv("SMTP_USERNAME")
    password = os.getenv("SMTP_PASSWORD")
    from_email = os.getenv("SMTP_FROM_EMAIL") or username
    port = int(os.getenv("SMTP_PORT", "587"))
    if not all((host, username, password, from_email)):
        print("Email not sent: SMTP settings are not configured.")
        return False
    if not email_address:
        print("Email not sent: recipient has no registered email address.")
        return False
    try:
        email = EmailMessage()
        email["Subject"] = "Smart Lost & Found: Potential item match"
        email["From"] = from_email
        email["To"] = email_address
        email.set_content(build_match_message(
            lost_item_name, found_item_name, final_score,
            recipient_name, other_person_name, recipient_role
        ))
        with smtplib.SMTP(host, port, timeout=20) as server:
            server.starttls()
            server.login(username, password)
            server.send_message(email)
        print(f"Match email sent to {email_address}.")
        return True
    except Exception as exc:
        print("Email sending error:", repr(exc))
        return False


def send_match_whatsapp(phone_number, lost_item_name, found_item_name,
                        final_score, recipient_name=None,
                        other_person_name=None, recipient_role="owner"):
    """Send WhatsApp through Twilio when WhatsApp sender credentials are configured."""
    account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN")
    whatsapp_sender = os.getenv("TWILIO_WHATSAPP_FROM")
    if not all((account_sid, auth_token, whatsapp_sender)):
        print("WhatsApp not sent: Twilio WhatsApp settings are not configured.")
        return False
    if not phone_number:
        print("WhatsApp not sent: recipient has no phone number.")
        return False
    try:
        normalized_phone = normalize_phone(str(phone_number))
        sender = whatsapp_sender if whatsapp_sender.startswith("whatsapp:") else f"whatsapp:{whatsapp_sender}"
        recipient = normalized_phone if normalized_phone.startswith("whatsapp:") else f"whatsapp:{normalized_phone}"
        client = Client(account_sid, auth_token)
        msg = client.messages.create(
            body=build_match_message(
                lost_item_name, found_item_name, final_score,
                recipient_name, other_person_name, recipient_role
            ),
            from_=sender,
            to=recipient
        )
        print(f"WhatsApp message accepted by Twilio. Message SID: {msg.sid}")
        return True
    except Exception as exc:
        print("WhatsApp sending error:", repr(exc))
        return False


def notify_match_channels(phone_number, email_address, lost_item_name,
                          found_item_name, final_score, recipient_name=None,
                          other_person_name=None, recipient_role="owner"):
    """Try each configured channel independently; in-app notification is stored separately."""
    send_match_sms(
        phone_number, lost_item_name, found_item_name, final_score,
        recipient_name=recipient_name,
        other_person_name=other_person_name,
        recipient_role=recipient_role
    )
    send_match_email(
        email_address, lost_item_name, found_item_name, final_score,
        recipient_name=recipient_name,
        other_person_name=other_person_name,
        recipient_role=recipient_role
    )
    send_match_whatsapp(
        phone_number, lost_item_name, found_item_name, final_score,
        recipient_name=recipient_name,
        other_person_name=other_person_name,
        recipient_role=recipient_role
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
    # API: FETCH LIVE NOTIFICATIONS
@app.route("/api/notifications")
def get_live_notifications():

    if "user_id" not in session:
        return jsonify({
            "success": False,
            "message": "Please login"
        }), 401

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT id, message
            FROM notifications
            WHERE user_id = %s
            ORDER BY created_at DESC
            """,
            (session["user_id"],)
        )

        notification_list = cursor.fetchall()

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

        return jsonify({
            "success": True,
            "unread_count": unread_result["unread_count"],
            "notifications": notification_list
        })

    finally:
        cursor.close()
        connection.close()


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

        phone = normalize_phone(country_code + phone_number)
        hashed_password = generate_password_hash(password)

        connection = get_db_connection()
        cursor = connection.cursor()

        try:
            cursor.execute(
                "SELECT id FROM users WHERE email = %s LIMIT 1",
                (email,)
            )
            existing_user = cursor.fetchone()
            if existing_user:
                return "An account with this email or phone number already exists.", 409

            cursor.execute(
                """
                INSERT INTO users (name, email, phone, password)
                VALUES (%s, %s, %s, %s)
                """,
                (name, email, phone, hashed_password)
            )
            connection.commit()
        except Exception as e:
            connection.rollback()
            print("Registration error:", repr(e))
            return "Registration failed. Please check your details and try again.", 400
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
        phone_login_value = normalize_phone(login_value) if not "@" in login_value else login_value

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        try:
            cursor.execute(
                """
                SELECT *
                FROM users
                WHERE email = %s OR phone = %s
                """,
                (login_value, phone_login_value)
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
            safe_name = secure_filename(image.filename)
            if not safe_name:
                return "Invalid image filename.", 400
            extension = safe_name.rsplit(".", 1)[1].lower()
            filename = f"{uuid4().hex}.{extension}"
            os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
            image.save(
                os.path.join(app.config["UPLOAD_FOLDER"], filename)
            )
            image_path = filename
        elif image and image.filename:
            return "Unsupported image type. Use PNG, JPG, JPEG, or GIF.", 400

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
            try:
                matching_results = match_lost_item(
                    lost_item_data,
                    radius_km=5
                ) or []
            except Exception as e:
                print("Lost-item matching error:", repr(e))
                matching_results = []

        # Notify the owners of found items returned by the matcher.
        # Avoid duplicate notifications/SMS for the same item pair.
        for result in matching_results:
            found_item_id = result.get("found_item_id")
            final_score = result.get("final_score", 0)
            if not found_item_id:
                print("Matcher result is missing found_item_id:", result)
                continue

            notify_connection = None
            notify_cursor = None
            try:
                notify_connection = get_db_connection()
                notify_cursor = notify_connection.cursor(dictionary=True)
                notify_cursor.execute(
                    """
                    SELECT
                        f.id, f.user_id, f.item_name,
                        finder.name AS finder_name,
                        finder.phone AS finder_phone,
                        finder.email AS finder_email,
                        owner.name AS owner_name
                    FROM found_items f
                    JOIN users finder ON finder.id = f.user_id
                    JOIN lost_items l ON l.id = %s
                    JOIN users owner ON owner.id = l.user_id
                    WHERE f.id = %s AND f.user_id != %s
                    """,
                    (lost_item_id, found_item_id, session["user_id"])
                )
                found_owner = notify_cursor.fetchone()
                if not found_owner:
                    continue

                notify_cursor.execute(
                    """
                    SELECT id FROM notifications
                    WHERE user_id = %s
                      AND related_lost_item_id = %s
                      AND related_found_item_id = %s
                    LIMIT 1
                    """,
                    (found_owner["user_id"], lost_item_id, found_item_id)
                )
                already_notified = notify_cursor.fetchone()
                if already_notified:
                    continue

                message = (
                    f"Potential match found: your found item '{found_owner['item_name']}' "
                    f"may match the lost item '{item_name}'. AI Match Score: {final_score}. "
                    "Please log in to review and verify the match."
                )
                notify_cursor.execute(
                    """ INSERT INTO notifications
                    (user_id,message,related_lost_item_id,related_found_item_id,final_score)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (found_owner["user_id"],message,lost_item_id,found_item_id,final_score
                    )
                )
                
            except Exception as e:
                if notify_connection:
                    try:
                        notify_connection.rollback()
                    except Exception:
                        pass
                print("Lost-item notification error:", repr(e))
            finally:
                if notify_cursor:
                    try:
                        notify_cursor.close()
                    except Exception:
                        pass
                if notify_connection:
                    try:
                        notify_connection.close()
                    except Exception:
                        pass

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
        return redirect(url_for("login"))

    matching_results = session.get("matching_results", []) or []
    lost_item_id = session.get("lost_item_id")
    lost_image = None
    lost_item_name = "Your reported item"

    if lost_item_id:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        try:
            cursor.execute(
                "SELECT image_path, item_name FROM lost_items WHERE id = %s AND user_id = %s",
                (lost_item_id, session["user_id"])
            )
            lost_item = cursor.fetchone()
            if not lost_item:
                return "You are not authorized to view these potential matches.", 403
            lost_image = lost_item.get("image_path")
            lost_item_name = lost_item.get("item_name") or lost_item_name
        finally:
            cursor.close()
            connection.close()

    for result in matching_results:
        # Match engines may use different score key names. Normalize it for the UI.
        score = result.get("final_score", result.get("match_score", result.get("score")))
        result["final_score"] = score
        result["lost_item_image"] = lost_image
        result["lost_item_name"] = lost_item_name
        result["found_item_image"] = None
        result["found_owner_name"] = None
        result["found_owner_id"] = None
        result["found_item_name"] = result.get("found_item_name") or result.get("item_name") or "Found item"

        found_item_id = result.get("found_item_id")
        if not found_item_id:
            continue

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        try:
            cursor.execute(
                """
                SELECT f.image_path, f.item_name, f.user_id, u.name AS owner_name
                FROM found_items f
                JOIN users u ON u.id = f.user_id
                WHERE f.id = %s
                """,
                (found_item_id,)
            )
            found_item = cursor.fetchone()
            if found_item:
                result["found_item_image"] = found_item.get("image_path")
                result["found_item_name"] = found_item.get("item_name") or result["found_item_name"]
                result["found_owner_name"] = found_item.get("owner_name")
                result["found_owner_id"] = found_item.get("user_id")
        finally:
            cursor.close()
            connection.close()

    return render_template(
        "match_results.html",
        matching_results=matching_results,
        lost_item_id=lost_item_id
    )


# VIEW A USER'S PUBLIC PROFILE FROM A POTENTIAL MATCH
@app.route("/user-profile/<int:profile_user_id>")
def view_user_profile(profile_user_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute(
            "SELECT id, name, created_at FROM users WHERE id = %s",
            (profile_user_id,)
        )
        profile_user = cursor.fetchone()
        if not profile_user:
            return "User profile not found", 404

        cursor.execute(
            """
            SELECT id, item_name, category, description, color, brand, location,
                   image_path, created_at
            FROM found_items
            WHERE user_id = %s
            ORDER BY created_at DESC
            """,
            (profile_user_id,)
        )
        found_items = cursor.fetchall()
    finally:
        cursor.close()
        connection.close()

    return render_template(
        "user_profile.html",
        profile_user=profile_user,
        found_items=found_items,
        match_score=request.args.get("match_score")
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
                finder.phone AS finder_phone,
                owner.email AS owner_email,
                finder.email AS finder_email,
                owner.name AS owner_name,
                finder.name AS finder_name
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

        # Only the lost-item owner can approve or reject.
        if user_id != owner_id:
            return "Only the lost-item owner can verify this match", 403

        if owner_id == finder_id:
            return "You cannot verify a match between your own items", 400

        cursor.execute(
            """
            SELECT id, verification_status, owner_approval
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

        already_confirmed = bool(
            match
            and match["verification_status"] == "confirmed"
            and match["owner_approval"] == "accepted"
        )

        if verification == "rejected":
            if match:
                cursor.execute(
                    """
                    UPDATE match_verifications
                    SET owner_approval = 'rejected',
                        verification_status = 'rejected'
                    WHERE id = %s
                    """,
                    (match["id"],)
                )
            else:
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
                    VALUES (%s, %s, %s, %s, 'rejected', 'rejected', 'pending')
                    """,
                    (lost_item_id, found_item_id, user_id, final_score)
                )

            connection.commit()
            return "Match rejected. Chat remains unavailable.", 200

        # Owner accepts: finder approval is not required.
        if not match:
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
                VALUES (%s, %s, %s, %s, 'confirmed', 'accepted', 'pending')
                """,
                (lost_item_id, found_item_id, user_id, final_score)
            )
        else:
            cursor.execute(
                """
                UPDATE match_verifications
                SET user_id = %s,
                    final_score = %s,
                    owner_approval = 'accepted',
                    verification_status = 'confirmed'
                WHERE id = %s
                """,
                (user_id, final_score, match["id"])
            )

        if not already_confirmed:
            owner_message = (
                f"Match confirmed: your lost item "
                f"'{parties['lost_item_name']}' matches the found item "
                f"'{parties['found_item_name']}'. "
                f"AI Match Score: {final_score}. "
                "Private chat is now available."
            )

            finder_message = (
                f"Match confirmed: your found item "
                f"'{parties['found_item_name']}' matches the lost item "
                f"'{parties['lost_item_name']}'. "
                f"AI Match Score: {final_score}. "
                "Private chat is now available."
            )

            cursor.execute(
    """
    INSERT INTO notifications
    (
        user_id,
        message,
        related_lost_item_id,
        related_found_item_id,
        final_score
    )
    VALUES (%s, %s, %s, %s, %s),
           (%s, %s, %s, %s, %s)
    """,
    (
        owner_id, owner_message, lost_item_id, found_item_id, final_score,
        finder_id, finder_message, lost_item_id, found_item_id, final_score
    )
)

        connection.commit()

        if not already_confirmed:
            notify_match_channels(
                parties["owner_phone"],
                parties.get("owner_email"),
                parties["lost_item_name"],
                parties["found_item_name"],
                final_score,
                recipient_name=parties.get("owner_name"),
                other_person_name=parties.get("finder_name"),
                recipient_role="owner"
            )

            notify_match_channels(
                parties["finder_phone"],
                parties.get("finder_email"),
                parties["lost_item_name"],
                parties["found_item_name"],
                final_score,
                recipient_name=parties.get("finder_name"),
                other_person_name=parties.get("owner_name"),
                recipient_role="finder"
            )

        return redirect(
            url_for(
                "private_chat",
                lost_item_id=lost_item_id,
                found_item_id=found_item_id
            )
        )

    except Exception:
        connection.rollback()
        raise

    finally:
        cursor.close()
        connection.close()



# PRIVATE CHAT

@app.route("/chat/<int:lost_item_id>/<int:found_item_id>")
def private_chat(lost_item_id, found_item_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT
                li.user_id AS owner_id,
                fi.user_id AS finder_id,
                owner.name AS owner_name,
                finder.name AS finder_name,
                mv.verification_status
            FROM lost_items li
            JOIN found_items fi ON fi.id = %s
            JOIN users owner ON owner.id = li.user_id
            JOIN users finder ON finder.id = fi.user_id
            JOIN match_verifications mv
                ON mv.lost_item_id = li.id
                AND mv.found_item_id = fi.id
            WHERE li.id = %s
            ORDER BY mv.id DESC
            LIMIT 1
            """,
            (found_item_id, lost_item_id)
        )

        match = cursor.fetchone()

        if not match:
            return "Match not found", 404

        if user_id not in (match["owner_id"], match["finder_id"]):
            return "You are not allowed to access this chat", 403

        if match["verification_status"] != "confirmed":
            return "Chat is available only after owner confirmation", 403

        other_person = (
            match["finder_name"]
            if user_id == match["owner_id"]
            else match["owner_name"]
        )

        return render_template(
            "chat.html",
            lost_item_id=lost_item_id,
            found_item_id=found_item_id,
            other_person=other_person
        )

    finally:
        cursor.close()
        connection.close()


@app.route("/api/chat/<int:lost_item_id>/<int:found_item_id>", methods=["GET"])
def get_chat_messages(lost_item_id, found_item_id):
    if "user_id" not in session:
        return jsonify({"success": False, "message": "Please login"}), 401

    user_id = session["user_id"]
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT li.user_id AS owner_id, fi.user_id AS finder_id
            FROM lost_items li
            JOIN found_items fi ON fi.id = %s
            JOIN match_verifications mv
                ON mv.lost_item_id = li.id
                AND mv.found_item_id = fi.id
            WHERE li.id = %s
              AND mv.verification_status = 'confirmed'
            ORDER BY mv.id DESC
            LIMIT 1
            """,
            (found_item_id, lost_item_id)
        )

        match = cursor.fetchone()

        if not match or user_id not in (match["owner_id"], match["finder_id"]):
            return jsonify({"success": False, "message": "Chat not available"}), 403

                # Mark messages received by the current user as read
        cursor.execute(
            """
            UPDATE chat_messages
            SET is_read = 1
            WHERE lost_item_id = %s
              AND found_item_id = %s
              AND receiver_id = %s
              AND is_read = 0
            """,
            (lost_item_id, found_item_id, user_id)
        )
        connection.commit()

        # Fetch all messages in this conversation
        cursor.execute(
            """
            SELECT
                id,
                sender_id,
                receiver_id,
                message,
                created_at,
                is_read
            FROM chat_messages
            WHERE lost_item_id = %s
              AND found_item_id = %s
              AND (
                  (sender_id = %s AND receiver_id = %s)
                  OR
                  (sender_id = %s AND receiver_id = %s)
              )
            ORDER BY created_at ASC, id ASC
            """,
            (
                lost_item_id, found_item_id,
                match["owner_id"], match["finder_id"],
                match["finder_id"], match["owner_id"]
            )
        )

        messages = cursor.fetchall()

        return jsonify({
            "success": True,
            "current_user_id": user_id,
            "messages": messages
        })

    finally:
        cursor.close()
        connection.close()


@app.route("/api/chat/<int:lost_item_id>/<int:found_item_id>", methods=["POST"])
def send_chat_message(lost_item_id, found_item_id):
    if "user_id" not in session:
        return jsonify({"success": False, "message": "Please login"}), 401

    user_id = session["user_id"]
    data = request.get_json(silent=True) or {}
    message = data.get("message", "").strip()

    if not message:
        return jsonify({"success": False, "message": "Message cannot be empty"}), 400

    if len(message) > 2000:
        return jsonify({"success": False, "message": "Message is too long"}), 400

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT li.user_id AS owner_id, fi.user_id AS finder_id
            FROM lost_items li
            JOIN found_items fi ON fi.id = %s
            JOIN match_verifications mv
                ON mv.lost_item_id = li.id
                AND mv.found_item_id = fi.id
            WHERE li.id = %s
              AND mv.verification_status = 'confirmed'
            ORDER BY mv.id DESC
            LIMIT 1
            """,
            (found_item_id, lost_item_id)
        )

        match = cursor.fetchone()

        if not match or user_id not in (match["owner_id"], match["finder_id"]):
            return jsonify({"success": False, "message": "Chat not available"}), 403

        receiver_id = (
            match["finder_id"]
            if user_id == match["owner_id"]
            else match["owner_id"]
        )

        cursor.execute(
            """
            INSERT INTO chat_messages
            (lost_item_id, found_item_id, sender_id, receiver_id, message)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (lost_item_id, found_item_id, user_id, receiver_id, message)
        )

        cursor.execute(
            """
            INSERT INTO notifications
            (
                user_id,
                message,
                related_lost_item_id,
                related_found_item_id,
                final_score
            )
            VALUES (%s, %s, %s, %s, %s)
            """,
            (
                receiver_id,
                "You received a new chat message.",
                lost_item_id,
                found_item_id,
                None
            )
        )

        connection.commit()

        return jsonify({"success": True, "message": "Message sent"})

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
            n.final_score,
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
            l.user_id AS owner_id,
            f.id AS found_id,
            f.user_id AS finder_id,
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
        match=match,
        current_user_id=session["user_id"]
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
            safe_name = secure_filename(image.filename)
            if not safe_name:
                return "Invalid image filename.", 400
            extension = safe_name.rsplit(".", 1)[1].lower()
            filename = f"{uuid4().hex}.{extension}"
            os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
            image.save(
                os.path.join(app.config["UPLOAD_FOLDER"], filename)
            )
            image_path = filename
        elif image and image.filename:
            return "Unsupported image type. Use PNG, JPG, JPEG, or GIF.", 400

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
                    ) or []
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
                                related_found_item_id,
                                final_score
                                )
                                VALUES (%s, %s, %s, %s, %s)
                                """,
                                (
                                    lost_item_data["user_id"],
                                    message,
                                    lost_item_data["id"],
                                    found_item_id,
                                    final_score
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
                                SELECT name, phone, email
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
                                # Fetch the name of the person who reported finding it.
                                finder_connection = get_db_connection()
                                finder_cursor = finder_connection.cursor(dictionary=True)
                                finder_cursor.execute(
                                    "SELECT name, email FROM users WHERE id = %s",
                                    (session["user_id"],)
                                )
                                finder_data = finder_cursor.fetchone()
                                finder_cursor.close()
                                finder_connection.close()
                                
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
# =========================================================
# FETCH THE OTHER PERSON'S PROFILE FOR A MATCH
# =========================================================

@app.route(
    "/api/match-profile/<int:lost_item_id>/<int:found_item_id>",
    methods=["GET"]
)
def get_match_profile():

    # 1. User must be logged in
    if "user_id" not in session:
        return jsonify({
            "success": False,
            "message": "Please log in first."
        }), 401

    current_user_id = session["user_id"]

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        # 2. Check that the lost and found items exist
        #    and identify their respective owners.

        cursor.execute(
            """
            SELECT
                li.id AS lost_item_id,
                li.user_id AS owner_id,
                fi.id AS found_item_id,
                fi.user_id AS finder_id
            FROM lost_items li
            JOIN found_items fi
                ON fi.id = %s
            WHERE li.id = %s
            """,
            (
                found_item_id,
                lost_item_id
            )
        )

        match_items = cursor.fetchone()

        if not match_items:
            return jsonify({
                "success": False,
                "message": "Lost or found item not found."
            }), 404

        owner_id = match_items["owner_id"]
        finder_id = match_items["finder_id"]

        # 3. Only the owner or finder can access
        #    the other person's profile.

        if current_user_id not in (owner_id, finder_id):
            return jsonify({
                "success": False,
                "message": "You are not allowed to view this profile."
            }), 403

        if owner_id == finder_id:
            return jsonify({
                "success": False,
                "message": "These items belong to the same user."
            }), 400

        # 4. Identify the OTHER person dynamically.
        if current_user_id == owner_id:
            other_user_id = finder_id
        else:
            other_user_id = owner_id

        # 5. Check whether both users have confirmed the match.
        cursor.execute(
            """
            SELECT
                owner_approval,
                finder_approval,
                verification_status
            FROM match_verifications
            WHERE lost_item_id = %s
              AND found_item_id = %s
            ORDER BY id DESC
            LIMIT 1
            """,
            (
                lost_item_id,
                found_item_id
            )
        )

        verification = cursor.fetchone()

        match_confirmed = bool(
            verification
            and verification["verification_status"] == "confirmed"
            and verification["owner_approval"] == "accepted"
            and verification["finder_approval"] == "accepted"
        )

        # 6. Fetch the other person's profile from MySQL.
        #    Never fetch the password.

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
            (other_user_id,)
        )

        person = cursor.fetchone()

        if not person:
            return jsonify({
                "success": False,
                "message": "User profile not found."
            }), 404

        # 7. Return basic profile information.
        profile = {
            "id": person["id"],
            "name": person["name"],
            "created_at": (
                str(person["created_at"])
                if person["created_at"]
                else None
            )
        }

        # Share email only after both people confirm the match.
        if match_confirmed:
            profile["email"] = person["email"]

        return jsonify({
            "success": True,
            "match_confirmed": match_confirmed,
            "profile": profile
        }), 200

    except Exception as error:
        print("Error fetching match profile:", error)

        return jsonify({
            "success": False,
            "message": "Unable to fetch the profile."
        }), 500

    finally:
        cursor.close()
        connection.close()

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
        name = request.form["name"].strip()
        email = request.form["email"].strip()
        phone = normalize_phone(request.form["phone"].strip())
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
    debug_mode = os.getenv("FLASK_DEBUG", "false").strip().lower() == "true"
    port = int(os.getenv("PORT", "5001"))
    app.run(debug=debug_mode, port=port)