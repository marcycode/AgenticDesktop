import subprocess
import os
import time
from system_info import is_wayland, detect_desktop_environment
from desktop_capture import capture_desktop

class WorkspaceManager:
    """Manages workspace switching and desktop capture for different workspaces"""
    
    def __init__(self):
        self.is_wayland = is_wayland()
        self.desktop_env = detect_desktop_environment()
        self.current_workspace = self.get_current_workspace()
        self.agent_workspace = None
        
    def get_current_workspace(self):
        """Get the current workspace number/name"""
        try:
            if self.desktop_env == 'macos':
                # macOS space detection using AppleScript
                result = subprocess.run([
                    'osascript', '-e', 
                    'tell application "System Events" to get the index of current space of current desktop'
                ], capture_output=True, text=True, timeout=5)
                
                if result.returncode == 0:
                    try:
                        return int(result.stdout.strip()) - 1  # Convert to 0-based indexing
                    except ValueError:
                        pass
                        
            elif self.desktop_env == 'gnome':
                # GNOME workspace detection
                result = subprocess.run([
                    'gdbus', 'call', '--session',
                    '--dest', 'org.gnome.Shell',
                    '--object-path', '/org/gnome/Shell',
                    '--method', 'org.gnome.Shell.Eval',
                    'global.workspace_manager.get_active_workspace_index()'
                ], capture_output=True, text=True, timeout=5)
                
                if result.returncode == 0:
                    # Parse the result to extract workspace number
                    output = result.stdout.strip()
                    if 'true' in output:
                        # Extract number from output like "(true, 0)"
                        import re
                        match = re.search(r'\(true,\s*(\d+)\)', output)
                        if match:
                            return int(match.group(1))
                
            elif self.desktop_env in ['kde', 'plasma']:
                # KDE workspace detection
                result = subprocess.run([
                    'qdbus', 'org.kde.KWin', '/KWin',
                    'org.kde.KWin.currentDesktop'
                ], capture_output=True, text=True, timeout=5)
                
                if result.returncode == 0:
                    return int(result.stdout.strip()) - 1  # KDE uses 1-based indexing
                    
            elif self.desktop_env in ['i3', 'sway']:
                # i3/Sway workspace detection
                result = subprocess.run(['i3-msg', '-t', 'get_workspaces'], 
                                      capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    import json
                    workspaces = json.loads(result.stdout)
                    for ws in workspaces:
                        if ws.get('focused'):
                            return ws.get('num', 0)
                            
        except Exception as e:
            print(f"Error getting current workspace: {e}")
            
        return 0  # Default to workspace 0
    
    def switch_to_workspace(self, workspace_num):
        """Switch to a specific workspace"""
        try:
            if self.desktop_env == 'macos':
                # macOS space switching using AppleScript
                # Convert to 1-based indexing for AppleScript
                space_index = workspace_num + 1
                
                # Try multiple approaches for macOS space switching
                methods = [
                    # Method 1: Direct dock click
                    lambda: subprocess.run([
                        'osascript', '-e', 
                        f'tell application "System Events" to tell process "Dock" to click (every button whose value of attribute "AXDescription" is "Desktop {space_index}")'
                    ], check=True, timeout=5),
                    
                    # Method 2: Mission Control + number key
                    lambda: subprocess.run([
                        'osascript', '-e',
                        f'tell application "System Events" to key code 18 using {{control down}}'
                    ], check=True, timeout=5) and subprocess.run([
                        'osascript', '-e',
                        f'tell application "System Events" to key code {48 + workspace_num}'
                    ], check=True, timeout=5),
                    
                    # Method 3: Simple key combination
                    lambda: subprocess.run([
                        'osascript', '-e',
                        f'tell application "System Events" to key code {48 + workspace_num} using {{control down}}'
                    ], check=True, timeout=5)
                ]
                
                for i, method in enumerate(methods):
                    try:
                        method()
                        print(f"macOS workspace switch successful using method {i+1}")
                        break
                    except Exception as e:
                        print(f"macOS workspace switch method {i+1} failed: {e}")
                        if i == len(methods) - 1:  # Last method
                            raise e
                        continue
                
            elif self.desktop_env == 'gnome':
                # GNOME workspace switching
                subprocess.run([
                    'gdbus', 'call', '--session',
                    '--dest', 'org.gnome.Shell',
                    '--object-path', '/org/gnome/Shell',
                    '--method', 'org.gnome.Shell.Eval',
                    f'global.workspace_manager.get_workspace_by_index({workspace_num}).activate(global.get_current_time())'
                ], check=True, timeout=5)
                
            elif self.desktop_env in ['kde', 'plasma']:
                # KDE workspace switching
                subprocess.run([
                    'qdbus', 'org.kde.KWin', '/KWin',
                    'org.kde.KWin.setCurrentDesktop', str(workspace_num + 1)
                ], check=True, timeout=5)
                
            elif self.desktop_env in ['i3', 'sway']:
                # i3/Sway workspace switching
                subprocess.run(['i3-msg', 'workspace', str(workspace_num)], 
                             check=True, timeout=5)
                             
            else:
                # Generic approach using wmctrl (if available)
                subprocess.run(['wmctrl', '-s', str(workspace_num)], 
                             check=True, timeout=5)
            
            time.sleep(0.5)  # Give time for workspace switch
            return True
            
        except Exception as e:
            print(f"Error switching to workspace {workspace_num}: {e}")
            return False
    
    def create_agent_workspace(self):
        """Create or switch to a dedicated workspace for the agent"""
        try:
            # Try to find an empty workspace or create a new one
            available_workspace = self.find_empty_workspace()
            if available_workspace is None:
                available_workspace = self.get_next_workspace_number()
            
            if self.switch_to_workspace(available_workspace):
                self.agent_workspace = available_workspace
                print(f"Agent workspace set to: {available_workspace}")
                return available_workspace
            
        except Exception as e:
            print(f"Error creating agent workspace: {e}")
            
        return None
    
    def find_empty_workspace(self):
        """Find an empty workspace that can be used for the agent"""
        try:
            if self.desktop_env == 'macos':
                # macOS: Get total number of spaces
                result = subprocess.run([
                    'osascript', '-e',
                    'tell application "System Events" to get the count of spaces of current desktop'
                ], capture_output=True, text=True, timeout=5)
                
                if result.returncode == 0:
                    try:
                        n_spaces = int(result.stdout.strip())
                        # Return the last space as it's likely empty
                        return n_spaces - 1
                    except ValueError:
                        pass
                        
            elif self.desktop_env == 'gnome':
                result = subprocess.run([
                    'gdbus', 'call', '--session',
                    '--dest', 'org.gnome.Shell',
                    '--object-path', '/org/gnome/Shell',
                    '--method', 'org.gnome.Shell.Eval',
                    'global.workspace_manager.get_n_workspaces()'
                ], capture_output=True, text=True, timeout=5)
                
                if result.returncode == 0:
                    # Look for an empty workspace
                    import re
                    match = re.search(r'\(true,\s*(\d+)\)', result.stdout)
                    if match:
                        n_workspaces = int(match.group(1))
                        # Return the last workspace as it's likely empty
                        return n_workspaces - 1
                        
            elif self.desktop_env in ['i3', 'sway']:
                result = subprocess.run(['i3-msg', '-t', 'get_workspaces'], 
                                      capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    import json
                    workspaces = json.loads(result.stdout)
                    # Find first workspace with no windows
                    for ws in workspaces:
                        if not ws.get('urgent', False) and len(ws.get('nodes', [])) == 0:
                            return ws.get('num', 0)
                            
        except Exception:
            pass
            
        return None
    
    def get_next_workspace_number(self):
        """Get the next available workspace number"""
        try:
            if self.desktop_env == 'macos':
                # macOS: Get total number of spaces
                result = subprocess.run([
                    'osascript', '-e',
                    'tell application "System Events" to get the count of spaces of current desktop'
                ], capture_output=True, text=True, timeout=5)
                
                if result.returncode == 0:
                    try:
                        n_spaces = int(result.stdout.strip())
                        return n_spaces  # Return the next space number (0-based)
                    except ValueError:
                        pass
                        
            elif self.desktop_env == 'gnome':
                # GNOME: get total number of workspaces and add 1
                result = subprocess.run([
                    'gdbus', 'call', '--session',
                    '--dest', 'org.gnome.Shell',
                    '--object-path', '/org/gnome/Shell',
                    '--method', 'org.gnome.Shell.Eval',
                    'global.workspace_manager.get_n_workspaces()'
                ], capture_output=True, text=True, timeout=5)
                
                if result.returncode == 0:
                    import re
                    match = re.search(r'\(true,\s*(\d+)\)', result.stdout)
                    if match:
                        return int(match.group(1))
                        
            elif self.desktop_env in ['i3', 'sway']:
                result = subprocess.run(['i3-msg', '-t', 'get_workspaces'], 
                                      capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    import json
                    workspaces = json.loads(result.stdout)
                    if workspaces:
                        max_num = max(ws.get('num', 0) for ws in workspaces)
                        return max_num + 1
                        
        except Exception:
            pass
            
        return 9  # Default to workspace 9 as it's usually empty
    
    def switch_to_agent_workspace(self):
        """Switch to the agent's workspace"""
        try:
            if self.agent_workspace is not None:
                success = self.switch_to_workspace(self.agent_workspace)
                if not success:
                    print("Warning: Failed to switch to existing agent workspace")
                    return False
                return True
            else:
                # Create agent workspace if it doesn't exist
                workspace_num = self.create_agent_workspace()
                if workspace_num is not None:
                    return True
                else:
                    print("Warning: Failed to create agent workspace")
                    return False
        except Exception as e:
            print(f"Error in switch_to_agent_workspace: {e}")
            return False
    
    def switch_back_to_user_workspace(self):
        """Switch back to the user's original workspace"""
        return self.switch_to_workspace(self.current_workspace)
    
    def capture_agent_workspace(self):
        """Capture screenshot of the agent's workspace without switching user's view"""
        original_workspace = self.get_current_workspace()
        
        try:
            # Switch to agent workspace
            if self.switch_to_workspace(self.agent_workspace):
                time.sleep(0.2)  # Brief pause for workspace switch
                screenshot = capture_desktop()
                
                # Switch back to original workspace
                self.switch_to_workspace(original_workspace)
                
                return screenshot
        except Exception as e:
            # Make sure we switch back even if capture fails
            self.switch_to_workspace(original_workspace)
            raise e
        
        return None
    
    def run_agent_action_in_workspace(self, action_func):
        """Run an agent action in the dedicated agent workspace"""
        original_workspace = self.get_current_workspace()
        
        try:
            # Ensure agent workspace exists
            if self.agent_workspace is None:
                self.create_agent_workspace()
            
            # Try to switch to agent workspace
            if self.switch_to_workspace(self.agent_workspace):
                time.sleep(0.3)  # Give time for workspace switch
                
                # Execute the action
                result = action_func()
                
                return result
            else:
                # Fallback: if workspace switching fails, run in current workspace
                print("Warning: Failed to switch to agent workspace. Running action in current workspace.")
                result = action_func()
                return result
                
        except Exception as e:
            # If workspace switching completely fails, run in current workspace
            print(f"Workspace switching failed: {e}. Running action in current workspace.")
            try:
                result = action_func()
                return result
            except Exception as action_error:
                raise Exception(f"Action failed: {action_error}")
        finally:
            # Always try to switch back to user's workspace
            try:
                self.switch_to_workspace(original_workspace)
            except Exception as e:
                print(f"Warning: Failed to switch back to user workspace: {e}")

# Global workspace manager instance
workspace_manager = WorkspaceManager() 