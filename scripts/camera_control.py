#!/usr/bin/env python3
import sys
import subprocess
import json
import os
import glob

CONFIG_DIR = os.path.expanduser("~/printer_data/config/camera-settings")
if not os.path.exists(CONFIG_DIR):
    os.makedirs(CONFIG_DIR, exist_ok=True)

DEVICES_FILE = os.path.join(CONFIG_DIR, "camera_devices.json")

def get_settings_file(device_path):
    # Sanitize device path to create a filename (e.g., /dev/video0 -> camera_settings_video0.json)
    dev_name = os.path.basename(device_path)
    return os.path.join(CONFIG_DIR, f"camera_settings_{dev_name}.json")

def list_devices():
    devices = []
    try:
        # Use v4l2-ctl to list devices
        result = subprocess.run(['v4l2-ctl', '--list-devices'], capture_output=True, text=True)
        if result.returncode == 0:
            lines = result.stdout.split('\n')
            current_name = None
            
            for line in lines:
                if not line.strip():
                    continue
                if not line.startswith('\t'):
                    # It's a device name (e.g. "USB Camera (usb-...)":)
                    current_name = line.strip().rstrip(':')
                elif current_name:
                    # It's a device path (e.g. /dev/video0)
                    path = line.strip()
                    if path.startswith('/dev/video'):
                        devices.append({'name': current_name, 'path': path})
                        # Only take the first path for each device group to avoid duplicates
                        current_name = None 
    except Exception as e:
        print(f"Error listing devices: {e}", file=sys.stderr)
        
    # Write to file for UI to consume
    try:
        with open(DEVICES_FILE, 'w') as f:
            json.dump(devices, f, indent=2)
        print(json.dumps(devices))
    except Exception as e:
        print(f"Error saving devices file: {e}", file=sys.stderr)

def get_controls(device):
    try:
        # Get raw output from v4l2-ctl
        result = subprocess.run(['v4l2-ctl', '-d', device, '--list-ctrls'], capture_output=True, text=True)
        if result.returncode != 0:
            return {}

        controls = {}
        lines = result.stdout.split('\n')
        for line in lines:
            if not line.strip():
                continue
            
            parts = line.split()
            if len(parts) < 3:
                continue
                
            name = parts[0]
            ctrl_type = parts[2].strip('()')
            
            params = {}
            for part in parts[3:]:
                if '=' in part:
                    k, v = part.split('=', 1)
                    try:
                        params[k] = int(v)
                    except ValueError:
                        params[k] = v
            
            controls[name] = {
                'type': ctrl_type,
                'current': params.get('value'),
                'min': params.get('min'),
                'max': params.get('max'),
                'step': params.get('step'),
                'default': params.get('default'),
                'flags': params.get('flags', '')
            }
            
        return controls
    except Exception as e:
        print(f"Error getting controls for {device}: {e}", file=sys.stderr)
        return {}

def save_settings(device, settings):
    try:
        with open(get_settings_file(device), 'w') as f:
            json.dump(settings, f, indent=2)
    except Exception as e:
        print(f"Error saving settings: {e}", file=sys.stderr)

def load_settings(device):
    fpath = get_settings_file(device)
    if not os.path.exists(fpath):
        return {}
    try:
        with open(fpath, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading settings: {e}", file=sys.stderr)
        return {}

def cmd_get(device):
    # Fetch fresh state from hardware
    current_hw_controls = get_controls(device)
    
    # Save the full structure so UI has metadata
    save_settings(device, current_hw_controls)
    
    print(json.dumps(current_hw_controls))

def cmd_set(device, control, value):
    try:
        # 1. Update hardware
        cmd = ['v4l2-ctl', '-d', device, '--set-ctrl', f'{control}={value}']
        subprocess.run(cmd, check=True)
        
        # 2. Update persistence
        cmd_get(device)
        
    except subprocess.CalledProcessError as e:
        print(f"Error setting control: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
         print(f"Error updating setting file: {e}", file=sys.stderr)

def cmd_restore(device_filter=None):
    # If a specific device is passed, restore only that.
    # Otherwise, iterate through all known settings files.
    
    files = []
    if device_filter:
         files.append(get_settings_file(device_filter))
    else:
        files = glob.glob(os.path.join(CONFIG_DIR, "camera_settings_*.json"))

    for fpath in files:
        try:
            # Extract device name from filename "camera_settings_video0.json"
            fname = os.path.basename(fpath)
            dev_name = fname.replace("camera_settings_", "").replace(".json", "")
            device = f"/dev/{dev_name}"
            
            if not os.path.exists(device):
                print(f"Device {device} not found, skipping restore.")
                continue

            with open(fpath, 'r') as f:
                settings = json.load(f)

            print(f"Restoring settings for {device}...")
            for control, info in settings.items():
                if isinstance(info, dict) and 'current' in info:
                    value = info['current']
                    if value is None: 
                        continue
                    try:
                        cmd = ['v4l2-ctl', '-d', device, '--set-ctrl', f'{control}={value}']
                        subprocess.run(cmd, check=True)
                    except subprocess.CalledProcessError:
                        pass # Ignore errors for read-only or unsupported ctrls
                        
        except Exception as e:
            print(f"Error restoring {fpath}: {e}")


def main():
    if len(sys.argv) < 2:
        sys.exit(1)

    action = sys.argv[1]
    
    # Optional device argument
    device = "/dev/video0"
    if len(sys.argv) > 2:
        device = sys.argv[2]

    if action == "list":
        list_devices()
    elif action == "get":
        cmd_get(device)
    elif action == "set":
        if len(sys.argv) < 4:
            sys.exit(1)
        value = sys.argv[3]
        # Control name is actually device, value is buffer, wait.
        # Usage: python script.py set /dev/video0 control_name value
        if len(sys.argv) < 5:
             sys.exit(1)
        control = sys.argv[3]
        value = sys.argv[4]
        cmd_set(device, control, value)
    elif action == "restore":
        # If a device is explicitly passed, restore just that one
        # Otherwise restore all found configs
        if len(sys.argv) > 2:
             cmd_restore(sys.argv[2])
        else:
             cmd_restore()
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()
