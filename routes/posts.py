"""routes/posts.py — Full CRUD for posts + publish + filter."""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timezone
import random

from database import db
from models   import Post, Notification

posts_bp = Blueprint("posts", __name__)


def _notif(user_id, text, typ="info"):
    n = Notification(user_id=user_id, text=text, type=typ)
    db.session.add(n)


def _fake_engagement():
    """Simulate engagement numbers when a post is published."""
    return {
        "likes":    random.randint(10, 200),
        "comments": random.randint(2,  60),
        "shares":   random.randint(1,  50),
        "reach":    random.randint(200, 5000),
    }


# ── GET /api/posts ───────────────────────────────────────────────
# Query params: status=all|published|scheduled|draft  page=1  per_page=20
@posts_bp.route("", methods=["GET"])
@jwt_required()
def get_posts():
    uid     = int(get_jwt_identity())
    status  = request.args.get("status", "all")
    page    = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 50))

    q = Post.query.filter_by(user_id=uid).order_by(Post.created_at.desc())
    if status != "all":
        q = q.filter_by(status=status)

    paginated = q.paginate(page=page, per_page=per_page, error_out=False)
    return jsonify({
        "posts":    [p.to_dict() for p in paginated.items],
        "total":    paginated.total,
        "page":     page,
        "pages":    paginated.pages,
    }), 200


# ── POST /api/posts ──────────────────────────────────────────────
@posts_bp.route("", methods=["POST"])
@jwt_required()
def create_post():
    uid  = int(get_jwt_identity())
    data = request.get_json(silent=True) or {}

    text      = (data.get("text") or "").strip()
    platforms = data.get("platforms") or []
    status    = data.get("status", "draft")
    img       = data.get("img") or None
    scheduled_at_str = data.get("scheduled_at") or None

    if not text:
        return jsonify({"error": "text is required"}), 400
    if not platforms:
        return jsonify({"error": "at least one platform required"}), 400
    if status not in ("draft", "scheduled", "published"):
        return jsonify({"error": "status must be draft | scheduled | published"}), 400

    scheduled_at = None
    if scheduled_at_str:
        try:
            scheduled_at = datetime.fromisoformat(scheduled_at_str.replace("Z", "+00:00"))
            status = "scheduled"
        except ValueError:
            return jsonify({"error": "Invalid scheduled_at format (use ISO 8601)"}), 400

    post = Post(
        user_id=uid,
        text=text,
        status=status,
        img=img,
        scheduled_at=scheduled_at,
        created_at=datetime.now(timezone.utc),
    )
    post.set_platforms(platforms)

    if status == "published":
        eng = _fake_engagement()
        post.likes    = eng["likes"]
        post.comments = eng["comments"]
        post.shares   = eng["shares"]
        post.reach    = eng["reach"]
        post.published_at = datetime.now(timezone.utc)
        _notif(uid, f'Post published on {", ".join(platforms)}.', "success")
    elif status == "scheduled":
        _notif(uid, f'Post scheduled for {scheduled_at.strftime("%b %d %H:%M")}.', "info")
    else:
        _notif(uid, "Draft saved.", "info")

    db.session.add(post)
    db.session.commit()
    return jsonify({"post": post.to_dict()}), 201


# ── GET /api/posts/<id> ──────────────────────────────────────────
@posts_bp.route("/<int:post_id>", methods=["GET"])
@jwt_required()
def get_post(post_id):
    uid  = int(get_jwt_identity())
    post = Post.query.filter_by(id=post_id, user_id=uid).first_or_404()
    return jsonify({"post": post.to_dict()}), 200


# ── PUT /api/posts/<id> ──────────────────────────────────────────
@posts_bp.route("/<int:post_id>", methods=["PUT"])
@jwt_required()
def update_post(post_id):
    uid  = int(get_jwt_identity())
    post = Post.query.filter_by(id=post_id, user_id=uid).first_or_404()
    data = request.get_json(silent=True) or {}

    if "text" in data:
        text = data["text"].strip()
        if not text:
            return jsonify({"error": "text cannot be empty"}), 400
        post.text = text

    if "platforms" in data:
        post.set_platforms(data["platforms"])

    if "status" in data:
        if data["status"] not in ("draft", "scheduled", "published"):
            return jsonify({"error": "Invalid status"}), 400
        post.status = data["status"]

    if "img" in data:
        post.img = data["img"] or None

    if "scheduled_at" in data:
        val = data["scheduled_at"]
        if val:
            try:
                post.scheduled_at = datetime.fromisoformat(val.replace("Z", "+00:00"))
            except ValueError:
                return jsonify({"error": "Invalid scheduled_at format"}), 400
        else:
            post.scheduled_at = None

    db.session.commit()
    return jsonify({"post": post.to_dict()}), 200


# ── DELETE /api/posts/<id> ───────────────────────────────────────
@posts_bp.route("/<int:post_id>", methods=["DELETE"])
@jwt_required()
def delete_post(post_id):
    uid  = int(get_jwt_identity())
    post = Post.query.filter_by(id=post_id, user_id=uid).first_or_404()
    db.session.delete(post)
    _notif(uid, "A post was deleted.", "info")
    db.session.commit()
    return jsonify({"message": "Post deleted"}), 200


# ── POST /api/posts/<id>/publish ─────────────────────────────────
@posts_bp.route("/<int:post_id>/publish", methods=["POST"])
@jwt_required()
def publish_post(post_id):
    uid  = int(get_jwt_identity())
    post = Post.query.filter_by(id=post_id, user_id=uid).first_or_404()

    eng = _fake_engagement()
    post.status       = "published"
    post.likes        = eng["likes"]
    post.comments     = eng["comments"]
    post.shares       = eng["shares"]
    post.reach        = eng["reach"]
    post.scheduled_at = None
    post.published_at = datetime.now(timezone.utc)

    _notif(uid, "Post published successfully! 🚀", "success")
    db.session.commit()
    return jsonify({"post": post.to_dict()}), 200
