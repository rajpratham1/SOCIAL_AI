"""routes/notifs.py — Get, read-all, clear notifications."""
from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from database import db
from models   import Notification

notifs_bp = Blueprint("notifs", __name__)


# ── GET /api/notifications ───────────────────────────────────────
@notifs_bp.route("", methods=["GET"])
@jwt_required()
def get_notifs():
    uid    = int(get_jwt_identity())
    notifs = (
        Notification.query
        .filter_by(user_id=uid)
        .order_by(Notification.created_at.desc())
        .limit(50)
        .all()
    )
    unread = sum(1 for n in notifs if not n.read)
    return jsonify({
        "notifications": [n.to_dict() for n in notifs],
        "unread": unread,
    }), 200


# ── POST /api/notifications/read-all ────────────────────────────
@notifs_bp.route("/read-all", methods=["POST"])
@jwt_required()
def read_all():
    uid = int(get_jwt_identity())
    Notification.query.filter_by(user_id=uid, read=False).update({"read": True})
    db.session.commit()
    return jsonify({"message": "All notifications marked as read"}), 200


# ── DELETE /api/notifications ────────────────────────────────────
@notifs_bp.route("", methods=["DELETE"])
@jwt_required()
def clear_all():
    uid = int(get_jwt_identity())
    Notification.query.filter_by(user_id=uid).delete()
    db.session.commit()
    return jsonify({"message": "Notifications cleared"}), 200


# ── DELETE /api/notifications/<id> ──────────────────────────────
@notifs_bp.route("/<int:notif_id>", methods=["DELETE"])
@jwt_required()
def delete_notif(notif_id):
    uid   = int(get_jwt_identity())
    notif = Notification.query.filter_by(id=notif_id, user_id=uid).first_or_404()
    db.session.delete(notif)
    db.session.commit()
    return jsonify({"message": "Notification deleted"}), 200
