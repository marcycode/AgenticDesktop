from flask import Flask, render_template, request, jsonify, session
from flask_socketio import SocketIO, emit
import uuid
from prompt_agent import get_command_steps
from desktop_actions import execute_steps
from speech_input import get_voice_command
from desktop_capture import capture_desktop
from workspace_manager import workspace_manager
import json
import threading
import time

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here' # left blank is for now
socketio = SocketIO(app, cors_allowed_origins="*")

# Store command history and status
command_history = {}

# Desktop streaming variables
desktop_streaming = False
desktop_stream_thread = None
agent_workspace_streaming = False
agent_stream_thread = None

def capture_desktop_frame():
    """Capture desktop screenshot and return as base64 encoded image"""
    try:
        return capture_desktop()
    except Exception as e:
        print(f"Error capturing desktop: {e}")
        return None

def capture_agent_workspace_frame():
    """Capture agent workspace screenshot without switching user's view"""
    try:
        if workspace_manager.agent_workspace is not None:
            return workspace_manager.capture_agent_workspace()
        else:
            # If no agent workspace, capture current desktop
            return capture_desktop()
    except Exception as e:
        print(f"Error capturing agent workspace: {e}")
        return None

def desktop_streaming_worker():
    """Background worker for desktop streaming"""
    global desktop_streaming
    while desktop_streaming:
        try:
            screenshot = capture_desktop_frame()
            if screenshot:
                socketio.emit('desktop_frame', {'image': screenshot})
            time.sleep(0.1)  # 10 FPS
        except Exception as e:
            print(f"Desktop streaming error: {e}")
            time.sleep(1)

def agent_workspace_streaming_worker():
    """Background worker for agent workspace streaming"""
    global agent_workspace_streaming
    while agent_workspace_streaming:
        try:
            screenshot = capture_agent_workspace_frame()
            if screenshot:
                socketio.emit('agent_workspace_frame', {'image': screenshot})
            time.sleep(0.2)  # 5 FPS for agent workspace
        except Exception as e:
            print(f"Agent workspace streaming error: {e}")
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

@socketio.on('start_agent_workspace_stream')
def handle_start_agent_workspace_stream():
    """Start agent workspace streaming"""
    global agent_workspace_streaming, agent_stream_thread
    if not agent_workspace_streaming:
        # Ensure agent workspace is created
        if workspace_manager.agent_workspace is None:
            workspace_manager.create_agent_workspace()
        
        agent_workspace_streaming = True
        agent_stream_thread = threading.Thread(target=agent_workspace_streaming_worker)
        agent_stream_thread.daemon = True
        agent_stream_thread.start()
        emit('agent_workspace_stream_status', {'status': 'started', 'workspace': workspace_manager.agent_workspace})
        print(f"[Agent Workspace Stream] Started streaming workspace {workspace_manager.agent_workspace}")

@socketio.on('stop_agent_workspace_stream')
def handle_stop_agent_workspace_stream():
    """Stop agent workspace streaming"""
    global agent_workspace_streaming
    agent_workspace_streaming = False
    emit('agent_workspace_stream_status', {'status': 'stopped'})
    print("[Agent Workspace Stream] Stopped agent workspace streaming")

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
        use_agent_workspace = data.get('use_agent_workspace', True)
        
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
                
                if use_agent_workspace:
                    # Execute in agent workspace
                    def action():
                        return execute_steps(command_data['steps'])
                    
                    workspace_manager.run_agent_action_in_workspace(action)
                else:
                    # Execute in current workspace
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

@app.route('/api/workspace/info')
def get_workspace_info():
    """Get workspace information"""
    try:
        return jsonify({
            'current_workspace': workspace_manager.current_workspace,
            'agent_workspace': workspace_manager.agent_workspace,
            'desktop_environment': workspace_manager.desktop_env,
            'is_wayland': workspace_manager.is_wayland
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/workspace/create_agent', methods=['POST'])
def create_agent_workspace():
    """Create a dedicated workspace for the agent"""
    try:
        workspace_num = workspace_manager.create_agent_workspace()
        if workspace_num is not None:
            return jsonify({
                'success': True,
                'agent_workspace': workspace_num,
                'message': f'Agent workspace created: {workspace_num}'
            })
        else:
            return jsonify({
                'success': False, 
                'error': 'Failed to create agent workspace'
            }), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/workspace/switch_to_agent', methods=['POST'])
def switch_to_agent_workspace():
    """Switch user's view to agent workspace"""
    try:
        success = workspace_manager.switch_to_agent_workspace()
        if success:
            return jsonify({
                'success': True,
                'agent_workspace': workspace_manager.agent_workspace
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to switch to agent workspace'
            }), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/workspace/switch_back', methods=['POST'])
def switch_back_to_user_workspace():
    """Switch back to user's original workspace"""
    try:
        success = workspace_manager.switch_back_to_user_workspace()
        if success:
            return jsonify({
                'success': True,
                'user_workspace': workspace_manager.current_workspace
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to switch back to user workspace'
            }), 500
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
    socketio.run(app, debug=True, host='0.0.0.0', port=5001) 