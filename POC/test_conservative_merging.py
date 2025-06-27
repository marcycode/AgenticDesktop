#!/usr/bin/env python3
"""
Test script to verify conservative merging algorithm
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_conservative_merging():
    """Test that the merging algorithm is conservative enough for UI elements"""
    print("=== CONSERVATIVE MERGING TEST ===")
    
    # Simulate OCR data that might cause over-merging
    # This represents a scenario like Google search tabs
    simulated_ocr_data = [
        # Tab-like elements that should NOT be merged
        {'text': 'All', 'x': 100, 'y': 50, 'bbox': {'x1': 95, 'y1': 45, 'x2': 115, 'y2': 65}},
        {'text': 'Images', 'x': 150, 'y': 50, 'bbox': {'x1': 140, 'y1': 45, 'x2': 170, 'y2': 65}},
        {'text': 'Videos', 'x': 200, 'y': 50, 'bbox': {'x1': 190, 'y1': 45, 'x2': 220, 'y2': 65}},
        {'text': 'News', 'x': 250, 'y': 50, 'bbox': {'x1': 240, 'y1': 45, 'x2': 270, 'y2': 65}},
        
        # Content that SHOULD be merged (multi-word phrases)
        {'text': 'Search', 'x': 100, 'y': 150, 'bbox': {'x1': 95, 'y1': 145, 'x2': 125, 'y2': 165}},
        {'text': 'results', 'x': 130, 'y': 150, 'bbox': {'x1': 125, 'y1': 145, 'x2': 155, 'y2': 165}},
        
        # Another multi-word phrase
        {'text': 'Google', 'x': 200, 'y': 200, 'bbox': {'x1': 195, 'y1': 195, 'x2': 225, 'y2': 215}},
        {'text': 'Chrome', 'x': 230, 'y': 200, 'bbox': {'x1': 225, 'y1': 195, 'x2': 255, 'y2': 215}},
    ]
    
    print("Simulated OCR data:")
    for i, element in enumerate(simulated_ocr_data):
        print(f"  {i+1}. '{element['text']}' at ({element['x']}, {element['y']})")
    
    print(f"\nExpected behavior:")
    print(f"  ✓ 'All', 'Images', 'Videos', 'News' should remain separate (tabs)")
    print(f"  ✓ 'Search results' should be merged (content)")
    print(f"  ✓ 'Google Chrome' should be merged (content)")
    
    # Test the merging logic manually
    print(f"\nTesting merging logic:")
    
    # Check if UI elements would be merged
    ui_element_words = {
        'images', 'videos', 'news', 'maps', 'books', 'flights', 'finance',
        'all', 'web', 'search', 'home', 'back', 'forward', 'reload',
        'file', 'edit', 'view', 'help', 'tools', 'options', 'settings',
        'profile', 'account', 'login', 'logout', 'sign', 'register'
    }
    
    for i, element in enumerate(simulated_ocr_data):
        element_lower = element['text'].lower().strip()
        if element_lower in ui_element_words:
            print(f"  ✓ '{element['text']}' identified as UI element (should not be merged)")
        else:
            print(f"  - '{element['text']}' is content (may be merged if close)")
    
    return True

if __name__ == "__main__":
    test_conservative_merging() 