from flask import Flask, render_template, request, redirect, url_for, session, Response
import qrcode
import io
import base64
import os
from datetime import datetime, date

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'

# In-memory storage (resets when server restarts)
queue_data = {
    'is_active': False,
    'business_name': 'Our Business',
    'created_by': 'Admin',
    'session_started': None,
    'queue': [],  # List of queue numbers in order
    'serving_number': 0,
    'served_numbers': []  # Track served numbers for reporting
}

# Helper functions
def is_queue_active():
    return queue_data['is_active']

def set_queue_active(active, business_name="Our Business", created_by="Admin"):
    queue_data['is_active'] = active
    queue_data['business_name'] = business_name
    queue_data['created_by'] = created_by
    if active:
        queue_data['session_started'] = datetime.now()
        # Reset queue when starting new session
        queue_data['queue'] = []
        queue_data['serving_number'] = 0
        queue_data['served_numbers'] = []

def get_business_info():
    return (queue_data['business_name'], 
            queue_data['created_by'], 
            queue_data['session_started'] or datetime.now())

def get_queue_data():
    current_number = queue_data['serving_number']
    waiting = [num for num in queue_data['queue'] if num > current_number]
    total_waiting = len(waiting)
    return current_number, waiting, total_waiting

def calculate_wait_time(position):
    return max(0, (position - 1) * 5)

def generate_qr_code(url):
    """Generate QR code and return as base64 string"""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(url)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Convert to base64
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    
    img_str = base64.b64encode(buffer.getvalue()).decode()
    return f"data:image/png;base64,{img_str}"

def get_daily_stats():
    """Get today's statistics"""
    total_today = len(queue_data['queue']) + len(queue_data['served_numbers'])
    served_today = len(queue_data['served_numbers'])
    return total_today, served_today

# Routes
@app.route('/')
def home():
    if not is_queue_active():
        return '''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Queue Not Active</title>
            <style>
                body { font-family: Arial; text-align: center; padding: 50px; }
                .card { background: white; padding: 40px; border-radius: 10px; box-shadow: 0 5px 15px rgba(0,0,0,0.1); max-width: 500px; margin: 0 auto; }
                .btn { display: inline-block; padding: 12px 25px; background: #667eea; color: white; text-decoration: none; border-radius: 25px; margin: 10px; }
            </style>
        </head>
        <body>
            <div class="card">
                <h1>⏸️ Queue Not Active</h1>
                <p>The queue system is currently not active.</p>
                <a href="/admin/init" class="btn">Start Queue Management</a>
            </div>
        </body>
        </html>
        '''
    
    business_name, created_by, session_started = get_business_info()
    
    # Generate QR code for the main join page
    join_url = f"{request.url_root}join"
    qr_code = generate_qr_code(join_url)
    
    return f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>{business_name} - QuickQueue</title>
        <style>
            body {{ font-family: Arial; text-align: center; padding: 20px; }}
            .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 40px; border-radius: 10px; margin-bottom: 30px; }}
            .card {{ background: white; padding: 30px; border-radius: 10px; box-shadow: 0 5px 15px rgba(0,0,0,0.1); margin: 20px auto; max-width: 300px; }}
            .btn {{ display: inline-block; padding: 12px 30px; background: #28a745; color: white; text-decoration: none; border-radius: 25px; margin: 10px; }}
            .qr-code {{ max-width: 200px; margin: 20px auto; }}
            .qr-code img {{ width: 100%; border: 1px solid #ddd; border-radius: 10px; padding: 10px; background: white; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🚀 {business_name}</h1>
            <p>Queue Management System</p>
        </div>

        <div class="card">
            <h3>📱 Scan to Join Queue</h3>
            <div class="qr-code">
                <img src="{qr_code}" alt="Scan to join queue">
            </div>
            <a href="/join" class="btn">Get Queue Number</a>
        </div>

        <div class="card">
            <a href="/status" class="btn" style="background: #667eea;">View Queue Status</a>
        </div>
    </body>
    </html>
    '''

@app.route('/join')
def join_queue():
    if not is_queue_active():
        return redirect('/')
    
    # Get next queue number
    if queue_data['queue']:
        next_number = max(queue_data['queue']) + 1
    else:
        next_number = 1
    
    # Add to queue
    queue_data['queue'].append(next_number)
    
    # Get waiting position
    position = len([num for num in queue_data['queue'] if num < next_number]) + 1
    
    wait_time = calculate_wait_time(position)
    business_name, created_by, session_started = get_business_info()
    
    # Generate QR code for status page
    status_url = f"{request.url_root}status"
    qr_code = generate_qr_code(status_url)
    
    # Store user's queue number in session
    session['user_queue_number'] = next_number
    
    return f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Your Queue Number</title>
        <style>
            body {{ font-family: Arial; text-align: center; padding: 50px 20px; }}
            .success-card {{ background: white; padding: 40px; border-radius: 15px; box-shadow: 0 10px 30px rgba(0,0,0,0.1); max-width: 500px; margin: 0 auto; border: 2px solid #28a745; }}
            .queue-number {{ font-size: 4em; color: #28a745; margin: 20px 0; font-weight: bold; }}
            .info {{ background: #f8f9fa; padding: 20px; border-radius: 10px; margin: 20px 0; }}
            .btn {{ display: inline-block; padding: 12px 25px; background: #667eea; color: white; text-decoration: none; border-radius: 25px; margin: 10px; }}
            .qr-code {{ max-width: 150px; margin: 20px auto; }}
            .qr-code img {{ width: 100%; border: 1px solid #ddd; border-radius: 10px; padding: 10px; background: white; }}
        </style>
    </head>
    <body>
        <div class="success-card">
            <h1 style="color: #28a745;">✅ You're in Line!</h1>
            <div class="queue-number">#{next_number}</div>
            
            <div class="info">
                <p><strong>Position in line:</strong> {position}</p>
                <p><strong>Estimated wait:</strong> {wait_time} minutes</p>
            </div>

            <div class="qr-code">
                <img src="{qr_code}" alt="Scan to check status">
            </div>
            
            <a href="/status/{next_number}" class="btn">View My Status</a><br>
            <a href="/status" class="btn">View Full Queue</a><br>
            <a href="/" class="btn" style="background: #6c757d;">Back to Home</a>
        </div>
    </body>
    </html>
    '''

@app.route('/status')
def queue_status():
    if not is_queue_active():
        return redirect('/')
    
    current_number, waiting, total_waiting = get_queue_data()
    wait_time = calculate_wait_time(total_waiting + 1)
    business_name, created_by, session_started = get_business_info()
    
    waiting_display = ''.join([f'<div style="display: inline-block; background: white; padding: 10px 15px; margin: 5px; border-radius: 5px; border: 1px solid #dee2e6;">#{num}</div>' for num in waiting[:12]])
    
    return f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Queue Status</title>
        <meta http-equiv="refresh" content="15">
        <style>
            body {{ font-family: Arial; text-align: center; padding: 30px 20px; }}
            .current {{ background: #28a745; color: white; padding: 30px; border-radius: 10px; margin: 20px 0; }}
            .btn {{ display: inline-block; padding: 12px 25px; background: #667eea; color: white; text-decoration: none; border-radius: 25px; margin: 10px; }}
        </style>
    </head>
    <body>
        <h1>📊 Queue Status</h1>
        
        <div class="current">
            <h2>Now Serving</h2>
            <div style="font-size: 2.5em; font-weight: bold;">#{current_number if current_number else "---"}</div>
        </div>
        
        <div style="background: #f8f9fa; padding: 20px; border-radius: 10px; margin: 20px 0;">
            <h3>Waiting: {len(waiting)} people</h3>
            <div>{waiting_display}</div>
            {f'<p>... and {len(waiting) - 12} more</p>' if len(waiting) > 12 else ''}
        </div>
        
        <p>Estimated wait time: {wait_time} minutes</p>
        <a href="/join" class="btn" style="background: #28a745;">Join Queue</a>
        <a href="/" class="btn" style="background: #6c757d;">Home</a>
    </body>
    </html>
    '''

@app.route('/status/<int:queue_number>')
def user_queue_status(queue_number):
    if not is_queue_active():
        return redirect('/')
    
    current_number, waiting, total_waiting = get_queue_data()
    
    # Check if queue number exists
    if queue_number not in queue_data['queue'] and queue_number not in queue_data['served_numbers']:
        return '''
        <!DOCTYPE html>
        <html>
        <head><title>Error</title><style>body { font-family: Arial; text-align: center; padding: 50px; }</style></head>
        <body>
            <h1>❌ Queue Number Not Found</h1>
            <p>Please check your queue number or get a new one.</p>
            <a href="/join" style="padding: 10px 20px; background: #667eea; color: white; text-decoration: none; border-radius: 5px;">Get Queue Number</a>
        </body>
        </html>
        '''
    
    # Determine user's status
    if queue_number in queue_data['served_numbers']:
        status = 'served'
        user_position = 0
    elif queue_number == current_number:
        status = 'serving'
        user_position = 0
    else:
        status = 'waiting'
        user_position = len([num for num in queue_data['queue'] if num < queue_number]) + 1
    
    wait_time = calculate_wait_time(user_position) if user_position > 0 else 0
    business_name, created_by, session_started = get_business_info()
    
    status_html = ""
    if status == 'served':
        status_html = '<div style="background: #28a745; color: white; padding: 20px; border-radius: 10px; margin: 20px 0;"><h3>✅ Completed</h3><p>You have been served. Thank you!</p></div>'
    elif status == 'serving':
        status_html = '<div style="background: #28a745; color: white; padding: 20px; border-radius: 10px; margin: 20px 0;"><h3>🎉 It\'s Your Turn!</h3><p>Please proceed to the counter</p></div>'
    else:
        status_html = f'''
        <div style="background: #ffc107; color: #856404; padding: 15px; border-radius: 20px; margin: 15px 0; font-size: 1.2em;">
            Position in Line: {user_position}
        </div>
        <div style="background: #f8f9fa; padding: 20px; border-radius: 10px; margin: 20px 0; text-align: left;">
            <p><strong>Estimated wait time:</strong> {wait_time} minutes</p>
            <p><strong>People ahead of you:</strong> {user_position - 1}</p>
        </div>
        '''
    
    return f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Your Status</title>
        <meta http-equiv="refresh" content="30">
        <style>
            body {{ font-family: Arial; text-align: center; padding: 30px 20px; }}
            .queue-number {{ font-size: 3em; color: #28a745; margin: 20px 0; font-weight: bold; }}
            .btn {{ display: inline-block; padding: 12px 25px; background: #667eea; color: white; text-decoration: none; border-radius: 25px; margin: 10px; }}
        </style>
    </head>
    <body>
        <h1>Your Queue Status</h1>
        <div class="queue-number">#{queue_number}</div>
        
        {status_html}

        <div style="background: #28a745; color: white; padding: 15px; border-radius: 10px; margin: 20px 0;">
            <h3>Now Serving</h3>
            <div style="font-size: 2em; font-weight: bold;">#{current_number if current_number else "---"}</div>
        </div>
        
        <a href="/status" class="btn">View Full Queue</a>
        <a href="/" class="btn" style="background: #6c757d;">Home</a>
    </body>
    </html>
    '''

@app.route('/admin/init')
def admin_init():
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Start Queue</title>
        <style>
            body {{ font-family: Arial; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; display: flex; align-items: center; justify-content: center; padding: 20px; }}
            .card {{ background: white; padding: 40px; border-radius: 15px; box-shadow: 0 15px 35px rgba(0,0,0,0.1); max-width: 500px; width: 100%; }}
            input {{ width: 100%; padding: 12px; margin: 10px 0; border: 1px solid #ddd; border-radius: 5px; }}
            .btn {{ width: 100%; padding: 12px; background: #28a745; color: white; border: none; border-radius: 5px; font-size: 1.1em; cursor: pointer; }}
        </style>
    </head>
    <body>
        <div class="card">
            <h1 style="text-align: center;">🚀 Start Queue Management</h1>
            <form action="/admin/start" method="POST">
                <input type="text" name="business_name" placeholder="Business Name" required>
                <input type="text" name="created_by" placeholder="Your Name" required>
                <button type="submit" class="btn">Start Queue System</button>
            </form>
        </div>
    </body>
    </html>
    '''

@app.route('/admin/start', methods=['POST'])
def start_queue():
    business_name = request.form.get('business_name', 'Our Business')
    created_by = request.form.get('created_by', 'Admin')
    set_queue_active(True, business_name, created_by)
    return redirect('/admin')

@app.route('/admin')
def admin_panel():
    if not is_queue_active():
        return redirect('/admin/init')
    
    current_number, waiting, total_waiting = get_queue_data()
    business_name, created_by, session_started = get_business_info()
    
    # Generate QR codes
    join_url = f"{request.url_root}join"
    status_url = f"{request.url_root}status"
    join_qr = generate_qr_code(join_url)
    status_qr = generate_qr_code(status_url)
    
    total_today, served_today = get_daily_stats()
    
    waiting_html = ''.join([f'<div style="display: inline-block; background: white; padding: 15px; margin: 5px; border-radius: 5px; border: 1px solid #dee2e6; position: relative;">{num}<form action="/admin/remove/{num}" method="POST" style="display: inline; position: absolute; top: -5px; right: -5px;"><button type="submit" style="background: #dc3545; color: white; border: none; border-radius: 50%; width: 20px; height: 20px; font-size: 12px; cursor: pointer;">×</button></form></div>' for num in waiting])
    
    return f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Admin Panel</title>
        <style>
            body {{ font-family: Arial; padding: 20px; }}
            .btn {{ padding: 12px 25px; margin: 5px; border: none; border-radius: 5px; color: white; cursor: pointer; }}
            .btn-next {{ background: #28a745; }}
            .btn-add {{ background: #007bff; }}
            .btn-end {{ background: #dc3545; }}
        </style>
    </head>
    <body>
        <h1>⚙️ Admin Panel - {business_name}</h1>
        
        <div style="background: #f8f9fa; padding: 20px; border-radius: 10px; margin: 20px 0;">
            <h2>Now Serving: <span style="color: #28a745;">#{current_number if current_number else "None"}</span></h2>
            
            <form action="/admin/next" method="POST" style="display: inline;">
                <button type="submit" class="btn btn-next">✅ Serve Next</button>
            </form>
            <form action="/admin/add" method="POST" style="display: inline;">
                <button type="submit" class="btn btn-add">➕ Add Number</button>
            </form>
            <form action="/admin/end" method="POST" style="display: inline;">
                <button type="submit" class="btn btn-end">🛑 End Queue</button>
            </form>
        </div>

        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin: 20px 0;">
            <div style="text-align: center;">
                <h3>Join QR</h3>
                <img src="{join_qr}" style="max-width: 150px; border: 1px solid #ddd; padding: 10px; background: white;">
            </div>
            <div style="text-align: center;">
                <h3>Status QR</h3>
                <img src="{status_qr}" style="max-width: 150px; border: 1px solid #ddd; padding: 10px; background: white;">
            </div>
        </div>

        <h3>Waiting Queue ({len(waiting)} people):</h3>
        <div>{waiting_html}</div>
    </body>
    </html>
    '''

@app.route('/admin/next', methods=['POST'])
def serve_next():
    if not is_queue_active():
        return redirect('/admin/init')
    
    current_number = queue_data['serving_number']
    
    if current_number > 0:
        if current_number in queue_data['queue']:
            queue_data['queue'].remove(current_number)
        queue_data['served_numbers'].append(current_number)
    
    if queue_data['queue']:
        next_number = min(queue_data['queue'])
        queue_data['serving_number'] = next_number
    else:
        queue_data['serving_number'] = 0
    
    return redirect('/admin')

@app.route('/admin/add', methods=['POST'])
def add_manual():
    if not is_queue_active():
        return redirect('/admin/init')
    
    if queue_data['queue']:
        next_number = max(queue_data['queue']) + 1
    else:
        next_number = 1
    
    queue_data['queue'].append(next_number)
    return redirect('/admin')

@app.route('/admin/remove/<int:queue_number>', methods=['POST'])
def remove_customer(queue_number):
    if not is_queue_active():
        return redirect('/admin/init')
    
    if queue_number in queue_data['queue']:
        queue_data['queue'].remove(queue_number)
    
    return redirect('/admin')

@app.route('/admin/end', methods=['POST'])
def end_queue():
    set_queue_active(False)
    return redirect('/admin/init')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)