from flask import Blueprint, render_template, request, redirect
from database import db_connection

bp = Blueprint('trip', __name__)

@bp.route('/', methods=['GET', 'POST'])
def list_trips():
    conn = db_connection()
    cur = conn.cursor()

    if request.method == 'POST':
        title = request.form['title']
        start_date = request.form['start_date']
        end_date = request.form['end_date']
        user_id = 1

        cur.execute(
            'INSERT INTO trips (title, start_date, end_date, user_id) VALUES (%s, %s, %s, %s)',
            (title, start_date, end_date, user_id)
        )

        conn.commit()

    cur.execute('SELECT id, title, start_date, end_date FROM trips')
    trips = cur.fetchall()

    cur.execute("""
        SELECT visits.trip_id,
               destinations.id,
               destinations.name,
               visits.arrival,
               visits.departure
        FROM visits
        JOIN destinations ON visits.destination_id = destinations.id
        ORDER BY visits.arrival
    """)

    destination_rows = cur.fetchall()

    trip_destinations = {}

    for row in destination_rows:
        trip_id = row[0]

        if trip_id not in trip_destinations:
            trip_destinations[trip_id] = []

        trip_destinations[trip_id].append(row)

    cur.close()
    conn.close()

    return render_template(
        'trip.html',
        trips=trips,
        trip_destinations=trip_destinations
    )


@bp.route("/trips/<int:trip_id>/delete", methods=["POST"])
def delete_trip(trip_id):
    conn = db_connection()
    cur = conn.cursor()

    cur.execute("""
        DELETE FROM visits
        WHERE trip_id = %s
    """, (trip_id,))

    cur.execute("""
        DELETE FROM packitems
        WHERE packlist_id IN (
            SELECT id FROM packlists
            WHERE trip_id = %s
        )
    """, (trip_id,))

    cur.execute("""
        DELETE FROM packlists
        WHERE trip_id = %s
    """, (trip_id,))

    cur.execute("""
        DELETE FROM trips
        WHERE id = %s
    """, (trip_id,))

    conn.commit()

    cur.close()
    conn.close()

    return redirect("/")