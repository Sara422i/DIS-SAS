from flask import Blueprint, render_template, request, redirect, url_for
from database import db_connection

destination_bp = Blueprint("destination", __name__)


@destination_bp.route("/trips/<int:trip_id>/destinations", methods=["GET", "POST"])
def show_destinations(trip_id):
    conn = db_connection()
    cur = conn.cursor()

    if request.method == "POST":
        name = request.form["name"]
        destination_type = request.form["destination_type"]
        currency = request.form["currency"]
        arrival = request.form["arrival"]
        departure = request.form["departure"]

        cur.execute("""
            SELECT start_date, end_date
            FROM trips
            WHERE id = %s
        """, (trip_id,))

        trip_dates = cur.fetchone()

        if arrival < str(trip_dates[0]) or departure > str(trip_dates[1]) or arrival > departure:
            cur.close()
            conn.close()
            return "Destinationens datoer skal ligge inden for rejsens datoer."

        cur.execute("""
            INSERT INTO destinations (name, destination_type, currency)
            VALUES (%s, %s, %s)
            RETURNING id
        """, (name, destination_type, currency))

        destination_id = cur.fetchone()[0]

        cur.execute("""
            INSERT INTO visits (trip_id, destination_id, arrival, departure)
            VALUES (%s, %s, %s, %s)
        """, (trip_id, destination_id, arrival, departure))

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