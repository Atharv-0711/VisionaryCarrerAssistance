import os

from app import app, socketio


def main():
    debug_mode = os.getenv("FLASK_DEBUG", "0").strip().lower() in {"1", "true", "yes"}
    port = int(os.getenv("PORT", "5053"))
    socketio.run(
        app,
        host="0.0.0.0",
        port=port,
        debug=debug_mode,
        use_reloader=debug_mode,
    )


if __name__ == "__main__":
    main()
