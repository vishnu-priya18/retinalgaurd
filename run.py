import os
import sys
import webbrowser
import uvicorn

def main():
    print("=" * 70)
    print("      RETINAGUARD AI - DR SCREENING & DECISION SUPPORT SYSTEM      ")
    print("=" * 70)
    print("Starting local server on http://127.0.0.1:8000...")
    print("Press Ctrl+C to stop server.\n")

    # Automatically open browser after server start
    webbrowser.open("http://127.0.0.1:8000")

    sys.path.append(os.path.join(os.path.dirname(__file__), "backend"))
    from backend.app import app

    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")

if __name__ == "__main__":
    main()
