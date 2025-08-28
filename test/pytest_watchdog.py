import unittest
from unittest.mock import patch, MagicMock, call
import os
import subprocess
import time
from datetime import datetime
import sys
import importlib.util

# Add the parent directory to sys.path
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, parent_dir)

# Find the watchdog_net.py file
watchdog_file = os.path.join(parent_dir, "watchdog_net.py")
if not os.path.exists(watchdog_file):
    print(f"Looking for watchdog_net.py in: {watchdog_file}")
    print("File not found. Checking alternative locations...")
    
    # Check if it's in a subdirectory
    watchdog_file = os.path.join(parent_dir, "watchdog_net", "watchdog_net.py")
    if os.path.exists(watchdog_file):
        print(f"Found at: {watchdog_file}")
    else:
        print("File not found in expected locations.")
        print("Current directory:", os.getcwd())
        print("Files in parent directory:", os.listdir(parent_dir))
        sys.exit(1)

print(f"Loading watchdog_net from: {watchdog_file}")

# Import the module directly using importlib
spec = importlib.util.spec_from_file_location("watchdog_net_module", watchdog_file)
watchdog_net = importlib.util.module_from_spec(spec)
spec.loader.exec_module(watchdog_net)

# Get the functions directly from the module
get_log_filename = watchdog_net.get_log_filename
ping_device = watchdog_net.ping_device
update_status_loop = watchdog_net.update_status_loop
ping_stream = watchdog_net.ping_stream
devices = watchdog_net.devices
app = watchdog_net.app

class TestWatchdogNet(unittest.TestCase):
    
    def test_1_get_log_filename(self):
        """Test get_log_filename returns the correct format"""
        with patch('watchdog_net_module.datetime') as mock_datetime:
            mock_now = MagicMock()
            mock_now.strftime.return_value = '2023-05-15-10-30'
            mock_datetime.now.return_value = mock_now
            
            # Call the function
            result = get_log_filename()
            
            # The function should return what the strftime mock returns
            self.assertEqual(result, '2023-05-15-10-30')
            print("\n✓ get_log_filename returns the correct format")
    
    @patch('watchdog_net_module.subprocess.check_output')
    def test_2_ping_device_reachable(self, mock_check_output):
        """Test ping_device correctly detects reachable devices"""
        mock_check_output.return_value = "64 bytes from 192.168.1.1: icmp_seq=1 ttl=64 time=0.123 ms"
        reachable, latency = ping_device("192.168.1.1")
        
        self.assertTrue(reachable)
        self.assertAlmostEqual(latency, 0.123)
        print("\n✓ ping_device correctly detects reachable devices")
    
    @patch('watchdog_net_module.subprocess.check_output')
    def test_3_ping_device_reachable_no_time(self, mock_check_output):
        """Test ping_device handles reachable devices with no time info"""
        mock_check_output.return_value = "64 bytes from 192.168.1.1: icmp_seq=1 ttl=64"
        reachable, latency = ping_device("192.168.1.1")
        
        self.assertTrue(reachable)
        self.assertIsNone(latency)
        print("\n✓ ping_device correctly handles reachable devices with no time info")
    
    @patch('watchdog_net_module.subprocess.check_output')
    def test_4_ping_device_unreachable(self, mock_check_output):
        """Test ping_device correctly detects unreachable devices"""
        mock_check_output.side_effect = subprocess.CalledProcessError(1, "cmd")
        reachable, latency = ping_device("192.168.1.1")
        
        self.assertFalse(reachable)
        self.assertIsNone(latency)
        print("\n✓ ping_device correctly detects unreachable devices")
    
    def test_5_update_status_loop(self):
        """Test update_status_loop correctly logs device status"""
        with patch('watchdog_net_module.ping_device') as mock_ping_device, \
             patch('watchdog_net_module.time.sleep') as mock_sleep, \
             patch('builtins.open', new_callable=unittest.mock.mock_open) as mock_open, \
             patch('watchdog_net_module.get_log_filename', return_value="2023-05-15-10-30"), \
             patch('watchdog_net_module.datetime') as mock_datetime:
            
            # Setup to run once and exit immediately after first iteration
            mock_sleep.side_effect = Exception("Stop loop")
            
            # Setup ping_device mock
            mock_ping_device.return_value = (True, 0.5)
            
            # Setup datetime mock
            mock_now = MagicMock()
            mock_now.strftime.return_value = "2023-05-15 10:30:00"
            mock_datetime.now.return_value = mock_now
            
            # Run the function and catch the exception to exit the loop
            try:
                update_status_loop()
            except Exception as e:
                if str(e) != "Stop loop":
                    raise
            
            # Verify the file was opened with the correct path
            expected_path = os.path.join("logs", "2023-05-15-10-30")
            mock_open.assert_called_with(expected_path, "a")
            
            # Verify ping_device was called for each device
            self.assertEqual(mock_ping_device.call_count, len(devices))
            print("\n✓ update_status_loop correctly logs device status")
    
    @patch('watchdog_net_module.subprocess.Popen')
    @patch('watchdog_net_module.time.sleep')
    def test_6_ping_stream(self, mock_sleep, mock_popen):
        """Test ping_stream correctly streams ping output"""
        # Setup mock process
        mock_process = MagicMock()
        mock_process.stdout.readline.side_effect = ["Line 1", "Line 2", ""]
        mock_popen.return_value = mock_process
        
        # Collect the generator output
        result = list(ping_stream("192.168.1.1"))
        
        # Verify the output format
        self.assertEqual(result, ["data: Line 1\n\n", "data: Line 2\n\n"])
        
        # Verify sleep was called after each line
        self.assertEqual(mock_sleep.call_count, 2)
        mock_sleep.assert_called_with(1)
        print("\n✓ ping_stream correctly streams ping output")

if __name__ == '__main__':
    unittest.main(verbosity=2)
