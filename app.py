from flask import Flask, render_template, request, redirect

import mysql.connector
import os
from werkzeug.utils import secure_filename
app = Flask(__name__)
UPLOAD_FOLDER = 'static/upload'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
# -----------database connection

db = mysql.connector.connect(

    host="localhost",

    user="root",

    password="aswin11",

    database="rental_house"

)
cursor = db.cursor()
print("Database Connected Successfully")


# -------User Home Page


@app.route('/')
def home():

    cursor.execute("""
    SELECT * FROM houses
    WHERE availability='Available'
    LIMIT 3
    """)

    featured_houses = cursor.fetchall()

    return render_template(
        'index.html',
        featured_houses=featured_houses
    )

# -----------Houses Page


@app.route('/houses')
def houses():

    search = request.args.get('search')

    if search:

        cursor.execute(
            "SELECT * FROM houses WHERE location LIKE %s AND availability='Available'",
            ('%' + search + '%',)
        )

    else:

        cursor.execute(
            "SELECT id, house_name, location, rent, description, availability, image FROM houses WHERE availability='Available'"
        )

    all_houses = cursor.fetchall()

    return render_template(
        'house.html',
        houses=all_houses
    )
# -----------Admin Dashboard


@app.route('/admin')
def admin():

    cursor.execute("SELECT COUNT(*) FROM houses")
    total_houses = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM bookings")
    total_bookings = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(*) FROM bookings WHERE status='Pending'"
    )
    pending_bookings = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(*) FROM bookings WHERE status='Accepted'"
    )
    accepted_bookings = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(*) FROM bookings WHERE status='Rejected'"
    )
    rejected_bookings = cursor.fetchone()[0]

    return render_template(
        'admin/admin.html',
        total_houses=total_houses,
        total_bookings=total_bookings,
        pending_bookings=pending_bookings,
        accepted_bookings=accepted_bookings,
        rejected_bookings=rejected_bookings
    )
# -------------------------------------------------------------------------------------------------


@app.route('/type/<property_type>')
def property_type(property_type):

    query = """
    SELECT *
    FROM houses
    WHERE property_type=%s
    """

    cursor.execute(query, (property_type,))

    houses = cursor.fetchall()

    return render_template(
        'houses.html',
        houses=houses
    )

# ------- Add House Page


@app.route('/add_house', methods=['GET', 'POST'])
def add_house():

    if request.method == 'POST':

        house_name = request.form['house_name']
        location = request.form['location']
        rent = request.form['rent']
        description = request.form['description']
        property_type = request.form['property_type']

        image = request.files.get('image')
        filename = ""

        if image and image.filename != "":
            filename = secure_filename(image.filename)

            image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        query = """
        INSERT INTO houses
        (house_name, location, rent, description, image, property_type)
        VALUES (%s,%s,%s,%s,%s,%s)
        """

        values = (
            house_name,
            location,
            rent,
            description,
            filename,
            property_type
        )

        cursor.execute(query, values)
        db.commit()

        return redirect('/houses')

    return render_template('admin/add_house.html')

# -------------booking page----


@app.route('/book/<int:house_id>', methods=['GET', 'POST'])
def book_house(house_id):

    if request.method == 'POST':

        user_name = request.form['user_name']

        user_email = request.form['user_email']

        message = request.form['message']

        query = """
        INSERT INTO bookings
        (house_id, user_name, user_email, message)

        VALUES (%s, %s, %s, %s)
        """

        values = (
            house_id,
            user_name,
            user_email,
            message
        )

        cursor.execute(query, values)

        db.commit()

        return "Booking Request Sent Successfully"

    return render_template('booking.html')

# --------booking statuse-----


@app.route('/accept-booking/<int:id>')
def accept_booking(id):

    cursor.execute(
        "UPDATE bookings SET status='Accepted' WHERE id=%s",
        (id,)
    )

    cursor.execute(
        "SELECT house_id FROM bookings WHERE id=%s",
        (id,)
    )

    house = cursor.fetchone()

    if house and house[0]:
        cursor.execute(
            "UPDATE houses SET availability='Booked' WHERE id=%s",
            (house[0],)
        )

    db.commit()

    return redirect('/admin/bookings')


@app.route('/reject-booking/<int:id>')
def reject_booking(id):

    query = """
    UPDATE bookings
    SET status='Rejected'
    WHERE id=%s
    """

    cursor.execute(query, (id,))
    db.commit()

    return redirect('/admin/bookings')

    # ------------- Manage House Block ----------


@app.route('/admin/houses')
def managehouses():

    cursor.execute("SELECT * FROM houses")

    all_houses = cursor.fetchall()

    return render_template(
        'admin/managehouse.html',
        houses=all_houses
    )
# ---------- Delete House ----------


@app.route('/delete-house/<int:id>')
def delete_house(id):

    cursor.execute(
        "DELETE FROM bookings WHERE house_id = %s",
        (id,)
    )

    cursor.execute(
        "DELETE FROM houses WHERE id = %s",
        (id,)
    )

    db.commit()

    return redirect('/admin/houses')
# --------


@app.route('/admin/bookings')
def view_bookings():

    cursor.execute("""
                   SELECT
                   bookings.id,
                   houses.house_name,
                   bookings.user_name,
                   bookings.user_email,
                   bookings.message,
                   bookings.status

                   FROM bookings

                   JOIN houses
                   ON bookings.house_id = houses.id""")

    all_bookings = cursor.fetchall()

    return render_template(
        'admin/bookings.html',
        bookings=all_bookings
    )
# -------- Edit House ----------


@app.route('/edit-house/<int:id>', methods=['GET', 'POST'])
def edit_house(id):

    # GET request
    if request.method == 'GET':
        query = "SELECT * FROM houses WHERE id=%s"
        cursor.execute(query, (id,))
        house = cursor.fetchone()
        return render_template('admin/edit.html', house=house)

    # POST request
    house_name = request.form['house_name']
    location = request.form['location']
    rent = request.form['rent']
    description = request.form['description']
    image = request.files.get('image')

    if image and image.filename != "":
        filename = secure_filename(image.filename)
        image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        query = """
        UPDATE houses
        SET house_name=%s,
            location=%s,
            rent=%s,
            description=%s,
            image=%s
        WHERE id=%s
        """

        values = (house_name, location, rent, description, filename, id)

    else:
        query = """
        UPDATE houses
        SET house_name=%s,
            location=%s,
            rent=%s,
            description=%s
        WHERE id=%s
        """

        values = (house_name, location, rent, description, id)

    cursor.execute(query, values)
    db.commit()

    return redirect('/admin/houses')


if __name__ == '__main__':
    app.run(debug=True)
