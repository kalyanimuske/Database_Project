from flask import Flask, render_template, request, redirect, url_for, session , flash
import mysql.connector
from mysql.connector import Error
from flask_bcrypt import Bcrypt
from flask import jsonify
import os 
import sys 
import ssl
from OpenSSL import crypto

app = Flask(__name__)

bcrypt = Bcrypt(app)

app.secret_key = 'your_secret_key'

def generate_self_signed_cert(cert_file, key_file):
    """
    Generate a self-signed SSL certificate and key
    """
    # Create a key pair
    k = crypto.PKey()
    k.generate_key(crypto.TYPE_RSA, 4096)

    # Create a self-signed cert
    cert = crypto.X509()
    cert.get_subject().CN = 'localhost'  # Certificate subject (Common Name)
    cert.set_serial_number(1000)  # Serial number for the certificate
    cert.gmtime_adj_notBefore(0)  # Validity start time (current time)
    cert.gmtime_adj_notAfter(10*365*24*60*60)  # Validity duration (10 years)
    cert.set_issuer(cert.get_subject())  # The issuer is the subject in case of self-signed cert
    cert.set_pubkey(k)  # Public key for the certificate
    cert.sign(k, 'sha256')  # Sign the certificate with the private key using SHA-256

    # Write the certificate and key to the files
    with open(cert_file, "wt") as f:
        f.write(crypto.dump_certificate(crypto.FILETYPE_PEM, cert).decode('utf-8'))
    with open(key_file, "wt") as f:
        f.write(crypto.dump_privatekey(crypto.FILETYPE_PEM, k).decode('utf-8'))


# MySQL Connection
def get_db_connection():
    return mysql.connector.connect(
        host='localhost',
        user='root',
        password='root',
        database='CulturalFestivalPlanner3'
    )

# Home route - Welcome page
@app.route('/')
def home():
    return render_template('home.html')


@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Get form data
        user_name = request.form['user_name']
        user_email = request.form['user_email']
        address = request.form['address']
        user_contact = request.form['user_contact']
        role = request.form['role']
        password = request.form['password']  # New password field

        if not user_name or not user_email or not address or not user_contact or not role or not password:
            return 'Please fill in all fields.'

        try:
            # Connect to MySQL
            connection = get_db_connection()
            cursor = connection.cursor()

            # Check if the user already exists
            check_query = "SELECT * FROM User WHERE user_email = %s"
            cursor.execute(check_query, (user_email,))
            existing_user = cursor.fetchone()

            if existing_user:
                return render_template('register.html', error="User already exists! Please login.")

            # Hash the password before storing
            hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

            # Insert data into User table
            query = """INSERT INTO User (user_name, user_email, address, user_contact, role, password) 
                       VALUES (%s, %s, %s, %s, %s, %s)"""
            values = (user_name, user_email, address, user_contact, role, hashed_password)
            cursor.execute(query, values)
            connection.commit()

            session['user_id'] = cursor.lastrowid  # Store user_id in session
            session['role'] = role  # Store role in session
            return render_template('register_success.html', user_name=user_name)

        except Error as e:
            print(f"Error: {e}")
            return 'There was an error with the registration. Please try again.'

        finally:
            if connection:
                cursor.close()
                connection.close()

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role')  # Get the role from the form

        try:
            # Connect to MySQL
            connection = get_db_connection()
            cursor = connection.cursor()

            # Check if the user exists with the given role
            query = "SELECT * FROM User WHERE user_email = %s AND role = %s"
            cursor.execute(query, (email, role))
            user = cursor.fetchone()

            if user and bcrypt.check_password_hash(user[6], password):  # Password column
                session['user_id'] = user[0]  # Store user_id in session
                session['role'] = user[5]  # Store role in session
                session['user_name'] = user[1]  # Store user_name in session
                
                # Redirect based on role
                if role == 'Admin':
                    return redirect(url_for('admin_dashboard'))
                else:
                    return redirect(url_for('login_success'))

            else:
                error_message = "Invalid email, password, or role!"
                return render_template('login.html', error=error_message)

        except Error as e:
            print(f"Error: {e}")
            return 'There was an error. Please try again later.'

        finally:
            if connection:
                cursor.close()
                connection.close()

    return render_template('login.html')

@app.route('/login_success')
def login_success():
    user_name = session.get('user_name', 'Guest')  # Default to 'Guest' if not found
    return render_template('login_success.html', user_name=user_name)



@app.route('/admin_dashboard', methods=['GET', 'POST'])
def admin_dashboard():
    # Check if the user is logged in and their role is either 'Admin' or 'Organizer'
    if 'user_id' not in session or session.get('role') not in ['Admin', 'Organizer']:
        return "Access Denied. Admins Only!", 403

    try:
        # Connect to MySQL
        connection = get_db_connection()
        cursor = connection.cursor()
        
        # Retrieve table names
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()

        # Retrieve data from each table
        database_data = {}
        for (table_name,) in tables:
            cursor.execute(f"SELECT * FROM {table_name}")
            columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()
            database_data[table_name] = {
                "columns": columns,
                "rows": rows
            }

        return render_template('admin_dashboard.html', database_data=database_data)

    except Exception as e:
        print(f"Error: {e}")  # Log the exact error
        return f"An error occurred while fetching data: {e}"

    finally:
        if connection:
            cursor.close()
            connection.close()
     


@app.route('/add_new/<table_name>', methods=['GET', 'POST'])
def add_new_row(table_name):
    if 'user_id' not in session or session.get('role') != 'Admin':
        return "Access Denied. Admins Only!", 403

    # Ensure the table name is valid
    table_mapping = {
        "festival": "Festival",
        "event": "Event",
        "venue": "Venue"
    }

    if table_name not in table_mapping:
        flash("Invalid table name.")
        return redirect(url_for('admin_dashboard'))

    try:
        # Connect to MySQL
        connection = get_db_connection()
        cursor = connection.cursor()

        # Retrieve column names for the table
        cursor.execute(f"DESCRIBE {table_mapping[table_name]}")
        columns = cursor.fetchall()

        # Handle form submission
        if request.method == 'POST':
            column_names = [col[0] for col in columns if col[0] != 'id']  # Exclude 'id' from the input form
            values = [request.form[col] for col in column_names]
            query = f"INSERT INTO {table_mapping[table_name]} ({', '.join(column_names)}) VALUES ({', '.join(['%s'] * len(values))})"
            cursor.execute(query, tuple(values))
            connection.commit()
            flash(f"New row added to {table_name} successfully!")
            return redirect(url_for('admin_dashboard'))

        return render_template('add_new_row.html', table_name=table_name, columns=columns)

    except Exception as e:
        print(f"Error: {e}")
        flash(f"Error adding row: {e}")
        return redirect(url_for('admin_dashboard'))

    finally:
        if connection:
            cursor.close()
            connection.close()




@app.route('/edit/<table_name>/<int:row_id>', methods=['GET'])
def edit_row(table_name, row_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    # Map normalized table names to their actual database names and primary keys
    table_mapping = {
        "festival": {"db_name": "Festival", "primary_key": "festival_id"},
        "venue": {"db_name": "Venue", "primary_key": "venue_id"},
        "user": {"db_name": "User", "primary_key": "user_id"},
        "event": {"db_name": "Event", "primary_key": "event_id"}
    }

    # Ensure the table name is valid
    normalized_table_name = table_name.lower()
    if normalized_table_name not in table_mapping:
        flash(f"Unknown table: {table_name}")
        return redirect(url_for('dashboard'))

    table_info = table_mapping[normalized_table_name]
    primary_key_column = table_info["primary_key"]

    # Fetch data for the row to be edited
    cursor.execute(f"SELECT * FROM {table_info['db_name']} WHERE {primary_key_column} = %s", (row_id,))
    row = cursor.fetchone()

    # Fetch column names for the table
    cursor.execute(f"SHOW COLUMNS FROM {table_info['db_name']}")
    columns = [col[0] for col in cursor.fetchall()]

    conn.close()
    if row:
        return render_template('edit_row.html', table_name=table_name, row=row, columns=columns, enumerate=enumerate)
    else:
        flash("Row not found!")
        return redirect(url_for('admin_dashboard'))  # Redirect to the dashboard or another page



@app.route('/update/<table_name>/<int:row_id>', methods=['POST'])
def update_row(table_name, row_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    # Map normalized table names to their actual database names and primary keys
    table_mapping = {
        "festival": {"db_name": "Festival", "primary_key": "festival_id"},
        "venue": {"db_name": "Venue", "primary_key": "venue_id"},
        "user": {"db_name": "User", "primary_key": "user_id"},
        "event": {"db_name": "Event", "primary_key": "event_id"}
    }

    # Ensure the table name is valid
    normalized_table_name = table_name.lower()
    if normalized_table_name not in table_mapping:
        flash(f"Unknown table: {table_name}")
        return redirect(url_for('dashboard'))

    table_info = table_mapping[normalized_table_name]
    primary_key_column = table_info["primary_key"]

    # Dynamically build the update query based on form data
    updates = []
    values = []
    for key, value in request.form.items():
        updates.append(f"{key} = %s")
        values.append(value)

    values.append(row_id)  # Add row ID for the WHERE clause
    query = f"UPDATE {table_info['db_name']} SET {', '.join(updates)} WHERE {primary_key_column} = %s"

    # Debugging query
    print(f"Executing query: {query}")
    print(f"Values: {values}")

    try:
        cursor.execute(query, tuple(values))
        conn.commit()
        flash("Row updated successfully!")
    except Exception as e:
        conn.rollback()
        flash(f"Error updating row: {e}")
    finally:
        conn.close()

    return redirect(url_for('admin_dashboard')) 




@app.route('/delete_row/<table_name>/<int:row_id>', methods=['POST'])
def delete_row(table_name, row_id):
    connection = None
    try:
        print("Starting delete_row function...")
        
        # Map normalized table names to their actual database names and primary keys
        table_mapping = {
            "festival": {"db_name": "Festival", "primary_key": "festival_id", "dependent_tables": ["Event"]},
            "venue": {"db_name": "Venue", "primary_key": "venue_id"},
            "user": {"db_name": "User", "primary_key": "user_id"},
            "event": {"db_name": "Event", "primary_key": "event_id"}
        }

        normalized_table_name = table_name.lower()
        if normalized_table_name not in table_mapping:
            raise ValueError(f"Unknown table: {table_name}")

        table_info = table_mapping[normalized_table_name]
        db_table_name = table_info["db_name"]
        primary_key_column = table_info["primary_key"]

        # Connect to the database
        connection = get_db_connection()

        cursor = connection.cursor()

        # Delete dependent rows if applicable (e.g., in Event table for Festival)
        if "dependent_tables" in table_info:
            for dependent_table in table_info["dependent_tables"]:
                dependent_column = f"{db_table_name.lower()}_id"
                delete_dependent_query = f"DELETE FROM {dependent_table} WHERE {dependent_column} = %s"
                cursor.execute(delete_dependent_query, (row_id,))

        # Now delete the row from the main table
        query = f"DELETE FROM {db_table_name} WHERE {primary_key_column} = %s"
        cursor.execute(query, (row_id,))

        # Commit the transaction
        connection.commit()

        return jsonify(success=True, message=f"Row with ID {row_id} deleted successfully from table {db_table_name}!")

    except Exception as e:
        print(f"Error occurred during row deletion: {e}")
        return jsonify(success=False, error=str(e))

    finally:
        if connection:
            connection.close()


# Festival Registration Route
@app.route('/festival', methods=['GET', 'POST'])
def festivals():
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT festival_id, festival_name, festival_date FROM Festival")
    festivals = cursor.fetchall()

    selected_festival = None
    selected_festival_name = None
    events = []

    if request.method == 'POST':
        user_id = session.get('user_id')
        role = session.get('role')

        if not user_id or not role:
            return redirect(url_for('register'))

        selected_festival = request.form['festival_id']

        if not selected_festival:
            return 'Please select a festival.'

        try:
            # Check if the user has already registered for the same festival
            cursor.execute("""
                SELECT COUNT(*) FROM UserFestival 
                WHERE user_id = %s AND festival_id = %s
            """, (user_id, selected_festival))
            already_registered = cursor.fetchone()[0]

            if already_registered == 0:
                # If the user is not yet registered, insert into UserFestival
                cursor.execute("""
                    INSERT INTO UserFestival (user_id, festival_id, role) 
                    VALUES (%s, %s, %s)
                """, (user_id, selected_festival, role))
                connection.commit()

            # Fetch the name of the selected festival
            cursor.execute("""
                SELECT festival_name FROM Festival WHERE festival_id = %s
            """, (selected_festival,))
            selected_festival_name = cursor.fetchone()[0]

            # Fetch events related to this festival
            cursor.execute("""
                SELECT 
                    e.event_id, e.event_name, e.event_date, e.event_feedback, 
                    e.event_starttime, e.event_endtime, e.ticket_price, 
                    v.venue_name, v.venue_location, v.venue_des 
                FROM 
                    Event e 
                JOIN 
                    Venue v 
                ON 
                    e.venue_id = v.venue_id 
                WHERE 
                    e.festival_id = %s
            """, (selected_festival,))
            events = cursor.fetchall()

            success_message = "You have successfully registered for the Festival!"
            return render_template(
                'festival.html', 
                festivals=festivals, 
                events=events, 
                success=success_message, 
                selected_festival=selected_festival, 
                festival_locked=True, 
                selected_festival_name=selected_festival_name
            )

        except Error as e:
            print(f"Database Error: {e}")
            return f'There was an error with the festival registration. Error details: {e}'

        finally:
            cursor.close()
            connection.close()

    return render_template('festival.html', festivals=festivals, selected_festival=selected_festival)


@app.route('/event', methods=['POST'])
def event_registration():
    user_id = session.get('user_id')
    role = session.get('role')
    
    if not user_id:
        return redirect(url_for('register'))
    
    event_id = request.form['event_id']
    festival_id = request.form['festival_id']

    if not event_id or not festival_id:
        return 'Please select both a festival and an event.'
    
    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        # Check if the user has already registered for this specific event
        cursor.execute("""
            SELECT COUNT(*) FROM UserEvent WHERE user_id = %s AND event_id = %s
        """, (user_id, event_id))
        already_registered = cursor.fetchone()[0]

        if already_registered > 0:
            # User has already registered for this event
            return 'You have already registered for this event.'

        # Insert into UserEvent table
        cursor.execute("""
            INSERT INTO UserEvent (user_id, event_id, role) 
            VALUES (%s, %s, %s)
        """, (user_id, event_id, role))
        
        # Insert into Registration table
        cursor.execute("""
            INSERT INTO Registration (reg_date, user_id, event_id) 
            VALUES (CURDATE(), %s, %s)
        """, (user_id, event_id))
        
        # Commit the changes
        connection.commit()

        session['event_id'] = event_id
        
        # Fetch festival and event names and ticket price for display
        cursor.execute("SELECT festival_name FROM Festival WHERE festival_id = %s", (festival_id,))
        festival_name = cursor.fetchone()[0]
        
        cursor.execute("SELECT event_name, ticket_price FROM Event WHERE event_id = %s", (event_id,))
        event_name, ticket_price = cursor.fetchone()

        connection.close()

        # Redirect to the payment page
        return render_template('payment.html', festival_name=festival_name, event_name=event_name, ticket_price=ticket_price)

    except Error as e:
        print(f"Error: {e}")
        return 'There was an error with the event registration. Please try again.'


@app.route('/fetch-registrations', methods=['GET'])
def fetch_registrations():
    user_id = session.get('user_id')
    
    if not user_id:
        return jsonify({"error": "User not logged in"}), 401

    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        # Fetch user's registered festivals and events
        cursor.execute("""
            SELECT 
                f.festival_name, 
                e.event_name, 
                v.venue_name 
            FROM 
                UserEvent ue 
            JOIN 
                Event e ON ue.event_id = e.event_id
            JOIN 
                Festival f ON e.festival_id = f.festival_id
            JOIN 
                Venue v ON e.venue_id = v.venue_id
            WHERE 
                ue.user_id = %s
        """, (user_id,))
        registrations = cursor.fetchall()

        # Convert data to JSON format
        results = [
            {"festival": r[0], "event": r[1], "venue": r[2]} for r in registrations
        ]

        return jsonify(results)

    except Error as e:
        print(f"Database Error: {e}")
        return jsonify({"error": "Failed to fetch registrations"}), 500

    finally:
        cursor.close()
        connection.close()


@app.route('/process_payment', methods=['POST'])
def process_payment():
    try:
        # Retrieve user_id and event_id from the session (like in event_registration)
        user_id = session.get('user_id')
        event_id = session.get('event_id')

        if not user_id or not event_id:
            return redirect(url_for('register'))  # Redirect to register if not logged in or event_id not found

        # Retrieve form data
        ticket_price = request.form.get('ticket_price')
        payment_method = request.form.get('payment_method')

        # Debugging prints
        print("DEBUG: user_id =", user_id)
        print("DEBUG: event_id =", event_id)
        print("DEBUG: ticket_price =", ticket_price)
        print("DEBUG: payment_method =", payment_method)

        if not ticket_price or not payment_method:
            return 'Missing required fields!', 400

        # Ensure all required fields are received
        connection = get_db_connection()
        cursor = connection.cursor()

        # Step 1: Insert data into `Ticket` table
        ticket_query = """
            INSERT INTO Ticket (ticket_price, user_id, event_id)
            VALUES (%s, %s, %s)
        """
        cursor.execute(ticket_query, (ticket_price, user_id, event_id))
        connection.commit()
        ticket_id = cursor.lastrowid  # Retrieve the last inserted ticket_id

        # Step 2: Insert data into `Payment` table
        payment_query = """
            INSERT INTO Payment (amount, payment_date, mode, user_id, ticket_id)
            VALUES (%s, NOW(), %s, %s, %s)
        """
        cursor.execute(payment_query, (ticket_price, payment_method, user_id, ticket_id))
        connection.commit()

        # Step 3: Fetch event and festival details
        cursor.execute("SELECT event_name FROM Event WHERE event_id = %s", (event_id,))
        event_name_result = cursor.fetchone()
        event_name = event_name_result[0] if event_name_result else "Unknown Event"

        cursor.execute(""" 
            SELECT festival_name 
            FROM Festival 
            WHERE festival_id = (SELECT festival_id FROM Event WHERE event_id = %s)
        """, (event_id,))
        festival_name_result = cursor.fetchone()
        festival_name = festival_name_result[0] if festival_name_result else "Unknown Festival"

        connection.close()

        # Debugging: Ensure all variables are passed correctly
        print(f"DEBUG: Ticket Price: {ticket_price}")
        print(f"DEBUG: Event Name: {event_name}")
        print(f"DEBUG: Festival Name: {festival_name}")

        # Redirect to the success page
        return render_template(
            'final_success.html',
            event_name=event_name,
            festival_name=festival_name,
            ticket_price=ticket_price  # Pass ticket_price to the template
        )

    except Exception as e:
        print(f"Error: {e}")
        return 'There was an error processing the payment. Please try again.', 500

@app.route('/fetch_graph_data')
def fetch_graph_data():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # SQL query to fetch ticket sales data
        query = """
        SELECT 
            f.festival_name, 
            COUNT(t.ticket_id) AS tickets_sold
        FROM 
            Festival f
        JOIN 
            Event e ON f.festival_id = e.festival_id
        JOIN 
            Ticket t ON e.event_id = t.event_id
        GROUP BY 
            f.festival_name;
        """
        cursor.execute(query)
        results = cursor.fetchall()

        # Prepare data for the graph
        data = {"labels": [], "values": []}
        for row in results:
            data["labels"].append(row[0])  # Festival names
            data["values"].append(row[1])  # Tickets sold

        return jsonify(data)

    except Exception as e:
        return jsonify({"error": str(e)})
    finally:
        cursor.close()
        conn.close()

@app.route('/fetch_total_collection', methods=['GET'])
def fetch_total_collection():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Run the SQL query to calculate the total collection and collection per festival
        cursor.execute("""
            SELECT f.festival_name, SUM(p.amount) AS festival_collection
            FROM Festival f
            JOIN Event e ON f.festival_id = e.festival_id
            JOIN Ticket t ON e.event_id = t.event_id
            JOIN Payment p ON t.ticket_id = p.ticket_id
            GROUP BY f.festival_name
        """)

        # Fetch all results (collections per festival)
        festival_collections = cursor.fetchall()

        # Calculate total collection across all festivals
        cursor.execute("""
            SELECT SUM(p.amount) AS total_collection
            FROM Festival f
            JOIN Event e ON f.festival_id = e.festival_id
            JOIN Ticket t ON e.event_id = t.event_id
            JOIN Payment p ON t.ticket_id = p.ticket_id
        """)
        total_result = cursor.fetchone()
        total_collection = total_result[0] if total_result else 0

        # Close the connection
        cursor.close()
        conn.close()

        # Return both festival collections and total collection as JSON
        return jsonify({'festival_collections': festival_collections, 'total_collection': total_collection})

    except Exception as e:
        return jsonify({'error': str(e)})


if __name__ == '__main__':
    cert_file = 'cert.pem'  # Certificate file
    key_file = 'key.pem'    # Private key file

    # Check if the certificate and key files exist, if not generate them
    if not os.path.exists(cert_file) or not os.path.exists(key_file):
        generate_self_signed_cert(cert_file, key_file)

    # Create SSL context
    context = ssl.SSLContext(ssl.PROTOCOL_TLS)
    context.load_cert_chain(certfile=cert_file, keyfile=key_file)

    # Run the Flask app with SSL context
    app.run(host='0.0.0.0', port=3000, debug=True)
