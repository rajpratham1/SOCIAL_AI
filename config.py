"""
config.py — App configuration
All sensitive values can be overridden via environment variables.
"""
import os
from datetime import timedelta
from dotenv import load_dotenv

# Load local environment variables if they exist
load_dotenv(dotenv_path="env.local")
load_dotenv() # also load .env if it exists

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    # ── Security ────────────────────────────────────────────────
    SECRET_KEY = os.environ.get("SECRET_KEY", "socialai-super-secret-change-in-prod")
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "socialai-jwt-secret-change-in-prod")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(days=7)

    # ── Database (SQLite — stored in instance/ folder) ──────────
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        f"sqlite:///{os.path.join(BASE_DIR, 'instance', 'socialai.db')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # ── AI Services ──────────────────────────────────────────────
    # Anthropic (legacy)
    ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
    # Google Gemini
    GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
    if not GEMINI_API_KEY or GEMINI_API_KEY == "[GCP_API_KEY]":
        GEMINI_API_KEY = "AIzaSyBZD6-jGhJ-95VXqGuBpLnTEYwgK4nCdWw" # Fallback to known working key

    # ── CORS ────────────────────────────────────────────────────
    CORS_ORIGINS = ["http://localhost:3000", "http://localhost:5000",
                    "http://127.0.0.1:5000", "http://127.0.0.1:3000"]

    # ── Scheduler ───────────────────────────────────────────────
    SCHEDULER_INTERVAL_SECONDS = 60   # check for scheduled posts every 60s
