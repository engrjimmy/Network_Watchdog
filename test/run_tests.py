#!/usr/bin/env python3
import os
import subprocess
import sys

def run_command(cmd, title):
    print(f"\n{'=' * 80}")
    print(f"Running: {title}")
    print(f"Command: {cmd}")
    print(f"{'=' * 80}")
    
    # Run the command and capture output
    process = subprocess.Popen(
        cmd, 
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True
    )
    
    # Print output in real-time
    for line in process.stdout:
        print(line, end='')
    
    # Wait for process to complete
    process.wait()
    
    # Print any stderr if there was an error
    if process.returncode != 0:
        print(f"\nCommand failed with exit code {process.returncode}")
        print("Error output:")
        for line in process.stderr:
            print(line, end='')
    
    print(f"\n{'=' * 80}\n")
    return process.returncode

def main():
    # Get the directory of this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Change to the script directory
    os.chdir(script_dir)
    
    # Run tests with direct Python execution
    run_command("python3 test_watchdog_net.py", "Direct Python execution")
    
    # Run tests with pytest
    run_command("python3 -m pytest test_watchdog_net.py -v", "Pytest execution")
    
    # Run tests with unittest module
    run_command("cd .. && python3 -m unittest test/test_watchdog_net.py", "Unittest module execution")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
