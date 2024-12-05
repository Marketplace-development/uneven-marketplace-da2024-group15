from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# User Model
class User(db.Model):
    __tablename__ = 'user'
    username = db.Column(db.String, unique=True, nullable=False)  
    phonenumber = db.Column(db.BigInteger, primary_key=True)  
    email = db.Column(db.Text, unique=True, nullable=False)
    registration_date = db.Column(db.TIMESTAMP, server_default=db.func.now(), nullable=False)  

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
    created_at = db.Column(db.TIMESTAMP, server_default=db.func.now(), nullable=False)  
    description = db.Column(db.Text, nullable=True) 
    street_address = db.Column(db.Text, nullable=False)
    postal_code = db.Column(db.BigInteger, nullable=False)
    city = db.Column(db.Text, nullable=False)  
    host_id = db.Column(db.BigInteger, db.ForeignKey('host.phonenumber'), nullable=False)  
    
    host = db.relationship('Host', backref=db.backref('parking_spots', lazy=True))

# Availability Model
class Availability(db.Model):
    __tablename__ = 'availability'
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)  
    starttime = db.Column(db.TIMESTAMP, nullable=False)  
    endtime = db.Column(db.TIMESTAMP, nullable=False)  
    parkingspot_id = db.Column(db.BigInteger, db.ForeignKey('parking_spots.id'), nullable=False)  
    price = db.Column(db.Numeric, nullable=False)  
    is_booked = db.Column(db.Boolean, nullable=False, default=False)

    parking_spot = db.relationship('ParkingSpot', backref=db.backref('availabilities', lazy=True))

# Transaction Model
class Transaction(db.Model):
    __tablename__ = 'transaction'
    transaction_id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)  
    transaction_date = db.Column(db.TIMESTAMP, server_default=db.func.now(), nullable=False)  
    status = db.Column(db.Text, nullable=False)  
    commission_fee = db.Column(db.Numeric, nullable=False, default=5)  
    phonec = db.Column(db.BigInteger, db.ForeignKey('customer.phonenumber'), nullable=False)  
    phoneh = db.Column(db.BigInteger, db.ForeignKey('host.phonenumber'), nullable=False)  
    parkingid = db.Column(db.BigInteger, db.ForeignKey('parking_spots.id'), nullable=False)
    availability_id = db.Column(db.BigInteger, db.ForeignKey('availability.id'), nullable=False)  
   
    customer = db.relationship('Customer', backref=db.backref('transactions', lazy=True))
    host = db.relationship('Host', backref=db.backref('transactions', lazy=True))
    parking_spot = db.relationship('ParkingSpot', backref=db.backref('transactions', lazy=True))
    availability = db.relationship('Availability', backref=db.backref('transactions', lazy=True))

# Review Model
class Review(db.Model):
    __tablename__ = 'review'
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)  
    parking_spot_id = db.Column(db.BigInteger, db.ForeignKey('parking_spots.id'), nullable=False)  
    created_at = db.Column(db.TIMESTAMP, server_default=db.func.now(), nullable=False)  
    customer_id = db.Column(db.BigInteger, db.ForeignKey('customer.phonenumber'), nullable=False) 
    rating = db.Column(db.Integer, nullable=False)  
    comment = db.Column(db.Text, nullable=True)  
    id_from_transaction = db.Column(db.BigInteger, db.ForeignKey('transaction.transaction_id'), nullable=False)

    customer = db.relationship('Customer', backref=db.backref('reviews', lazy=True))
    parking_spot = db.relationship('ParkingSpot', backref=db.backref('reviews', lazy=True))
    transaction = db.relationship('Transaction', backref=db.backref('reviews', lazy=True))

# Alembic Version Model
class AlembicVersion(db.Model):
    __tablename__ = 'alembic_version'
    version_num = db.Column(db.String, primary_key=True)
    