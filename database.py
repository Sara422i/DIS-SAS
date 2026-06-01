import psycopg2
import os

user = os.environ.get('PGUSER', 'postgres')
password = os.environ.get('PGPASSWORD', '1234')
host = os.environ.get('HOST', '127.0.0.1')

def db_connection():
    db = "dbname='Travelpack' user=" + user + " host=" + host + " password=" + password
    conn = psycopg2.connect(db)
    return conn

def init_db():
    conn = db_connection()
    cur = conn.cursor()

    cur.execute('''CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        username TEXT NOT NULL UNIQUE,
        login TEXT NOT NULL UNIQUE)''')
    
    cur.execute('''CREATE TABLE IF NOT EXISTS trips (
        id SERIAL PRIMARY KEY,
        title TEXT NOT NULL,
        start_date DATE NOT NULL,
        end_date DATE NOT NULL,
        user_id INTEGER NOT NULL REFERENCES users(id))''')

    cur.execute('''CREATE TABLE IF NOT EXISTS destinations (
        id SERIAL PRIMARY KEY,
        name TEXT NOT NULL,
        destination_type TEXT NOT NULL,
        currency TEXT)''')

    cur.execute('''CREATE TABLE IF NOT EXISTS visits (
        trip_id INTEGER NOT NULL REFERENCES trips(id),
        destination_id INTEGER NOT NULL REFERENCES destinations(id),
        arrival DATE NOT NULL,
        departure DATE NOT NULL,
        PRIMARY KEY (trip_id, destination_id))''')

    cur.execute('''CREATE TABLE IF NOT EXISTS weather (
        destination_id INTEGER NOT NULL REFERENCES destinations(id),
        date DATE NOT NULL,
        temperature_min FLOAT,
        temperature_max FLOAT,
        precipitation FLOAT,
        uv_index FLOAT,
        weather_code INTEGER,
        PRIMARY KEY (destination_id, date))''')

    cur.execute('''CREATE TABLE IF NOT EXISTS packlists (
        id SERIAL PRIMARY KEY,
        trip_id INTEGER NOT NULL UNIQUE REFERENCES trips(id))''')

    cur.execute('''CREATE TABLE IF NOT EXISTS packitems (
        id SERIAL PRIMARY KEY,
        name TEXT NOT NULL,
        category TEXT,
        is_packed BOOLEAN DEFAULT FALSE,
        packlist_id INTEGER NOT NULL REFERENCES packlists(id))''')

    cur.execute("""INSERT INTO users (username, login)
        VALUES (%s, %s)
        ON CONFLICT (username)
        DO UPDATE SET login = EXCLUDED.login""", ("testbruger", "test@test.dk"))

    conn.commit()
    cur.close()
    conn.close()