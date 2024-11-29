from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

# User Model
class User(db.Model):
    __tablename__ = 'user'
    username = db.Column(db.String, primary_key=True)
    phonenumber = db.Column(db.BigInteger, nullable=False, unique=True)
    registration_date = db.Column(db.DateTime, default=datetime.utcnow)

# Host Model
class Host(db.Model):
    __tablename__ = 'host'
    phonenumber = db.Column(db.BigInteger, primary_key=True)

# Customer Model
class Customer(db.Model):
    __tablename__ = 'customer'
    phonenumber = db.Column(db.BigInteger, primary_key=True)

# Parking Spot Model
class ParkingSpot(db.Model):
    __tablename__ = 'parking_spots'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    description = db.Column(db.Text, nullable=True)
    picture = db.Column(db.Text, nullable=True)
    status = db.Column(db.String, nullable=False)
    timeslot = db.Column(db.String, nullable=False)
    location = db.Column(db.String, nullable=False)
    price = db.Column(db.Numeric, nullable=False)
    host_id = db.Column(db.BigInteger, db.ForeignKey('host.phonenumber'), nullable=False)

# Transaction Model
class Transaction(db.Model):
    __tablename__ = 'transaction'
    transaction_id = db.Column(db.Integer, primary_key=True)
    transaction_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String, nullable=False)
    commission_fee = db.Column(db.Numeric, nullable=False)
    phonec = db.Column(db.BigInteger, db.ForeignKey('customer.phonenumber'), nullable=False)
    phoneh = db.Column(db.BigInteger, db.ForeignKey('host.phonenumber'), nullable=False)
    parkingid = db.Column(db.Integer, db.ForeignKey('parking_spots.id'), nullable=False)

# Review Model
class Review(db.Model):
    __tablename__ = 'review'
    id = db.Column(db.Integer, primary_key=True)
    parking_spot_id = db.Column(db.Integer, db.ForeignKey('parking_spots.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    customer_id = db.Column(db.BigInteger, db.ForeignKey('customer.phonenumber'), nullable=False)

# Alembic Version Model
class AlembicVersion(db.Model):
    __tablename__ = 'alembic_version'
    version_num = db.Column(db.String, primary_key=True)