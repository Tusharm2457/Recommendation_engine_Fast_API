#!/usr/bin/env python3
"""
Simple script to view CrewAI debug logs
"""

import os
import sys
from datetime import datetime

def view_logs():
    """View the latest CrewAI debug logs"""
    log_file = "logs/crewai_debug.log"
    
    if not os.path.exists(log_file):
        print("❌ No log file found at logs/crewai_debug.log")
        print("Run your crew first to generate logs.")
        return
    
    print(f"📝 Viewing logs from: {log_file}")
    print(f"📅 Last modified: {datetime.fromtimestamp(os.path.getmtime(log_file))}")
    print("=" * 80)
    
    try:
        with open(log_file, 'r') as f:
            lines = f.readlines()
            
        # Show last 50 lines by default
        if len(sys.argv) > 1 and sys.argv[1] == "--all":
            content = ''.join(lines)
        else:
            content = ''.join(lines[-50:])
            if len(lines) > 50:
                print(f"... (showing last 50 lines of {len(lines)} total lines)")
                print("Use 'python view_logs.py --all' to see all logs")
                print("=" * 80)
        
        print(content)
        
    except Exception as e:
        print(f"❌ Error reading log file: {e}")

if __name__ == "__main__":
    view_logs()
