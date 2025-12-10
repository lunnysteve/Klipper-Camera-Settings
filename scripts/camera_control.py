#!/usr/bin/env python3
import sys
import subprocess
import json
import os

CONFIG_DIR = os.path.expanduser("~/printer_data/config")
SETTINGS_FILE = os.path.join(CONFIG_DIR, "camera_settings.json")
DEVICE = "/dev/video0"

def get_controls():
    try:
        # Get raw output from v4l2-ctl
        result = subprocess.run(['v4l2-ctl', '-d', DEVICE, '--list-ctrls'], capture_output=True, text=True)
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
        print(f"Error getting controls: {e}", file=sys.stderr)
        return {}

def save_settings(settings):
    try:
        with open(SETTINGS_FILE, 'w') as f:
            json.dump(settings, f, indent=2)
    except Exception as e:
        print(f"Error saving settings: {e}", file=sys.stderr)

def load_settings():
    if not os.path.exists(SETTINGS_FILE):
        return {}
    try:
        with open(SETTINGS_FILE, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading settings: {e}", file=sys.stderr)
        return {}

def cmd_get():
    # Fetch fresh state from hardware
    current_hw_controls = get_controls()
    
    # Save the full structure so UI has metadata
    save_settings(current_hw_controls)
    
    print(json.dumps(current_hw_controls))

def cmd_set(control, value):
    try:
        # 1. Update hardware
        cmd = ['v4l2-ctl', '-d', DEVICE, '--set-ctrl', f'{control}={value}']
        subprocess.run(cmd, check=True)
        
        # 2. Update persistence and capture side effects (flags changing)
        # by doing a full refresh of controls
        cmd_get()
        
    except subprocess.CalledProcessError as e:
        print(f"Error setting control: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
         print(f"Error updating setting file: {e}", file=sys.stderr)

def cmd_restore():
    settings = load_settings()
    if not settings:
        print("No settings to restore")
        return

    for control, info in settings.items():
        if isinstance(info, dict) and 'current' in info:
            value = info['current']
            # Skip inactive or read-only if we can detect, but v4l2-ctl usually complains if invalid.
            # Also skip if value is None
            if value is None: 
                continue
                
            try:
                cmd = ['v4l2-ctl', '-d', DEVICE, '--set-ctrl', f'{control}={value}']
                subprocess.run(cmd, check=True)
                print(f"Restored {control}={value}")
            except subprocess.CalledProcessError:
                # Some controls might be auto-only or conflict
                print(f"Failed to restore {control}", file=sys.stderr)

def main():
    if len(sys.argv) < 2:
        # sys.stderr.write("Usage: camera_control.py [get|set|restore] [control] [value]\n")
        sys.exit(1)

    action = sys.argv[1]

    if action == "get":
        cmd_get()
    elif action == "set":
        if len(sys.argv) < 4:
            sys.exit(1)
        cmd_set(sys.argv[2], sys.argv[3])
    elif action == "restore":
        cmd_restore()
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()
