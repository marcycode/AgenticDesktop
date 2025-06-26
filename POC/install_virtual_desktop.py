#!/usr/bin/env python3
"""
Virtual Desktop Setup Script
Installs additional system dependencies for virtual desktop support
"""

import platform
import subprocess
import sys
import os

def get_os_type():
    return platform.system().lower()

def install_linux_dependencies():
    """Install Linux dependencies for virtual desktop support"""
    print("Installing Linux virtual desktop dependencies...")
    
    # Detect Linux distribution
    try:
        with open('/etc/os-release') as f:
            content = f.read()
            if 'ubuntu' in content.lower() or 'debian' in content.lower():
                # Ubuntu/Debian
                deps = ['wmctrl', 'xdotool', 'python3-tk']
                subprocess.run(['sudo', 'apt-get', 'update'], check=True)
                subprocess.run(['sudo', 'apt-get', 'install', '-y'] + deps, check=True)
                print("✅ Installed Ubuntu/Debian dependencies")
                
            elif 'fedora' in content.lower() or 'centos' in content.lower() or 'rhel' in content.lower():
                # Fedora/CentOS/RHEL
                deps = ['wmctrl', 'xdotool', 'tkinter']
                subprocess.run(['sudo', 'dnf', 'install', '-y'] + deps, check=True)
                print("✅ Installed Fedora/RHEL dependencies")
                
            elif 'arch' in content.lower():
                # Arch Linux
                deps = ['wmctrl', 'xdotool', 'tk']
                subprocess.run(['sudo', 'pacman', '-S', '--noconfirm'] + deps, check=True)
                print("✅ Installed Arch Linux dependencies")
                
            else:
                print("⚠️ Unknown Linux distribution. Please install wmctrl and xdotool manually.")
                
    except Exception as e:
        print(f"❌ Error installing Linux dependencies: {e}")
        print("Please install wmctrl and xdotool manually:")
        print("  Ubuntu/Debian: sudo apt-get install wmctrl xdotool")
        print("  Fedora/RHEL: sudo dnf install wmctrl xdotool")
        print("  Arch: sudo pacman -S wmctrl xdotool")

def install_windows_dependencies():
    """Install Windows dependencies for virtual desktop support"""
    print("Installing Windows virtual desktop dependencies...")
    
    try:
        # Check if PowerShell is available
        result = subprocess.run(['powershell', '-Command', 'Get-Host'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ PowerShell is available")
        
        # Install pywin32 if not already installed
        subprocess.run([sys.executable, '-m', 'pip', 'install', 'pywin32'], check=True)
        print("✅ Installed pywin32")
        
    except Exception as e:
        print(f"❌ Error installing Windows dependencies: {e}")
        print("Please install pywin32 manually: pip install pywin32")

def install_macos_dependencies():
    """Install macOS dependencies for virtual desktop support"""
    print("Installing macOS virtual desktop dependencies...")
    
    try:
        # Check if AppleScript is available (should be by default)
        result = subprocess.run(['osascript', '-e', 'return "AppleScript OK"'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ AppleScript is available")
        
        # Install pyobjc if not already installed (for better macOS integration)
        subprocess.run([sys.executable, '-m', 'pip', 'install', 'pyobjc-core', 'pyobjc-framework-Cocoa'], check=True)
        print("✅ Installed pyobjc for better macOS integration")
        
    except Exception as e:
        print(f"❌ Error installing macOS dependencies: {e}")
        print("AppleScript should work out of the box on macOS")

def test_virtual_desktop_support():
    """Test if virtual desktop functionality works"""
    print("\n🧪 Testing virtual desktop support...")
    
    try:
        from virtual_desktop import virtual_desktop_manager
        
        # Test getting virtual desktops
        desktops = virtual_desktop_manager.get_virtual_desktops()
        print(f"✅ Found {len(desktops)} virtual desktops:")
        
        for desktop in desktops:
            status = "🟢 Active" if desktop.get('active') else "🔵 Inactive"
            print(f"   {desktop['name']} (ID: {desktop['id']}) {status}")
        
        # Test screen capture
        screenshot = virtual_desktop_manager.capture_desktop()
        if screenshot:
            print("✅ Screen capture is working")
        else:
            print("⚠️ Screen capture may have issues")
            
        print("\n🎉 Virtual desktop support is ready!")
        
    except Exception as e:
        print(f"❌ Virtual desktop test failed: {e}")
        print("Please check the installation and try again.")

def main():
    print("🖥️ Virtual Desktop Setup for AgenticDesktop")
    print("=" * 50)
    
    os_type = get_os_type()
    print(f"Detected OS: {os_type}")
    
    if os_type == 'linux':
        install_linux_dependencies()
    elif os_type == 'windows':
        install_windows_dependencies()
    elif os_type == 'darwin':
        install_macos_dependencies()
    else:
        print(f"❌ Unsupported OS: {os_type}")
        sys.exit(1)
    
    # Test the installation
    test_virtual_desktop_support()

if __name__ == "__main__":
    main() 