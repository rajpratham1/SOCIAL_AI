"""routes/auth.py — Register, Login, Profile."""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash

from database import db
from models   import User

auth_bp = Blueprint("auth", __name__)


# ── POST /api/auth/register ──────────────────────────────────────
@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json(silent=True) or {}
    name     = (data.get("name") or "").strip()
    email    = (data.get("email") or "").strip().lower()
    password = (data.get("password") or "")

    if not name or not email or not password:
        return jsonify({"error": "name, email and password are required"}), 400
    if len(password) < 6:
        return jsonify({"error": "Password must be at least 6 characters"}), 400
    if User.query.filter_by(email=email).first():
        return jsonify({"error": "Email already registered"}), 409

    user = User(
        name=name,
        email=email,
        password_hash=generate_password_hash(password),
    )
    db.session.add(user)
    db.session.commit()

    # Create default platform account stubs
    _create_default_accounts(user.id)

    token = create_access_token(identity=str(user.id))
    return jsonify({"token": token, "user": user.to_dict()}), 201


# ── POST /api/auth/login ─────────────────────────────────────────
@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    email    = (data.get("email") or "").strip().lower()
    password = (data.get("password") or "")

    if not email or not password:
        return jsonify({"error": "email and password are required"}), 400

    user = User.query.filter_by(email=email).first()
    if not user or not check_password_hash(user.password_hash, password):
        return jsonify({"error": "Invalid email or password"}), 401

    token = create_access_token(identity=str(user.id))
    return jsonify({"token": token, "user": user.to_dict()}), 200


# ── GET /api/auth/me ─────────────────────────────────────────────
@auth_bp.route("/me", methods=["GET"])
@jwt_required()
def me():
    uid  = int(get_jwt_identity())
    user = User.query.get_or_404(uid)
    return jsonify({"user": user.to_dict()}), 200


# ── PUT /api/auth/me  (update profile) ───────────────────────────
@auth_bp.route("/me", methods=["PUT"])
@jwt_required()
def update_profile():
    uid  = int(get_jwt_identity())
    user = User.query.get_or_404(uid)
    data = request.get_json(silent=True) or {}

    if "name" in data and data["name"].strip():
        user.name = data["name"].strip()
    if "password" in data and data["password"]:
        if len(data["password"]) < 6:
            return jsonify({"error": "Password must be at least 6 characters"}), 400
        user.password_hash = generate_password_hash(data["password"])

    db.session.commit()
    return jsonify({"user": user.to_dict()}), 200


# ── helper ───────────────────────────────────────────────────────
def _create_default_accounts(user_id):
    from models import Account
    defaults = [
        ("fb",  "Facebook",    "📘"),
        ("ig",  "Instagram",   "📷"),
        ("tw",  "X (Twitter)", "🐦"),
        ("li",  "LinkedIn",    "💼"),
        ("yt",  "YouTube",     "▶️"),
    ]
    for pid, name, icon in defaults:
        acc = Account(user_id=user_id, platform_id=pid, name=name, icon=icon,
                      connected=False, handle="")
        db.session.add(acc)
    db.session.commit()
