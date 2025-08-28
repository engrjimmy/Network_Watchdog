import os
import sys

# Add the parent directory to sys.path
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, parent_dir)

# Try to import the module
try:
    import watchdog_net
    print("Successfully imported watchdog_net module")
    print(f"get_log_filename() returns: {watchdog_net.get_log_filename()}")
    print(f"devices: {watchdog_net.devices}")
except Exception as e:
    print(f"Error importing watchdog_net: {e}")
    print(f"sys.path: {sys.path}")
    print(f"parent_dir: {parent_dir}")
    print(f"Files in parent_dir: {os.listdir(parent_dir)}")

# If the import fails, print the error and sys.path for debugging
if 'watchdog_net' not in sys.modules:
    print("watchdog_net module not found in sys.modules")
    print("Current sys.path:")
    for path in sys.path:
        print(f"  {path}")
else:
    print("watchdog_net module is loaded successfully")
    print(f"Available functions: {dir(watchdog_net)}")
    print(f"devices: {watchdog_net.devices}")
    print(f"get_log_filename() output: {watchdog_net.get_log_filename()}")
    print(f"status_data: {watchdog_net.status_data}")
    print(f"config: {watchdog_net.config}")
    print("Module appears to be working correctly")
