"""
models.py — All database models for SocialAI.
Tables: users, posts, accounts, notifications, ai_suggestions
"""
from datetime import datetime, timezone
from database import db
import json


# ── helpers ─────────────────────────────────────────────────────
def utcnow():
    return datetime.now(timezone.utc)


# ── User ────────────────────────────────────────────────────────
class User(db.Model):
    __tablename__ = "users"

    id            = db.Column(db.Integer, primary_key=True)
    name          = db.Column(db.String(120), nullable=False)
    email         = db.Column(db.String(200), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at    = db.Column(db.DateTime(timezone=True), default=utcnow)

    # relationships
    posts         = db.relationship("Post",         back_populates="user", cascade="all, delete-orphan")
    accounts      = db.relationship("Account",      back_populates="user", cascade="all, delete-orphan")
    notifications = db.relationship("Notification", back_populates="user", cascade="all, delete-orphan")
    suggestions   = db.relationship("AISuggestion", back_populates="user", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id":         self.id,
            "name":       self.name,
            "email":      self.email,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


# ── Post ────────────────────────────────────────────────────────
class Post(db.Model):
    __tablename__ = "posts"

    id           = db.Column(db.Integer, primary_key=True)
    user_id      = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    text         = db.Column(db.Text, nullable=False)
    platforms    = db.Column(db.Text, default="[]")   # JSON list, e.g. ["fb","ig"]
    status       = db.Column(db.String(20), default="draft", index=True)
    # analytics (simulated / real)
    likes        = db.Column(db.Integer, default=0)
    comments     = db.Column(db.Integer, default=0)
    shares       = db.Column(db.Integer, default=0)
    reach        = db.Column(db.Integer, default=0)
    # optional image URL
    img          = db.Column(db.Text, nullable=True)
    # timestamps
    created_at   = db.Column(db.DateTime(timezone=True), default=utcnow, index=True)
    scheduled_at = db.Column(db.DateTime(timezone=True), nullable=True)
    published_at = db.Column(db.DateTime(timezone=True), nullable=True)

    user = db.relationship("User", back_populates="posts")

    # ── Platform helpers ─────────────────────────────────────────
    def get_platforms(self):
        try:
            return json.loads(self.platforms or "[]")
        except Exception:
            return []

    def set_platforms(self, lst):
        self.platforms = json.dumps(lst)

    def to_dict(self):
        return {
            "id":           self.id,
            "user_id":      self.user_id,
            "text":         self.text,
            "platforms":    self.get_platforms(),
            "status":       self.status,
            "likes":        self.likes,
            "comments":     self.comments,
            "shares":       self.shares,
            "reach":        self.reach,
            "img":          self.img,
            "created_at":   self.created_at.isoformat() if self.created_at else None,
            "scheduled_at": self.scheduled_at.isoformat() if self.scheduled_at else None,
            "published_at": self.published_at.isoformat() if self.published_at else None,
        }


# ── Social Media Account ─────────────────────────────────────────
class Account(db.Model):
    __tablename__ = "accounts"

    id          = db.Column(db.Integer, primary_key=True)
    user_id     = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    platform_id = db.Column(db.String(10), nullable=False)   # "fb","ig","tw","li","yt"
    name        = db.Column(db.String(60))                   # display name
    icon        = db.Column(db.String(10), default="")
    connected   = db.Column(db.Boolean, default=False)
    handle      = db.Column(db.String(120), default="")
    connected_at = db.Column(db.DateTime(timezone=True), nullable=True)

    user = db.relationship("User", back_populates="accounts")

    def to_dict(self):
        return {
            "id":           self.id,
            "platform_id":  self.platform_id,
            "name":         self.name,
            "icon":         self.icon,
            "connected":    self.connected,
            "handle":       self.handle,
            "connected_at": self.connected_at.isoformat() if self.connected_at else None,
        }


# ── Notification ────────────────────────────────────────────────
class Notification(db.Model):
    __tablename__ = "notifications"

    id         = db.Column(db.Integer, primary_key=True)
    user_id    = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    text       = db.Column(db.Text, nullable=False)
    type       = db.Column(db.String(20), default="info")   # info | success | error
    read       = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow)

    user = db.relationship("User", back_populates="notifications")

    def to_dict(self):
        return {
            "id":         self.id,
            "text":       self.text,
            "type":       self.type,
            "read":       self.read,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


# ── AI Suggestion (saved) ────────────────────────────────────────
class AISuggestion(db.Model):
    __tablename__ = "ai_suggestions"

    id         = db.Column(db.Integer, primary_key=True)
    user_id    = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    type       = db.Column(db.String(60), default="Suggestion")
    content    = db.Column(db.Text, nullable=False)
    hashtags   = db.Column(db.Text, default="")
    topic      = db.Column(db.String(120), default="")
    platform   = db.Column(db.String(60), default="")
    tone       = db.Column(db.String(40), default="")
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow)

    user = db.relationship("User", back_populates="suggestions")

    def to_dict(self):
        return {
            "id":         self.id,
            "type":       self.type,
            "content":    self.content,
            "hashtags":   self.hashtags,
            "topic":      self.topic,
            "platform":   self.platform,
            "tone":       self.tone,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
