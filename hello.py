from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
from flask_cors import CORS  # Import CORS
from flask_migrate import Migrate
from datetime import datetime
import os
from dotenv import load_dotenv

app = Flask(__name__)
CORS(app)
# Set the SECRET_KEY for Flask
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql+pymysql://root:{app.config['SECRET_KEY']}@localhost/sakila"
db = SQLAlchemy(app)
migrate = Migrate(app, db)

class Film(db.Model):
    __tablename__ = 'film'
    film_id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255))
    description = db.Column(db.Text)
    release_year = db.Column(db.Integer)
    rating = db.Column(db.String(10))
    special_features = db.Column(db.String(255))


class Inventory(db.Model):
    __tablename__ = 'inventory'
    inventory_id = db.Column(db.Integer, primary_key=True)
    film_id = db.Column(db.Integer, db.ForeignKey('film.film_id'))
    film = db.relationship('Film', backref='inventory')
    available_copies = db.Column(db.Integer)

class Rental(db.Model):
    __tablename__ = 'rental'
    rental_id = db.Column(db.Integer, primary_key=True)
    rental_date = db.Column(db.DateTime)
    inventory_id = db.Column(db.Integer, db.ForeignKey('inventory.inventory_id'))
    inventory = db.relationship('Inventory', backref='rentals')
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.customer_id'))
    customer = db.relationship('Customer', backref='rentals')

class Customer(db.Model):
    __tablename__ = 'customer'
    customer_id = db.Column(db.Integer, primary_key=True)
    
    
    
# Route to check if a customer ID exists
@app.route('/check_customer/<int:customer_id>')
def check_customer(customer_id):
    customer_exists = Customer.query.filter_by(customer_id=customer_id).first() is not None
    return jsonify({'customer_exists': customer_exists})

# Route to check if a movie is available
@app.route('/check_movie_availability/<int:film_id>')
def check_movie_availability(film_id):
    inventory = Inventory.query.filter_by(film_id=film_id).filter(Inventory.available_copies > 0).first()
    return jsonify({'movie_available': inventory is not None})



# Route to rent a movie to a customer
@app.route('/rent_movie/<int:film_id>/<int:customer_id>', methods=['POST'])
def rent_movie(film_id, customer_id):
    movie = Film.query.get(film_id)
    customer = Customer.query.get(customer_id)

    if movie is not None and customer is not None:
        # Check if the movie has available copies
        inventory = Inventory.query.filter_by(film_id=film_id).filter(Inventory.available_copies > 0).first()

        if inventory is not None:
            # Update the available copies in the inventory
            inventory.available_copies -= 1

            # Create a new rental record
            rental = Rental(
                rental_date=datetime.utcnow(),  # Use the current date and time
                inventory_id=inventory.inventory_id,
                customer_id=customer.customer_id
            )

            # Add the new rental record to the database
            db.session.add(rental)
            db.session.commit()

            return jsonify({'message': 'Movie rented successfully.'})
        else:
            return jsonify({'message': 'Movie is not available for rent.'})
    else:
        return jsonify({'message': 'Invalid movie or customer ID.'})

@app.route('/all_films')
def display_films():
    films = Film.query.all()
    
    # Convert the list of films to a list of dictionaries with desired fields
    films_data = [
        {
            'film_id': film.film_id,
            'title': film.title,
            'description': film.description,
            'release_year': film.release_year,
            'rating': film.rating,
            'special_features': film.special_features
        } for film in films
    ]
    # Return the list of films as JSON
    return jsonify({'films': films_data})

# New API endpoint to get the top 5 most rented movies
@app.route('/top_rented_movies')
def top_rented_movies():
    # Query the database to get the top 5 most rented movies
    top_movies = db.session.query(
        Film.title,
        Film.description,
        Film.release_year,
        Film.rating,
        Film.special_features,
        func.count(Rental.rental_id).label('rental_count')
    ).join(Inventory, Film.film_id == Inventory.film_id).join(Rental, Inventory.inventory_id == Rental.inventory_id).group_by(Film.film_id).order_by(func.count(Rental.rental_id).desc()).limit(5).all()

    # Convert the result to a list of dictionaries
    top_movies_data = [
        {
            'title': title,
            'description': description,
            'releaseYear': release_year,
            'rating': rating,
            'specialFeatures': special_features,
            'rentalCount': rental_count
        } for title, description, release_year, rating, special_features, rental_count in top_movies
    ]
    
    return jsonify({'top_movies': top_movies_data})

# New API endpoint to get additional details for a specific movie
@app.route('/movie_details/<string:title>')
def movie_details(title):
    movie = Film.query.filter_by(title=title).first()

    if movie:
        return jsonify({
            'description': movie.description,
            'releaseYear': movie.release_year,
            'rating': movie.rating,
            'specialFeatures': movie.special_features
        })
    else:
        return jsonify({'error': 'Movie not found'})


if __name__ == '__main__':
    app.run(debug=True)
