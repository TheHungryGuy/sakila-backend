# app/routes.py

from datetime import datetime
from flask import jsonify, request
from sqlalchemy import Text, text, func
from . import app
from .models import *


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

# Route to fetch movie list based on requested genre
@app.route('/films_by_genre', methods=['GET'])
def films_by_genre():
    # Get the genre name from the request or use an empty string if not provided
    genre_name = request.args.get('genre_name', '')

    with db.engine.connect() as connection:
        # SQL query to retrieve films by genre
        sql = """
            SELECT film.*
            FROM film
            JOIN film_category ON film.film_id = film_category.film_id
            JOIN category ON film_category.category_id = category.category_id
            WHERE category.name LIKE :genre_name
        """

        # Execute the query
        result = connection.execute(text(sql), {'genre_name': '%' + genre_name + '%'})

        # Fetch all results
        results = result.fetchall()

        # Convert results to a list of dictionaries
        films = [dict(row._mapping)for row in results]

        return jsonify({'films': films})
    
# Route to fetch movie list based on requested actor name
@app.route('/films_by_actor', methods=['GET'])
def films_by_actor():
    # Get the genre name from the request or use an empty string if not provided
    actor_name = request.args.get('actor_name', '')

    with db.engine.connect() as connection:
        # SQL query to retrieve films by actor
        sql = """
            SELECT film.*
            FROM film
            JOIN film_actor ON film.film_id = film_actor.film_id
            JOIN actor ON film_actor.actor_id = actor.actor_id
            WHERE CONCAT(actor.first_name, ' ', actor.last_name) LIKE :actor_name
        """

        # Execute the query
        result = connection.execute(text(sql), {'actor_name': '%' + actor_name + '%'})

        # Fetch all results
        results = result.fetchall()

        # Convert results to a list of dictionaries
        films = [dict(row._mapping)for row in results]

        return jsonify({'films': films})

# Route to fetch movie list based on requested movie title
@app.route('/films_by_title', methods=['GET'])
def films_by_title():
    # Get the genre name from the request or use an empty string if not provided
    title = request.args.get('title', '')

    with db.engine.connect() as connection:
        # SQL query to retrieve films by title
        sql = """
            SELECT *
            FROM film
            WHERE title LIKE :title
        """

        # Execute the query
        result = connection.execute(text(sql), {'title': '%' + title + '%'})

        # Fetch all results
        results = result.fetchall()

        # Convert results to a list of dictionaries
        films = [dict(row._mapping)for row in results]

        return jsonify({'films': films})
    
    
# Route to add a customer
@app.route('/insert_customer', methods=['POST'])
def insert_customer():
    # Extracting data from the request
    data = request.json
    store_id = 1 #We are combining both stores for the sake of the project timeline
    first_name = data.get('first_name')
    last_name = data.get('last_name')
    email = data.get('email')
    # address_id = data.get('address_id')
    address_id = 1 # Setting everyones address to 1 for the time being
    # SQL query to insert a new customer
    sql = """
        INSERT INTO customer (store_id, first_name, last_name, email, address_id)
        VALUES (:store_id, :first_name, :last_name, :email, :address_id)
    """

    with db.engine.connect() as connection:
        # Execute the query
        connection.execute(text(sql), {'store_id': store_id, 'first_name': first_name, 'last_name': last_name,
                                       'email': email, 'address_id': address_id})
        connection.commit()

    return jsonify({'message': 'Customer inserted successfully'})

# Route to update a customer
@app.route('/update_customer/<int:customer_id>', methods=['PUT'])
def update_customer(customer_id):
    # Extracting data from the request
    data = request.json
    first_name = data.get('first_name')
    last_name = data.get('last_name')
    email = data.get('email')

    # SQL query to update a customer
    sql = """
        UPDATE customer
        SET first_name = :first_name, last_name = :last_name, email = :email
        WHERE customer_id = :customer_id
    """

    with db.engine.connect() as connection:
        # Execute the query
        connection.execute(text(sql), {'first_name': first_name, 'last_name': last_name,
                                       'email': email, 'customer_id': customer_id})
        connection.commit()

    return jsonify({'message': 'Customer updated successfully'})

#Route to Delete a Customer
@app.route('/delete_customer/<int:customer_id>', methods=['DELETE']) 
def delete_customer(customer_id):
    # SQL query to delete a customer
    sql = """
        DELETE FROM customer
        WHERE customer_id = :customer_id
    """

    with db.engine.connect() as connection:
        # Execute the query
        connection.execute(text(sql), {'customer_id': customer_id})
        connection.commit()

    return jsonify({'message': 'Customer deleted successfully'})


# Route to fetch rental information for a customer
@app.route('/customer_rentals/<int:customer_id>', methods=['GET'])
def get_customer_rentals(customer_id):
    # SQL query to fetch rental information for the customer
    sql = """
        SELECT 
            rental.rental_id,
            film.title,
            rental.inventory_id,
            rental.rental_date,
            rental.return_date
        FROM 
            rental
        INNER JOIN 
            inventory ON rental.inventory_id = inventory.inventory_id
        INNER JOIN 
            film ON inventory.film_id = film.film_id
        WHERE 
            rental.customer_id = :customer_id
        ORDER BY 
            rental.return_date IS NULL DESC, rental.return_date DESC
    """

    with db.engine.connect() as connection:
        # Execute the query
        result = connection.execute(text(sql), {'customer_id': customer_id})
        # Fetch all results
        results = result.fetchall()

        # Convert results to a list of dictionaries
        rentals = [dict(row._mapping)for row in results]


        return jsonify({'rentals': rentals})
    
# Route to update the return date of a rental
@app.route('/update_return_date/<int:rental_id>', methods=['PUT'])
def update_return_date(rental_id):
    # Get the current timestamp
    current_timestamp = datetime.now()

    # SQL query to check if the return date is null
    check_sql = """
        SELECT return_date FROM rental WHERE rental_id = :rental_id
    """

    with db.engine.connect() as connection:
        # Execute the query to check return date
        result = connection.execute(text(check_sql), {'rental_id': rental_id})
        rental = result.fetchone()

        if rental is None:
            # If rental doesn't exist
            return jsonify({'error': 'Rental not found'}),404

        if rental[0] is not None:
            # If return date is not null, throw an error
            return jsonify({'error': 'Rental already Returned'}),400

        # SQL query to update the return date of a rental
        update_sql = """
            UPDATE rental
            SET return_date = :current_timestamp
            WHERE rental_id = :rental_id
        """
        # Execute the query to update return date
        connection.execute(text(update_sql), {'current_timestamp': current_timestamp, 'rental_id': rental_id})
        connection.commit()

    return jsonify({'message': 'Return date updated successfully'})