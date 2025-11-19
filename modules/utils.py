import requests
import os
import ctypes
import threading
from colorama import Fore, Style, init

# Initialize Colorama
init()

# --- Global Flags & Locks ---
DEVICE_UNPLUGGED_FLAG = False
PRINT_LOCK = threading.Lock() 
CURRENT_STATUS_MESSAGE = "" 

# --- Thread-safe print function ---
def print_event(message):
    global CURRENT_STATUS_MESSAGE
    with PRINT_LOCK:
        color = Fore.WHITE # Default color
        
        if "[VIOLATION]" in message or "[CRITICAL FAULT]" in message:
            color = Fore.RED + Style.BRIGHT
        elif "[INFO]" in message:
            color = Fore.CYAN
        elif "[Status]" in message:
            color = Fore.YELLOW
        elif "[Monitoring]" in message:
            color = Fore.BLUE
        elif "[Screenshot]" in message:
            color = Fore.MAGENTA
        elif "[Ticket Gen]" in message:
            color = Fore.GREEN
        elif "[Device Monitor]" in message:
            color = Fore.WHITE
        elif "[Speech Error]" in message or "[Screenshot Error]" in message or "[Device Monitor ERROR]" in message:
            color = Fore.RED + Style.BRIGHT
        elif "Reason:" in message: # For the debug reason lines
            color = Fore.LIGHTBLACK_EX # A subtle gray

        print(" " * 100, end='\r') # Clear current line
        print(f"{color}{message}{Style.RESET_ALL}")
        print(CURRENT_STATUS_MESSAGE, end='\r')

def setup(log_file, screenshot_folder, sessions_folder):
    # Create log file if needed (and clear it for a new session)
    with open(log_file, 'w') as f:
        f.write("Timestamp | Violation | Points\n")
    
    # Create folders if needed
    os.makedirs(screenshot_folder, exist_ok=True)
    os.makedirs(sessions_folder, exist_ok=True)


def get_telemetry(url):
    try:
        resp = requests.get(url, timeout=0.5)
        if resp.status_code == 200:
            return resp.json()
        return None
    except:
        return None

def get_game_window():
    try:
        user32 = ctypes.windll.user32
        hwnd = user32.GetForegroundWindow()
        length = user32.GetWindowTextLengthW(hwnd)
        buff = ctypes.create_unicode_buffer(length + 1)
        user32.GetWindowTextW(hwnd, buff, length + 1)
        window_title = buff.value.lower()
        ets2_keywords = ['euro truck simulator', 'eurotrucks2', 'ets2', 'ets 2']
        is_ets2 = any(keyword in window_title for keyword in ets2_keywords)
        if is_ets2:
            return True
        return False
    except:
        return False