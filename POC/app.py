from flask import Flask, render_template, request, jsonify, session
from flask_socketio import SocketIO, emit
import uuid
from prompt_agent import get_command_steps
from desktop_actions import execute_steps
from speech_input import get_voice_command
import json
import threading
import time

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here' # left blank is for now
socketio = SocketIO(app, cors_allowed_origins="*")

# Store command history and status
command_history = {}

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

if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=5000) 