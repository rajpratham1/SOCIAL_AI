"""routes/analytics.py — Analytics summary and per-post data."""
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from models import Post

analytics_bp = Blueprint("analytics", __name__)


# ── GET /api/analytics/summary ───────────────────────────────────
@analytics_bp.route("/summary", methods=["GET"])
@jwt_required()
def summary():
    uid   = int(get_jwt_identity())
    posts = Post.query.filter_by(user_id=uid).all()

    published  = [p for p in posts if p.status == "published"]
    scheduled  = [p for p in posts if p.status == "scheduled"]
    drafts     = [p for p in posts if p.status == "draft"]

    total_likes    = sum(p.likes    for p in published)
    total_comments = sum(p.comments for p in published)
    total_shares   = sum(p.shares   for p in published)
    total_reach    = sum(p.reach    for p in published)

    # Platform breakdown — how many posts per platform
    platform_counts = {"fb": 0, "ig": 0, "tw": 0, "li": 0, "yt": 0}
    for p in posts:
        for pl in p.get_platforms():
            if pl in platform_counts:
                platform_counts[pl] += 1

    return jsonify({
        "total_posts":  len(posts),
        "published":    len(published),
        "scheduled":    len(scheduled),
        "drafts":       len(drafts),
        "total_likes":    total_likes,
        "total_comments": total_comments,
        "total_shares":   total_shares,
        "total_reach":    total_reach,
        "platform_counts": platform_counts,
    }), 200


# ── GET /api/analytics/posts ─────────────────────────────────────
# Returns published posts sorted by engagement desc (for leaderboard)
@analytics_bp.route("/posts", methods=["GET"])
@jwt_required()
def post_analytics():
    uid   = int(get_jwt_identity())
    limit = int(request.args.get("limit", 10))

    posts = (
        Post.query
        .filter_by(user_id=uid, status="published")
        .all()
    )
    posts.sort(key=lambda p: p.likes + p.comments + p.shares, reverse=True)

    return jsonify({
        "posts": [
            {
                **p.to_dict(),
                "engagement": p.likes + p.comments + p.shares,
            }
            for p in posts[:limit]
        ]
    }), 200
