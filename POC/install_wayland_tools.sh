#!/bin/bash

# Install Wayland screenshot tools
# This script helps install the necessary tools for Wayland desktop capture

echo "🚀 Installing Wayland screenshot tools..."

# Detect distribution
if command -v dnf &> /dev/null; then
    echo "📦 Detected Fedora/RHEL - using dnf"
    sudo dnf install -y gnome-screenshot grim wayshot flameshot wl-clipboard wtype ydotool xdotool
elif command -v apt &> /dev/null; then
    echo "📦 Detected Ubuntu/Debian - using apt"
    sudo apt update
    sudo apt install -y gnome-screenshot grim wayshot flameshot wl-clipboard-tools wtype ydotool xdotool
elif command -v pacman &> /dev/null; then
    echo "📦 Detected Arch Linux - using pacman"
    sudo pacman -S --noconfirm gnome-screenshot grim wayshot flameshot wl-clipboard wtype ydotool xdotool
elif command -v zypper &> /dev/null; then
    echo "📦 Detected openSUSE - using zypper"
    sudo zypper install -y gnome-screenshot grim wayshot flameshot wl-clipboard wtype ydotool xdotool
else
    echo "❌ Could not detect package manager. Please install manually:"
    echo "   - gnome-screenshot (for GNOME Wayland)"
    echo "   - grim (for wlroots-based compositors)"
    echo "   - wayshot (alternative screenshot tool)"
    echo "   - flameshot (cross-platform screenshot tool)"
    echo "   - wl-clipboard (clipboard utilities)"
    exit 1
fi

echo ""
echo "✅ Installation complete!"
echo ""
echo "Testing installed tools:"

# Test each tool
echo -n "📷 gnome-screenshot: "
if command -v gnome-screenshot &> /dev/null; then
    echo "✅ Available"
else
    echo "❌ Not found"
fi

echo -n "📷 grim: "
if command -v grim &> /dev/null; then
    echo "✅ Available"
else
    echo "❌ Not found"
fi

echo -n "📷 wayshot: "
if command -v wayshot &> /dev/null; then
    echo "✅ Available"
else
    echo "❌ Not found"
fi

echo -n "📷 flameshot: "
if command -v flameshot &> /dev/null; then
    echo "✅ Available"
else
    echo "❌ Not found"
fi

echo -n "📋 wl-paste: "
if command -v wl-paste &> /dev/null; then
    echo "✅ Available"
else
    echo "❌ Not found"
fi

echo -n "⌨️  wtype: "
if command -v wtype &> /dev/null; then
    echo "✅ Available"
else
    echo "❌ Not found"
fi

echo -n "⌨️  ydotool: "
if command -v ydotool &> /dev/null; then
    echo "✅ Available"
else
    echo "❌ Not found"
fi

echo -n "⌨️  xdotool: "
if command -v xdotool &> /dev/null; then
    echo "✅ Available"
else
    echo "❌ Not found"
fi

echo ""
echo "🖥️  Current display server: $XDG_SESSION_TYPE"
echo "🖥️  Desktop environment: $XDG_CURRENT_DESKTOP"

echo ""
echo "🎉 You can now run the AgenticDesktop with Wayland support!"
echo "   Run: python app.py" 