#!/usr/bin/env python3
"""
Test script to verify key handling improvements
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from desktop_actions import KEY_MAP, find_text_coordinates

def test_key_mapping():
    """Test the key mapping functionality"""
    print("=== KEY MAPPING TEST ===")
    
    # Test key mappings
    test_keys = ['enter', 'return', 'tab', 'space', 'escape', 'esc', 'backspace', 'delete']
    
    print("Testing key mappings:")
    for key in test_keys:
        if key in KEY_MAP:
            print(f"  ✓ '{key}' -> '{KEY_MAP[key]}'")
        else:
            print(f"  ✗ '{key}' -> NOT FOUND")
    
    # Test text matching with sample OCR data
    sample_ocr = [
        {'text': 'Enter', 'x': 100, 'y': 200},
        {'text': 'Submit', 'x': 150, 'y': 250},
        {'text': 'Cancel', 'x': 200, 'y': 300},
        {'text': 'File Menu', 'x': 50, 'y': 100},
        {'text': 'New Document', 'x': 300, 'y': 150},
    ]
    
    print(f"\nTesting text matching:")
    test_targets = ['Enter', 'enter', 'Submit', 'File Menu', 'New Document', 'File', 'Document']
    
    for target in test_targets:
        x, y = find_text_coordinates(target, sample_ocr)
        if x is not None and y is not None:
            print(f"  ✓ Found '{target}' at ({x}, {y})")
        else:
            print(f"  ✗ Not found: '{target}'")
    
    return True

if __name__ == "__main__":
    test_key_mapping() 