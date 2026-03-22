"""
run.py — Simple runner script.
Usage:
    python run.py
"""
from app import app
from scheduler import start_scheduler

if __name__ == "__main__":
    start_scheduler(app)
    print("\n🚀  SocialAI backend running at http://localhost:5000")
    print("📋  API docs at         http://localhost:5000/api/docs\n")
    app.run(host="0.0.0.0", port=5000, debug=True, use_reloader=False)
