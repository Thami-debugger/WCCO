import os
from flask import Flask, render_template, jsonify, redirect, url_for, request
import qrcode
from dotenv import load_dotenv
import signal

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'supersecretkey')

queue = []
served_queue = []
missing_queue = []
current_number = 0
average_time_per_person = int(os.getenv('AVERAGE_TIME_PER_PERSON', 5))  # in minutes
serving_started = False
global_counter = 1  # Global counter to assign unique queue numbers

# Ensure the static directory exists
if not os.path.exists('static'):
    os.makedirs('static')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/join_queue')
def join_queue():
    global queue, global_counter
    new_number = global_counter
    global_counter += 1
    queue.append(new_number)
    img = qrcode.make(f'{request.host_url}confirm_served/{new_number}')
    img_path = f'static/queue_{new_number}.png'
    img.save(img_path)
    position_in_queue = queue.index(new_number) + 1

    # Ensure the image is deleted after rendering
    return render_template('queue.html', number=new_number, image_url=img_path, position=position_in_queue, img_path=img_path)

@app.route('/queue_status/<int:number>')
def queue_status(number):
    img_path = f'static/queue_{number}.png'
    return render_template('queue.html', number=number, image_url=img_path, img_path=img_path)

@app.route('/delete_image/<path:img_path>', methods=['POST'])
def delete_image(img_path):
    if os.path.exists(img_path):
        os.remove(img_path)
    return '', 204

@app.route('/confirm_served/<int:number>')
def confirm_served(number):
    global queue, served_queue, current_number, missing_queue
    if number == current_number:
        served_queue.append(queue.pop(0))
        while queue and current_number in missing_queue:
            missing_queue.remove(current_number)
            served_queue.append(queue.pop(0))
        if queue:
            current_number = queue[0]
        else:
            current_number = 0
    return render_template('confirm_served.html', number=number, current_number=current_number)

@app.route('/current_status')
def current_status():
    global current_number, queue, average_time_per_person, serving_started
    if queue:
        current_number = queue[0]
    wait_time = (len(queue) * average_time_per_person) - average_time_per_person
    return jsonify({
        'current_number': current_number,
        'queue_length': len(queue),
        'average_wait_time': max(0, wait_time) if serving_started else 'Serving not started',
        'serving_started': serving_started
    })

@app.route('/admin')
def admin():
    return render_template('admin.html', queue=queue, current_number=current_number, serving_started=serving_started, missing_queue=missing_queue)

@app.route('/start_serving', methods=['POST'])
def start_serving():
    global serving_started
    serving_started = True
    return redirect(url_for('admin'))

@app.route('/serve_next', methods=['POST'])
def serve_next():
    global queue, served_queue, current_number
    if queue:
        current_number = queue.pop(0)
        while current_number in missing_queue:
            missing_queue.remove(current_number)
            served_queue.append(current_number)
            if queue:
                current_number = queue.pop(0)
            else:
                current_number = 0
                break
        if current_number:
            served_queue.append(current_number)
    return redirect(url_for('admin'))

@app.route('/mark_missing/<int:number>', methods=['POST'])
def mark_missing(number):
    global queue, missing_queue
    if number in queue:
        queue.remove(number)
        missing_queue.append(number)
    return redirect(url_for('admin'))

@app.route('/reset', methods=['POST'])
def reset():
    global queue, served_queue, missing_queue, current_number, global_counter, serving_started
    queue.clear()
    served_queue.clear()
    missing_queue.clear()
    current_number = 0
    global_counter = 1
    serving_started = False
    return redirect(url_for('admin'))

@app.route('/shutdown', methods=['POST'])
def shutdown():
    os.kill(os.getpid(), signal.SIGINT)
    return 'Server shutting down...'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=os.getenv('FLASK_DEBUG', 'False').lower() in ['true', '1']))
