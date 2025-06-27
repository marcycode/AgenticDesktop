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
            if self.desktop_env == 'gnome':
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
            if self.desktop_env == 'gnome':
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
            if self.desktop_env == 'gnome':
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
            if self.desktop_env == 'gnome':
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
        if self.agent_workspace is not None:
            return self.switch_to_workspace(self.agent_workspace)
        else:
            # Create agent workspace if it doesn't exist
            return self.create_agent_workspace() is not None
    
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
            
            # Switch to agent workspace
            if self.switch_to_workspace(self.agent_workspace):
                time.sleep(0.3)  # Give time for workspace switch
                
                # Execute the action
                result = action_func()
                
                return result
            else:
                raise Exception("Failed to switch to agent workspace")
                
        finally:
            # Always switch back to user's workspace
            self.switch_to_workspace(original_workspace)

# Global workspace manager instance
workspace_manager = WorkspaceManager() 