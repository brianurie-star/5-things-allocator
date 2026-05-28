import os

from flask import Blueprint, render_template, url_for

_PACKAGE_DIR = os.path.dirname(os.path.abspath(__file__))

ADVISOR_APPOINTMENT_URL = os.environ.get(
    "ADVISOR_APPOINTMENT_URL",
    "https://www.macu.com/burie",
)
VIRTUAL_ASSISTANT_URL = os.environ.get(
    "VIRTUAL_ASSISTANT_URL",
    ADVISOR_APPOINTMENT_URL,
)


def create_blueprint(url_prefix="/"):
    blueprint = Blueprint(
        "alpine_consulting",
        __name__,
        template_folder=os.path.join(_PACKAGE_DIR, "templates"),
        static_folder=os.path.join(_PACKAGE_DIR, "static"),
        static_url_path="/alpine-retirement-consulting-static",
        url_prefix=url_prefix,
    )

    @blueprint.route("/")
    def home():
        try:
            allocator_url = url_for("allocator")
        except RuntimeError:
            allocator_url = os.environ.get("ALLOCATOR_URL", "/allocator")

        try:
            five_things_home_url = url_for("home")
        except RuntimeError:
            five_things_home_url = os.environ.get("FIVE_THINGS_HOME_URL", "/five-things")

        return render_template(
            "open_for_business.html",
            advisor_url=ADVISOR_APPOINTMENT_URL,
            virtual_assistant_url=VIRTUAL_ASSISTANT_URL,
            allocator_url=allocator_url,
            five_things_home_url=five_things_home_url,
        )

    return blueprint
