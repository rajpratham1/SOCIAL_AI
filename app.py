"""
SocialAI — Flask Backend
Run:  python app.py
Docs: http://localhost:5000/api/docs
"""

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from flask_jwt_extended import (
    JWTManager, create_access_token, jwt_required, get_jwt_identity
)
from datetime import timedelta
import os

from config import Config
from database import db
from routes.auth      import auth_bp
from routes.posts     import posts_bp
from routes.accounts  import accounts_bp
from routes.analytics import analytics_bp
from routes.notifs    import notifs_bp
from routes.ai        import ai_bp
from scheduler        import start_scheduler

# ── App Factory ─────────────────────────────────────────────────
def create_app(config=None):
    app = Flask(__name__, static_folder="static", template_folder="templates")
    app.config.from_object(Config)
    if config:
        app.config.update(config)

    # Extensions
    db.init_app(app)
    CORS(app, origins="*", supports_credentials=True)
    JWTManager(app)

    # Blueprints
    app.register_blueprint(auth_bp,      url_prefix="/api/auth")
    app.register_blueprint(posts_bp,     url_prefix="/api/posts")
    app.register_blueprint(accounts_bp,  url_prefix="/api/accounts")
    app.register_blueprint(analytics_bp, url_prefix="/api/analytics")
    app.register_blueprint(notifs_bp,    url_prefix="/api/notifications")
    app.register_blueprint(ai_bp,        url_prefix="/api/ai")

    # Serve frontend HTML from /static/index.html at root
    @app.route("/", defaults={"path": ""})
    @app.route("/<path:path>")
    def serve_frontend(path):
        if path and os.path.exists(os.path.join(app.static_folder, path)):
            return send_from_directory(app.static_folder, path)
        index = os.path.join(app.static_folder, "index.html")
        if os.path.exists(index):
            return send_from_directory(app.static_folder, "index.html")
        return jsonify({"message": "SocialAI API running", "docs": "/api/docs"}), 200

    # Docs endpoint
    @app.route("/api/docs")
    def api_docs():
        return jsonify({
            "app": "SocialAI Backend",
            "version": "1.0.0",
            "endpoints": {
                "auth":          ["POST /api/auth/register", "POST /api/auth/login", "GET /api/auth/me"],
                "posts":         ["GET /api/posts", "POST /api/posts", "PUT /api/posts/<id>",
                                  "DELETE /api/posts/<id>", "POST /api/posts/<id>/publish"],
                "accounts":      ["GET /api/accounts", "POST /api/accounts/<id>/connect",
                                  "DELETE /api/accounts/<id>/disconnect"],
                "analytics":     ["GET /api/analytics/summary", "GET /api/analytics/posts"],
                "notifications": ["GET /api/notifications", "POST /api/notifications/read-all",
                                  "DELETE /api/notifications"],
                "ai":            ["POST /api/ai/suggest", "GET /api/ai/suggestions",
                                  "POST /api/ai/suggestions", "DELETE /api/ai/suggestions/<id>"],
            }
        })

    # Global error handlers
    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": "Not found"}), 404

    @app.errorhandler(500)
    def server_error(e):
        return jsonify({"error": "Internal server error"}), 500

    # Create tables + seed demo user on first run
    with app.app_context():
        db.create_all()
        _seed_demo(app)

    return app


def _seed_demo(app):
    """Create demo account if it doesn't exist yet."""
    from models import User, Post, Account, Notification
    from werkzeug.security import generate_password_hash
    import json
    from datetime import datetime, timezone

    if User.query.filter_by(email="demo@demo.com").first():
        return  # already seeded

    user = User(name="Demo User", email="demo@demo.com",
                password_hash=generate_password_hash("demo123"))
    db.session.add(user)
    db.session.flush()

    # Sample posts
    now = datetime.now(timezone.utc)
    posts = [
        Post(user_id=user.id, text="🚀 Excited to launch our new product line! Check it out. #launch #product",
             platforms=json.dumps(["fb","ig","tw"]), status="published",
             likes=142, comments=28, shares=19, reach=2340,
             created_at=datetime(2025,3,18,10,0,tzinfo=timezone.utc)),
        Post(user_id=user.id, text="💡 Top 5 productivity tips for remote workers:\n\n1. Morning routine\n2. Time-blocking\n3. Regular breaks\n4. Minimize distractions\n5. End-of-day review\n\n#productivity #remotework",
             platforms=json.dumps(["li","tw"]), status="published",
             likes=89, comments=34, shares=56, reach=1890,
             created_at=datetime(2025,3,19,14,0,tzinfo=timezone.utc)),
        Post(user_id=user.id, text="🌟 Coming this weekend — our biggest sale of the year! Stay tuned. #sale #deals",
             platforms=json.dumps(["fb","ig"]), status="scheduled",
             scheduled_at=datetime(2025,3,22,9,0,tzinfo=timezone.utc),
             created_at=now),
        Post(user_id=user.id, text="Draft: ideas for Q4 campaign — product benefits, testimonials, holiday theme",
             platforms=json.dumps(["tw"]), status="draft", created_at=now),
    ]
    db.session.add_all(posts)

    # Demo accounts
    platforms = [
        Account(user_id=user.id, platform_id="fb",  name="Facebook",   icon="📘", connected=True,  handle="@DemoPage"),
        Account(user_id=user.id, platform_id="ig",  name="Instagram",  icon="📷", connected=True,  handle="@demobrand"),
        Account(user_id=user.id, platform_id="tw",  name="X (Twitter)",icon="🐦", connected=True,  handle="@DemoUser"),
        Account(user_id=user.id, platform_id="li",  name="LinkedIn",   icon="💼", connected=True,  handle="Demo Company"),
        Account(user_id=user.id, platform_id="yt",  name="YouTube",    icon="▶️", connected=False, handle=""),
    ]
    db.session.add_all(platforms)

    # Welcome notifications
    notifs = [
        Notification(user_id=user.id, text="Welcome to SocialAI! Start by creating your first post.", type="info"),
        Notification(user_id=user.id, text='Post "Excited to launch our new product" published successfully.', type="success"),
        Notification(user_id=user.id, text='Post "Coming this weekend" is scheduled.', type="info"),
    ]
    db.session.add_all(notifs)
    db.session.commit()
    print("✅  Demo data seeded — login: demo@demo.com / demo123")


# ── Entry Point ─────────────────────────────────────────────────
app = create_app()

if __name__ == "__main__":
    start_scheduler(app)          # background scheduler for auto-publish
    print("\n🚀  SocialAI backend running at http://localhost:5000")
    print("📋  API docs at         http://localhost:5000/api/docs\n")
    app.run(host="0.0.0.0", port=5000, debug=True, use_reloader=False)
