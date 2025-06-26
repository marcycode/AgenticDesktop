from flask import Flask, render_template, request, jsonify, session
from flask_socketio import SocketIO, emit
import uuid
from prompt_agent import get_command_steps, get_opposite_command_steps
from desktop_actions import execute_steps
from speech_input import get_voice_command
import json
import threading
import time
import base64
import io
import mss
from PIL import Image

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here' # left blank is for now
socketio = SocketIO(app, cors_allowed_origins="*")

# Store command history and status
command_history = {}

# Desktop streaming variables
desktop_streaming = False
desktop_stream_thread = None

def capture_desktop():
    """Capture desktop screenshot and return as base64 encoded image"""
    try:
        with mss.mss() as sct:
            # Capture the entire screen (monitor 1)
            monitor = sct.monitors[1]
            screenshot = sct.grab(monitor)
            
            # Convert to PIL Image
            img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
            
            # Resize image for better performance (max width 1280)
            width, height = img.size
            if width > 1280:
                ratio = 1280 / width
                new_height = int(height * ratio)
                img = img.resize((1280, new_height), Image.Resampling.LANCZOS)
            
            # Convert to base64
            buffer = io.BytesIO()
            img.save(buffer, format='JPEG', quality=85, optimize=True)
            img_str = base64.b64encode(buffer.getvalue()).decode()
            
            return img_str
    except Exception as e:
        print(f"Error capturing desktop: {e}")
        return None

def desktop_streaming_worker():
    """Background worker for desktop streaming"""
    global desktop_streaming
    while desktop_streaming:
        try:
            screenshot = capture_desktop()
            if screenshot:
                socketio.emit('desktop_frame', {'image': screenshot})
            time.sleep(0.1)  # 10 FPS
        except Exception as e:
            print(f"Desktop streaming error: {e}")
            time.sleep(1)

@socketio.on('start_desktop_stream')
def handle_start_desktop_stream():
    """Start desktop streaming"""
    global desktop_streaming, desktop_stream_thread
    if not desktop_streaming:
        desktop_streaming = True
        desktop_stream_thread = threading.Thread(target=desktop_streaming_worker)
        desktop_stream_thread.daemon = True
        desktop_stream_thread.start()
        emit('desktop_stream_status', {'status': 'started'})
        print("[Desktop Stream] Started desktop streaming")

@socketio.on('stop_desktop_stream')
def handle_stop_desktop_stream():
    """Stop desktop streaming"""
    global desktop_streaming
    desktop_streaming = False
    emit('desktop_stream_status', {'status': 'stopped'})
    print("[Desktop Stream] Stopped desktop streaming")

@socketio.on('connect')
def handle_connect():
    print(f"[SocketIO] Client connected: {request.sid}")

@socketio.on('disconnect')
def handle_disconnect():
    print(f"[SocketIO] Client disconnected: {request.sid}")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/process_command', methods=['POST'])
def process_command():
    try:
        data = request.json
        user_input = data.get('command', '')
        command_id = str(uuid.uuid4())
        
        # store initial command
        command_history[command_id] = {
            'id': command_id,
            'command': user_input,
            'status': 'processing',
            'steps': None,
            'timestamp': time.time()
        }
        
        # process command in background
        def process_in_background():
            try:
                steps = get_command_steps(user_input)
                command_history[command_id]['steps'] = steps
                command_history[command_id]['status'] = 'ready'
                command_history[command_id]['undone'] = False
                
                # emit update to client
                socketio.emit('command_update', command_history[command_id])
            except Exception as e:
                command_history[command_id]['status'] = 'error'
                command_history[command_id]['error'] = str(e)
                socketio.emit('command_update', command_history[command_id])
        
        thread = threading.Thread(target=process_in_background)
        thread.start()
        
        return jsonify({'command_id': command_id, 'status': 'processing'})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/undo_command', methods=['POST'])
def undo_command():
    try:
        old_command_id = request.json.get('command_id')
        
        if old_command_id in command_history:
            old_command_data = command_history[old_command_id]
            command_id = str(uuid.uuid4())

            # store initial command
            command_history[command_id] = {
                'id': command_id,
                'command': old_command_data['command'] + " (undo)",
                'status': 'processing',
                'steps': None,
                'timestamp': time.time()
            }

            def process_in_background():
                # process command in background
                try:
                    opposite_steps = get_opposite_command_steps(old_command_data['steps'])
                    command_history[command_id]['steps'] = opposite_steps
                    command_history[command_id]['status'] = 'ready'
                    command_history[command_id]['undone'] = False
                        
                    # emit update to client
                    socketio.emit('command_update', command_history[command_id])
                except Exception as e:
                    command_history[command_id]['status'] = 'error'
                    command_history[command_id]['error'] = str(e)
                    socketio.emit('command_update', command_history[command_id])
                
            thread = threading.Thread(target=process_in_background)
            thread.start()
            
            return jsonify({'command_id': command_id, 'status': 'processing'})    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/execute_command', methods=['POST'])
def execute_command():
    try:
        data = request.json
        command_id = data.get('command_id')
        
        if command_id not in command_history:
            return jsonify({'error': 'Command not found'}), 404
        
        command_data = command_history[command_id]
        if command_data['status'] != 'ready':
            return jsonify({'error': 'Command not ready for execution'}), 400
        
        # execute in background
        def execute_in_background():
            try:
                command_history[command_id]['status'] = 'executing'
                socketio.emit('command_update', command_history[command_id])
                
                execute_steps(command_data['steps'])
                
                command_history[command_id]['status'] = 'completed'
                socketio.emit('command_update', command_history[command_id])
            except Exception as e:
                command_history[command_id]['status'] = 'error'
                command_history[command_id]['error'] = str(e)
                socketio.emit('command_update', command_history[command_id])
        
        thread = threading.Thread(target=execute_in_background)
        thread.start()
        
        return jsonify({'status': 'executing'})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/history')
def get_history():
    # return last 20 commands
    history = list(command_history.values())
    history.sort(key=lambda x: x['timestamp'], reverse=True)
    return jsonify(history[:20])

@app.route('/api/voice_command', methods=['POST'])
def get_voice():
    try:
        voice_command = get_voice_command()
        return jsonify({'command': voice_command})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/system_info')
def get_system_capabilities():
    try:
        from system_info import get_system_info
        system_info = get_system_info()
        return jsonify(system_info)
    except ImportError:
        return jsonify({'error': 'System info not available'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=5000) 