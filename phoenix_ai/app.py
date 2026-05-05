# ============================================================
# Phoenix AI – Customer Support System
# app.py  –  Merged Final Version
#
# Combines:
#   • Your RESPONSES dict, FALLBACKS, mood system, order statuses
#   • MySQL storage (no JSON files)
#   • Bug fixes: close-ticket indent, order-ID regex, complaint flow
#   • Full REST API with PUT / DELETE / export
# ============================================================

import csv
import io
import random
import re
from datetime import datetime
from functools import wraps

from flask import Flask, Response, jsonify, redirect, render_template, request, session, url_for

import db

app = Flask(__name__)
app.secret_key = "phoenix_ai_secret_2024"


# ─────────────────────────────────────────────────────────────
# Auth helper
# ─────────────────────────────────────────────────────────────

def login_required(f):
    """Redirect to login page if admin is not authenticated."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("admin_logged_in"):
            return redirect(url_for("admin_login"))
        return f(*args, **kwargs)
    return decorated


# ─────────────────────────────────────────────────────────────
# ① KEYWORD → (reply text, mood)   ← your RESPONSES dict
# ─────────────────────────────────────────────────────────────
RESPONSES = {
    "hi":        ("👋 Hello! Welcome to Phoenix Support. How can I assist you today?",                              "info"),
    "hello":     ("👋 Hi there! Great to have you here. What can I help you with?",                                 "info"),
    "hey":       ("👋 Hey! Phoenix Support is at your service.",                                                    "info"),
    "delivery":  ("📦 Most deliveries arrive within **48 hours**. If delayed, share your Order ID!",               "info"),
    "payment":   ("💳 Payment issues resolve within **24 hours**. Type `complaint` to raise a ticket.",             "warning"),
    "refund":    ("💰 Refunds process in **5–7 business days** after approval. Type `complaint` to begin.",         "warning"),
    "track":     ("🔍 Please share your **Order ID** to track your order.",                                         "info"),
    "order":     ("📋 Share your **Order ID** or type `complaint` to raise an issue.",                              "info"),
    "cancel":    ("❌ To cancel an order, type `complaint` and select the relevant category.",                       "warning"),
    "return":    ("🔄 Returns accepted within **7 days** of delivery. Type `complaint` to initiate.",               "info"),
    "services":  ("🛠️ **Our Services:**\n• Order Tracking\n• Payment Support\n• Returns & Refunds\n• Product Assistance\n• Technical Support\n• 24/7 Customer Care", "info"),
    "contact":   ("📞 **Helpline:** 1800-123-4567 (Toll Free)\n📧 **Email:** support@phoenix.com\n🕐 **Hours:** Mon–Sat, 9 AM – 9 PM", "info"),
    "help":      ("🤝 **What you can do:**\n• `complaint` — Register a complaint\n• `history` — View complaints\n• `search ST101` — Find a ticket\n• `close ST101` — Close a ticket\n• Share an Order ID to track it", "info"),
    "technical": ("🔧 Type `complaint` and select **Technical**. Our team resolves issues within **12 hours**.",   "info"),
    "broken":    ("😔 I'm sorry to hear that! Type `complaint` to raise a broken product issue.",                   "error"),
    "damaged":   ("😟 Sorry about that! Share your Order ID so I can arrange a replacement or refund.",             "error"),
    "late":      ("⏰ We apologise for the delay! Type `complaint` to file a late-delivery complaint.",             "warning"),
    "wrong":     ("😕 Received the wrong item? Type `complaint` — we'll arrange a replacement or refund.",         "warning"),
    "thanks":    ("🙏 You're welcome! Anything else I can help with?",                                              "success"),
    "thank you": ("🙏 Happy to help! Feel free to reach out anytime.",                                              "success"),
    "bye":       ("👋 Goodbye! Thank you for contacting Phoenix Support. Have a wonderful day!",                    "info"),
    "goodbye":   ("👋 Take care! Come back anytime you need help. 😊",                                             "info"),
}

FALLBACKS = [
    ("🤔 I didn't quite catch that. Try rephrasing, or type `help` to see what I can do.", "info"),
    ("❓ Not sure about that. Type `complaint` to raise a ticket or `help` for options.",   "info"),
    ("💬 Could you provide more details? I want to make sure I help you correctly!",        "info"),
    ("🔄 Try asking about delivery, payment, refund, or type `help`.",                     "info"),
]

ORDER_STATUSES = [
    "processing ⏳",
    "packed 📦",
    "shipped 🚚",
    "out for delivery 🚀",
    "delivered ✅",
]


# ─────────────────────────────────────────────────────────────
# ② DB helpers
# ─────────────────────────────────────────────────────────────

def generate_ticket_id() -> str:
    """Sequential ticket IDs: ST101, ST102 …"""
    conn = db.get_conn()
    cur  = conn.cursor()
    cur.execute("SELECT ticket_id FROM complaints ORDER BY id DESC LIMIT 1")
    row  = cur.fetchone()
    conn.close()
    num  = int(re.sub(r"\D", "", row[0])) + 1 if row else 101
    return f"ST{num}"


def get_or_create_order(order_id: str) -> str:
    """Persist order status in MySQL; create random one on first look-up."""
    conn = db.get_conn()
    cur  = conn.cursor(dictionary=True)
    cur.execute("SELECT status FROM orders WHERE order_id = %s", (order_id,))
    row  = cur.fetchone()
    if row:
        conn.close()
        return row["status"]
    status = random.choice(ORDER_STATUSES)
    cur.execute("INSERT INTO orders (order_id, status) VALUES (%s, %s)", (order_id, status))
    conn.commit()
    conn.close()
    return status


# ─────────────────────────────────────────────────────────────
# ③ Chatbot brain  (your logic + MySQL + bug fixes)
# ─────────────────────────────────────────────────────────────

def chatbot_response(msg: str) -> dict:
    """
    Returns a dict:  { "text": "...", "mood": "info|warning|error|success" }
    """
    raw = msg.strip()
    t   = raw.lower()

    # ── close ST101 ─────────────────────────────────────────
    m = re.match(r"close\s+(st\d+)", t)
    if m:
        tid  = m.group(1).upper()
        conn = db.get_conn()
        cur  = conn.cursor()
        cur.execute("UPDATE complaints SET status='Closed' WHERE ticket_id=%s", (tid,))
        affected = cur.rowcount
        conn.commit()
        conn.close()
        if affected:
            return {"text": f"✅ Ticket **{tid}** has been marked as **Closed**.", "mood": "success"}
        return {"text": f"❌ Ticket **{tid}** not found. Check the ID and try again.", "mood": "error"}

    # ── search ST101 ─────────────────────────────────────────
    m = re.match(r"search\s+(st\d+)", t)
    if m:
        tid  = m.group(1).upper()
        conn = db.get_conn()
        cur  = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM complaints WHERE ticket_id=%s", (tid,))
        row  = cur.fetchone()
        conn.close()
        if row:
            ts = row["created_at"].strftime("%d %b %Y %H:%M")
            return {
                "text": (
                    f"🎫 **Ticket {row['ticket_id']}**\n"
                    f"• Category : {row['category']}\n"
                    f"• Status   : {row['status']}\n"
                    f"• Filed on : {ts}\n"
                    f"• Issue    : {row['description']}"
                ),
                "mood": "info",
            }
        return {
            "text": f"🔍 No ticket found with ID **{tid}**. Check the number and try again.",
            "mood": "error",
        }

    # ── bare ticket ID: ST101 ────────────────────────────────
    if re.match(r"^st\d+$", t):
        tid  = t.upper()
        conn = db.get_conn()
        cur  = conn.cursor(dictionary=True)
        cur.execute("SELECT status FROM complaints WHERE ticket_id=%s", (tid,))
        row  = cur.fetchone()
        conn.close()
        if row:
            return {"text": f"📋 Ticket **{tid}** status: **{row['status']}**", "mood": "success"}
        return {"text": f"❌ No such ticket: **{tid}**. Please check your Ticket ID.", "mood": "error"}

    # ── history ───────────────────────────────────────────────
    if t == "history":
        conn = db.get_conn()
        cur  = conn.cursor(dictionary=True)
        cur.execute(
            "SELECT ticket_id, category, status, created_at "
            "FROM complaints ORDER BY id DESC LIMIT 10"
        )
        rows = cur.fetchall()
        conn.close()
        if not rows:
            return {"text": "📭 No complaints found yet.", "mood": "info"}
        lines = ["📋 **Recent Complaints (last 10):**"]
        for r in rows:
            lines.append(
                f"• **{r['ticket_id']}** | {r['category']} | "
                f"{r['status']} | {r['created_at'].strftime('%d %b %Y')}"
            )
        return {"text": "\n".join(lines), "mood": "info"}

    # ── complaint wizard ─────────────────────────────────────
    if "complaint" in t:
        session["awaiting"] = "complaint_category"
        return {
            "text": (
                "📝 I'll help you file a complaint.\n"
                "Please tell me the **category**:\n"
                "delivery · payment · refund · technical · other"
            ),
            "mood": "info",
        }

    awaiting = session.get("awaiting", "")

    if awaiting == "complaint_category":
        session["complaint_category"] = raw.strip().capitalize()
        session["awaiting"]           = "complaint_description"
        return {
            "text": f"Got it — **{session['complaint_category']}**.\nNow briefly describe the issue:",
            "mood": "info",
        }

    if awaiting == "complaint_description":
        category = session.pop("complaint_category", "General")
        session.pop("awaiting", None)
        tid  = generate_ticket_id()
        conn = db.get_conn()
        cur  = conn.cursor()
        cur.execute(
            "INSERT INTO complaints (ticket_id, category, description) VALUES (%s,%s,%s)",
            (tid, category, raw.strip()),
        )
        conn.commit()
        conn.close()
        return {
            "text": (
                f"✅ Complaint registered!\n"
                f"🎫 Ticket ID : **{tid}**\n"
                f"📂 Category  : {category}\n"
                f"Use `search {tid}` to check status anytime."
            ),
            "mood": "success",
        }

    # ── auto-ticket on issue keywords (your idea, MySQL version) ─
    issue_words = ["damaged", "broken", "late", "wrong", "failed", "missing", "not received"]
    if any(w in t for w in issue_words) and not awaiting:
        cat_map = {
            "damaged": "Product", "broken": "Product",
            "late": "Delivery",   "wrong": "Delivery",
            "missing": "Delivery","not received": "Delivery",
            "failed": "Payment",
        }
        category = next((cat_map[w] for w in issue_words if w in t), "General")
        tid  = generate_ticket_id()
        conn = db.get_conn()
        cur  = conn.cursor()
        cur.execute(
            "INSERT INTO complaints (ticket_id, category, description) VALUES (%s,%s,%s)",
            (tid, category, raw.strip()),
        )
        conn.commit()
        conn.close()
        return {
            "text": (
                f"😔 I'm sorry to hear that! I've automatically raised a ticket.\n"
                f"✅ Ticket ID : **{tid}**\n"
                f"📂 Category  : {category}\n"
                f"Our team will contact you soon."
            ),
            "mood": "warning",
        }

    # ── Order ID detection (your regex, extended + fixed) ────
    # Matches: N642DT684, ORD1234, ABC123XY etc. — but NOT ST-tickets
    order_match = re.search(r"\b[A-Z]{2,}\d+[A-Z0-9]*\b", raw.upper())
    if order_match and not re.match(r"^ST\d+$", order_match.group(0)):
        oid    = order_match.group(0)
        status = get_or_create_order(oid)
        if "delivered" in status.lower():
            return {
                "text": (
                    f"✅ Order **{oid}** has been **delivered**! 🎉\n"
                    "If you have any issues with it, type `complaint`."
                ),
                "mood": "success",
            }
        return {
            "text": f"📦 Your order **{oid}** status: **{status}**\nWe'll keep you updated!",
            "mood": "info",
        }

    # ── Keyword dictionary (your RESPONSES, long keys first) ─
    for keyword in sorted(RESPONSES, key=len, reverse=True):
        if keyword in t:
            text, mood = RESPONSES[keyword]
            return {"text": text, "mood": mood}

    # ── Fallback ─────────────────────────────────────────────
    text, mood = random.choice(FALLBACKS)
    return {"text": text, "mood": mood}


# ─────────────────────────────────────────────────────────────
# ④ Flask Routes
# ─────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")


# ── Admin login ───────────────────────────────────────────────
@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if session.get("admin_logged_in"):
        return redirect(url_for("admin"))

    error   = None
    prefill = None

    if request.method == "POST":
        email    = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "").strip()
        prefill  = email

        conn = db.get_conn()
        cur  = conn.cursor(dictionary=True)
        cur.execute(
            "SELECT * FROM users WHERE email=%s AND role='admin'", (email,)
        )
        user = cur.fetchone()
        conn.close()

        if user and user["password"] == password:
            session["admin_logged_in"] = True
            session["admin_name"]      = user["name"]
            session["admin_email"]     = user["email"]
            return redirect(url_for("admin"))
        else:
            error = "Invalid email or password. Please try again."

    return render_template("login.html", error=error, prefill=prefill)


# ── Admin logout ──────────────────────────────────────────────
@app.route("/admin/logout")
def admin_logout():
    session.pop("admin_logged_in", None)
    session.pop("admin_name",      None)
    session.pop("admin_email",     None)
    return redirect(url_for("admin_login"))


# ── Admin dashboard (protected) ───────────────────────────────
@app.route("/admin")
@login_required
def admin():
    conn = db.get_conn()
    cur  = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM complaints ORDER BY id DESC")
    complaints = cur.fetchall()
    cur.execute("SELECT * FROM orders ORDER BY id DESC")
    orders = cur.fetchall()
    conn.close()
    return render_template(
        "admin.html",
        complaints=complaints,
        orders=orders,
        admin_name=session.get("admin_name", "Admin"),
    )


# ── /api/chat ─────────────────────────────────────────────────
@app.route("/api/chat", methods=["POST"])
def api_chat():
    data = request.get_json(silent=True) or {}
    msg  = data.get("message", "").strip()
    if not msg:
        return jsonify({"error": "Empty message"}), 400

    result = chatbot_response(msg)
    result["timestamp"] = datetime.now().strftime("%H:%M")
    result["reply"]     = result["text"]   # frontend uses "reply"
    return jsonify(result)


# ── /api/complaint  (direct POST) ─────────────────────────────
@app.route("/api/complaint", methods=["POST"])
def api_complaint():
    data        = request.get_json(silent=True) or {}
    category    = data.get("category", "General").strip()
    description = data.get("description", "").strip()
    if not description:
        return jsonify({"error": "Description required"}), 400

    tid  = generate_ticket_id()
    now  = datetime.now()
    conn = db.get_conn()
    cur  = conn.cursor()
    cur.execute(
        "INSERT INTO complaints (ticket_id, category, description) VALUES (%s,%s,%s)",
        (tid, category, description),
    )
    conn.commit()
    conn.close()
    return jsonify({
        "type":      "ticket",
        "ticket_id": tid,
        "category":  category,
        "status":    "Open",
        "date":      now.strftime("%Y-%m-%d"),
        "time":      now.strftime("%H:%M:%S"),
    })


# ── /api/complaints  (list) ───────────────────────────────────
@app.route("/api/complaints", methods=["GET"])
def api_complaints():
    conn = db.get_conn()
    cur  = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM complaints ORDER BY id DESC")
    rows = cur.fetchall()
    conn.close()
    for r in rows:
        r["created_at"] = r["created_at"].strftime("%Y-%m-%d %H:%M")
    return jsonify(rows)


# ── /api/complaint/<id>  PUT ──────────────────────────────────
@app.route("/api/complaint/<int:cid>", methods=["PUT"])
def api_update_complaint(cid):
    data   = request.get_json(silent=True) or {}
    status = data.get("status", "Open")
    conn   = db.get_conn()
    cur    = conn.cursor()
    cur.execute("UPDATE complaints SET status=%s WHERE id=%s", (status, cid))
    conn.commit()
    conn.close()
    return jsonify({"success": True})


# ── /api/complaint/<id>  DELETE ───────────────────────────────
@app.route("/api/complaint/<int:cid>", methods=["DELETE"])
def api_delete_complaint(cid):
    conn = db.get_conn()
    cur  = conn.cursor()
    cur.execute("DELETE FROM complaints WHERE id=%s", (cid,))
    conn.commit()
    conn.close()
    return jsonify({"success": True})


# ── /api/export  CSV ──────────────────────────────────────────
@app.route("/api/export", methods=["GET"])
def api_export():
    conn = db.get_conn()
    cur  = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM complaints ORDER BY id")
    rows = cur.fetchall()
    conn.close()

    output = io.StringIO()
    writer = csv.DictWriter(
        output,
        fieldnames=["id", "ticket_id", "category", "description", "status", "created_at"],
    )
    writer.writeheader()
    for r in rows:
        r["created_at"] = r["created_at"].strftime("%Y-%m-%d %H:%M")
        writer.writerow(r)

    fname = f"phoenix_complaints_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename={fname}"},
    )


if __name__ == "__main__":
    app.run(debug=True, port=5000)
