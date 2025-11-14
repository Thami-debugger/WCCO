from flask import Flask, render_template_string, request, redirect, url_for, session
import qrcode
from qrcode.constants import ERROR_CORRECT_L
import io
import base64
import os
from datetime import datetime, date

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'quickqueue-pro-secure-key-2024')

# In-memory storage
queue_data = {
    'is_active': False,
    'business_name': 'Business Name',
    'created_by': 'Manager',
    'session_started': None,
    'queue': [],
    'serving_number': 0,
    'served_numbers': []
}

# Helper functions
def is_queue_active():
    return queue_data['is_active']

def set_queue_active(active, business_name="Business Name", created_by="Manager"):
    queue_data['is_active'] = active
    queue_data['business_name'] = business_name
    queue_data['created_by'] = created_by
    if active:
        queue_data['session_started'] = datetime.now()
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
    qr = qrcode.QRCode(version=1, error_correction=ERROR_CORRECT_L, box_size=10, border=4)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#2c3e50", back_color="white")
    buffer = io.BytesIO()
    img.save(buffer, "PNG")
    buffer.seek(0)
    img_str = base64.b64encode(buffer.getvalue()).decode()
    return f"data:image/png;base64,{img_str}"

# HTML Template
BASE_STYLE = '''
<style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body { 
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
        background: #f8fafc; 
        color: #2d3748; 
        line-height: 1.6;
    }
    .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
    .header { 
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white; 
        padding: 3rem 2rem; 
        border-radius: 12px;
        margin-bottom: 2rem;
        text-align: center;
    }
    .card {
        background: white;
        padding: 2rem;
        border-radius: 12px;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
        border: 1px solid #e2e8f0;
        margin-bottom: 1.5rem;
    }
    .btn {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        padding: 12px 24px;
        background: #667eea;
        color: white;
        text-decoration: none;
        border-radius: 8px;
        font-weight: 500;
        border: none;
        cursor: pointer;
        transition: all 0.2s ease;
    }
    .btn:hover { background: #5a67d8; transform: translateY(-1px); }
    .btn-primary { background: #48bb78; }
    .btn-primary:hover { background: #38a169; }
    .btn-secondary { background: #718096; }
    .btn-secondary:hover { background: #4a5568; }
    .btn-danger { background: #e53e3e; }
    .btn-danger:hover { background: #c53030; }
    .qr-container { text-align: center; padding: 1.5rem; background: #f7fafc; border-radius: 8px; margin: 1.5rem 0; }
    .qr-code { max-width: 200px; margin: 0 auto; }
    .queue-number { font-size: 4rem; font-weight: 700; color: #48bb78; margin: 1rem 0; }
    .form-group { margin-bottom: 1.5rem; }
    .form-label { display: block; margin-bottom: 0.5rem; font-weight: 500; color: #4a5568; }
    .form-input { width: 100%; padding: 12px 16px; border: 2px solid #e2e8f0; border-radius: 8px; font-size: 16px; }
    .form-input:focus { outline: none; border-color: #667eea; }
    .grid { display: grid; gap: 1.5rem; margin: 2rem 0; }
    .grid-2 { grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); }
    .grid-3 { grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); }
    .stat-card { text-align: center; padding: 1.5rem; background: white; border-radius: 8px; box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1); }
    .stat-number { font-size: 2.5rem; font-weight: 700; color: #667eea; margin-bottom: 0.5rem; }
    .footer { text-align: center; margin-top: 3rem; padding: 2rem; color: #718096; border-top: 1px solid #e2e8f0; }
</style>
'''

# Routes
@app.route('/')
def home():
    if not is_queue_active():
        return f'''
        <!DOCTYPE html>
        <html>
        <head><title>Queue System</title>{BASE_STYLE}</head>
        <body>
            <div class="container">
                <div style="max-width: 500px; margin: 100px auto; text-align: center;">
                    <div class="card">
                        <div style="font-size: 4rem; margin-bottom: 1rem;">⏸️</div>
                        <h1 style="margin-bottom: 1rem;">Queue System Inactive</h1>
                        <p style="color: #718096; margin-bottom: 2rem;">The queue management system is currently not active.</p>
                        <a href="/admin/init" class="btn">Activate Queue System</a>
                    </div>
                </div>
            </div>
        </body>
        </html>
        '''
    
    business_name, created_by, session_started = get_business_info()
    join_url = f"{request.url_root}join"
    qr_code = generate_qr_code(join_url)
    
    return f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>{business_name} - Queue Management</title>
        {BASE_STYLE}
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1 style="font-size: 2.5rem; margin-bottom: 0.5rem;">🚀 {business_name}</h1>
                <p style="font-size: 1.2rem; opacity: 0.9;">Digital Queue Management System</p>
            </div>

            <div class="qr-container">
                <h3 style="margin-bottom: 1rem;">Scan to Join Queue</h3>
                <div class="qr-code">
                    <img src="{qr_code}" alt="Join Queue QR Code" style="width: 100%; border-radius: 8px;">
                </div>
                <p style="margin-top: 1rem; color: #718096;">Scan QR code or use the button below</p>
            </div>

            <div class="grid grid-2">
                <div class="card" style="text-align: center;">
                    <div style="font-size: 3rem; margin-bottom: 1rem;">👥</div>
                    <h3 style="margin-bottom: 1rem;">Join Queue</h3>
                    <p style="color: #718096; margin-bottom: 1.5rem;">Get your digital queue number</p>
                    <a href="/join" class="btn btn-primary">Get Queue Number</a>
                </div>
                
                <div class="card" style="text-align: center;">
                    <div style="font-size: 3rem; margin-bottom: 1rem;">📊</div>
                    <h3 style="margin-bottom: 1rem;">Queue Status</h3>
                    <p style="color: #718096; margin-bottom: 1.5rem;">View current queue progress</p>
                    <a href="/status" class="btn">View Live Status</a>
                </div>
            </div>

            <div class="footer">
                <p>QuickQueue Professional &copy; 2024</p>
            </div>
        </div>
    </body>
    </html>
    '''

@app.route('/join')
def join_queue():
    if not is_queue_active():
        return redirect('/')
    
    if queue_data['queue']:
        next_number = max(queue_data['queue']) + 1
    else:
        next_number = 1
    
    queue_data['queue'].append(next_number)
    position = len([num for num in queue_data['queue'] if num < next_number]) + 1
    wait_time = calculate_wait_time(position)
    business_name, created_by, session_started = get_business_info()
    
    status_url = f"{request.url_root}status/{next_number}"
    qr_code = generate_qr_code(status_url)
    
    return f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Your Queue Number</title>
        {BASE_STYLE}
    </head>
    <body>
        <div class="container">
            <div style="max-width: 600px; margin: 2rem auto;">
                <div class="card">
                    <div style="text-align: center;">
                        <div style="font-size: 4rem; color: #48bb78; margin-bottom: 1rem;">✅</div>
                        <h1 style="margin-bottom: 1rem;">You're in the Queue</h1>
                        <p style="color: #718096; margin-bottom: 2rem;">Your digital queue number has been assigned</p>
                        
                        <div class="queue-number">#{next_number}</div>
                        
                        <div class="card" style="background: #f0fff4; border-color: #9ae6b4;">
                            <h3 style="margin-bottom: 1rem; color: #2f855a;">Queue Information</h3>
                            <p><strong>Position in line:</strong> {position}</p>
                            <p><strong>Estimated wait time:</strong> {wait_time} minutes</p>
                            <p><strong>Business:</strong> {business_name}</p>
                        </div>

                        <div class="qr-container">
                            <h4 style="margin-bottom: 1rem;">Track Your Status</h4>
                            <div class="qr-code">
                                <img src="{qr_code}" alt="Status QR Code" style="width: 100%; border-radius: 8px;">
                            </div>
                            <p style="margin-top: 1rem; color: #718096;">Scan to track your real-time queue position</p>
                        </div>

                        <div style="display: flex; gap: 1rem; justify-content: center; flex-wrap: wrap; margin-top: 2rem;">
                            <a href="/status/{next_number}" class="btn">Track My Status</a>
                            <a href="/status" class="btn btn-secondary">View Full Queue</a>
                            <a href="/" class="btn btn-secondary">Return Home</a>
                        </div>
                    </div>
                </div>
            </div>
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
    
    return f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Queue Status</title>
        {BASE_STYLE}
        <meta http-equiv="refresh" content="15">
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>📊 Live Queue Status</h1>
                <p>{business_name}</p>
            </div>

            <div class="grid grid-3">
                <div class="stat-card">
                    <div class="stat-number">{current_number if current_number else '--'}</div>
                    <div>Now Serving</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">{len(waiting)}</div>
                    <div>Waiting</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">{wait_time}</div>
                    <div>Est. Wait (min)</div>
                </div>
            </div>

            <div class="card">
                <h3 style="margin-bottom: 1rem;">Currently Waiting</h3>
                <div style="min-height: 100px;">
                    {' '.join([f'<span style="display: inline-block; background: white; padding: 8px 16px; margin: 0.5rem; border-radius: 20px; border: 1px solid #e2e8f0;">#{num}</span>' for num in waiting]) if waiting else '<p style="color: #718096; text-align: center;">No customers waiting</p>'}
                </div>
            </div>

            <div style="text-align: center; margin-top: 2rem;">
                <a href="/join" class="btn btn-primary">Join Queue</a>
                <a href="/" class="btn btn-secondary">Return Home</a>
            </div>
        </div>
    </body>
    </html>
    '''

@app.route('/status/<int:queue_number>')
def user_queue_status(queue_number):
    if not is_queue_active():
        return redirect('/')
    
    current_number, waiting, total_waiting = get_queue_data()
    
    if queue_number not in queue_data['queue'] and queue_number not in queue_data['served_numbers']:
        return f'''
        <!DOCTYPE html>
        <html>
        <head><title>Error</title>{BASE_STYLE}</head>
        <body>
            <div class="container">
                <div style="max-width: 500px; margin: 100px auto; text-align: center;">
                    <div class="card">
                        <div style="font-size: 4rem; color: #e53e3e; margin-bottom: 1rem;">❌</div>
                        <h1 style="margin-bottom: 1rem;">Queue Number Not Found</h1>
                        <p style="color: #718096; margin-bottom: 2rem;">Please verify your queue number.</p>
                        <a href="/join" class="btn btn-primary">Get Queue Number</a>
                    </div>
                </div>
            </div>
        </body>
        </html>
        '''
    
    if queue_number in queue_data['served_numbers']:
        status = 'served'
        user_position = 0
        status_icon = '✅'
        status_color = '#48bb78'
        status_message = 'Service Completed'
    elif queue_number == current_number:
        status = 'serving'
        user_position = 0
        status_icon = '🎉'
        status_color = '#ed8936'
        status_message = 'Your Turn Now'
    else:
        status = 'waiting'
        user_position = len([num for num in queue_data['queue'] if num < queue_number]) + 1
        status_icon = '⏳'
        status_color = '#4299e1'
        status_message = 'In Queue'
    
    wait_time = calculate_wait_time(user_position) if user_position > 0 else 0
    business_name, created_by, session_started = get_business_info()
    
    return f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Your Status</title>
        {BASE_STYLE}
        <meta http-equiv="refresh" content="30">
    </head>
    <body>
        <div class="container">
            <div style="max-width: 600px; margin: 2rem auto;">
                <div class="card">
                    <div style="text-align: center;">
                        <div style="font-size: 4rem; margin-bottom: 1rem;">{status_icon}</div>
                        <h1 style="margin-bottom: 0.5rem;">Queue Status</h1>
                        <p style="color: #718096; margin-bottom: 2rem;">{business_name}</p>
                        
                        <div class="queue-number">#{queue_number}</div>
                        
                        <div style="background: {status_color}; color: white; padding: 1.5rem; border-radius: 8px; margin: 1.5rem 0;">
                            <h2 style="margin-bottom: 0.5rem;">{status_message}</h2>
                            {f'<p style="font-size: 1.2rem;">Position {user_position} in line</p>' if status == 'waiting' else ''}
                        </div>

                        <div class="grid grid-2" style="margin: 2rem 0;">
                            <div class="stat-card">
                                <div class="stat-number">{current_number if current_number else '--'}</div>
                                <div>Now Serving</div>
                            </div>
                            <div class="stat-card">
                                <div class="stat-number">{wait_time if status == 'waiting' else 0}</div>
                                <div>Est. Wait (min)</div>
                            </div>
                        </div>

                        <div style="display: flex; gap: 1rem; justify-content: center; flex-wrap: wrap;">
                            <a href="/status" class="btn">View Full Queue</a>
                            <a href="/" class="btn btn-secondary">Return Home</a>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </body>
    </html>
    '''

@app.route('/admin/init')
def admin_init():
    return f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Activate Queue System</title>
        {BASE_STYLE}
    </head>
    <body>
        <div class="container">
            <div style="max-width: 500px; margin: 50px auto;">
                <div class="card">
                    <div style="text-align: center; margin-bottom: 2rem;">
                        <div style="font-size: 3rem; color: #667eea; margin-bottom: 1rem;">🚀</div>
                        <h1 style="margin-bottom: 0.5rem;">Activate Queue System</h1>
                        <p style="color: #718096;">Configure your digital queue management</p>
                    </div>
                    
                    <form action="/admin/start" method="POST">
                        <div class="form-group">
                            <label class="form-label">Business/Organization Name</label>
                            <input type="text" name="business_name" class="form-input" placeholder="Enter business name" required>
                        </div>
                        
                        <div class="form-group">
                            <label class="form-label">Manager/Administrator Name</label>
                            <input type="text" name="created_by" class="form-input" placeholder="Enter administrator name" required>
                        </div>
                        
                        <button type="submit" class="btn" style="width: 100%;">🚀 Activate Queue System</button>
                    </form>
                </div>
            </div>
        </div>
    </body>
    </html>
    '''

@app.route('/admin/start', methods=['POST'])
def start_queue():
    business_name = request.form.get('business_name', 'Business Name')
    created_by = request.form.get('created_by', 'Manager')
    set_queue_active(True, business_name, created_by)
    return redirect('/admin')

@app.route('/admin')
def admin_panel():
    if not is_queue_active():
        return redirect('/admin/init')
    
    current_number, waiting, total_waiting = get_queue_data()
    business_name, created_by, session_started = get_business_info()
    
    join_url = f"{request.url_root}join"
    status_url = f"{request.url_root}status"
    join_qr = generate_qr_code(join_url)
    status_qr = generate_qr_code(status_url)
    
    total_customers = len(queue_data['queue']) + len(queue_data['served_numbers'])
    served_today = len(queue_data['served_numbers'])
    
    return f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Admin Dashboard</title>
        {BASE_STYLE}
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>⚙️ Queue Management Dashboard</h1>
                <p>{business_name} • Managed by {created_by}</p>
            </div>

            <div class="grid grid-3">
                <div class="stat-card">
                    <div class="stat-number">{current_number if current_number else '--'}</div>
                    <div>Now Serving</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">{total_customers}</div>
                    <div>Total Today</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">{served_today}</div>
                    <div>Served</div>
                </div>
            </div>

            <div class="grid grid-2">
                <div class="card">
                    <h3 style="margin-bottom: 1rem;">Queue Actions</h3>
                    <div style="display: flex; gap: 1rem; flex-wrap: wrap;">
                        <form action="/admin/next" method="POST" style="display: inline;">
                            <button type="submit" class="btn btn-primary">✅ Serve Next</button>
                        </form>
                        <form action="/admin/add" method="POST" style="display: inline;">
                            <button type="submit" class="btn">➕ Add Entry</button>
                        </form>
                        <form action="/admin/end" method="POST" style="display: inline;">
                            <button type="submit" class="btn btn-danger">🛑 End Session</button>
                        </form>
                    </div>
                </div>

                <div class="card">
                    <h3 style="margin-bottom: 1rem;">Quick Links</h3>
                    <div style="display: flex; gap: 1rem;">
                        <a href="{join_url}" target="_blank" class="btn btn-secondary">Join Page</a>
                        <a href="{status_url}" target="_blank" class="btn btn-secondary">Status Page</a>
                    </div>
                </div>
            </div>

            <div class="grid grid-2">
                <div class="card">
                    <h3 style="margin-bottom: 1rem;">Join Queue QR</h3>
                    <div class="qr-code">
                        <img src="{join_qr}" alt="Join QR" style="width: 100%; border-radius: 8px;">
                    </div>
                </div>
                
                <div class="card">
                    <h3 style="margin-bottom: 1rem;">Status QR</h3>
                    <div class="qr-code">
                        <img src="{status_qr}" alt="Status QR" style="width: 100%; border-radius: 8px;">
                    </div>
                </div>
            </div>

            <div class="card">
                <h3 style="margin-bottom: 1rem;">Waiting Queue ({len(waiting)} customers)</h3>
                <div style="min-height: 100px;">
                    {' '.join([f"""
                    <div style="display: inline-block; background: white; padding: 1rem; margin: 0.5rem; border-radius: 8px; border: 1px solid #e2e8f0; position: relative;">
                        #{num}
                        <form action="/admin/remove/{num}" method="POST" style="display: inline; position: absolute; top: -8px; right: -8px;">
                            <button type="submit" style="background: #e53e3e; color: white; border: none; border-radius: 50%; width: 24px; height: 24px; cursor: pointer;">×</button>
                        </form>
                    </div>
                    """ for num in waiting]) if waiting else '<p style="color: #718096; text-align: center;">No customers waiting</p>'}
                </div>
            </div>
        </div>
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
    app.run(host='0.0.0.0', port=port, debug=False)