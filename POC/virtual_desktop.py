"""
Virtual Desktop Capture Module
Supports capturing from different virtual desktops across Linux, Windows, and macOS
"""

import platform
import subprocess
import time
import os
import json
from typing import List, Dict, Optional, Tuple
import mss
from PIL import Image
import io
import base64

class VirtualDesktopManager:
    def __init__(self):
        self.os_type = platform.system().lower()
        self.desktop_environment = self._detect_desktop_environment()
        
    def _detect_desktop_environment(self) -> str:
        """Detect the desktop environment on Linux"""
        if self.os_type != 'linux':
            return self.os_type
            
        # Check common environment variables
        de_vars = ['XDG_CURRENT_DESKTOP', 'DESKTOP_SESSION', 'GDMSESSION']
        for var in de_vars:
            de = os.environ.get(var, '').lower()
            if de:
                if 'gnome' in de:
                    return 'gnome'
                elif 'kde' in de or 'plasma' in de:
                    return 'kde'
                elif 'xfce' in de:
                    return 'xfce'
                elif 'mate' in de:
                    return 'mate'
                elif 'cinnamon' in de:
                    return 'cinnamon'
        
        return 'unknown'
    
    def get_virtual_desktops(self) -> List[Dict]:
        """Get list of available virtual desktops with their info"""
        if self.os_type == 'windows':
            return self._get_windows_virtual_desktops()
        elif self.os_type == 'darwin':
            return self._get_macos_spaces()
        elif self.os_type == 'linux':
            return self._get_linux_workspaces()
        else:
            return [{'id': 0, 'name': 'Desktop 1', 'active': True}]
    
    def _get_windows_virtual_desktops(self) -> List[Dict]:
        """Get Windows 10/11 Virtual Desktops"""
        try:
            # PowerShell script to get virtual desktops
            ps_script = '''
            Add-Type -TypeDefinition @"
                using System;
                using System.Runtime.InteropServices;
                public class VirtualDesktop {
                    [DllImport("user32.dll")]
                    public static extern IntPtr GetDesktopWindow();
                    
                    [DllImport("user32.dll")]
                    public static extern bool EnumDesktops(IntPtr hwinsta, EnumDesktopProc lpEnumFunc, IntPtr lParam);
                    
                    public delegate bool EnumDesktopProc(string lpszDesktop, IntPtr lParam);
                }
"@
            
            # Get virtual desktop info using Windows API
            $desktops = @()
            $counter = 0
            
            # For Windows 10/11, we'll use a simpler approach
            # Get the current desktop and assume others exist
            $currentDesktop = Get-Process -Name "dwm" -ErrorAction SilentlyContinue
            if ($currentDesktop) {
                $desktops += @{id=0; name="Desktop 1"; active=$true}
                $desktops += @{id=1; name="Desktop 2"; active=$false}
                $desktops += @{id=2; name="Desktop 3"; active=$false}
            }
            
            $desktops | ConvertTo-Json
            '''
            
            result = subprocess.run(['powershell', '-Command', ps_script], 
                                  capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0 and result.stdout.strip():
                desktops = json.loads(result.stdout.strip())
                return desktops if isinstance(desktops, list) else [desktops]
            
        except Exception as e:
            print(f"[Virtual Desktop] Windows detection error: {e}")
        
        # Fallback: assume at least current desktop exists
        return [{'id': 0, 'name': 'Desktop 1', 'active': True}]
    
    def _get_macos_spaces(self) -> List[Dict]:
        """Get macOS Spaces (Mission Control)"""
        try:
            # AppleScript to get Spaces info
            applescript = '''
            tell application "System Events"
                tell process "Dock"
                    set spaceCount to count of spaces of desktop 1
                    set currentSpace to index of current space of desktop 1
                    
                    set spaceList to {}
                    repeat with i from 1 to spaceCount
                        if i = currentSpace then
                            set end of spaceList to {id:i, name:("Space " & i), active:true}
                        else
                            set end of spaceList to {id:i, name:("Space " & i), active:false}
                        end if
                    end repeat
                    
                    return my listToJSON(spaceList)
                end tell
            end tell
            
            on listToJSON(lst)
                set json to "["
                repeat with i from 1 to count of lst
                    set item to item i of lst
                    set json to json & "{\"id\":" & (id of item) & ",\"name\":\"" & (name of item) & "\",\"active\":" & (active of item) & "}"
                    if i < count of lst then set json to json & ","
                end repeat
                set json to json & "]"
                return json
            end listToJSON
            '''
            
            result = subprocess.run(['osascript', '-e', applescript], 
                                  capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0 and result.stdout.strip():
                spaces = json.loads(result.stdout.strip())
                return spaces
                
        except Exception as e:
            print(f"[Virtual Desktop] macOS detection error: {e}")
        
        # Fallback: assume at least current space exists
        return [{'id': 1, 'name': 'Space 1', 'active': True}]
    
    def _get_linux_workspaces(self) -> List[Dict]:
        """Get Linux workspaces based on desktop environment"""
        try:
            if self.desktop_environment == 'gnome':
                return self._get_gnome_workspaces()
            elif self.desktop_environment == 'kde':
                return self._get_kde_workspaces()
            elif self.desktop_environment in ['xfce', 'mate', 'cinnamon']:
                return self._get_generic_x11_workspaces()
            else:
                return self._get_generic_x11_workspaces()
                
        except Exception as e:
            print(f"[Virtual Desktop] Linux detection error: {e}")
            return [{'id': 0, 'name': 'Workspace 1', 'active': True}]
    
    def _get_gnome_workspaces(self) -> List[Dict]:
        """Get GNOME workspaces"""
        try:
            # Get total workspaces
            result = subprocess.run(['gsettings', 'get', 'org.gnome.desktop.wm.preferences', 'num-workspaces'], 
                                  capture_output=True, text=True)
            total_workspaces = int(result.stdout.strip()) if result.returncode == 0 else 4
            
            # Get current workspace (0-indexed)
            result = subprocess.run(['wmctrl', '-d'], capture_output=True, text=True)
            current_workspace = 0
            
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if '*' in line:  # Current workspace marked with *
                        current_workspace = int(line.split()[0])
                        break
            
            workspaces = []
            for i in range(total_workspaces):
                workspaces.append({
                    'id': i,
                    'name': f'Workspace {i + 1}',
                    'active': i == current_workspace
                })
            
            return workspaces
            
        except Exception as e:
            print(f"[Virtual Desktop] GNOME error: {e}")
            return [{'id': 0, 'name': 'Workspace 1', 'active': True}]
    
    def _get_kde_workspaces(self) -> List[Dict]:
        """Get KDE virtual desktops"""
        try:
            # Use qdbus to get KDE workspace info
            result = subprocess.run(['qdbus', 'org.kde.KWin', '/KWin', 'org.kde.KWin.numberOfDesktops'], 
                                  capture_output=True, text=True)
            total_desktops = int(result.stdout.strip()) if result.returncode == 0 else 4
            
            result = subprocess.run(['qdbus', 'org.kde.KWin', '/KWin', 'org.kde.KWin.currentDesktop'], 
                                  capture_output=True, text=True)
            current_desktop = int(result.stdout.strip()) - 1 if result.returncode == 0 else 0  # Convert to 0-indexed
            
            desktops = []
            for i in range(total_desktops):
                desktops.append({
                    'id': i,
                    'name': f'Desktop {i + 1}',
                    'active': i == current_desktop
                })
            
            return desktops
            
        except Exception as e:
            print(f"[Virtual Desktop] KDE error: {e}")
            return [{'id': 0, 'name': 'Desktop 1', 'active': True}]
    
    def _get_generic_x11_workspaces(self) -> List[Dict]:
        """Get workspaces using generic X11 methods"""
        try:
            result = subprocess.run(['wmctrl', '-d'], capture_output=True, text=True)
            workspaces = []
            
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if line.strip():
                        parts = line.split()
                        if len(parts) >= 2:
                            workspace_id = int(parts[0])
                            is_active = '*' in parts[1]
                            name = f'Workspace {workspace_id + 1}'
                            
                            workspaces.append({
                                'id': workspace_id,
                                'name': name,
                                'active': is_active
                            })
            
            return workspaces if workspaces else [{'id': 0, 'name': 'Workspace 1', 'active': True}]
            
        except Exception as e:
            print(f"[Virtual Desktop] X11 error: {e}")
            return [{'id': 0, 'name': 'Workspace 1', 'active': True}]
    
    def switch_to_desktop(self, desktop_id: int) -> bool:
        """Switch to a specific virtual desktop"""
        try:
            if self.os_type == 'windows':
                return self._switch_windows_desktop(desktop_id)
            elif self.os_type == 'darwin':
                return self._switch_macos_space(desktop_id)
            elif self.os_type == 'linux':
                return self._switch_linux_workspace(desktop_id)
            return False
        except Exception as e:
            print(f"[Virtual Desktop] Switch error: {e}")
            return False
    
    def _switch_windows_desktop(self, desktop_id: int) -> bool:
        """Switch Windows virtual desktop"""
        try:
            # Windows 10/11 keyboard shortcut: Ctrl+Win+Left/Right Arrow
            import pyautogui
            current_desktops = self.get_virtual_desktops()
            current_id = next((d['id'] for d in current_desktops if d['active']), 0)
            
            if desktop_id == current_id:
                return True
            
            # Use Win+Tab to open Task View, then arrow keys to navigate
            pyautogui.hotkey('win', 'tab')
            time.sleep(0.5)
            
            # Navigate to desired desktop
            if desktop_id > current_id:
                for _ in range(desktop_id - current_id):
                    pyautogui.press('right')
                    time.sleep(0.1)
            else:
                for _ in range(current_id - desktop_id):
                    pyautogui.press('left')
                    time.sleep(0.1)
            
            pyautogui.press('enter')
            time.sleep(0.5)
            return True
            
        except Exception as e:
            print(f"[Virtual Desktop] Windows switch error: {e}")
            return False
    
    def _switch_macos_space(self, space_id: int) -> bool:
        """Switch macOS Space"""
        try:
            applescript = f'''
            tell application "System Events"
                tell process "Dock"
                    set current space of desktop 1 to space {space_id} of desktop 1
                end tell
            end tell
            '''
            
            result = subprocess.run(['osascript', '-e', applescript], 
                                  capture_output=True, text=True, timeout=10)
            return result.returncode == 0
            
        except Exception as e:
            print(f"[Virtual Desktop] macOS switch error: {e}")
            return False
    
    def _switch_linux_workspace(self, workspace_id: int) -> bool:
        """Switch Linux workspace"""
        try:
            if self.desktop_environment == 'gnome':
                # Use gsettings or wmctrl
                result = subprocess.run(['wmctrl', '-s', str(workspace_id)], 
                                      capture_output=True, text=True)
                return result.returncode == 0
            elif self.desktop_environment == 'kde':
                # Use qdbus
                result = subprocess.run(['qdbus', 'org.kde.KWin', '/KWin', 'org.kde.KWin.setCurrentDesktop', str(workspace_id + 1)], 
                                      capture_output=True, text=True)
                return result.returncode == 0
            else:
                # Generic X11 approach
                result = subprocess.run(['wmctrl', '-s', str(workspace_id)], 
                                      capture_output=True, text=True)
                return result.returncode == 0
                
        except Exception as e:
            print(f"[Virtual Desktop] Linux switch error: {e}")
            return False
    
    def capture_desktop(self, desktop_id: Optional[int] = None) -> Optional[str]:
        """Capture screenshot from specified virtual desktop"""
        if desktop_id is None:
            # Capture current desktop
            return self._capture_current_desktop()
        
        # Need to switch to target desktop, capture, then switch back
        current_desktops = self.get_virtual_desktops()
        current_id = next((d['id'] for d in current_desktops if d['active']), 0)
        
        if desktop_id == current_id:
            return self._capture_current_desktop()
        
        # Switch to target desktop
        if self.switch_to_desktop(desktop_id):
            time.sleep(0.5)  # Wait for desktop switch
            screenshot = self._capture_current_desktop()
            
            # Switch back to original desktop
            self.switch_to_desktop(current_id)
            time.sleep(0.3)
            
            return screenshot
        
        return None
    
    def _capture_current_desktop(self) -> Optional[str]:
        """Capture current desktop using mss"""
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


# Global instance
virtual_desktop_manager = VirtualDesktopManager() 