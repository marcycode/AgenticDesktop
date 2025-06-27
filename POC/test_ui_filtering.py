#!/usr/bin/env python3
"""
Test script to verify UI control filtering
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from desktop_actions import execute_steps

def test_ui_control_filtering():
    """Test that UI control elements are properly filtered out"""
    print("=== UI CONTROL FILTERING TEST ===")
    
    # Test OCR annotations with UI controls
    test_ocr = [
        {'text': 'STOP', 'x': 1247, 'y': 311},
        {'text': 'Submit', 'x': 150, 'y': 250},
        {'text': 'Cancel', 'x': 200, 'y': 300},
        {'text': 'File Menu', 'x': 50, 'y': 100},
        {'text': 'New Document', 'x': 300, 'y': 150},
        {'text': 'Close', 'x': 400, 'y': 50},  # Edge position
        {'text': 'Save', 'x': 500, 'y': 50},   # Edge position
    ]
    
    # Test actions that should be blocked
    test_actions = [
        {"action": "click_text", "target": "STOP"},
        {"action": "click_text", "target": "Cancel"},
        {"action": "click_text", "target": "Close"},
        {"action": "click_text", "target": "Submit"},  # Should work
        {"action": "click_text", "target": "File Menu"},  # Should work
    ]
    
    print("Testing UI control filtering:")
    for action in test_actions:
        print(f"\nTesting action: {action}")
        execute_steps([action], test_ocr)
    
    return True

if __name__ == "__main__":
    test_ui_control_filtering() 