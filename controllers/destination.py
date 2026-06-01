import re
from datetime import date
from flask import Blueprint, render_template, request, redirect, url_for
from database import db_connection
from services.weather_service import (
    get_coordinates, 
    get_weather_forecast, 
    save_weather_data, 
    add_weather_items_to_packlist
)

destination_bp = Blueprint("destination", __name__)


# Regex patterns
NAME_RE = re.compile(r"^[A-Za-zÆØÅæøå\s\-,\.]{2,100}$")
CURRENCY_RE = re.compile(r"^[A-Z]{3}$")
DATE_RE = re.compile(r"^\d{4}-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01])$")
DESTINATION_TYPE_RE = re.compile(
    r"^(by|strand|ski|cykeltur|fest|vandring|camping|arbejde|familie|andet)$"
)


def validate_name(value):
    return bool(NAME_RE.match(value)) if value else False


def validate_currency(value):
    return bool(CURRENCY_RE.match(value)) if value else False


def validate_date_format(value):
    return bool(DATE_RE.match(value)) if value else False


def validate_destination_type(value):
    return bool(DESTINATION_TYPE_RE.match(value)) if value else False


def parse_date(value):
    """
    Regex tjekker formatet YYYY-MM-DD.
    date.fromisoformat tjekker bagefter, om datoen faktisk findes.
    Fx bliver 2026-02-31 afvist.
    """
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


@destination_bp.route("/trips/<int:trip_id>/destinations", methods=["GET", "POST"])
def show_destinations(trip_id):
    conn = db_connection()
    cur = conn.cursor()

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        destination_type = request.form.get("destination_type", "").strip()
        currency = request.form.get("currency", "").strip().upper()
        arrival = request.form.get("arrival", "").strip()
        departure = request.form.get("departure", "").strip()

        errors = []

        # Regex validation
        if not validate_name(name):
            errors.append(
                "Destinationsnavnet er ugyldigt. Brug 2-100 tegn og kun bogstaver, mellemrum, bindestreg, komma eller punktum."
            )

        if not validate_destination_type(destination_type):
            errors.append("Destinationstypen er ugyldig.")

        if not validate_currency(currency):
            errors.append("Valuta skal være præcis 3 store bogstaver, fx DKK, EUR eller USD.")

        if not validate_date_format(arrival):
            errors.append("Ankomstdato skal være på formatet YYYY-MM-DD.")

        if not validate_date_format(departure):
            errors.append("Afrejsedato skal være på formatet YYYY-MM-DD.")

        arrival_date = parse_date(arrival)
        departure_date = parse_date(departure)

        if arrival_date is None:
            errors.append("Ankomstdatoen er ikke en gyldig dato.")

        if departure_date is None:
            errors.append("Afrejsedatoen er ikke en gyldig dato.")

        cur.execute("""
            SELECT start_date, end_date
            FROM trips
            WHERE id = %s
        """, (trip_id,))

        trip_dates = cur.fetchone()

        if trip_dates is None:
            cur.close()
            conn.close()
            return "Rejsen findes ikke.", 404

        trip_start = trip_dates[0]
        trip_end = trip_dates[1]

        if arrival_date is not None and departure_date is not None:
            if arrival_date < trip_start or departure_date > trip_end or arrival_date > departure_date:
                errors.append("Destinationens datoer skal ligge inden for rejsens datoer.")

        if errors:
            cur.close()
            conn.close()
            return "Fejl i input:<br>" + "<br>".join(errors), 400

        cur.execute("""
            INSERT INTO destinations (name, destination_type, currency)
            VALUES (%s, %s, %s)
            RETURNING id
        """, (name, destination_type, currency))

        destination_id = cur.fetchone()[0]

        cur.execute("""
            INSERT INTO visits (trip_id, destination_id, arrival, departure)
            VALUES (%s, %s, %s, %s)
        """, (trip_id, destination_id, arrival_date, departure_date))

        try:
            coordinates = get_coordinates(name)

            if coordinates:
                weather_data = get_weather_forecast(
                    coordinates["latitude"],
                    coordinates["longitude"],
                    arrival,
                    departure
                )

                save_weather_data(cur, destination_id, weather_data)

                add_weather_items_to_packlist(cur, trip_id, destination_id)

        except Exception as e:
            print(f"Weather data could not be fetched: {e}")
        
        conn.commit()

        cur.close()
        conn.close()

        return redirect(url_for("destination.show_destinations", trip_id=trip_id))

    cur.execute("""
        SELECT id, title, start_date, end_date
        FROM trips
        WHERE id = %s
    """, (trip_id,))

    trip = cur.fetchone()

    cur.execute("""
        SELECT destinations.name,
               destinations.destination_type,
               destinations.currency,
               visits.arrival,
               visits.departure
        FROM visits
        JOIN destinations ON visits.destination_id = destinations.id
        WHERE visits.trip_id = %s
        ORDER BY visits.arrival
    """, (trip_id,))

    destinations = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        "destination.html",
        trip=trip,
        destinations=destinations
    )


@destination_bp.route("/trips/<int:trip_id>/destinations/<int:destination_id>/delete", methods=["POST"])
def delete_destination(trip_id, destination_id):
    conn = db_connection()
    cur = conn.cursor()

    cur.execute("""
        DELETE FROM visits
        WHERE trip_id = %s AND destination_id = %s
    """, (trip_id, destination_id))

    cur.execute("""
        DELETE FROM destinations
        WHERE id = %s
    """, (destination_id,))

    conn.commit()

    cur.close()
    conn.close()

    return redirect(url_for("trip.list_trips"))