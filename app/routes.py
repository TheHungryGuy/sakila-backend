# app/routes.py

from datetime import datetime
from flask import jsonify, request
from sqlalchemy import Text, text, func
from . import app
from .models import Actor, Film, FilmActor, Inventory, Rental, Customer, db


# Route to check if a customer ID exists
@app.route("/check_customer/<int:customer_id>")
def check_customer(customer_id):
    # Check if the customer ID exists in the database
    customer_exists = (
        Customer.query.filter_by(customer_id=customer_id).first() is not None
    )
    return jsonify({"customer_exists": customer_exists})


# Route to check if a movie is available
@app.route("/check_movie_availability/<int:film_id>")
def check_movie_availability(film_id):
    # Check if the movie with the given ID is available in the inventory
    inventory = (
        Inventory.query.filter_by(film_id=film_id)
        .filter(Inventory.available_copies > 0)
        .first()
    )
    return jsonify({"movie_available": inventory is not None})


# Route to rent a movie to a customer
@app.route("/rent_movie/<int:inventory_id>/<int:customer_id>", methods=["POST"])
def rent_movie(inventory_id, customer_id):
    # Get the current date and time
    rental_date = datetime.utcnow()

    # Hardcode the staff ID for now
    staff_id = 1

    # Insert a new rental record into the database
    new_rental = Rental(
        rental_date=rental_date,
        inventory_id=inventory_id,
        customer_id=customer_id,
        staff_id=staff_id,
    )
    db.session.add(new_rental)
    db.session.commit()

    return jsonify({"message": f"Movie rented successfully to ID#{customer_id}"})


# Route to display all films
@app.route("/all_films")
def display_films():
    # Retrieve all films from the database
    films = Film.query.all()

    # Convert the list of films to JSON format
    films_data = [
        {
            "film_id": film.film_id,
            "title": film.title,
            "description": film.description,
            "release_year": film.release_year,
            "rating": film.rating,
            "special_features": film.special_features,
        }
        for film in films
    ]
    return jsonify({"films": films_data})


# Route to get the top 5 most rented movies
@app.route("/top_rented_movies")
def top_rented_movies():
    # Query the database to get the top 5 most rented movies
    top_movies = (
        db.session.query(
            Film.title,
            Film.description,
            Film.release_year,
            Film.rating,
            Film.special_features,
            func.count(Rental.rental_id).label("rental_count"),
        )
        .join(Inventory, Film.film_id == Inventory.film_id)
        .join(Rental, Inventory.inventory_id == Rental.inventory_id)
        .group_by(Film.film_id)
        .order_by(func.count(Rental.rental_id).desc())
        .limit(5)
        .all()
    )

    # Convert the result to a list of dictionaries
    top_movies_data = [
        {
            "title": title,
            "description": description,
            "releaseYear": release_year,
            "rating": rating,
            "specialFeatures": special_features,
            "rentalCount": rental_count,
        }
        for title, description, release_year, rating, special_features, rental_count in top_movies
    ]

    return jsonify({"top_movies": top_movies_data})


# Route to get additional details for a specific movie
@app.route("/movie_details/<string:title>")
def movie_details(title):
    # Query the database to get details of the movie with the given title
    movie = Film.query.filter_by(title=title).first()

    if movie:
        # Return movie details as JSON
        return jsonify(
            {
                "description": movie.description,
                "releaseYear": movie.release_year,
                "rating": movie.rating,
                "specialFeatures": movie.special_features,
            }
        )
    else:
        return jsonify({"error": "Movie not found"})


# Route to get the top actors based on movie count
@app.route("/top_actors")
def top_actors():
    # Query the database to get the top actors based on movie count
    top_actors = (
        db.session.query(
            Actor.actor_id,
            Actor.first_name,
            Actor.last_name,
            func.concat(Actor.first_name, " ", Actor.last_name).label("full_name"),
            func.count(FilmActor.film_id).label("film_count"),
        )
        .join(FilmActor, Actor.actor_id == FilmActor.actor_id)
        .group_by(Actor.actor_id, Actor.first_name, Actor.last_name)
        .order_by(-func.count(FilmActor.film_id))
        .limit(5)
        .all()
    )

    # Convert the result to a list of dictionaries
    top_actors_data = [
        {
            "actor_id": actor.actor_id,
            "first_name": actor.first_name,
            "last_name": actor.last_name,
            "full_name": actor.full_name,
            "film_count": actor.film_count,
        }
        for actor in top_actors
    ]

    return jsonify({"top_actors": top_actors_data})


# Route to get the top 5 movies for a specific actor
@app.route("/top_movies_for_actor/<int:actor_id>")
def top_movies_for_actor(actor_id):
    # Query the database to get the top 5 movies for the actor with the given ID
    top_movies = (
        db.session.query(
            Film.film_id, Film.title, func.count(Rental.rental_id).label("rental_count")
        )
        .join(FilmActor, Film.film_id == FilmActor.film_id)
        .join(Actor, FilmActor.actor_id == Actor.actor_id)
        .join(Inventory, Film.film_id == Inventory.film_id)
        .join(Rental, Inventory.inventory_id == Rental.inventory_id)
        .filter(Actor.actor_id == actor_id)
        .group_by(Film.film_id, Film.title)
        .order_by(func.count(Rental.rental_id).desc())
        .limit(5)
        .all()
    )

    # Convert the result to a list of dictionaries
    top_movies_data = [
        {"film_id": film_id, "title": title, "rental_count": rental_count}
        for film_id, title, rental_count in top_movies
    ]

    return jsonify({"top_movies": top_movies_data})


# Route to get information about movie copies
@app.route("/movie_copies_info")
def movie_copies_info():
    # Query to get information about the total number of copies, rentals, and remaining copies per movie
    movie_copies_info = (
        db.session.query(
            Film.film_id,
            Film.title.label("film_title"),
            func.count(Inventory.inventory_id).label("number_of_copies"),
        )
        .outerjoin(Inventory, Film.film_id == Inventory.film_id)
        .group_by(Film.film_id, Film.title)
        .order_by(Film.film_id, func.count(Inventory.inventory_id).desc())
        .all()
    )

    # Convert the result to a list of dictionaries
    movie_copies_data = [
        {
            "film_id": film_id,
            "film_title": film_title,
            "number_of_copies": number_of_copies,
        }
        for film_id, film_title, number_of_copies in movie_copies_info
    ]

    return jsonify({"movie_copies_info": movie_copies_data})


# Route to get information about movies
@app.route("/movie_info")
def movie_info():
    # Get the movie_id from the query parameters
    movie_id = request.args.get("movie_id", type=int)

    # If movie_id is not provided, return information for all movies
    if movie_id is None:
        # Query to get information about the total number of copies, rentals, and remaining copies for all movies
        results = (
            db.session.query(
                Film.film_id,
                Film.title.label("film_title"),
                db.func.coalesce(db.func.count(Inventory.inventory_id), 0).label(
                    "number_of_copies"
                ),
                db.func.coalesce(db.func.count(Rental.rental_id), 0).label(
                    "number_of_rentals_out"
                ),
                db.func.coalesce(
                    db.func.count(Inventory.inventory_id)
                    - db.func.count(Rental.rental_id),
                    0,
                ).label("remaining_copies"),
            )
            .outerjoin(Inventory, Film.film_id == Inventory.film_id)
            .outerjoin(
                Rental,
                (Inventory.inventory_id == Rental.inventory_id)
                & (Rental.return_date.is_(None)),
            )
            .group_by(Film.film_id, Film.title)
            .order_by(Film.film_id)
            .all()
        )

        films_info = []
        for result in results:
            films_info.append(
                {
                    "film_id": result.film_id,
                    "film_title": result.film_title,
                    "number_of_copies": result.number_of_copies,
                    "number_of_rentals_out": result.number_of_rentals_out,
                    "remaining_copies": result.remaining_copies,
                }
            )

        return jsonify(films_info)

    # If movie_id is provided, return information for the specific movie
    result = (
        db.session.query(
            Film.film_id,
            Film.title.label("film_title"),
            db.func.coalesce(db.func.count(Inventory.inventory_id), 0).label(
                "number_of_copies"
            ),
            db.func.coalesce(db.func.count(Rental.rental_id), 0).label(
                "number_of_rentals_out"
            ),
            db.func.coalesce(
                db.func.count(Inventory.inventory_id) - db.func.count(Rental.rental_id),
                0,
            ).label("remaining_copies"),
        )
        .outerjoin(Inventory, Film.film_id == Inventory.film_id)
        .outerjoin(
            Rental,
            (Inventory.inventory_id == Rental.inventory_id)
            & (Rental.return_date.is_(None)),
        )
        .filter(Film.film_id == movie_id)
        .group_by(Film.film_id, Film.title)
        .first()
    )

    if result is None:
        return jsonify({"error": "Movie not found"}), 404

    film_info = {
        "film_id": result.film_id,
        "film_title": result.film_title,
        "number_of_copies": result.number_of_copies,
        "number_of_rentals_out": result.number_of_rentals_out,
        "remaining_copies": result.remaining_copies,
    }

    return jsonify(film_info)


# Route to get remaining inventory for a movie
@app.route('/remaining_inventory/<int:film_id>', methods=['GET'])
def remaining_inventory(film_id):
    # SQL query to get remaining inventory for a movie
    query = """
        SELECT
            i.inventory_id,
            f.film_id,
            f.title AS film_title
        FROM
            inventory i
        JOIN
            film f ON i.film_id = f.film_id
        LEFT JOIN
            rental r ON i.inventory_id = r.inventory_id AND r.return_date IS NULL
        WHERE
            r.rental_id IS NULL
            AND f.film_id = :film_id
        ORDER BY
            i.inventory_id;
    """
    with db.engine.connect() as connection:
        result = connection.execute(text(query), {'film_id': film_id})  # Use text() function
        # Convert each row to a dictionary
        data = [dict(row._mapping) for row in result]
        return jsonify(data)


# Route to fetch customer list
@app.route('/customers', methods=['GET'])
def get_customer_list():
    # SQL query to fetch customer list with additional details
    query = """
            SELECT 
                customer.customer_id,
                customer.first_name,
                customer.last_name,
                customer.email,
                address.address,
                city.city,
                country.country,
                address.phone,
                customer.store_id,
                customer.create_date AS registration_date,
                customer.last_update
            FROM 
                customer
            JOIN 
                address ON customer.address_id = address.address_id
            JOIN 
                city ON address.city_id = city.city_id
            JOIN 
                country ON city.country_id = country.country_id
            ORDER BY
                customer.customer_id;
        """
    with db.engine.connect() as connection:
        result = connection.execute(text(query))
        # Convert each row to a dictionary
        data = [dict(row._mapping) for row in result]
        return jsonify(data)


