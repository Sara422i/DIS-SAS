from flask import Flask
from database import init_db
from controllers import trip
from controllers.destination import destination_bp
from controllers.packlist import packlist_bp

init_db()

app = Flask(__name__)

@app.template_filter("dkdate")
def dkdate(value):
    months = [
        "",
        "januar",
        "februar",
        "marts",
        "april",
        "maj",
        "juni",
        "juli",
        "august",
        "september",
        "oktober",
        "november",
        "december"
    ]

    return f"{value.day}. {months[value.month]} {value.year}"

app.register_blueprint(trip.bp)

app.register_blueprint(destination_bp)

app.register_blueprint(packlist_bp)