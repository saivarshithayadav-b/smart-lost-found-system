
const lostItemId = document.body.dataset.lostItemId;
const foundItemId = document.body.dataset.foundItemId;

const messagesDiv = document.getElementById("messages");
const messageInput = document.getElementById("message-input");
const sendButton = document.getElementById("send-button");

const apiUrl = `/api/chat/${lostItemId}/${foundItemId}`;

async function loadMessages() {
    try {
        const response = await fetch(apiUrl);
        const data = await response.json();

        if (!response.ok || !data.success) {
            messagesDiv.textContent = "Unable to load messages.";
            return;
        }

        messagesDiv.replaceChildren();

        data.messages.forEach(message => {
            const messageBox = document.createElement("div");
            messageBox.className = "message";

            const isMine =
                Number(message.sender_id) === Number(data.current_user_id);

            if (isMine) {
                messageBox.classList.add("mine");
            }

            // Sender name
            const sender = document.createElement("div");
            sender.className = "sender";
            sender.textContent = isMine ? "You" : "Other person";

            // Message text
            const messageText = document.createElement("div");
            messageText.textContent = message.message;

            // Timestamp
            const time = document.createElement("div");
            time.className = "message-time";

            const messageDate = new Date(message.created_at);
            time.textContent = messageDate.toLocaleString();

            messageBox.appendChild(sender);
            messageBox.appendChild(messageText);
            messageBox.appendChild(time);

            // Sent / Seen status (only for your messages)
            if (isMine) {
                const status = document.createElement("div");
                status.className = "message-time";

                status.textContent =
                    Number(message.is_read) === 1
                        ? "Seen ✓✓"
                        : "Sent ✓";

                messageBox.appendChild(status);
            }

            messagesDiv.appendChild(messageBox);
        });

        messagesDiv.scrollTop = messagesDiv.scrollHeight;

    } catch (error) {
        console.error("Chat error:", error);
    }
}

async function sendMessage() {
    const message = messageInput.value.trim();

    if (!message) {
        return;
    }

    sendButton.disabled = true;

    try {
        const response = await fetch(apiUrl, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ message: message })
        });

        const data = await response.json();

        if (response.ok && data.success) {
            messageInput.value = "";
            await loadMessages();
        } else {
            alert(data.message || "Unable to send message.");
        }

    } catch (error) {
        alert("Something went wrong while sending the message.");
        console.error(error);

    } finally {
        sendButton.disabled = false;
    }
}

// Send button click
sendButton.addEventListener("click", sendMessage);

// Send message using Enter key
messageInput.addEventListener("keydown", function(event) {
    if (event.key === "Enter") {
        event.preventDefault();
        sendMessage();
    }
});

// Load messages
loadMessages();

// Refresh messages every 2 seconds
setInterval(loadMessages, 2000);
