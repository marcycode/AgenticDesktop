import subprocess
import tempfile
import base64
import io
from PIL import Image
import os
import platform
from system_info import is_wayland
import mss

def capture_desktop_wayland():
    """Capture desktop screenshot on Wayland using various methods"""
    # Try different Wayland screenshot methods in order of preference
    methods = [
        _try_grim_wayland,
        _try_gnome_screenshot_wayland,
        _try_wl_screenshot,
        _try_wayshot,
        _try_flameshot_wayland
    ]
    
    for method in methods:
        try:
            return method()
        except Exception as e:
            continue
    
    # If all methods fail, try portal-based capture
    try:
        return _try_portal_capture()
    except Exception as e:
        raise Exception(f"Failed to capture desktop on Wayland. Tried all available methods. "
                       f"Last error: {str(e)}. "
                       f"Consider installing: grim, gnome-screenshot, wayshot, or flameshot.")

def _try_grim_wayland():
    """Try capturing with grim (works with wlroots compositors)"""
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
        try:
            result = subprocess.run(['grim', tmp.name], check=True, capture_output=True)
            return _process_screenshot_file(tmp.name)
        finally:
            if os.path.exists(tmp.name):
                os.unlink(tmp.name)

def _try_gnome_screenshot_wayland():
    """Try capturing with gnome-screenshot (GNOME Wayland)"""
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
        try:
            result = subprocess.run(['gnome-screenshot', '-f', tmp.name], check=True, capture_output=True)
            return _process_screenshot_file(tmp.name)
        finally:
            if os.path.exists(tmp.name):
                os.unlink(tmp.name)

def _try_wl_screenshot():
    """Try capturing with wl-clipboard screenshot"""
    try:
        # Use wl-clipboard to capture screenshot
        result = subprocess.run(['wl-paste', '--type', 'image/png'], 
                              check=True, capture_output=True)
        if result.returncode == 0 and result.stdout:
            img = Image.open(io.BytesIO(result.stdout))
            return _process_pil_image(img)
    except:
        pass
    
    # Alternative method: screenshot to clipboard then paste
    try:
        subprocess.run(['gnome-screenshot', '-c'], check=True, timeout=5)
        result = subprocess.run(['wl-paste', '--type', 'image/png'], 
                              check=True, capture_output=True, timeout=5)
        if result.stdout:
            img = Image.open(io.BytesIO(result.stdout))
            return _process_pil_image(img)
    except:
        pass
    
    raise Exception("wl-clipboard method failed")

def _try_wayshot():
    """Try capturing with wayshot"""
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
        try:
            result = subprocess.run(['wayshot', '-f', tmp.name], check=True, capture_output=True)
            return _process_screenshot_file(tmp.name)
        finally:
            if os.path.exists(tmp.name):
                os.unlink(tmp.name)

def _try_flameshot_wayland():
    """Try capturing with flameshot on Wayland"""
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
        try:
            result = subprocess.run(['flameshot', 'full', '-p', tmp.name], 
                                  check=True, capture_output=True, timeout=10)
            return _process_screenshot_file(tmp.name)
        finally:
            if os.path.exists(tmp.name):
                os.unlink(tmp.name)

def _try_portal_capture():
    """Try using XDG Desktop Portal for screen capture"""
    try:
        # This is a more complex method that would require D-Bus interaction
        # For now, we'll use a simple shell command approach
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
            # Try using xdg-desktop-portal-gtk screenshot
            result = subprocess.run([
                'gdbus', 'call', '--session',
                '--dest', 'org.freedesktop.portal.Desktop',
                '--object-path', '/org/freedesktop/portal/desktop',
                '--method', 'org.freedesktop.portal.Screenshot.Screenshot',
                '', '{}'
            ], check=True, capture_output=True, timeout=15)
            
            # This is a simplified approach - in reality, portal capture is more complex
            raise Exception("Portal method not fully implemented")
    except:
        raise Exception("Portal capture failed")

def _process_screenshot_file(filepath):
    """Process a screenshot file and return base64 encoded image"""
    if not os.path.exists(filepath) or os.path.getsize(filepath) == 0:
        raise Exception("Screenshot file is empty or doesn't exist")
    
    img = Image.open(filepath)
    return _process_pil_image(img)

def _process_pil_image(img):
    """Process a PIL image and return base64 encoded string"""
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

def capture_desktop_x11():
    """Capture desktop screenshot on X11 using mss"""
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

def capture_desktop_macos():
    """Capture desktop screenshot on macOS using screencapture"""
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
        try:
            # Use macOS screencapture command
            result = subprocess.run(['screencapture', '-x', tmp.name], 
                                  check=True, capture_output=True, timeout=10)
            return _process_screenshot_file(tmp.name)
        finally:
            if os.path.exists(tmp.name):
                os.unlink(tmp.name)

def capture_desktop():
    """Capture desktop screenshot, automatically choosing the right method"""
    try:
        # Check if we're on macOS
        if platform.system().lower() == 'darwin':
            return capture_desktop_macos()
        elif is_wayland():
            return capture_desktop_wayland()
        else:
            return capture_desktop_x11()
    except Exception as e:
        raise Exception(f"Failed to capture desktop: {str(e)}") 