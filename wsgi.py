from gevent import monkey
monkey.patch_all()

import os
from app import create_app

try:
    from app.config import ProdConfig
    app = create_app(ProdConfig)
except Exception:
    os.environ.setdefault("FLASK_DEBUG", "0")
    app = create_app()