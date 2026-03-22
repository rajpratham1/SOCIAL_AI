"""routes/ai.py — AI suggestions via Anthropic Claude API + save/list/delete."""
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
import json
import re

from database import db
from models   import AISuggestion

ai_bp = Blueprint("ai", __name__)


def _call_gemini(prompt: str) -> str:
    """Call Google Gemini API and return the text response."""
    import urllib.request
    import urllib.error

    api_key = current_app.config.get("GEMINI_API_KEY", "")
    if not api_key:
        raise ValueError("GEMINI_API_KEY is not set in config.py or environment")

    # Gemini API expects a specific structure
    payload = json.dumps({
        "contents": [{
            "parts": [{"text": prompt}]
        }]
    }).encode()

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"

    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read())
            # Gemini response structure: candidate -> content -> parts -> text
            candidates = data.get("candidates", [])
            if not candidates:
                return ""
            parts = candidates[0].get("content", {}).get("parts", [])
            return "".join(p.get("text", "") for p in parts)
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        raise RuntimeError(f"Gemini API error {e.code}: {body}")


# ── POST /api/ai/suggest ─────────────────────────────────────────
# Body: { topic, tone, platform }
# Returns: { suggestions: [{type, content, hashtags}, ...] }
@ai_bp.route("/suggest", methods=["POST"])
@jwt_required()
def suggest():
    data     = request.get_json(silent=True) or {}
    topic    = (data.get("topic")    or "").strip()
    tone     = (data.get("tone")     or "Professional").strip()
    platform = (data.get("platform") or "Instagram").strip()

    if not topic:
        return jsonify({"error": "topic is required"}), 400

    prompt = f"""You are a world-class social media strategist.
Generate exactly 3 distinct post suggestions for:
- Topic:    {topic}
- Tone:     {tone}
- Platform: {platform}

Respond ONLY with valid JSON (no markdown, no backticks):
{{
  "suggestions": [
    {{"type": "Post Idea",        "content": "...", "hashtags": "#tag1 #tag2 #tag3"}},
    {{"type": "Engaging Question","content": "...", "hashtags": "#tag1 #tag2"}},
    {{"type": "Call to Action",   "content": "...", "hashtags": "#tag1 #tag2 #tag3"}}
  ]
}}"""

    try:
        raw  = _call_gemini(prompt)
        # Strip possible markdown fences
        clean = re.sub(r"```(?:json)?|```", "", raw).strip()
        parsed = json.loads(clean)
        suggestions = parsed.get("suggestions", [])
    except (ValueError, RuntimeError) as e:
        return jsonify({"error": str(e)}), 502
    except json.JSONDecodeError:
        return jsonify({"error": "AI returned invalid JSON", "raw": raw[:500]}), 502

    return jsonify({"suggestions": suggestions}), 200


# ── POST /api/ai/caption ─────────────────────────────────────────
# Body: { text? }  → returns a single caption string
@ai_bp.route("/caption", methods=["POST"])
@jwt_required()
def caption():
    data = request.get_json(silent=True) or {}
    text = (data.get("text") or "").strip()
    prompt = (
        f"Generate 1 creative, engaging social media caption for: {text}"
        if text else
        "Generate 1 creative, engaging social media caption for a general post."
    )
    prompt += "\nReturn ONLY the caption text, nothing else."
    try:
        result = _call_gemini(prompt)
        return jsonify({"caption": result.strip()}), 200
    except (ValueError, RuntimeError) as e:
        return jsonify({"error": str(e)}), 502


# ── POST /api/ai/hashtags ────────────────────────────────────────
# Body: { text? }  → returns hashtag string
@ai_bp.route("/hashtags", methods=["POST"])
@jwt_required()
def hashtags():
    data = request.get_json(silent=True) or {}
    text = (data.get("text") or "").strip()
    prompt = (
        f"Generate 10 relevant trending hashtags for: {text}"
        if text else
        "Generate 10 relevant trending hashtags for a general social media post."
    )
    prompt += "\nReturn ONLY the hashtags separated by spaces, nothing else."
    try:
        result = _call_gemini(prompt)
        return jsonify({"hashtags": result.strip()}), 200
    except (ValueError, RuntimeError) as e:
        return jsonify({"error": str(e)}), 502


# ── POST /api/ai/timing ──────────────────────────────────────────
# Returns best posting times advice
@ai_bp.route("/timing", methods=["POST"])
@jwt_required()
def timing():
    prompt = ("What are the 3 best times to post on social media for maximum engagement? "
              "Give a short, practical answer with specific times and reasons.")
    try:
        result = _call_claude(prompt, max_tokens=300)
        return jsonify({"advice": result.strip()}), 200
    except (ValueError, RuntimeError) as e:
        return jsonify({"error": str(e)}), 502


# ── GET /api/ai/suggestions ──────────────────────────────────────
@ai_bp.route("/suggestions", methods=["GET"])
@jwt_required()
def list_suggestions():
    uid = int(get_jwt_identity())
    suggs = (
        AISuggestion.query
        .filter_by(user_id=uid)
        .order_by(AISuggestion.created_at.desc())
        .all()
    )
    return jsonify({"suggestions": [s.to_dict() for s in suggs]}), 200


# ── POST /api/ai/suggestions ─────────────────────────────────────
# Body: { type, content, hashtags, topic, platform, tone }
@ai_bp.route("/suggestions", methods=["POST"])
@jwt_required()
def save_suggestion():
    uid  = int(get_jwt_identity())
    data = request.get_json(silent=True) or {}

    content = (data.get("content") or "").strip()
    if not content:
        return jsonify({"error": "content is required"}), 400

    sugg = AISuggestion(
        user_id  = uid,
        type     = data.get("type", "Suggestion"),
        content  = content,
        hashtags = data.get("hashtags", ""),
        topic    = data.get("topic", ""),
        platform = data.get("platform", ""),
        tone     = data.get("tone", ""),
    )
    db.session.add(sugg)
    db.session.commit()
    return jsonify({"suggestion": sugg.to_dict()}), 201


# ── DELETE /api/ai/suggestions/<id> ─────────────────────────────
@ai_bp.route("/suggestions/<int:sugg_id>", methods=["DELETE"])
@jwt_required()
def delete_suggestion(sugg_id):
    uid  = int(get_jwt_identity())
    sugg = AISuggestion.query.filter_by(id=sugg_id, user_id=uid).first_or_404()
    db.session.delete(sugg)
    db.session.commit()
    return jsonify({"message": "Suggestion deleted"}), 200
