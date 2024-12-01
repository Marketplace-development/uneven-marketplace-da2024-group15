from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

# User Model
class User(db.Model):
    __tablename__ = 'user'
    username = db.Column(db.String, unique=True, nullable=False)  
    phonenumber = db.Column(db.BigInteger, primary_key=True)  
    registration_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)  

class Host(db.Model):
    __tablename__ = 'host'
    phonenumber = db.Column(db.BigInteger, db.ForeignKey('user.phonenumber'), primary_key=True)  

    user = db.relationship('User', backref=db.backref('hosts', lazy=True))

# Customer Model
class Customer(db.Model):
    __tablename__ = 'customer'
    phonenumber = db.Column(db.BigInteger, db.ForeignKey('user.phonenumber'), primary_key=True)
    
    user = db.relationship('User', backref=db.backref('customers', lazy=True))

# Parking Spot Model
class ParkingSpot(db.Model):
    __tablename__ = 'parking_spots'
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)  
    name = db.Column(db.Text, nullable=False) 
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)  
    description = db.Column(db.Text, nullable=True)  
    status = db.Column(db.Text, nullable=False, default='available') 
    location = db.Column(db.Text, nullable=False)  
    price = db.Column(db.Numeric, nullable=False)  
    host_id = db.Column(db.BigInteger, db.ForeignKey('host.phonenumber'), nullable=False)  
    starttime = db.Column(db.DateTime, nullable=False)
    endtime = db.Column(db.DateTime, nullable=False)
    
    host = db.relationship('Host', backref=db.backref('parking_spots', lazy=True))


# Transaction Model
class Transaction(db.Model):
    __tablename__ = 'transaction'
    transaction_id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)  
    transaction_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)  
    status = db.Column(db.Text, nullable=False)  
    commission_fee = db.Column(db.Numeric, nullable=False, default=5)  
    phonec = db.Column(db.BigInteger, db.ForeignKey('customer.phonenumber'), nullable=False)  
    phoneh = db.Column(db.BigInteger, db.ForeignKey('host.phonenumber'), nullable=False)  
    parkingid = db.Column(db.BigInteger, db.ForeignKey('parking_spots.id'), nullable=False)  
   
    customer = db.relationship('Customer', backref=db.backref('transactions', lazy=True))
    host = db.relationship('Host', backref=db.backref('transactions', lazy=True))
    parking_spot = db.relationship('ParkingSpot', backref=db.backref('transactions', lazy=True))

# Review Model
class Review(db.Model):
    __tablename__ = 'review'
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)  
    parking_spot_id = db.Column(db.BigInteger, db.ForeignKey('parking_spots.id'), nullable=False)  
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)  
    customer_id = db.Column(db.BigInteger, db.ForeignKey('customer.phonenumber'), nullable=False) 

    customer = db.relationship('Customer', backref=db.backref('reviews', lazy=True))
    parking_spot = db.relationship('ParkingSpot', backref=db.backref('reviews', lazy=True))

# Alembic Version Model
class AlembicVersion(db.Model):
    __tablename__ = 'alembic_version'
    version_num = db.Column(db.String, primary_key=True)

    