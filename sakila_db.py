from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func, text
from flask_cors import CORS  # Import CORS
from flask_migrate import Migrate
from datetime import datetime
import os
from dotenv import load_dotenv

app = Flask(__name__)
CORS(app)
# Set the SECRET_KEY for Flask
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
app.config[
    "SQLALCHEMY_DATABASE_URI"
] = f"mysql+pymysql://root:{app.config['SECRET_KEY']}@localhost/sakila"
db = SQLAlchemy(app)
migrate = Migrate(app, db)


class Film(db.Model):
    __tablename__ = "film"
    film_id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255))
    description = db.Column(db.Text)
    release_year = db.Column(db.Integer)
    rating = db.Column(db.String(10))
    special_features = db.Column(db.String(255))
    # Define the relationship with film_actor
    actors = db.relationship("FilmActor", back_populates="film")


class Actor(db.Model):
    __tablename__ = "actor"

    actor_id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(45), nullable=False)
    last_name = db.Column(db.String(45), nullable=False)
    # Define the relationship with film_actor
    films = db.relationship("FilmActor", back_populates="actor")


class FilmActor(db.Model):
    __tablename__ = "film_actor"

    film_id = db.Column(db.Integer, db.ForeignKey("film.film_id"), primary_key=True)
    actor_id = db.Column(db.Integer, db.ForeignKey("actor.actor_id"), primary_key=True)
    # Define the relationship with actor
    actor = db.relationship("Actor", back_populates="films")
    film = db.relationship("Film", back_populates="actors")


class Inventory(db.Model):
    __tablename__ = "inventory"
    inventory_id = db.Column(db.Integer, primary_key=True)
    film_id = db.Column(db.Integer, db.ForeignKey("film.film_id"))
    film = db.relationship("Film", backref="inventory")
    available_copies = db.Column(db.Integer)
class Staff(db.Model):
    __tablename__ = "staff"
    staff_id = db.Column(db.Integer, primary_key=True)

class Rental(db.Model):
    __tablename__ = "rental"
    rental_id = db.Column(db.Integer, primary_key=True)
    rental_date = db.Column(db.DateTime)
    inventory_id = db.Column(db.Integer, db.ForeignKey("inventory.inventory_id"))
    inventory = db.relationship("Inventory", backref="rentals")
    customer_id = db.Column(db.Integer, db.ForeignKey("customer.customer_id"))
    customer = db.relationship("Customer", backref="rentals")
    return_date = db.Column(db.DateTime)
    staff_id = db.Column(db.Integer, db.ForeignKey("staff.staff_id"))  # Add this line
    staff = db.relationship("Staff")  # Add this line

class Customer(db.Model):
    __tablename__ = "customer"
    customer_id = db.Column(db.Integer, primary_key=True)


# Route to check if a customer ID exists
@app.route("/check_customer/<int:customer_id>")
def check_customer(customer_id):
    customer_exists = (
        Customer.query.filter_by(customer_id=customer_id).first() is not None
    )
    return jsonify({"customer_exists": customer_exists})


# Route to check if a movie is available
@app.route("/check_movie_availability/<int:film_id>")
def check_movie_availability(film_id):
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

    # Hardcode the staff ID for now, you can modify this based on your requirements
    staff_id = 1  # Change this as needed

    # Insert a new rental record into the database
    new_rental = Rental(
        rental_date=rental_date,
        inventory_id=inventory_id,
        customer_id=customer_id,
        staff_id=staff_id
    )
    db.session.add(new_rental)
    db.session.commit()

    return jsonify({"message": "Movie rented successfully."})


@app.route("/all_films")
def display_films():
    films = Film.query.all()

    # Convert the list of films to a list of dictionaries with desired fields
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
    # Return the list of films as JSON
    return jsonify({"films": films_data})


# New API endpoint to get the top 5 most rented movies
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


# New API endpoint to get additional details for a specific movie
@app.route("/movie_details/<string:title>")
def movie_details(title):
    movie = Film.query.filter_by(title=title).first()

    if movie:
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


# New API endpoint to get the top actors based on movie count
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


# New API endpoint to get the top 5 movies for a specific actor
@app.route("/top_movies_for_actor/<int:actor_id>")
def top_movies_for_actor(actor_id):
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

    top_movies_data = [
        {"film_id": film_id, "title": title, "rental_count": rental_count}
        for film_id, title, rental_count in top_movies
    ]

    return jsonify({"top_movies": top_movies_data})


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


# New route for the SQL query
@app.route('/remaining_inventory/<int:film_id>', methods=['GET'])
def remaining_inventory(film_id):
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
        result = connection.execute(text(query), {'film_id': film_id})  # Pass film_id as a dictionary
        # Convert each row to a dictionary
        data = [dict(row._mapping) for row in result]
        return jsonify(data)


# Flask Route to Fetch Customer List
@app.route('/customers', methods=['GET'])
def get_customer_list():
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


if __name__ == "__main__":
    app.run(debug=True)
