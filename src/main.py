import os

from . import create_app

app = create_app()


if __name__ == "__main__":
    debug_enabled = os.getenv("TCC_DEBUG", "false").lower() in {"1", "true", "yes", "on"}
    app.run(debug=debug_enabled)
