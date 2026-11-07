
document.addEventListener("DOMContentLoaded", function () {

    let lastNotificationId = null;

    // Create popup container
    const popup = document.createElement("div");
    popup.id = "live-notification-popup";
    document.body.appendChild(popup);

    // Add popup styling
    const style = document.createElement("style");

    style.textContent = `
        #live-notification-popup {
            position: fixed;
            top: 85px;
            right: 20px;
            width: 330px;
            max-width: calc(100% - 40px);
            background: white;
            padding: 20px;
            border-radius: 12px;
            box-shadow: 0 5px 25px rgba(0,0,0,0.2);
            border-left: 5px solid #2563eb;
            z-index: 9999;
            display: none;
        }

        #live-notification-popup h3 {
            margin: 0 0 10px;
            color: #2563eb;
        }

        #live-notification-popup p {
            color: #475569;
            line-height: 1.5;
            margin-bottom: 15px;
        }

        #live-notification-popup a {
            color: #2563eb;
            font-weight: bold;
            text-decoration: none;
        }

        #live-notification-popup button {
            float: right;
            border: none;
            background: none;
            font-size: 20px;
            cursor: pointer;
        }
    `;

    document.head.appendChild(style);

    // Show notification popup
    function showPopup(notification) {

        popup.innerHTML = `
            <button id="close-notification-popup">×</button>
            <h3>🔔 New Match Notification!</h3>
            <p>${escapeHTML(notification.message)}</p>
            <a href="/notifications/read/${notification.id}">
                View Notification →
            </a>
        `;

        popup.style.display = "block";

        document.getElementById(
            "close-notification-popup"
        ).addEventListener("click", function () {
            popup.style.display = "none";
        });
    }

    // Prevent HTML injection in notification messages
    function escapeHTML(value) {
        const element = document.createElement("div");
        element.textContent = value || "";
        return element.innerHTML;
    }

    // Fetch notifications from Flask
    async function checkNotifications() {

        try {

            const response = await fetch("/api/notifications");

            if (!response.ok) return;

            const data = await response.json();

            if (!data.success) return;

            // Update navbar unread badge
            let badge = document.querySelector(
                ".notification-badge"
            );

            if (data.unread_count > 0) {

                if (!badge) {

                    const icon = document.querySelector(
                        ".notification-icon"
                    );

                    if (icon) {
                        badge = document.createElement("span");
                        badge.className = "notification-badge";
                        icon.appendChild(badge);
                    }
                }

                if (badge) {
                    badge.textContent = data.unread_count;
                }

            } else if (badge) {
                badge.remove();
            }

            if (!data.notifications.length) {
                if (lastNotificationId === null) {
                    lastNotificationId = 0;
                }
                return;
            }

            const latest = data.notifications[0];

            // First check establishes the starting point.
            if (lastNotificationId === null) {
                lastNotificationId = latest.id;
                return;
            }

            // Show popup only for a genuinely newer notification.
            if (latest.id > lastNotificationId) {
                lastNotificationId = latest.id;
                showPopup(latest);
            }

        } catch (error) {
            console.error("Notification error:", error);
        }
    }

    // Check immediately and then every 5 seconds
    checkNotifications();

    setInterval(checkNotifications, 5000);

});
