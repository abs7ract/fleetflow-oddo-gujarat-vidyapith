from flask import Flask, render_template, request, redirect, url_for, session
import mysql.connector

app = Flask(__name__)
app.secret_key = 'super_secret_hackathon_key' 

def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="", # <--- CHANGE THIS!
        database="fleetflow"
    )

# ==========================================
# ROUTE 1 & 2: LOGIN AND DASHBOARD
# ==========================================
@app.route('/', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        role = request.form['role']
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM Users WHERE email = %s AND password_hash = %s AND role = %s", (email, password, role))
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if user:
            session['loggedin'] = True
            session['id'] = user['id']
            session['role'] = user['role']
            return redirect(url_for('dashboard'))
        else:
            error = 'Invalid email, password, or role.'
    return render_template('login.html', error=error)

@app.route('/dashboard')
def dashboard():
    if 'loggedin' not in session: return redirect(url_for('login'))
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT COUNT(*) as count FROM Vehicles WHERE status = 'On Trip'")
        active_fleet = cursor.fetchone()['count']
        cursor.execute("SELECT COUNT(*) as count FROM Vehicles WHERE status = 'In Shop'")
        in_shop = cursor.fetchone()['count']
        cursor.execute("SELECT COUNT(*) as count FROM Vehicles")
        total_fleet = cursor.fetchone()['count']
        utilization_rate = round((active_fleet / total_fleet) * 100, 1) if total_fleet > 0 else 0
        cursor.execute("SELECT name_model, license_plate, status FROM Vehicles LIMIT 5")
        vehicles = cursor.fetchall()
        cursor.close()
        conn.close()
        kpis = {'activeFleet': active_fleet, 'inShop': in_shop, 'utilizationRate': f"{utilization_rate}%"}
        return render_template('dashboard.html', kpis=kpis, vehicles=vehicles)
    except Exception:
        return render_template('dashboard.html', kpis={'activeFleet': 0, 'inShop': 0, 'utilizationRate': '0%'}, vehicles=[])

# ==========================================
# FLEET MANAGER ROUTES
# ==========================================
@app.route('/vehicles', methods=['GET', 'POST'])
def vehicles():
    if 'loggedin' not in session or session.get('role') != 'Manager': return redirect(url_for('login'))
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    if request.method == 'POST':
        name = request.form['name_model']
        plate = request.form['license_plate']
        capacity = request.form['max_load_capacity']
        cursor.execute("INSERT INTO Vehicles (name_model, license_plate, max_load_capacity) VALUES (%s, %s, %s)", (name, plate, capacity))
        conn.commit()
    cursor.execute("SELECT * FROM Vehicles")
    all_vehicles = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('vehicles.html', vehicles=all_vehicles)

@app.route('/retire_vehicle/<int:id>', methods=['POST'])
def retire_vehicle(id):
    if 'loggedin' not in session or session.get('role') != 'Manager': return redirect(url_for('login'))
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE Vehicles SET status = 'Out of Service' WHERE id = %s", (id,))
    conn.commit()
    cursor.close()
    conn.close()
    return redirect(url_for('vehicles'))

@app.route('/maintenance', methods=['GET', 'POST'])
def maintenance():
    if 'loggedin' not in session or session.get('role') != 'Manager': return redirect(url_for('login'))
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    if request.method == 'POST':
        vehicle_id = request.form['vehicle_id']
        description = request.form['description']
        cost = request.form['cost']
        service_date = request.form['service_date']
        cursor.execute("INSERT INTO MaintenanceLogs (vehicle_id, description, cost, service_date) VALUES (%s, %s, %s, %s)", (vehicle_id, description, cost, service_date))
        cursor.execute("UPDATE Vehicles SET status = 'In Shop' WHERE id = %s", (vehicle_id,))
        conn.commit()
    cursor.execute("SELECT id, name_model, license_plate FROM Vehicles WHERE status != 'Out of Service'")
    active_vehicles = cursor.fetchall()
    cursor.execute("SELECT m.*, v.name_model, v.license_plate FROM MaintenanceLogs m JOIN Vehicles v ON m.vehicle_id = v.id ORDER BY m.service_date DESC")
    logs = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('maintenance.html', vehicles=active_vehicles, logs=logs)

# ==========================================
# DISPATCHER ROUTES
# ==========================================
@app.route('/dispatch', methods=['GET', 'POST'])
def dispatch():
    if 'loggedin' not in session or session.get('role') != 'Dispatcher': return redirect(url_for('login'))
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    error, success = None, None
    if request.method == 'POST':
        if 'create_trip' in request.form:
            vehicle_id, driver_id, cargo_weight = request.form['vehicle_id'], request.form['driver_id'], float(request.form['cargo_weight'])
            cursor.execute("SELECT max_load_capacity FROM Vehicles WHERE id = %s", (vehicle_id,))
            vehicle = cursor.fetchone()
            if vehicle and cargo_weight > vehicle['max_load_capacity']:
                error = f"Validation Failed: Cargo weight exceeds max capacity ({vehicle['max_load_capacity']}kg)."
            else:
                cursor.execute("INSERT INTO Trips (vehicle_id, driver_id, cargo_weight, status) VALUES (%s, %s, %s, 'Dispatched')", (vehicle_id, driver_id, cargo_weight))
                cursor.execute("UPDATE Vehicles SET status = 'On Trip' WHERE id = %s", (vehicle_id,))
                cursor.execute("UPDATE Drivers SET status = 'On Trip' WHERE id = %s", (driver_id,))
                conn.commit()
                success = "Trip dispatched!"
        elif 'complete_trip' in request.form:
            trip_id, vehicle_id, driver_id = request.form['trip_id'], request.form['ret_vehicle_id'], request.form['ret_driver_id']
            cursor.execute("UPDATE Trips SET status = 'Completed' WHERE id = %s", (trip_id,))
            cursor.execute("UPDATE Vehicles SET status = 'Available' WHERE id = %s", (vehicle_id,))
            cursor.execute("UPDATE Drivers SET status = 'Available' WHERE id = %s", (driver_id,))
            conn.commit()
            success = "Trip marked completed!"

    cursor.execute("SELECT id, name_model, license_plate, max_load_capacity FROM Vehicles WHERE status = 'Available'")
    available_vehicles = cursor.fetchall()
    # Safety feature: Dispatcher can only assign Available drivers whose license is NOT expired!
    cursor.execute("SELECT id, name FROM Drivers WHERE status = 'Available' AND license_expiry >= CURDATE()")
    available_drivers = cursor.fetchall()
    cursor.execute("""
        SELECT t.id, t.cargo_weight, t.status, v.name_model, v.license_plate, v.id as vehicle_id, d.name as driver_name, d.id as driver_id 
        FROM Trips t JOIN Vehicles v ON t.vehicle_id = v.id JOIN Drivers d ON t.driver_id = d.id ORDER BY t.created_at DESC
    """)
    trips = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('dispatch.html', vehicles=available_vehicles, drivers=available_drivers, trips=trips, error=error, success=success)

# ==========================================
# SAFETY OFFICER ROUTES
# ==========================================
@app.route('/drivers', methods=['GET', 'POST'])
def drivers():
    if 'loggedin' not in session or session.get('role') != 'Safety Officer': return redirect(url_for('login'))
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    if request.method == 'POST':
        if 'add_driver' in request.form:
            name = request.form['name']
            license_expiry = request.form['license_expiry']
            cursor.execute("INSERT INTO Drivers (name, license_expiry, status) VALUES (%s, %s, 'Available')", (name, license_expiry))
            conn.commit()
        elif 'update_status' in request.form:
            driver_id = request.form['driver_id']
            new_status = request.form['new_status']
            cursor.execute("UPDATE Drivers SET status = %s WHERE id = %s", (new_status, driver_id))
            conn.commit()
            
    cursor.execute("SELECT * FROM Drivers")
    all_drivers = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('drivers.html', drivers=all_drivers)

# ==========================================
# FINANCIAL ANALYST ROUTES
# ==========================================
@app.route('/expenses', methods=['GET', 'POST'])
def expenses():
    if 'loggedin' not in session or session.get('role') != 'Financial Analyst': return redirect(url_for('login'))
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    if request.method == 'POST':
        vehicle_id = request.form['vehicle_id']
        liters = request.form['liters']
        cost = request.form['cost']
        log_date = request.form['log_date']
        cursor.execute("INSERT INTO FuelLogs (vehicle_id, liters, cost, log_date) VALUES (%s, %s, %s, %s)", (vehicle_id, liters, cost, log_date))
        conn.commit()

    cursor.execute("SELECT id, name_model, license_plate FROM Vehicles")
    vehicles = cursor.fetchall()
    
    cursor.execute("""
        SELECT f.*, v.name_model, v.license_plate 
        FROM FuelLogs f JOIN Vehicles v ON f.vehicle_id = v.id ORDER BY f.log_date DESC
    """)
    fuel_logs = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('expenses.html', vehicles=vehicles, logs=fuel_logs)

@app.route('/analytics')
def analytics():
    if 'loggedin' not in session or session.get('role') != 'Financial Analyst': return redirect(url_for('login'))
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Calculate Total Fleet ROI and Efficiency
    cursor.execute("SELECT SUM(revenue_generated) as total_rev, SUM(acquisition_cost) as total_acq FROM Vehicles")
    financials = cursor.fetchone()
    
    cursor.execute("SELECT SUM(cost) as total_maint FROM MaintenanceLogs")
    maint = cursor.fetchone()
    
    cursor.execute("SELECT SUM(cost) as total_fuel, SUM(liters) as total_liters FROM FuelLogs")
    fuel = cursor.fetchone()
    
    cursor.execute("SELECT SUM(odometer) as total_km FROM Vehicles")
    kms = cursor.fetchone()

    # Math safeguards
    rev = financials['total_rev'] or 0
    acq = financials['total_acq'] or 1
    total_cost = (maint['total_maint'] or 0) + (fuel['total_fuel'] or 0)
    
    # ROI Formula: (Revenue - (Maintenance + Fuel)) / Acquisition Cost
    fleet_roi = round(((rev - total_cost) / acq) * 100, 2)
    
    # Fuel Efficiency: km / L
    total_km = kms['total_km'] or 0
    total_liters = fuel['total_liters'] or 1
    efficiency = round(total_km / total_liters, 2) if total_liters > 0 else 0

    cursor.close()
    conn.close()
    
    return render_template('analytics.html', roi=fleet_roi, efficiency=efficiency, total_cost=total_cost)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True, port=5000)