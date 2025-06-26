from flask import Flask, render_template, request, jsonify, session
from flask_socketio import SocketIO, emit
import uuid
from prompt_agent import get_command_steps
from desktop_actions import execute_steps
from speech_input import get_voice_command
import json
import threading
import time
import base64
import io
import mss
from PIL import Image
from virtual_desktop import virtual_desktop_manager

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here' # left blank is for now
socketio = SocketIO(app, cors_allowed_origins="*")

# Store command history and status
command_history = {}

# Desktop streaming variables
desktop_streaming = False
desktop_stream_thread = None
current_desktop_id = None  # Track which desktop we're streaming

def desktop_streaming_worker():
    """Background worker for virtual desktop streaming"""
    global desktop_streaming, current_desktop_id
    while desktop_streaming:
        try:
            screenshot = virtual_desktop_manager.capture_desktop(current_desktop_id)
            if screenshot:
                socketio.emit('desktop_frame', {
                    'image': screenshot,
                    'desktop_id': current_desktop_id
                })
            time.sleep(0.1)  # 10 FPS
        except Exception as e:
            print(f"Desktop streaming error: {e}")
            time.sleep(1)

@app.route('/api/virtual_desktops')
def get_virtual_desktops():
    """Get list of available virtual desktops"""
    try:
        desktops = virtual_desktop_manager.get_virtual_desktops()
        return jsonify({
            'desktops': desktops,
            'os_type': virtual_desktop_manager.os_type,
            'desktop_environment': virtual_desktop_manager.desktop_environment
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/switch_desktop', methods=['POST'])
def switch_desktop():
    """Switch to a specific virtual desktop"""
    try:
        data = request.json
        desktop_id = data.get('desktop_id')
        
        if desktop_id is None:
            return jsonify({'error': 'desktop_id required'}), 400
        
        success = virtual_desktop_manager.switch_to_desktop(desktop_id)
        return jsonify({'success': success})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@socketio.on('start_desktop_stream')
def handle_start_desktop_stream(data=None):
    """Start desktop streaming for specific virtual desktop"""
    global desktop_streaming, desktop_stream_thread, current_desktop_id
    
    # Get desktop_id from data, default to current desktop
    desktop_id = None
    if data and isinstance(data, dict):
        desktop_id = data.get('desktop_id')
    
    current_desktop_id = desktop_id
    
    if not desktop_streaming:
        desktop_streaming = True
        desktop_stream_thread = threading.Thread(target=desktop_streaming_worker)
        desktop_stream_thread.daemon = True
        desktop_stream_thread.start()
        
        emit('desktop_stream_status', {
            'status': 'started',
            'desktop_id': current_desktop_id
        })
        print(f"[Desktop Stream] Started streaming desktop {current_desktop_id}")

@socketio.on('stop_desktop_stream')
def handle_stop_desktop_stream():
    """Stop desktop streaming"""
    global desktop_streaming, current_desktop_id
    desktop_streaming = False
    current_desktop_id = None
    emit('desktop_stream_status', {'status': 'stopped'})
    print("[Desktop Stream] Stopped desktop streaming")

@socketio.on('change_stream_desktop')
def handle_change_stream_desktop(data):
    """Change which desktop is being streamed without stopping stream"""
    global current_desktop_id
    
    desktop_id = data.get('desktop_id')
    if desktop_id is not None:
        current_desktop_id = desktop_id
        emit('desktop_stream_status', {
            'status': 'desktop_changed',
            'desktop_id': current_desktop_id
        })
        print(f"[Desktop Stream] Changed to streaming desktop {current_desktop_id}")

@socketio.on('connect')
def handle_connect():
    print(f"[SocketIO] Client connected: {request.sid}")
    # Send virtual desktop info on connect
    try:
        desktops = virtual_desktop_manager.get_virtual_desktops()
        emit('virtual_desktops', {
            'desktops': desktops,
            'os_type': virtual_desktop_manager.os_type,
            'desktop_environment': virtual_desktop_manager.desktop_environment
        })
    except Exception as e:
        print(f"[SocketIO] Error sending desktop info: {e}")

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