from flask import Blueprint, request, redirect, url_for, render_template, session
from werkzeug.security import generate_password_hash
from werkzeug.security import check_password_hash
from datetime import datetime
from app.models import db, User
from app.models import db, Listing
from app.models import db, Booking

main = Blueprint('main', __name__)

@main.route('/')
def index():
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        listings = Listing.query.filter_by(user_id=user.id).all()  # Fetch listings for logged-in user
        return render_template('index.html', username=user.username, listings=listings)
    return render_template('index.html', username=None)

#User story 1: registreren van een gebruiker
@main.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        if User.query.filter_by(username=username).first() is None:
            password_hash = generate_password_hash(password)
            new_user = User(username=username, email=email, password_hash=password_hash)
            db.session.add(new_user)
            db.session.commit()
            session['user_id'] = new_user.id
            return redirect(url_for('main.index'))
        return 'Username already registered'
    return render_template('register.html')

#User story 2: Inloggen
@main.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            session['user_id'] = user.id
            return redirect(url_for('main.index'))
        return 'Invalid credentials, please try again.'
    return render_template('login.html')

@main.route('/logout', methods=['POST'])
def logout():
    session.pop('user_id', None)
    return redirect(url_for('main.index'))

#User story 3: Zoeken naar parkeerplekken
@main.route('/search', methods=['GET'])
def search():
    query = request.args.get('q', '')
    listings = Listing.query.filter(Listing.listing_name.contains(query) | 
                                     Listing.location.contains(query)).all()
    return render_template('search_results.html', listings=listings)

#User story 4: Toevoegen van een Listing
@main.route('/add-listing', methods=['GET', 'POST'])
def add_listing():
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    
    if request.method == 'POST':
        listing_name = request.form['listing_name']
        location = request.form['location']
        price = float(request.form['price'])
        description = request.form.get('description', '')
        new_listing = Listing(listing_name=listing_name, location=location, price=price, description=description, user_id=session['user_id'])
        db.session.add(new_listing)
        db.session.commit()
        return redirect(url_for('main.listings'))

    return render_template('add_listing.html')

@main.route('/listings')
def listings():
    all_listings = Listing.query.all()
    return render_template('listings.html', listings=all_listings)

#User story 5: Beheren van Listings
@main.route('/edit-listing/<int:listing_id>', methods=['GET', 'POST'])
def edit_listing(listing_id):
    listing = Listing.query.get(listing_id)
    if listing.user_id != session.get('user_id'):
        return redirect(url_for('main.index'))  # Only the provider can edit the listing
    
    if request.method == 'POST':
        listing.listing_name = request.form['listing_name']
        listing.location = request.form['location']
        listing.price = float(request.form['price'])
        listing.description = request.form.get('description', '')
        db.session.commit()
        return redirect(url_for('main.listings'))
    
    return render_template('edit_listing.html', listing=listing)

@main.route('/delete-listing/<int:listing_id>', methods=['POST'])
def delete_listing(listing_id):
    listing = Listing.query.get(listing_id)
    if listing.user_id != session.get('user_id'):
        return redirect(url_for('main.index'))  # Only the provider can delete the listing
    
    db.session.delete(listing)
    db.session.commit()
    return redirect(url_for('main.listings'))

#User story 6: Boeken van een parkeerplek
@main.route('/book/<int:listing_id>', methods=['POST'])
def book_listing(listing_id):
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    
    listing = Listing.query.get(listing_id)
    if listing.status != 'available':
        return 'This listing is not available at the moment.'

    start_time = request.form['start_time']
    end_time = request.form['end_time']
    
    # Create a new booking
    new_booking = Booking(user_id=session['user_id'], listing_id=listing_id,
                          start_time=start_time, end_time=end_time, status='pending')
    db.session.add(new_booking)
    db.session.commit()

    # Mark listing as unavailable
    listing.status = 'booked'
    db.session.commit()

    return redirect(url_for('main.my_bookings'))

#User story 7: Bekijken van mijn boekingen
from .models import Booking

@main.route('/my-bookings')
def my_bookings():
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    
    bookings = Booking.query.filter_by(user_id=session['user_id']).all()
    return render_template('my_bookings.html', bookings=bookings)

#User story 8: Review laten voor een parkeerplek
from .models import Review, Listing

@main.route('/review-parking-spot/<int:listing_id>', methods=['POST'])
def review_parking_spot(listing_id):
    if 'user_id' not in session:
        return redirect(url_for('main.login'))

    rating = int(request.form['rating'])
    comment = request.form.get('comment', '')

    new_review = Review(user_id=session['user_id'], listing_id=listing_id, 
                        rating=rating, comment=comment, created_at=datetime.utcnow())
    db.session.add(new_review)
    db.session.commit()

    return redirect(url_for('main.listings'))

#User story 9: Review laten voor een huurder
@main.route('/review-renter/<int:rental_id>', methods=['POST'])
def review_renter(rental_id):
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    
    booking = Booking.query.get(rental_id)
    if booking.listing.user_id != session['user_id']:
        return 'You are not authorized to review this renter.'

    rating = int(request.form['rating'])
    comment = request.form.get('comment', '')

    new_review = Review(user_id=booking.user_id, listing_id=booking.listing_id, 
                        rating=rating, comment=comment, created_at=datetime.utcnow())
    db.session.add(new_review)
    db.session.commit()

    return redirect(url_for('main.listings'))

#User story 10: Betaling voor parkeerplek
@main.route('/make-payment/<int:rental_id>', methods=['POST'])
def make_payment(rental_id):
    booking = Booking.query.get(rental_id)
    if booking.status != 'pending':
        return 'This booking is not in a valid state for payment.'
    
    booking.payment_status = 'paid'
    booking.status = 'confirmed'
    db.session.commit()
    
    return redirect(url_for('main.my_bookings'))

#User story 11: Betaling ontvangen  (door providers)
@main.route('/payment-received/<int:rental_id>', methods=['POST'])
def payment_received(rental_id):
    booking = Booking.query.get(rental_id)
    if booking.listing.user_id != session['user_id']:
        return 'You are not authorized to confirm payment for this booking.'

    booking.payment_status = 'paid'
    db.session.commit()
    
    return redirect(url_for('main.my_bookings'))
