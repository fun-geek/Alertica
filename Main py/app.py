from flask import Flask, render_template, request, redirect, url_for, flash
from utils.notifier import send_alert
from database.firebase import db

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Replace with an environment variable in production

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/send_alert', methods=['POST'])
def send_alert_route():
    message = request.form['message']
    region = request.form['region']
    methods = request.form.getlist('methods')  # ['sms', 'email', 'push']
    
    result = send_alert(message, region, methods)
    
    if result:
        flash('Alert sent successfully!', 'success')
    else:
        flash('Failed to send alert.', 'error')
    
    return render_template('alert_sent.html', message=message, region=region, methods=methods)

if __name__ == '__main__':
    app.run(debug=True)
