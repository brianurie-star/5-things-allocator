"""Run the Alpine Retirement Consulting site standalone (dev)."""

import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from flask import Flask

from alpine_retirement_consulting.routes import create_blueprint
from brand_serve import brand_asset, register_brand_routes

app = Flask(__name__)
register_brand_routes(app)
app.register_blueprint(create_blueprint(url_prefix="/"))
app.context_processor(lambda: {"brand_asset": brand_asset})


if __name__ == "__main__":
    app.run(debug=True, port=int(os.environ.get("PORT", 5001)))
