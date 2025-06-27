#!/usr/bin/env python3
"""
Test script to verify OCR merging functionality
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agent_loop import capture_screen, ocr_screen_with_coordinates

def test_ocr_merging():
    """Test the OCR merging functionality"""
    print("=== OCR MERGING TEST ===")
    
    # Capture screen
    print("Capturing screen...")
    img_bytes, img_b64 = capture_screen()
    
    # Perform OCR with merging
    print("Performing OCR with word merging...")
    screen_text, ocr_annotations = ocr_screen_with_coordinates(img_bytes)
    
    print(f"\nOCR Results:")
    print(f"Total screen text length: {len(screen_text)}")
    print(f"Number of clickable elements: {len(ocr_annotations)}")
    
    if ocr_annotations:
        print(f"\nTop 15 clickable elements:")
        for i, ann in enumerate(ocr_annotations[:15]):
            merged_info = f" (merged from {ann['merged_from']} words)" if 'merged_from' in ann else ""
            instance_info = f" [instance {ann['index']+1} of {ann['total_instances']}]" if ann['total_instances'] > 1 else ""
            print(f"  {i+1:2d}. '{ann['text']}' at ({ann['x']:4d}, {ann['y']:4d}){merged_info}{instance_info}")
        
        # Show statistics
        merged_count = sum(1 for ann in ocr_annotations if 'merged_from' in ann and ann['merged_from'] > 1)
        single_count = len(ocr_annotations) - merged_count
        
        print(f"\nStatistics:")
        print(f"  Single words: {single_count}")
        print(f"  Merged elements: {merged_count}")
        
        if merged_count > 0:
            print(f"\nExamples of merged elements:")
            merged_examples = [ann for ann in ocr_annotations if 'merged_from' in ann and ann['merged_from'] > 1]
            for i, ann in enumerate(merged_examples[:5]):
                print(f"  {i+1}. '{ann['text']}' (merged from {ann['merged_from']} words)")
    else:
        print("No text elements detected!")
    
    return ocr_annotations

if __name__ == "__main__":
    test_ocr_merging() 