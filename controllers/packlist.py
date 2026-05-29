from flask import Blueprint, render_template, request, redirect, url_for
from database import db_connection

packlist_bp = Blueprint("packlist", __name__)


@packlist_bp.route("/trips/<int:trip_id>/packlist", methods=["GET", "POST"])
def show_packlist(trip_id):
    conn = db_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT id, title, start_date, end_date
        FROM trips
        WHERE id = %s
    """, (trip_id,))

    trip = cur.fetchone()

    cur.execute("""
        SELECT id
        FROM packlists
        WHERE trip_id = %s
    """, (trip_id,))

    packlist = cur.fetchone()

    if packlist is None:
        cur.execute("""
            INSERT INTO packlists (trip_id)
            VALUES (%s)
            RETURNING id
        """, (trip_id,))

        packlist_id = cur.fetchone()[0]
        conn.commit()
    else:
        packlist_id = packlist[0]

    if request.method == "POST":
        name = request.form["name"]

        cur.execute("""
            INSERT INTO packitems (name, packlist_id)
            VALUES (%s, %s)
        """, (name, packlist_id))

        conn.commit()

        cur.close()
        conn.close()

        return redirect(url_for("packlist.show_packlist", trip_id=trip_id))

    cur.execute("""
        SELECT id, name, is_packed
        FROM packitems
        WHERE packlist_id = %s
        ORDER BY name
    """, (packlist_id,))

    items = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        "packlist.html",
        trip=trip,
        items=items
    )


@packlist_bp.route("/trips/<int:trip_id>/packitems/<int:item_id>/toggle", methods=["POST"])
def toggle_item(trip_id, item_id):
    conn = db_connection()
    cur = conn.cursor()

    cur.execute("""
        UPDATE packitems
        SET is_packed = NOT is_packed
        WHERE id = %s
    """, (item_id,))

    conn.commit()

    cur.close()
    conn.close()

    return redirect(url_for("packlist.show_packlist", trip_id=trip_id))


@packlist_bp.route("/trips/<int:trip_id>/packitems/<int:item_id>/delete", methods=["POST"])
def delete_item(trip_id, item_id):
    conn = db_connection()
    cur = conn.cursor()

    cur.execute("""
        DELETE FROM packitems
        WHERE id = %s
    """, (item_id,))

    conn.commit()

    cur.close()
    conn.close()

    return redirect(url_for("packlist.show_packlist", trip_id=trip_id))

@packlist_bp.route("/trips/<int:trip_id>/packlist/generate", methods=["POST"])
def generate_suggestions(trip_id):
    conn = db_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT id
        FROM packlists
        WHERE trip_id = %s
    """, (trip_id,))

    packlist = cur.fetchone()

    if packlist is None:
        cur.execute("""
            INSERT INTO packlists (trip_id)
            VALUES (%s)
            RETURNING id
        """, (trip_id,))

        packlist_id = cur.fetchone()[0]
    else:
        packlist_id = packlist[0]

    cur.execute("""
        SELECT DISTINCT destinations.destination_type
        FROM visits
        JOIN destinations ON visits.destination_id = destinations.id
        WHERE visits.trip_id = %s
    """, (trip_id,))

    destination_types = cur.fetchall()

    suggestions_by_type = {
        "by": ["Gode sko", "Rygsæk", "Solbriller"],
        "strand": ["Badetøj", "Solcreme", "Håndklæde", "Solbriller"],
        "ski": ["Skijakke", "Handsker", "Hue", "Termoundertøj", "Skistøvler"],
        "cykeltur": ["Cykelhjelm", "Drikkedunk", "Cykeltøj", "Solbriller"],
        "fest": ["Festtøj", "Pæne sko", "Parfume", "Makeup"],
        "vandring": ["Vandresko", "Rygsæk", "Drikkedunk"],
        "camping": ["Sovepose", "Lommelygte", "Myggespray", "Liggeunderlag", "Telt", "Toilettaske", "Powerbank"],
        "arbejde": ["Laptop", "Oplader", "Notesbog", "Skriveredskaber", "Høretelefoner"],
        "familie": ["Spil", "Snacks", "Ekstra tøj"],
        "andet": []
    }

    suggested_items = set()

    for destination_type in destination_types:
        type_name = destination_type[0]

        if type_name in suggestions_by_type:
            suggested_items.update(suggestions_by_type[type_name])

    cur.execute("""
        SELECT LOWER(name)
        FROM packitems
        WHERE packlist_id = %s
    """, (packlist_id,))

    existing_items = {row[0] for row in cur.fetchall()}

    for item in suggested_items:
        if item.lower() not in existing_items:
            cur.execute("""
                INSERT INTO packitems (name, packlist_id)
                VALUES (%s, %s)
            """, (item, packlist_id))

    conn.commit()

    cur.close()
    conn.close()

    return redirect(url_for("packlist.show_packlist", trip_id=trip_id))