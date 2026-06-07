## Members of the project:
Annis Isaac Nazaroi- WQD153
Sarah Rosenqvist Henriksen - RWZ996
Susanna Gerencer Heinesen - LNZ132

## How to Compile the Web Application from Source

The application is built and run using Docker and Docker Compose.

From the root directory of the project, run:

```bash
docker compose up --build
```

This command builds the Flask web application from source and starts both the application container and the PostgreSQL database container.

The database is initialized automatically when the application starts. The `init_db()` function in `database.py` creates all required tables if they do not already exist:

* `users`
* `trips`
* `destinations`
* `visits`
* `weather`
* `packlists`
* `packitems`

```

If the database should be reset completely, stop the containers and remove volumes:

```bash
docker compose down -v
```

Then rebuild and restart the application:

```bash
docker compose up --build
```

## How to Run and Interact with the Web Application

Start the application with:

```bash
docker compose up --build
```

When the application is running, open the following URL in a browser:

```text
http://localhost:5000
```

From the web interface, the user can:

1. Create a new trip by entering a title, start date, and end date.
2. Add destinations to a trip.
3. Select a destination type, such as city, beach, ski, hiking, camping, or work.
4. Add arrival and departure dates for each destination.
5. View the packing list for a trip.
6. Manually add items to the packing list.
7. Mark items as packed or unpacked.
8. Delete trips, destinations, or packing items.
9. Generate packing suggestions based on destination type.
10. Receive weather-based packing suggestions when weather data is available.

The application uses the Open-Meteo API to retrieve weather data for destinations. If the external API is unavailable, the application still works, but weather-based packing suggestions may not be generated.

## AI Declaration

AI tools were used during the development and writing process of this project.

AI assistance was used for:

* Explaining and debugging parts of the implementation
* Improving wording and clarity in written project material
* Generating suggestions for code organization and documentation

All code and project decisions were reviewed and adapted by the group members
