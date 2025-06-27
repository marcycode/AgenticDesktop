#!/usr/bin/env python3

"""
Test script to verify macOS workspace support
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_macos_support():
    """Test macOS workspace support"""
    print("🧪 Testing macOS Workspace Support")
    print("=" * 50)
    
    try:
        # Test system info
        from system_info import detect_desktop_environment, is_wayland
        desktop_env = detect_desktop_environment()
        wayland = is_wayland()
        
        print(f"✅ Desktop Environment: {desktop_env}")
        print(f"✅ Wayland: {wayland}")
        
        if desktop_env != 'macos':
            print("❌ Expected 'macos' but got '{desktop_env}'")
            return False
        
        # Test workspace manager
        from workspace_manager import workspace_manager
        
        print(f"✅ Workspace Manager Desktop: {workspace_manager.desktop_env}")
        print(f"✅ Current Workspace: {workspace_manager.current_workspace}")
        print(f"✅ Agent Workspace: {workspace_manager.agent_workspace}")
        
        # Test getting current workspace
        current = workspace_manager.get_current_workspace()
        print(f"✅ Get Current Workspace: {current}")
        
        # Test finding empty workspace
        empty = workspace_manager.find_empty_workspace()
        print(f"✅ Find Empty Workspace: {empty}")
        
        # Test getting next workspace number
        next_num = workspace_manager.get_next_workspace_number()
        print(f"✅ Next Workspace Number: {next_num}")
        
        # Test creating agent workspace
        print("\n🔄 Testing Agent Workspace Creation...")
        agent_ws = workspace_manager.create_agent_workspace()
        print(f"✅ Agent Workspace Created: {agent_ws}")
        
        if agent_ws is not None:
            # Test switching to agent workspace
            print("\n🔄 Testing Agent Workspace Switching...")
            success = workspace_manager.switch_to_agent_workspace()
            print(f"✅ Switch to Agent Workspace: {success}")
            
            if success:
                # Test switching back
                print("\n🔄 Testing Switch Back...")
                back_success = workspace_manager.switch_back_to_user_workspace()
                print(f"✅ Switch Back to User: {back_success}")
        
        print("\n🎉 All tests completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_macos_support()
    sys.exit(0 if success else 1) 