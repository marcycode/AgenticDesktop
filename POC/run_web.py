#!/usr/bin/env python3

import os
import sys
from app import socketio, app

def main():
    print("Starting AgenticDesktop Web UI...")
    print("=" * 50)
    print("Web Interface will be available at:")
    print("   • Local: http://localhost:5001")
    print("   • Network: http://0.0.0.0:5001")
    print("=" * 50)
    print("Make sure you have your Azure OpenAI credentials configured!")
    print("Press Ctrl+C to stop the server")
    print("=" * 50)
    
    try:
        # Check if AZURE_OPENAI_API_KEY is configured
        from config import AZURE_OPENAI_API_KEY, AZURE_OPENAI_ENDPOINT
        if not AZURE_OPENAI_API_KEY or not AZURE_OPENAI_ENDPOINT:
            print("WARNING: Azure OpenAI credentials not found in environment!")
            print("   Please check your config.py or .env file.")
            print("")
        
        # Start the Flask-SocketIO server
        socketio.run(app, debug=True, host='0.0.0.0', port=5001)
        
    except KeyboardInterrupt:
        print("\nShutting down AgenticDesktop Web UI...")
    except Exception as e:
        print(f"❌ Error starting web server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 