from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    registered_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    listings = db.relationship('Listing', backref='user', lazy=True)
    bookings = db.relationship('Booking', backref='user', lazy=True)
    reviews = db.relationship('Review', backref='user', lazy=True) 

    def __repr__(self):
        return f'<User id={self.id}, username={self.username}, email={self.email}>'
    
class Listing(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    listing_name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(255))
    location = db.Column(db.String(200), nullable=False) 
    status = db.Column(db.String(20), default='available') 
    price = db.Column(db.Float, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    bookings = db.relationship('Booking', backref='listing', lazy=True)
    reviews = db.relationship('Review', backref='listing', lazy=True)

    def __repr__(self):
        return f'<Listing id={self.id}, name={self.listing_name}, price=${self.price}, location={self.location}>'
    
class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    listing_id = db.Column(db.Integer, db.ForeignKey('listings.id'), nullable=False)
    booking_date = db.Column(db.DateTime, nullable=False)  
    start_time = db.Column(db.DateTime, nullable=False)  
    end_time = db.Column(db.DateTime, nullable=False)  
    status = db.Column(db.String(20), default='pending') 
    payment_status = db.Column(db.String(20), default='unpaid') 

    def __repr__(self):
        return f'<Booking id={self.id}, user_id={self.user_id}, listing_id={self.listing_id}, status={self.status}>'
    
class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    listing_id = db.Column(db.Integer, db.ForeignKey('listings.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)  # Waardering (bijv. 1-5 sterren)
    comment = db.Column(db.String(255))  # Optionele tekstuele beoordeling
    created_at = db.Column(db.DateTime, nullable=False)  

    def __repr__(self):
        return f'<Review id={self.id}, user_id={self.user_id}, listing_id={self.listing_id}, rating={self.rating}>'