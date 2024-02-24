# app/models.py

from . import db

# Define SQLAlchemy models to represent database tables


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
    staff_id = db.Column(db.Integer, db.ForeignKey("staff.staff_id")) 
    staff = db.relationship("Staff")  


class Customer(db.Model):
    __tablename__ = "customer"
    customer_id = db.Column(db.Integer, primary_key=True)

