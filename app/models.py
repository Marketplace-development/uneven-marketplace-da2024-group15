from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from sqlalchemy import TIMESTAMP, func
from sqlalchemy.dialects.postgresql import NUMERIC

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'user'
    user_id = db.Column(db.BigInteger, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    registration_date = db.Column(TIMESTAMP(timezone=True), server_default=func.now())
    email = db.Column(db.String(120), unique=True, nullable=False)
    notification = db.Column(db.Boolean, default=False)
    password_hash = db.Column(db.String(128), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.user_id}: {self.username}>'

class Transaction(db.Model):
    __tablename__ = 'transaction'
    id = db.Column(db.BigInteger, primary_key=True)
    transaction_date = db.Column(TIMESTAMP(timezone=True), server_default=func.now())
    status = db.Column(db.String)
    commission_fee = db.Column(NUMERIC(precision=10, scale=2))
    transaction_message = db.Column(db.String)
    user_id = db.Column(db.BigInteger, db.ForeignKey('user.user_id'))
    parking_spot_id = db.Column(db.BigInteger, db.ForeignKey('parking_spots.id'))

    user = db.relationship('User', backref=db.backref('transactions', lazy=True))
    parking_spot = db.relationship('ParkingSpot', backref=db.backref('transactions', lazy=True))

    def __repr__(self):
        return f'<Transaction {self.id}: {self.status}>'

class ParkingSpot(db.Model):
    __tablename__ = 'parking_spots'
    id = db.Column(db.BigInteger, primary_key=True)
    name = db.Column(db.String)
    created_at = db.Column(TIMESTAMP(timezone=True), server_default=func.now())
    description = db.Column(db.String)
    picture = db.Column(db.String)  
    status = db.Column(db.String)
    timeslot = db.Column(TIMESTAMP(timezone=True))
    location = db.Column(db.String)
    price = db.Column(NUMERIC(precision=10, scale=2)) 
    user_id = db.Column(db.BigInteger, db.ForeignKey('user.user_id'))
    transaction_id = db.Column(db.BigInteger, db.ForeignKey('transaction.id')) 
    host_id = db.Column(db.BigInteger, db.ForeignKey('user.user_id')) 

    user = db.relationship('User', foreign_keys=[user_id], backref=db.backref('parking_spots', lazy=True))
    transaction = db.relationship('Transaction', backref=db.backref('parking_spot', lazy=True))
    host = db.relationship('User', foreign_keys=[host_id], backref=db.backref('hosted_parking_spots', lazy=True))


    def __repr__(self):
        return f'<ParkingSpot {self.id}: {self.name}>'
    
class Review(db.Model):
    __tablename__ = 'review'
    id = db.Column(db.BigInteger, primary_key=True)
    parking_spot_review = db.Column(db.String)
    customer_review = db.Column(db.String)
    parking_spot_id = db.Column(db.BigInteger, db.ForeignKey('parking_spots.id'))
    created_at = db.Column(TIMESTAMP)
    customer_id = db.Column(db.BigInteger, db.ForeignKey('user.user_id'))
    provider_id = db.Column(db.BigInteger, db.ForeignKey('user.user_id'))

    parking_spot = db.relationship('ParkingSpot', backref=db.backref('reviews', lazy=True))
    customer = db.relationship('User', foreign_keys=[customer_id], backref=db.backref('customer_reviews', lazy=True))
    provider = db.relationship('User', foreign_keys=[provider_id], backref=db.backref('provider_reviews', lazy=True))

    def __repr__(self):
        return f'<Review {self.id}: {self.parking_spot_review[:20]}>'