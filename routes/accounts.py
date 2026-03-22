"""routes/accounts.py — Social media account connect / disconnect."""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timezone

from database import db
from models   import Account, Notification

accounts_bp = Blueprint("accounts", __name__)

ALL_PLATFORMS = [
    {"id": "fb",  "name": "Facebook",    "icon": "📘", "color": "#1877f2"},
    {"id": "ig",  "name": "Instagram",   "icon": "📷", "color": "#e1306c"},
    {"id": "tw",  "name": "X (Twitter)", "icon": "🐦", "color": "#1da1f2"},
    {"id": "li",  "name": "LinkedIn",    "icon": "💼", "color": "#0a66c2"},
    {"id": "yt",  "name": "YouTube",     "icon": "▶️", "color": "#ff0000"},
]


def _ensure_accounts(user_id):
    """Make sure all 5 platform stubs exist for a user."""
    existing = {a.platform_id for a in Account.query.filter_by(user_id=user_id).all()}
    for p in ALL_PLATFORMS:
        if p["id"] not in existing:
            db.session.add(Account(user_id=user_id, platform_id=p["id"],
                                   name=p["name"], icon=p["icon"]))
    db.session.commit()


# ── GET /api/accounts ────────────────────────────────────────────
@accounts_bp.route("", methods=["GET"])
@jwt_required()
def get_accounts():
    uid = int(get_jwt_identity())
    _ensure_accounts(uid)
    accounts = Account.query.filter_by(user_id=uid).all()
    # Return in canonical platform order
    order = [p["id"] for p in ALL_PLATFORMS]
    accounts.sort(key=lambda a: order.index(a.platform_id) if a.platform_id in order else 99)
    return jsonify({"accounts": [a.to_dict() for a in accounts]}), 200


# ── POST /api/accounts/<platform_id>/connect ─────────────────────
@accounts_bp.route("/<platform_id>/connect", methods=["POST"])
@jwt_required()
def connect_account(platform_id):
    uid  = int(get_jwt_identity())
    data = request.get_json(silent=True) or {}
    handle = (data.get("handle") or "").strip()

    if not handle:
        return jsonify({"error": "handle is required"}), 400

    acc = Account.query.filter_by(user_id=uid, platform_id=platform_id).first()
    if not acc:
        # find platform meta
        meta = next((p for p in ALL_PLATFORMS if p["id"] == platform_id), None)
        if not meta:
            return jsonify({"error": "Unknown platform"}), 404
        acc = Account(user_id=uid, platform_id=platform_id,
                      name=meta["name"], icon=meta["icon"])
        db.session.add(acc)

    acc.connected    = True
    acc.handle       = handle
    acc.connected_at = datetime.now(timezone.utc)

    n = Notification(user_id=uid, text=f"{acc.name} account connected.", type="success")
    db.session.add(n)
    db.session.commit()
    return jsonify({"account": acc.to_dict()}), 200


# ── DELETE /api/accounts/<platform_id>/disconnect ────────────────
@accounts_bp.route("/<platform_id>/disconnect", methods=["DELETE"])
@jwt_required()
def disconnect_account(platform_id):
    uid = int(get_jwt_identity())
    acc = Account.query.filter_by(user_id=uid, platform_id=platform_id).first_or_404()
    acc.connected    = False
    acc.handle       = ""
    acc.connected_at = None

    n = Notification(user_id=uid, text=f"{acc.name} account disconnected.", type="info")
    db.session.add(n)
    db.session.commit()
    return jsonify({"account": acc.to_dict()}), 200
