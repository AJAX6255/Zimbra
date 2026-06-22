import os
import subprocess
import sys

def main():
    print("Launching Streamlit Sentiment Dashboard...")
    port = os.getenv("PORT", "8501")
    cmd = [
        sys.executable, 
        "-m", 
        "streamlit", 
        "run", 
        "zimbra/ui/dashboard.py",
        "--server.port", port,
        "--server.address", "0.0.0.0"
    ]
    subprocess.run(cmd)

if __name__ == "__main__":
    main()
