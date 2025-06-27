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
from agent_loop import agent_autorun, get_agent_state, agent_state, stop_agent_loop

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here' # left blank is for now
socketio = SocketIO(app, cors_allowed_origins="*")

# Store command history and status (legacy, not used in new agentic mode)
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
    # This endpoint now starts the agentic autorun loop with the given goal
    try:
        data = request.json
        user_input = data.get('command', '')
        # Start the agent loop in a background thread
        def run_agent():
            agent_autorun(user_input)
        thread = threading.Thread(target=run_agent)
        thread.start()
        return jsonify({'status': 'agentic_loop_started'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/agent/state', methods=['GET'])
def get_agentic_state():
    # Return the current agent state for the web UI
    return jsonify(get_agent_state())

@app.route('/api/agent/stop', methods=['POST'])
def stop_agentic_loop():
    # Stop the currently running agent loop
    try:
        stop_agent_loop()
        return jsonify({'status': 'stopped'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# (Optional) Legacy endpoints can be removed or left for compatibility
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
    socketio.run(app, debug=True, host='0.0.0.0', port=5001) 