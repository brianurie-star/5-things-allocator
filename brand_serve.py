"""Serve shared brand assets from /brand/ for all apps in the monorepo."""

import os

from flask import send_from_directory, url_for

_REPO_ROOT = os.path.dirname(os.path.abspath(__file__))
BRAND_DIR = os.path.join(_REPO_ROOT, "brand")


def register_brand_routes(app):
    @app.route("/brand/<path:filename>")
    def brand_static(filename):
        return send_from_directory(BRAND_DIR, filename)


def brand_asset(filename):
    """Build a URL for a shared brand file (use in templates as brand_asset('theme.css'))."""
    return url_for("brand_static", filename=filename)
