import os
from datetime import datetime, timezone
from functools import wraps

from flask import Flask, request, session, jsonify, render_template_string
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

app = Flask(__name__)

# =========================================================
# CONFIG
# =========================================================

app.secret_key = os.getenv("SECRET_KEY", "CHANGE_THIS_SECRET_KEY")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError(
        "SUPABASE_URL and SUPABASE_KEY environment variables are required."
    )

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


# =========================================================
# HELPERS
# =========================================================

def current_user():
    user_id = session.get("user_id")

    if not user_id:
        return None

    result = (
        supabase
        .table("users")
        .select("id,username,email,avatar,bio,created_at")
        .eq("id", user_id)
        .limit(1)
        .execute()
    )

    if not result.data:
        session.clear()
        return None

    return result.data[0]


def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not session.get("user_id"):
            return jsonify({
                "ok": False,
                "error": "Login required"
            }), 401

        return fn(*args, **kwargs)

    return wrapper


def clean_username(username):
    return (
        str(username or "")
        .strip()
        .lower()
    )


def clean_message(message):
    return (
        str(message or "")
        .strip()
    )[:2000]


# =========================================================
# HOME
# =========================================================

@app.route("/")
def index():
    return render_template_string("""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport"
          content="width=device-width, initial-scale=1.0">

    <title>BAGAR BILLIIII 😾</title>

    <style>
        * {
            box-sizing: border-box;
        }

        body {
            margin: 0;
            min-height: 100vh;
            background: #07070b;
            color: white;
            font-family: Arial, sans-serif;
            display: flex;
            align-items: center;
            justify-content: center;
        }

        .box {
            width: 92%;
            max-width: 450px;
            background: #101018;
            border: 1px solid #292933;
            border-radius: 24px;
            padding: 30px;
            text-align: center;
            box-shadow: 0 0 35px rgba(255, 0, 255, .15);
        }

        .cat {
            font-size: 75px;
        }

        h1 {
            color: #ffcc00;
            margin-bottom: 5px;
        }

        .purple {
            color: #ff00ff;
        }

        button {
            width: 100%;
            border: 0;
            padding: 14px;
            border-radius: 14px;
            margin-top: 10px;
            font-weight: bold;
            cursor: pointer;
            background: #ffcc00;
            color: #07070b;
        }

        button.secondary {
            background: #ff00ff;
            color: white;
        }

        input {
            width: 100%;
            padding: 14px;
            margin-top: 10px;
            border-radius: 12px;
            border: 1px solid #33333d;
            background: #07070b;
            color: white;
            outline: none;
        }

        .hidden {
            display: none;
        }

        #result {
            margin-top: 15px;
            min-height: 25px;
        }

        .meow {
            color: #ffcc00;
            font-weight: bold;
        }
    </style>
</head>

<body>

<div class="box">

    <div class="cat">😾</div>

    <h1>BAGAR BILLIIII</h1>

    <p class="purple">MEOW MODE ON</p>

    <div id="intro">

        <p>
            Welcome to BILLINESTAN.
        </p>

        <button onclick="showLogin()">
            ENTER THE BILLINESTAN
        </button>

    </div>


    <div id="auth" class="hidden">

        <h2 id="authTitle">LOGIN</h2>

        <input
            id="username"
            placeholder="Username"
            autocomplete="username"
        >

        <input
            id="password"
            type="password"
            placeholder="Password"
            autocomplete="current-password"
        >

        <input
            id="email"
            class="hidden"
            placeholder="Email (optional)"
            type="email"
        >

        <button onclick="submitAuth()">
            CONTINUE 😾
        </button>

        <button
            class="secondary"
            onclick="toggleAuth()"
            id="switchBtn"
        >
            CREATE ACCOUNT
        </button>

        <div id="result"></div>

    </div>

</div>


<script>

let registerMode = false;

function showLogin() {

    document.getElementById("intro").classList.add("hidden");
    document.getElementById("auth").classList.remove("hidden");

}

function toggleAuth() {

    registerMode = !registerMode;

    document.getElementById("authTitle").innerText =
        registerMode ? "REGISTER" : "LOGIN";

    document.getElementById("email").classList.toggle(
        "hidden",
        !registerMode
    );

    document.getElementById("switchBtn").innerText =
        registerMode
        ? "BACK TO LOGIN"
        : "CREATE ACCOUNT";

}

async function submitAuth() {

    const username =
        document.getElementById("username").value.trim();

    const password =
        document.getElementById("password").value;

    const email =
        document.getElementById("email").value.trim();

    const result =
        document.getElementById("result");

    result.innerHTML = "😾 Processing...";

    const url =
        registerMode ? "/api/register" : "/api/login";

    const body =
        registerMode
        ? {username, password, email}
        : {username, password};

    try {

        const response = await fetch(url, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(body)
        });

        const data = await response.json();

        if (!data.ok) {

            result.innerHTML =
                "❌ " + (data.error || "Something went wrong");

            return;
        }

        result.innerHTML =
            '<span class="meow">' +
            "😾 Welcome @" +
            data.user.username +
            "</span>";

        setTimeout(() => {

            window.location.href = "/app";

        }, 700);

    } catch (error) {

        result.innerHTML =
            "❌ Server connection failed";

    }
}

</script>

</body>
</html>
""")


# =========================================================
# REGISTER
# =========================================================

@app.post("/api/register")
def register():

    data = request.get_json(silent=True) or {}

    username = clean_username(data.get("username"))
    password = str(data.get("password") or "")
    email = str(data.get("email") or "").strip() or None

    if len(username) < 3:
        return jsonify({
            "ok": False,
            "error": "Username must be at least 3 characters"
        }), 400

    if len(username) > 30:
        return jsonify({
            "ok": False,
            "error": "Username is too long"
        }), 400

    if not username.replace("_", "").isalnum():
        return jsonify({
            "ok": False,
            "error": "Use only letters, numbers and underscore"
        }), 400

    if len(password) < 6:
        return jsonify({
            "ok": False,
            "error": "Password must be at least 6 characters"
        }), 400

    existing = (
        supabase
        .table("users")
        .select("id")
        .eq("username", username)
        .limit(1)
        .execute()
    )

    if existing.data:
        return jsonify({
            "ok": False,
            "error": "Username already exists"
        }), 409

    password_hash = generate_password_hash(password)

    result = (
        supabase
        .table("users")
        .insert({
            "username": username,
            "password_hash": password_hash,
            "email": email,
            "avatar": "😾",
            "bio": "MEOW MODE ON 😾"
        })
        .execute()
    )

    if not result.data:
        return jsonify({
            "ok": False,
            "error": "Could not create account"
        }), 500

    user = result.data[0]

    session["user_id"] = user["id"]

    return jsonify({
        "ok": True,
        "user": {
            "id": user["id"],
            "username": user["username"]
        }
    })


# =========================================================
# LOGIN
# =========================================================

@app.post("/api/login")
def login():

    data = request.get_json(silent=True) or {}

    username = clean_username(data.get("username"))
    password = str(data.get("password") or "")

    result = (
        supabase
        .table("users")
        .select("*")
        .eq("username", username)
        .limit(1)
        .execute()
    )

    if not result.data:
        return jsonify({
            "ok": False,
            "error": "Invalid username or password"
        }), 401

    user = result.data[0]

    if not check_password_hash(
        user["password_hash"],
        password
    ):
        return jsonify({
            "ok": False,
            "error": "Invalid username or password"
        }), 401

    session["user_id"] = user["id"]

    return jsonify({
        "ok": True,
        "user": {
            "id": user["id"],
            "username": user["username"]
        }
    })


# =========================================================
# LOGOUT
# =========================================================

@app.post("/api/logout")
def logout():

    session.clear()

    return jsonify({
        "ok": True
    })


# =========================================================
# CURRENT USER
# =========================================================

@app.get("/api/me")
@login_required
def me():

    user = current_user()

    return jsonify({
        "ok": True,
        "user": user
    })


# =========================================================
# FRIEND SEARCH
# =========================================================

@app.get("/api/users/search")
@login_required
def search_users():

    q = clean_username(
        request.args.get("q")
    )

    if not q:
        return jsonify({
            "ok": True,
            "users": []
        })

    result = (
        supabase
        .table("users")
        .select("id,username,avatar,bio")
        .ilike("username", f"%{q}%")
        .limit(20)
        .execute()
    )

    return jsonify({
        "ok": True,
        "users": result.data or []
    })


# =========================================================
# SEND FRIEND REQUEST
# =========================================================

@app.post("/api/friends/request")
@login_required
def send_friend_request():

    data = request.get_json(silent=True) or {}

    username = clean_username(
        data.get("username")
    )

    me = current_user()

    if not me:
        return jsonify({
            "ok": False,
            "error": "User session expired"
        }), 401

    if username == me["username"]:
        return jsonify({
            "ok": False,
            "error": "You cannot add yourself"
        }), 400

    target_result = (
        supabase
        .table("users")
        .select("id,username")
        .eq("username", username)
        .limit(1)
        .execute()
    )

    if not target_result.data:
        return jsonify({
            "ok": False,
            "error": "User not found"
        }), 404

    target = target_result.data[0]

    # Check existing friendship
    friendship = (
        supabase
        .table("friendships")
        .select("id")
        .or_(
            f"and(user_id.eq.{me['id']},friend_id.eq.{target['id']}),"
            f"and(user_id.eq.{target['id']},friend_id.eq.{me['id']})"
        )
        .limit(1)
        .execute()
    )

    if friendship.data:
        return jsonify({
            "ok": False,
            "error": "Already friends"
        }), 409

    # Check pending request
    pending = (
        supabase
        .table("friend_requests")
        .select("id,status")
        .eq("sender_id", me["id"])
        .eq("receiver_id", target["id"])
        .eq("status", "pending")
        .limit(1)
        .execute()
    )

    if pending.data:
        return jsonify({
            "ok": False,
            "error": "Request already sent"
        }), 409

    # Check reverse pending request
    reverse = (
        supabase
        .table("friend_requests")
        .select("id,status")
        .eq("sender_id", target["id"])
        .eq("receiver_id", me["id"])
        .eq("status", "pending")
        .limit(1)
        .execute()
    )

    if reverse.data:
        return jsonify({
            "ok": False,
            "error": "This user already sent you a request"
        }), 409

    special_tag = (
        "SYIIM"
        if me["username"] == "jadugarni"
        else None
    )

    insert_data = {
        "sender_id": me["id"],
        "receiver_id": target["id"],
        "status": "pending"
    }

    if special_tag:
        insert_data["tag"] = special_tag

    result = (
        supabase
        .table("friend_requests")
        .insert(insert_data)
        .execute()
    )

    return jsonify({
        "ok": bool(result.data),
        "message": "Friend request sent 😾"
    })


# =========================================================
# INCOMING FRIEND REQUESTS
# =========================================================

@app.get("/api/friends/requests")
@login_required
def friend_requests():

    result = (
        supabase
        .table("friend_requests")
        .select(
            "id,status,tag,created_at,"
            "sender:users!friend_requests_sender_id_fkey("
            "id,username,avatar,bio)"
        )
        .eq("receiver_id", session["user_id"])
        .eq("status", "pending")
        .order("created_at", desc=True)
        .execute()
    )

    return jsonify({
        "ok": True,
        "requests": result.data or []
    })


# =========================================================
# ACCEPT FRIEND REQUEST
# =========================================================

@app.post("/api/friends/<request_id>/accept")
@login_required
def accept_request(request_id):

    result = (
        supabase
        .table("friend_requests")
        .select("*")
        .eq("id", request_id)
        .eq("receiver_id", session["user_id"])
        .eq("status", "pending")
        .limit(1)
        .execute()
    )

    if not result.data:
        return jsonify({
            "ok": False,
            "error": "Request not found"
        }), 404

    req = result.data[0]

    (
        supabase
        .table("friend_requests")
        .update({
            "status": "accepted"
        })
        .eq("id", request_id)
        .execute()
    )

    (
        supabase
        .table("friendships")
        .insert([
            {
                "user_id": req["sender_id"],
                "friend_id": req["receiver_id"]
            },
            {
                "user_id": req["receiver_id"],
                "friend_id": req["sender_id"]
            }
        ])
        .execute()
    )

    return jsonify({
        "ok": True,
        "message": "Friend added 😾"
    })


# =========================================================
# DECLINE FRIEND REQUEST
# =========================================================

@app.post("/api/friends/<request_id>/decline")
@login_required
def decline_request(request_id):

    result = (
        supabase
        .table("friend_requests")
        .update({
            "status": "declined"
        })
        .eq("id", request_id)
        .eq("receiver_id", session["user_id"])
        .eq("status", "pending")
        .execute()
    )

    return jsonify({
        "ok": True
    })


# =========================================================
# FRIEND LIST
# =========================================================

@app.get("/api/friends")
@login_required
def friends():

    uid = session["user_id"]

    result = (
        supabase
        .table("friendships")
        .select(
            "friend_id,"
            "friend:users!friendships_friend_id_fkey("
            "id,username,avatar,bio)"
        )
        .eq("user_id", uid)
        .execute()
    )

    friends_list = []

    for row in result.data or []:

        if row.get("friend"):
            friends_list.append(
                row["friend"]
            )

    return jsonify({
        "ok": True,
        "friends": friends_list
    })


# =========================================================
# PRIVATE CHAT - GET
# =========================================================

@app.get("/api/chat/<username>")
@login_required
def get_chat(username):

    username = clean_username(username)

    target_result = (
        supabase
        .table("users")
        .select("id,username,avatar")
        .eq("username", username)
        .limit(1)
        .execute()
    )

    if not target_result.data:
        return jsonify({
            "ok": False,
            "error": "User not found"
        }), 404

    target = target_result.data[0]

    uid = session["user_id"]

    result = (
        supabase
        .table("messages")
        .select(
            "id,sender_id,receiver_id,message,created_at"
        )
        .or_(
            f"and(sender_id.eq.{uid},receiver_id.eq.{target['id']}),"
            f"and(sender_id.eq.{target['id']},receiver_id.eq.{uid})"
        )
        .order("created_at", desc=False)
        .limit(100)
        .execute()
    )

    return jsonify({
        "ok": True,
        "friend": target,
        "messages": result.data or []
    })


# =========================================================
# PRIVATE CHAT - SEND
# =========================================================

@app.post("/api/chat/<username>")
@login_required
def send_message(username):

    username = clean_username(username)

    data = request.get_json(silent=True) or {}

    message = clean_message(
        data.get("message")
    )

    if not message:
        return jsonify({
            "ok": False,
            "error": "Message is empty"
        }), 400

    target_result = (
        supabase
        .table("users")
        .select("id,username")
        .eq("username", username)
        .limit(1)
        .execute()
    )

    if not target_result.data:
        return jsonify({
            "ok": False,
            "error": "User not found"
        }), 404

    target = target_result.data[0]

    if target["id"] == session["user_id"]:
        return jsonify({
            "ok": False,
            "error": "You cannot message yourself"
        }), 400

    # SYIIM spell commands
    spell = None

    command = message.lower()

    if command in ["love", "billi", "sach", "hug"]:
        spell = command

    result = (
        supabase
        .table("messages")
        .insert({
            "sender_id": session["user_id"],
            "receiver_id": target["id"],
            "message": message
        })
        .execute()
    )

    return jsonify({
        "ok": bool(result.data),
        "spell": spell,
        "message": result.data[0] if result.data else None
    })


# =========================================================
# SYIIM SPELL
# ============================================
