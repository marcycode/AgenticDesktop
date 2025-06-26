#!/usr/bin/env python3

import os
import sys
from app import socketio, app

def main():
    print("Starting AgenticDesktop Web UI...")
    print("=" * 50)
    print("Web Interface will be available at:")
    print("   • Local: http://localhost:5000")
    print("   • Network: http://0.0.0.0:5000")
    print("=" * 50)
    print("Make sure you have your .env file with OPENAI_API_KEY configured!")
    print("Press Ctrl+C to stop the server")
    print("=" * 50)
    
    try:
        # Check if OPENAI_API_KEY is configured
        from config import OPENAI_API_KEY
        if not OPENAI_API_KEY:
            print("WARNING: OPENAI_API_KEY not found in environment!")
            print("   Please create a .env file with your OpenAI API key.")
            print("   Example: OPENAI_API_KEY=your_api_key_here")
            print("")
        
        # Start the Flask-SocketIO server
        socketio.run(app, debug=True, host='0.0.0.0', port=5000)
        
    except KeyboardInterrupt:
        print("\nShutting down AgenticDesktop Web UI...")
    except Exception as e:
        print(f"❌ Error starting web server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 