from flask import Blueprint, request, redirect, url_for, render_template, session, flash
from .models import db, User, Host, Customer, ParkingSpot, Transaction, Review, Availability
from supabase import create_client
from datetime import datetime, timezone

# Blueprint instellen
main = Blueprint('main', __name__)

# Supabase configureren met de gegevens uit je Config
SUPABASE_URL = "https://dtdwcwplnobtjbstnqxd.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImR0ZHdjd3Bsbm9idGpic3RucXhkIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MzA4MDU1MTcsImV4cCI6MjA0NjM4MTUxN30.40ImlI3NoiA5wEs6Sp6EPwJBPA-u-dualZVxZ22isdw"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

@main.route('/')
def login():
    """
    Startpagina: toont de loginpagina.
    Als een gebruiker al ingelogd is, wordt deze doorgestuurd naar de dashboardpagina.
    """
    if 'username' in session:
        return redirect(url_for('main.index'))
    return render_template('login.html')

@main.route('/login', methods=['GET', 'POST'])
def login_post():
    """
    Verwerkt de login van de gebruiker. Controleert de lokale database op de ingevoerde gebruikersnaam.
    Als succesvol, wordt de gebruiker doorgestuurd naar de dashboardpagina (index).
    """
    if request.method == 'POST':
        username = request.form.get('username')
        
        # Controleer of de gebruikersnaam bestaat in de lokale database
        user = User.query.filter_by(username=username).first()
        
        if user:  # Gebruiker gevonden
            session['username'] = username  # Sla de gebruikersnaam op in de sessie
            flash("You are now logged in", "success")
            return redirect(url_for('main.index'))
        else:
            flash("This username does not exist", "danger")
            return redirect(url_for('main.login'))

    return render_template('login.html')

@main.route('/logout', methods=['POST'])
def logout():
    """
    Verwerkt het uitloggen van de gebruiker. De sessie wordt gewist en de gebruiker
    wordt teruggestuurd naar de loginpagina.
    """
    session.pop('username', None)
    flash("You have been logged out", "success")
    return redirect(url_for('main.login'))

@main.route('/index')
def index():
    """
    Dashboardpagina die alle parkeerplaatsen toont zonder tijdsfilters.
    """
    if 'username' not in session:
        flash("You need to be logged in to access the dashboard.", "danger")
        return redirect(url_for('main.login'))
    
    username = session['username']
    user = User.query.filter_by(username=username).first()

    # Fetch available parking spots not owned by the current user (without time filters),
    # excluding spots that are already booked.
    active_listings = (
        db.session.query(ParkingSpot, Availability)
        .join(Availability)
        .outerjoin(Transaction, ParkingSpot.id == Transaction.parkingid)
        .filter(
            ParkingSpot.host_id != user.phonenumber,
            db.or_(Transaction.transaction_id == None, Transaction.status != "Booked")
        )
        .all()
    )

    print(f"Active listings found: {len(active_listings)}")  # Debug: Print het aantal gevonden listings

    return render_template('index.html', username=username, active_listings=active_listings, search_city=None)

@main.route('/register', methods=['GET', 'POST'])
def register():
    """
    Registratiepagina. Voegt nieuwe gebruikers toe aan de database en registreert deze in Supabase.
    """
    if request.method == 'POST':
        username = request.form.get('username')
        phonenumber = request.form.get('phonenumber')
        email = request.form.get('email')

        print(f"Received username: {username}, phonenumber: {phonenumber}, email: {email}")  # Debug

        # Validatie: Controleer in de lokale database
        if User.query.filter_by(username=username).first():
            flash(f"Username '{username}' already exists in the local database!", "danger")
            return redirect(url_for('main.register'))
        if User.query.filter_by(phonenumber=phonenumber).first():
            flash(f"Phone number '{phonenumber}' already exists in the local database!", "danger")
            return redirect(url_for('main.register'))
        if User.query.filter_by(email=email).first():
            flash(f"Email '{email}' already exists in the local database!", "danger")
            return redirect(url_for('main.register'))

        # Validatie: Controleer in Supabase
        response = supabase.table('user').select('username').eq('username', username).execute()
        print(f"Supabase check response: {response.data}")  # Debugging
        if response.data and len(response.data) > 0:
            flash(f"Username '{username}' already exists in Supabase!", "danger")
            return redirect(url_for('main.register'))

        # Voeg gebruiker toe aan Supabase met upsert
        try:
            response = supabase.table('user').upsert({
                'username': username,
                'phonenumber': phonenumber,
                'email': email
            }).execute()
            print(f"User successfully added or updated in Supabase: {response.data}")  # Debugging
        except Exception as e:
            print(f"Supabase upsert error: {e}")  # Debugging
            flash("An error occurred while registering in Supabase.", "danger")
            return redirect(url_for('main.register'))

        # Controleer opnieuw in de lokale database voordat je invoegt
        if not User.query.filter_by(username=username).first():
            try:
                new_user = User(username=username, phonenumber=phonenumber, email=email)
                db.session.add(new_user)
                db.session.commit()
                print("User successfully added to local database.")  # Debugging
            except Exception as e:
                print(f"Local database insert error: {e}")  # Debugging
                flash("An error occurred while registering in the local database.", "danger")
                return redirect(url_for('main.register'))
        else:
            print(f"User '{username}' already exists in the local database after Supabase sync.")  # Debugging

        # Sla de gebruikersnaam op in de sessie
        session['username'] = username

        flash('Registration successful! Welcome to Rent My Spot!', "success")

        # Redirect naar de index-pagina
        return redirect(url_for('main.index'))

    return render_template('register.html')

@main.route('/listings')
def listings():
    """
    Pagina voor alle beschikbare parkeerplaatsen (voorbeeldimplementatie).
    """
    if 'username' not in session:
        flash("You need to be logged in to view listings.", "danger")
        return redirect(url_for('main.login'))
    
    username = session['username']
    user = User.query.filter_by(username=username).first()
    listings = ParkingSpot.query.filter_by(host_id=user.phonenumber).all()

    return render_template('listings.html', listings=listings)

@main.route('/add_listing', methods=['GET', 'POST'])
def add_listing():
    """
    Page for adding a new parking spot. Requires login.
    """
    if 'username' not in session:
        flash("You need to be logged in to add a listing.", "danger")
        return redirect(url_for('main.login'))

    username = session.get('username')
    user = User.query.filter_by(username=username).first()

    if not user:
        flash("User not found in the local database.", "danger")
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        street_address = request.form.get('street_address')
        postal_code = request.form.get('postal_code')
        city = request.form.get('city')

        # Ensure the user is a Host
        host = Host.query.filter_by(phonenumber=user.phonenumber).first()
        if not host:
            # Add as Host if not already
            host = Host(phonenumber=user.phonenumber)
            db.session.add(host)
            db.session.commit()

        try:
            # Add the new parking spot to the database
            new_parking_spot = ParkingSpot(
                name=name,
                description=description,
                street_address=street_address,
                postal_code=postal_code,
                city=city,
                host_id=host.phonenumber  # phonenumber of the logged-in user
            )
            db.session.add(new_parking_spot)
            db.session.commit()

            flash("Parking spot successfully added!", "success")
            return redirect(url_for('main.index'))

        except Exception as e:
            db.session.rollback()
            flash(f"An error occurred while adding the parking spot: {e}", "danger")
            return redirect(url_for('main.add_listing'))

    return render_template('add_listing.html')

@main.route('/account')
def account():
    """
    Account page: Shows user information, owned listings, and booked listings.
    """
    if 'username' not in session:
        flash("You need to be logged in to view your account.", "danger")
        return redirect(url_for('main.login'))

    username = session['username']
    user = User.query.filter_by(username=username).first()

    if not user:
        flash("User not found in the database.", "danger")
        return redirect(url_for('main.index'))

    # Listings owned by the user
    listings = ParkingSpot.query.filter_by(host_id=user.phonenumber).all()

    # Booked parking spots for the customer
    booked_listings = db.session.query(Transaction).filter_by(phonec=user.phonenumber).all()

    return render_template(
        'account.html', 
        user=user, 
        listings=listings, 
        booked_listings=booked_listings
    )

@main.route('/make_available/<int:parking_spot_id>', methods=['GET', 'POST'])
def make_available(parking_spot_id):
    """
    Route to add availability for a parking spot. Ensures no overlapping time periods are added.
    """
    if 'username' not in session:
        flash("You need to be logged in to perform this action.", "danger")
        return redirect(url_for('main.login'))

    username = session['username']
    user = User.query.filter_by(username=username).first()

    if not user:
        flash("User not found in the database.", "danger")
        return redirect(url_for('main.index'))


    parking_spot = ParkingSpot.query.get(parking_spot_id)
    if not parking_spot or parking_spot.host_id != user.phonenumber:
        flash("Parking spot not found or you do not have permission to modify it.", "danger")
        return redirect(url_for('main.account'))

    if request.method == 'POST':
        starttime = request.form.get('starttime')
        endtime = request.form.get('endtime')
        price = request.form.get('price')

        try:
            # Parse the times and force minutes to 00
            start_datetime = datetime.strptime(starttime, "%Y-%m-%dT%H:%M").replace(minute=0, second=0, microsecond=0)
            end_datetime = datetime.strptime(endtime, "%Y-%m-%dT%H:%M").replace(minute=0, second=0, microsecond=0)

            if end_datetime <= start_datetime:
                flash("End time must be later than start time.", "danger")
                return redirect(url_for('main.make_available', parking_spot_id=parking_spot_id))
        except ValueError:
            flash("Invalid date format. Please use the correct format (YYYY-MM-DD HH:MM).", "danger")
            return redirect(url_for('main.make_available', parking_spot_id=parking_spot_id))

        # Check for overlapping availability
        overlapping = db.session.query(Availability).filter(
            Availability.parkingspot_id == parking_spot_id,
            db.or_(
                db.and_(Availability.starttime <= start_datetime, Availability.endtime > start_datetime),
                db.and_(Availability.starttime < end_datetime, Availability.endtime >= end_datetime),
                db.and_(Availability.starttime >= start_datetime, Availability.endtime <= end_datetime)
            )
        ).first()

        if overlapping:
            flash("This parking spot is already available during this time period.", "danger")
            return redirect(url_for('main.make_available', parking_spot_id=parking_spot_id))


        # Add new availability
        try:
            availability = Availability(
                starttime=start_datetime,
                endtime=end_datetime,
                parkingspot_id=parking_spot_id,
                price=price
            )
            db.session.add(availability)
            db.session.commit()

            flash("Availability successfully added!", "success")
            return redirect(url_for('main.account'))
        except Exception as e:
            db.session.rollback()
            flash(f"An error occurred: {e}", "danger")
            return redirect(url_for('main.make_available', parking_spot_id=parking_spot_id))

    return render_template('make_available.html', parking_spot=parking_spot)

@main.route('/details/<int:parking_spot_id>')
def view_details(parking_spot_id):
    """
    Route to view details of a specific parking spot, including reviews.
    """
    # Fetch the parking spot and its availability
    parking_spot = db.session.query(ParkingSpot, Availability).join(Availability).filter(ParkingSpot.id == parking_spot_id).first()

    if not parking_spot:
        flash("Parking spot not found or no availability available.", "danger")
        return redirect(url_for('main.index'))

    # Fetch reviews for the parking spot
    reviews = Review.query.filter_by(parking_spot_id=parking_spot_id).all()

    return render_template(
        'details.html',
        parking_spot=parking_spot[0],
        availability=parking_spot[1],
        reviews=reviews
    )

@main.route('/book/<int:parking_spot_id>', methods=['POST'])
def book_now(parking_spot_id):
    """
    Route to book a parking spot, making it unavailable and associating it with the current user.
    Ensures that users can only book parking spots from other hosts.
    """
    if 'username' not in session:
        flash("You need to be logged in to book a parking spot.", "danger")
        return redirect(url_for('main.login'))

    username = session['username']
    user = User.query.filter_by(username=username).first()

    if not user:
        flash("User not found in the database.", "danger")
        return redirect(url_for('main.index'))

    # Ensure the user is in the Customer table
    customer = Customer.query.filter_by(phonenumber=user.phonenumber).first()
    if not customer:
        try:
            # Add the user to the Customer table
            new_customer = Customer(phonenumber=user.phonenumber)
            db.session.add(new_customer)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            flash(f"An error occurred while registering as a customer: {e}", "danger")
            return redirect(url_for('main.index'))

    # Fetch the parking spot and its availability
    parking_spot = ParkingSpot.query.get(parking_spot_id)
    availability = Availability.query.filter_by(parkingspot_id=parking_spot_id).first()

    if not parking_spot or not availability:
        flash("Parking spot not found or no availability available.", "danger")
        return redirect(url_for('main.index'))

    try:
        # Create a new transaction without deleting the availability
        transaction = Transaction(
            transaction_date=datetime.now(),
            status="Booked",
            commission_fee=5.00,
            phonec=user.phonenumber,  # Current user's phone number
            phoneh=parking_spot.host_id,  # Host's phone number
            parkingid=parking_spot.id
        )
        db.session.add(transaction)
        db.session.commit()

        flash("Your parking spot has been successfully booked. Thank you for your booking!", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"An error occurred while booking the parking spot: {e}", "danger")

    return redirect(url_for('main.index'))

from datetime import datetime, timezone

@main.route('/booked_parking_spots')
def view_booked_spots():
    """
    Page to view booked parking spots, split into active and expired bookings.
    """
    if 'username' not in session:
        flash("You need to be logged in to view booked parking spots.", "danger")
        return redirect(url_for('main.login'))

    username = session['username']
    user = User.query.filter_by(username=username).first()

    if not user:
        flash("User not found in the database.", "danger")
        return redirect(url_for('main.index'))

    # Fetch booked parking spots for the user
    current_time = datetime.now(timezone.utc)  # Make current_time timezone-aware
    booked_spots = (
        db.session.query(Transaction, Availability)
        .join(ParkingSpot, ParkingSpot.id == Transaction.parkingid)
        .join(Availability, Availability.parkingspot_id == ParkingSpot.id)
        .filter(Transaction.phonec == user.phonenumber, Transaction.status == "Booked")
        .all()
    )

    # Split bookings into active and expired
    active_bookings = []
    expired_bookings = []

    for booking, availability in booked_spots:
        # Ensure endtime is also timezone-aware
        if availability.endtime.replace(tzinfo=timezone.utc) >= current_time:
            active_bookings.append((booking, availability))
        else:
            expired_bookings.append((booking, availability))

    return render_template(
        'booked_spots.html',
        user=user,
        active_bookings=active_bookings,
        expired_bookings=expired_bookings
    )




@main.route('/add_review/<int:parking_spot_id>', methods=['GET'])
def add_review(parking_spot_id):
    """
    Route to display the review form for a parking spot.
    """
    if 'username' not in session:
        flash("You need to be logged in to leave a review.", "danger")
        return redirect(url_for('main.login'))

    username = session['username']
    user = User.query.filter_by(username=username).first()

    if not user:
        flash("User not found in the database.", "danger")
        return redirect(url_for('main.index'))

    parking_spot = ParkingSpot.query.get(parking_spot_id)

    if not parking_spot:
        flash("Parking spot not found.", "danger")
        return redirect(url_for('main.view_booked_spots'))

    # Fetch the transaction related to this user and parking spot
    transaction = Transaction.query.filter_by(
        phonec=user.phonenumber,
        parkingid=parking_spot_id
    ).first()

    if not transaction:
        flash("You cannot leave a review for a parking spot you haven't booked.", "danger")
        return redirect(url_for('main.view_booked_spots'))

    return render_template('add_review.html', parking_spot=parking_spot, transaction=transaction)

@main.route('/submit_review/<int:parking_spot_id>', methods=['POST'])
def submit_review(parking_spot_id):
    """
    Route to handle the submission of a review for a parking spot.
    """
    if 'username' not in session:
        flash("You need to be logged in to leave a review.", "danger")
        return redirect(url_for('main.login'))

    username = session['username']
    user = User.query.filter_by(username=username).first()

    if not user:
        flash("User not found in the database.", "danger")
        return redirect(url_for('main.index'))

    # Haal gegevens van het formulier op
    rating = request.form.get('rating')
    comment = request.form.get('comment', '')

    if not rating or not (1 <= int(rating) <= 5):
        flash("Please provide a valid rating between 1 and 5.", "danger")
        return redirect(url_for('main.add_review', parking_spot_id=parking_spot_id))

    # Controleer of de parkeerplaats bestaat
    parking_spot = ParkingSpot.query.get(parking_spot_id)
    if not parking_spot:
        flash("Parking spot not found.", "danger")
        return redirect(url_for('main.view_booked_spots'))

    try:
        # Voeg de review toe aan de database
        review = Review(
            parking_spot_id=parking_spot_id,
            customer_id=user.phonenumber,
            rating=int(rating),
            comment=comment,
            created_at=datetime.utcnow()
        )
        db.session.add(review)
        db.session.commit()

        # Voeg een specifieke flash-melding toe voor de parkeerplaats
        flash(f"Review for '{parking_spot.name}' has been successfully submitted.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"An error occurred while submitting your review: {e}", "danger")

    return redirect(url_for('main.view_booked_spots'))

@main.route('/view_reviews/<int:parking_spot_id>')
def view_reviews(parking_spot_id):
    """
    Route to view reviews for a specific parking spot.
    """
    if 'username' not in session:
        flash("You need to be logged in to view reviews.", "danger")
        return redirect(url_for('main.login'))

    parking_spot = ParkingSpot.query.get(parking_spot_id)

    if not parking_spot:
        flash("Parking spot not found.", "danger")
        return redirect(url_for('main.account'))

    reviews = Review.query.filter_by(parking_spot_id=parking_spot_id).all()

    return render_template('view_reviews.html', parking_spot=parking_spot, reviews=reviews)

@main.route('/search_listings', methods=['GET'])
def search_listings():
    """
    Search for available parking spots based on city.
    """
    if 'username' not in session:
        flash("You need to be logged in to search listings.", "danger")
        return redirect(url_for('main.login'))

    city = request.args.get('city', '').strip().lower()

    if not city:
        return redirect(url_for('main.index'))

    # Fetch available parking spots matching the city
    matching_listings = (
        db.session.query(ParkingSpot, Availability)
        .join(Availability)
        .filter(
            db.func.lower(ParkingSpot.city) == city,
            Availability.starttime <= datetime.utcnow(),
            Availability.endtime > datetime.utcnow()
        )
        .all()
    )

    return render_template(
        'index.html', 
        username=session['username'], 
        active_listings=matching_listings, 
        search_city=city
    )

@main.route('/about')
def about():
    """
    Render de About Us-pagina.
    """
    return render_template('about.html')

@main.route('/edit_availability/<int:availability_id>', methods=['GET', 'POST'])
def edit_availability(availability_id):
    """
    Route to edit an existing availability listing.
    """
    if 'username' not in session:
        flash("You need to be logged in to perform this action.", "danger")
        return redirect(url_for('main.login'))

    username = session['username']
    user = User.query.filter_by(username=username).first()

    if not user:
        flash("User not found in the database.", "danger")
        return redirect(url_for('main.index'))

    availability = Availability.query.get(availability_id)

    if not availability:
        flash("Availability not found.", "danger")
        return redirect(url_for('main.account'))

    parking_spot = ParkingSpot.query.get(availability.parkingspot_id)

    if not parking_spot or parking_spot.host_id != user.phonenumber:
        flash("You do not have permission to edit this availability.", "danger")
        return redirect(url_for('main.account'))

    if request.method == 'POST':
        starttime = request.form.get('starttime')
        endtime = request.form.get('endtime')
        price = request.form.get('price')

        try:
            # Validate times
            start_datetime = datetime.strptime(starttime, "%Y-%m-%dT%H:%M")
            end_datetime = datetime.strptime(endtime, "%Y-%m-%dT%H:%M")
            if end_datetime <= start_datetime:
                flash("End time must be later than start time.", "danger")
                return redirect(url_for('main.edit_availability', availability_id=availability_id))
        except ValueError:
            flash("Invalid date format. Please use the correct format (YYYY-MM-DD HH:MM).", "danger")
            return redirect(url_for('main.edit_availability', availability_id=availability_id))

        # Check for overlapping availability (excluding the current availability)
        overlapping = db.session.query(Availability).filter(
            Availability.parkingspot_id == parking_spot.id,
            Availability.id != availability_id,  # Exclude the current availability
            db.or_(
                db.and_(Availability.starttime <= start_datetime, Availability.endtime > start_datetime),
                db.and_(Availability.starttime < end_datetime, Availability.endtime >= end_datetime),
                db.and_(Availability.starttime >= start_datetime, Availability.endtime <= end_datetime)
            )
        ).first()

        if overlapping:
            flash("This parking spot is already available during this time period.", "danger")
            return redirect(url_for('main.edit_availability', availability_id=availability_id))

        # Update the availability
        try:
            availability.starttime = start_datetime
            availability.endtime = end_datetime
            availability.price = price
            db.session.commit()

            flash("Availability successfully updated!", "success")
            return redirect(url_for('main.account'))
        except Exception as e:
            db.session.rollback()
            flash(f"An error occurred: {e}", "danger")
            return redirect(url_for('main.edit_availability', availability_id=availability_id))

    return render_template('edit_availability.html', availability=availability, parking_spot=parking_spot)


@main.route('/delete_parking_spot/<int:parking_spot_id>', methods=['POST'])
def delete_parking_spot(parking_spot_id):
    """
    Route to delete a parking spot and its associated data.
    """
    if 'username' not in session:
        flash("You need to be logged in to delete a parking spot.", "danger")
        return redirect(url_for('main.login'))

    username = session['username']
    user = User.query.filter_by(username=username).first()

    if not user:
        flash("User not found in the database.", "danger")
        return redirect(url_for('main.index'))

    # Zoek de parkeerplaats op
    parking_spot = ParkingSpot.query.get(parking_spot_id)
    
    if not parking_spot or parking_spot.host_id != user.phonenumber:
        flash("Parking spot not found or you do not have permission to delete it.", "danger")
        return redirect(url_for('main.account'))

    try:
        # Verwijder gerelateerde data (availabilities, transactions, reviews)
        Availability.query.filter_by(parkingspot_id=parking_spot_id).delete()
        Transaction.query.filter_by(parkingid=parking_spot_id).delete()
        Review.query.filter_by(parking_spot_id=parking_spot_id).delete()
        
        # Verwijder de parkeerplaats zelf
        db.session.delete(parking_spot)
        db.session.commit()

        flash(f"Parking spot '{parking_spot.name}' has been successfully deleted.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"An error occurred while deleting the parking spot: {e}", "danger")

    return redirect(url_for('main.account'))
