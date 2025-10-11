from flask import Flask, render_template, request, redirect, url_for, session, flash
import os
import json
from datetime import datetime
import functools
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__, template_folder='../templates', static_folder='../static')
app.secret_key = os.urandom(24)  # For session management

# Create database directory if it doesn't exist
DATABASE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'database')
os.makedirs(DATABASE_DIR, exist_ok=True)

# Define paths for JSON files
USERS_FILE = os.path.join(DATABASE_DIR, 'users.json')
ALERTS_FILE = os.path.join(DATABASE_DIR, 'alerts.json')

# Initialize JSON files if they don't exist
if not os.path.exists(USERS_FILE):
    with open(USERS_FILE, 'w') as f:
        json.dump({"users": [
            {"username": "admin", "password": generate_password_hash("admin123"), "role": "admin"},
            {"username": "emergency_dept", "password": generate_password_hash("emergency123"), "role": "admin"},
            {"username": "fire_dept", "password": generate_password_hash("fire123"), "role": "admin"},
            {"username": "john_citizen", "password": generate_password_hash("citizen123"), "role": "user"},
            {"username": "jane_doe", "password": generate_password_hash("jane123"), "role": "user"}
        ]}, f)

if not os.path.exists(ALERTS_FILE):
    with open(ALERTS_FILE, 'w') as f:
        json.dump({"alerts": []}, f)

# Login required decorator
def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if not session.get('logged_in'):
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('login'))
        return view(**kwargs)
    return wrapped_view

# Admin required decorator
def admin_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if not session.get('logged_in'):
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('login'))
        if session.get('role') != 'admin':
            flash('You do not have permission to access this page.', 'error')
            return redirect(url_for('index'))
        return view(**kwargs)
    return wrapped_view

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user_type = request.form.get('user_type', 'citizen')  # Default to citizen
        
        # Load users
        with open(USERS_FILE, 'r') as f:
            users_data = json.load(f)
        
        # Check credentials
        user = next((user for user in users_data["users"] if user["username"] == username), None)
        
        if user and check_password_hash(user["password"], password):
            # Validate user type matches their role
            if user_type == 'organization' and user['role'] != 'admin':
                flash('Access denied. This account is not authorized for organization login.', 'error')
                return render_template('login.html')
            elif user_type == 'citizen' and user['role'] == 'admin':
                flash('Please use the organization login for administrative accounts.', 'error')
                return render_template('login.html')
            
            session['logged_in'] = True
            session['username'] = username
            session['role'] = user['role']
            session['user_type'] = user_type
            
            # Add organization name to session if available
            if 'org_name' in user:
                session['org_name'] = user['org_name']
            
            if user_type == 'organization':
                org_display_name = user.get('org_name', username)
                flash(f'Welcome back, {org_display_name}! Organization dashboard loaded.', 'success')
                return redirect(url_for('dashboard'))
            else:
                flash(f'Welcome back, {username}! Citizen portal loaded.', 'success')
                return redirect(url_for('alerts'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        account_type = request.form.get('account_type', 'citizen')
        
        # Load users
        with open(USERS_FILE, 'r') as f:
            users_data = json.load(f)
        
        # Check if username already exists
        if any(user["username"] == username for user in users_data["users"]):
            flash('Username already exists', 'error')
            return render_template('register.html')
        
        # Check if passwords match
        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return render_template('register.html')
        
        # Handle organization registration
        if account_type == 'organization':
            org_name = request.form.get('org_name')
            auth_code = request.form.get('auth_code')
            
            # Validate organization fields
            if not org_name or not auth_code:
                flash('Organization name and authorization code are required', 'error')
                return render_template('register.html')
            
            # Verify authorization code (simple check for demo)
            valid_auth_codes = ['ORG123', 'EMERGENCY456', 'GOVT789']
            if auth_code not in valid_auth_codes:
                flash('Invalid authorization code', 'error')
                return render_template('register.html')
            
            # Add new organization user
            users_data["users"].append({
                "username": username,
                "password": generate_password_hash(password),
                "role": "admin",  # Organizations are admins
                "org_name": org_name,
                "org_type": "emergency_service"  # Default org type
            })
            
            flash('Organization registration successful! Please log in.', 'success')
        else:
            # Add new regular user
            users_data["users"].append({
                "username": username,
                "password": generate_password_hash(password),
                "role": "user"  # Default role is user
            })
            
            flash('Registration successful! Please log in.', 'success')
        
        # Save updated users
        with open(USERS_FILE, 'w') as f:
            json.dump(users_data, f)
        
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out', 'success')
    return redirect(url_for('index'))

@app.route('/dashboard')
@admin_required
def dashboard():
    # Load alerts for display
    with open(ALERTS_FILE, 'r') as f:
        alerts_data = json.load(f)
    
    return render_template('dashboard.html', alerts=alerts_data["alerts"])

@app.route('/alerts')
@login_required
def alerts():
    # Load alerts for display
    with open(ALERTS_FILE, 'r') as f:
        alerts_data = json.load(f)
    
    return render_template('alerts.html', alerts=alerts_data["alerts"])

@app.route('/send_alert', methods=['POST'])
@admin_required
def send_alert_route():
    message = request.form['message']
    region = request.form['region']
    methods = request.form.getlist('methods')  # ['sms', 'email', 'push']
    severity = request.form['severity']  # Added severity parameter
    
    # Simplified version - just simulate sending alert
    result = True
    
    # Save alert to database
    with open(ALERTS_FILE, 'r') as f:
        alerts_data = json.load(f)
    
    alerts_data["alerts"].append({
        "message": message,
        "region": region,
        "methods": methods,
        "severity": severity,  # Added severity to the alert data
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "sent_by": session.get('username', 'system')
    })
    
    with open(ALERTS_FILE, 'w') as f:
        json.dump(alerts_data, f)
    
    if result:
        flash('Alert sent successfully!', 'success')
        return redirect(url_for('dashboard'))
    else:
        flash('Failed to send alert.', 'error')
        return render_template('alert_sent.html', message=message, region=region, methods=methods)

@app.route('/map')
@login_required
def map_view():
    # Load alerts for map display
    with open(ALERTS_FILE, 'r') as f:
        alerts_data = json.load(f)
    
    return render_template('map.html', alerts=alerts_data["alerts"])

@app.route('/profile')
@login_required
def profile():
    # Get user data
    user = None
    locations = []
    
    # Load users
    with open(USERS_FILE, 'r') as f:
        users_data = json.load(f)
        for u in users_data["users"]:
            if u['username'] == session['username']:
                user = u
                break
    
    # Define locations file path
    LOCATIONS_FILE = os.path.join(DATABASE_DIR, 'locations.json')
    
    # Get saved locations
    try:
        with open(LOCATIONS_FILE, 'r') as f:
            all_locations = json.load(f)
            locations = [loc for loc in all_locations if loc['user_id'] == session['username']]
    except (FileNotFoundError, json.JSONDecodeError):
        # Create the file if it doesn't exist
        with open(LOCATIONS_FILE, 'w') as f:
            json.dump([], f)
    
    return render_template('profile.html', user=user, locations=locations)

@app.route('/add_location', methods=['POST'])
@login_required
def add_location():
    import uuid
    
    name = request.form.get('name')
    address = request.form.get('address')
    latitude = request.form.get('latitude')
    longitude = request.form.get('longitude')
    
    if not name or not latitude or not longitude:
        flash('Please provide all required location information', 'error')
        return redirect(url_for('profile'))
    
    # Generate a unique ID
    location_id = str(uuid.uuid4())
    
    # Create location object
    new_location = {
        'id': location_id,
        'user_id': session['username'],
        'name': name,
        'address': address,
        'latitude': latitude,
        'longitude': longitude,
        'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    # Define locations file path
    LOCATIONS_FILE = os.path.join(DATABASE_DIR, 'locations.json')
    
    # Save to locations.json
    try:
        with open(LOCATIONS_FILE, 'r') as f:
            locations = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        locations = []
    
    locations.append(new_location)
    
    with open(LOCATIONS_FILE, 'w') as f:
        json.dump(locations, f, indent=4)
    
    flash('Location saved successfully!', 'success')
    return redirect(url_for('profile'))

@app.route('/delete_location/<location_id>', methods=['DELETE'])
@login_required
def delete_location(location_id):
    # Define locations file path
    LOCATIONS_FILE = os.path.join(DATABASE_DIR, 'locations.json')
    
    try:
        with open(LOCATIONS_FILE, 'r') as f:
            locations = json.load(f)
        
        # Filter out the location to delete
        locations = [loc for loc in locations if not (loc['id'] == location_id and loc['user_id'] == session['username'])]
        
        with open(LOCATIONS_FILE, 'w') as f:
            json.dump(locations, f, indent=4)
        
        return '', 204  # No content success response
    except Exception as e:
        return str(e), 500

@app.route('/alert/<alert_id>')
@login_required
def alert_details(alert_id):
    # Load alerts from JSON file
    try:
        with open(os.path.join(DATABASE_DIR, 'alerts.json'), 'r') as f:
            alerts_data = json.load(f)
            alerts = alerts_data["alerts"]
            alert = next((a for a in alerts if a['id'] == alert_id), None)
            
            if not alert:
                flash('Alert not found', 'error')
                return redirect(url_for('dashboard'))
    except (FileNotFoundError, json.JSONDecodeError):
        flash('Error loading alert data', 'error')
        return redirect(url_for('dashboard'))
    
    # Check if user is marked safe for this alert
    marked_safe = False
    try:
        SAFE_FILE = os.path.join(DATABASE_DIR, 'safe_marks.json')
        if os.path.exists(SAFE_FILE):
            with open(SAFE_FILE, 'r') as f:
                safe_marks = json.load(f)
                marked_safe = any(mark['alert_id'] == alert_id and mark['user_id'] == session['username'] for mark in safe_marks)
    except (FileNotFoundError, json.JSONDecodeError):
        pass
    
    # Load community reports for this alert
    reports = []
    try:
        REPORTS_FILE = os.path.join(DATABASE_DIR, 'reports.json')
        if os.path.exists(REPORTS_FILE):
            with open(REPORTS_FILE, 'r') as f:
                all_reports = json.load(f)
                reports = [r for r in all_reports if r['alert_id'] == alert_id]
                # Sort reports by timestamp (newest first)
                reports.sort(key=lambda x: x['timestamp'], reverse=True)
    except (FileNotFoundError, json.JSONDecodeError):
        pass
    
    return render_template('alert_details.html', alert=alert, marked_safe=marked_safe, reports=reports)

@app.route('/mark_safe/<alert_id>', methods=['POST'])
@login_required
def mark_safe(alert_id):
    import uuid
    
    # Create safe mark object
    safe_mark = {
        'id': str(uuid.uuid4()),
        'user_id': session['username'],
        'alert_id': alert_id,
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    # Save to safe_marks.json
    SAFE_FILE = os.path.join(DATABASE_DIR, 'safe_marks.json')
    try:
        if os.path.exists(SAFE_FILE):
            with open(SAFE_FILE, 'r') as f:
                safe_marks = json.load(f)
        else:
            safe_marks = []
        
        # Check if already marked safe
        if not any(mark['alert_id'] == alert_id and mark['user_id'] == session['username'] for mark in safe_marks):
            safe_marks.append(safe_mark)
            
            with open(SAFE_FILE, 'w') as f:
                json.dump(safe_marks, f, indent=4)
    except Exception as e:
        return str(e), 500
    
    return '', 204  # No content success response

@app.route('/submit_report', methods=['POST'])
@login_required
def submit_report():
    import uuid
    
    data = request.get_json()
    
    # Create report object
    report = {
        'id': str(uuid.uuid4()),
        'user_id': session['username'],
        'alert_id': data['alert_id'],
        'report_type': data['report_type'],
        'location': data['location'],
        'description': data['description'],
        'severity': data['severity'],
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'status': 'active'  # For future moderation
    }
    
    # Save to reports.json
    REPORTS_FILE = os.path.join(DATABASE_DIR, 'reports.json')
    try:
        if os.path.exists(REPORTS_FILE):
            with open(REPORTS_FILE, 'r') as f:
                reports = json.load(f)
        else:
            reports = []
        
        reports.append(report)
        
        with open(REPORTS_FILE, 'w') as f:
            json.dump(reports, f, indent=4)
    except Exception as e:
        return str(e), 500
    
    return '', 204  # No content success response

# Admin routes
@app.route('/admin')
@login_required
def admin():
    # Check if user has admin role
    USERS_FILE = os.path.join(DATABASE_DIR, 'users.json')
    try:
        with open(USERS_FILE, 'r') as f:
            users_data = json.load(f)
            current_user = next((u for u in users_data if u['username'] == session['username']), None)
            
            # If user is not an admin, redirect to dashboard
            if not current_user or current_user.get('role', 'citizen').lower() != 'admin':
                flash('You do not have permission to access the admin dashboard', 'error')
                return redirect(url_for('dashboard'))
    except (FileNotFoundError, json.JSONDecodeError):
        flash('Error loading user data', 'error')
        return redirect(url_for('dashboard'))
    
    # Load all users for the user management tab
    users = users_data
    
    # Calculate analytics stats
    stats = calculate_analytics_stats()
    
    # Get today's date for the date picker
    today = datetime.now().strftime('%Y-%m-%d')
    
    return render_template('admin.html', users=users, stats=stats, today=today)

@app.route('/api/users', methods=['GET', 'POST', 'PUT', 'DELETE'])
@login_required
def api_users():
    # Check if user has admin role
    USERS_FILE = os.path.join(DATABASE_DIR, 'users.json')
    try:
        with open(USERS_FILE, 'r') as f:
            users = json.load(f)
            current_user = next((u for u in users if u['username'] == session['username']), None)
            
            # If user is not an admin, return error
            if not current_user or current_user.get('role', 'citizen').lower() != 'admin':
                return jsonify({'error': 'Unauthorized'}), 403
    except (FileNotFoundError, json.JSONDecodeError):
        return jsonify({'error': 'Error loading user data'}), 500
    
    if request.method == 'GET':
        # Return all users
        return jsonify(users)
    
    elif request.method == 'POST':
        # Create new user
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['username', 'email', 'password', 'role']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Check if username already exists
        if any(u['username'] == data['username'] for u in users):
            return jsonify({'error': 'Username already exists'}), 400
        
        # Create new user object
        import uuid
        new_user = {
            'id': str(uuid.uuid4()),
            'username': data['username'],
            'email': data['email'],
            'password': data['password'],  # In a real app, this would be hashed
            'role': data['role'],
            'active': data.get('active', True),
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # Add to users list and save
        users.append(new_user)
        with open(USERS_FILE, 'w') as f:
            json.dump(users, f, indent=4)
        
        return jsonify(new_user), 201
    
    elif request.method == 'PUT':
        # Update existing user
        data = request.get_json()
        
        # Validate required fields
        if 'id' not in data:
            return jsonify({'error': 'Missing user ID'}), 400
        
        # Find user by ID
        user_index = next((i for i, u in enumerate(users) if u['id'] == data['id']), None)
        if user_index is None:
            return jsonify({'error': 'User not found'}), 404
        
        # Update user fields
        for field in ['username', 'email', 'role', 'active']:
            if field in data:
                users[user_index][field] = data[field]
        
        # Save changes
        with open(USERS_FILE, 'w') as f:
            json.dump(users, f, indent=4)
        
        return jsonify(users[user_index]), 200
    
    elif request.method == 'DELETE':
        # Delete user
        data = request.get_json()
        
        # Validate required fields
        if 'id' not in data:
            return jsonify({'error': 'Missing user ID'}), 400
        
        # Find user by ID
        user_index = next((i for i, u in enumerate(users) if u['id'] == data['id']), None)
        if user_index is None:
            return jsonify({'error': 'User not found'}), 404
        
        # Remove user
        deleted_user = users.pop(user_index)
        
        # Save changes
        with open(USERS_FILE, 'w') as f:
            json.dump(users, f, indent=4)
        
        return jsonify(deleted_user), 200

@app.route('/api/settings', methods=['GET', 'POST'])
@login_required
def api_settings():
    # Check if user has admin role
    USERS_FILE = os.path.join(DATABASE_DIR, 'users.json')
    try:
        with open(USERS_FILE, 'r') as f:
            users = json.load(f)
            current_user = next((u for u in users if u['username'] == session['username']), None)
            
            # If user is not an admin, return error
            if not current_user or current_user.get('role', 'citizen').lower() != 'admin':
                return jsonify({'error': 'Unauthorized'}), 403
    except (FileNotFoundError, json.JSONDecodeError):
        return jsonify({'error': 'Error loading user data'}), 500
    
    SETTINGS_FILE = os.path.join(DATABASE_DIR, 'settings.json')
    
    if request.method == 'GET':
        # Return current settings
        try:
            if os.path.exists(SETTINGS_FILE):
                with open(SETTINGS_FILE, 'r') as f:
                    settings = json.load(f)
            else:
                # Default settings
                settings = {
                    'requireApproval': True,
                    'autoExpire': True,
                    'defaultDuration': 24,
                    'durationUnit': 'hours',
                    'notifyNewUsers': True,
                    'notifyReports': True
                }
        except (FileNotFoundError, json.JSONDecodeError):
            return jsonify({'error': 'Error loading settings'}), 500
        
        return jsonify(settings)
    
    elif request.method == 'POST':
        # Update settings
        data = request.get_json()
        
        try:
            with open(SETTINGS_FILE, 'w') as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            return jsonify({'error': str(e)}), 500
        
        return jsonify(data), 200

@app.route('/api/analytics', methods=['GET'])
@login_required
def api_analytics():
    # Check if user has admin role
    USERS_FILE = os.path.join(DATABASE_DIR, 'users.json')
    try:
        with open(USERS_FILE, 'r') as f:
            users = json.load(f)
            current_user = next((u for u in users if u['username'] == session['username']), None)
            
            # If user is not an admin, return error
            if not current_user or current_user.get('role', 'citizen').lower() != 'admin':
                return jsonify({'error': 'Unauthorized'}), 403
    except (FileNotFoundError, json.JSONDecodeError):
        return jsonify({'error': 'Error loading user data'}), 500
    
    # Get query parameters
    from_date = request.args.get('from', '')
    to_date = request.args.get('to', '')
    alert_type = request.args.get('type', 'all')
    
    # Calculate analytics based on parameters
    stats = calculate_analytics_stats(from_date, to_date, alert_type)
    
    return jsonify(stats)

def calculate_analytics_stats(from_date=None, to_date=None, alert_type=None):
    """Calculate analytics statistics for the admin dashboard"""
    # In a real app, this would query the database for actual statistics
    # For now, we'll return placeholder data
    
    # Placeholder stats
    stats = {
        'total_alerts': 25,
        'total_recipients': 1250,
        'delivery_rate': 92,
        'safe_responses': 156,
        'reports_submitted': 42,
        'delivery_by_method': {
            'sms': 65,
            'email': 25,
            'push': 10
        },
        'engagement': {
            'viewed': 85,
            'marked_safe': 45,
            'reported': 15
        },
        'regions': {
            'north': {'delivery': 92, 'engagement': 75},
            'south': {'delivery': 88, 'engagement': 65},
            'east': {'delivery': 95, 'engagement': 80},
            'west': {'delivery': 90, 'engagement': 70},
            'central': {'delivery': 93, 'engagement': 85}
        }
    }
    
    return stats

@app.route('/analytics')
@login_required
def analytics():
    # Check if user has appropriate role (admin, creator, or approver)
    USERS_FILE = os.path.join(DATABASE_DIR, 'users.json')
    try:
        with open(USERS_FILE, 'r') as f:
            users = json.load(f)
            current_user = next((u for u in users if u['username'] == session['username']), None)
            
            # Get user role, default to citizen if not found
            user_role = current_user.get('role', 'citizen').lower() if current_user else 'citizen'
            
            # If user is not authorized, redirect to dashboard
            if user_role not in ['admin', 'creator', 'approver']:
                flash('You do not have permission to access analytics', 'error')
                return redirect(url_for('dashboard'))
    except (FileNotFoundError, json.JSONDecodeError):
        flash('Error loading user data', 'error')
        return redirect(url_for('dashboard'))
    
    # Load alerts for the selector
    alerts = []
    try:
        with open(os.path.join(DATABASE_DIR, 'alerts.json'), 'r') as f:
            alerts_data = json.load(f)
            alerts = alerts_data.get("alerts", [])
            # Sort alerts by timestamp (newest first)
            alerts.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
    except (FileNotFoundError, json.JSONDecodeError):
        pass
    
    # Load reports for the reports table
    reports = []
    try:
        REPORTS_FILE = os.path.join(DATABASE_DIR, 'reports.json')
        if os.path.exists(REPORTS_FILE):
            with open(REPORTS_FILE, 'r') as f:
                reports = json.load(f)
                # Sort reports by timestamp (newest first)
                reports.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
    except (FileNotFoundError, json.JSONDecodeError):
        pass
    
    # Calculate analytics stats
    stats = calculate_analytics_stats()
    
    # Get today's date for the date picker
    today = datetime.now().strftime('%Y-%m-%d')
    
    return render_template('analytics.html', 
                          alerts=alerts, 
                          reports=reports, 
                          stats=stats, 
                          today=today, 
                          user_role=user_role)

if __name__ == '__main__':
    app.run(debug=True)
