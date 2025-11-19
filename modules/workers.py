import os
import time
from datetime import datetime
import pyttsx3
import threading
import winsound
import wmi
import pythoncom
import queue
from PIL import ImageGrab

from modules.utils import print_event, DEVICE_UNPLUGGED_FLAG
from modules.config import PRINTER_ENABLED
from modules.printer_logic import send_to_printer

# --- Global Siren Flag ---
SIREN_ACTIVE = False


# --- Speech Worker Thread ---
def speech_thread_worker(speech_queue):
    engine = pyttsx3.init()
    engine.setProperty('rate', 170)
    engine.setProperty('volume', 1.0)
    
    while True:
        try:
            item = speech_queue.get()
            if item is None:
                break

            freq, duration, text = None, None, None
            
            if isinstance(item, tuple) and len(item) == 3:
                freq, duration, text = item
            elif isinstance(item, str):
                text = item
            else:
                continue # Ignore malformed items

            # Play beep if specified
            if freq and duration:
                winsound.Beep(freq, duration)
            
            # Speak text
            if text:
                engine.say(text)
                engine.runAndWait()

        except Exception as e:
            print_event(f"[Speech Error] {e}")
        finally:
            speech_queue.task_done()

# --- Screenshot Worker Thread ---
def screenshot_thread_worker(screenshot_queue, screenshot_folder):
    while True:
        try:
            filename = screenshot_queue.get()
            if filename is None:
                break
            
            path = os.path.join(screenshot_folder, filename)
            
            ss = ImageGrab.grab()
            ss.save(path)
            print_event(f"[Screenshot] Saved: {path}")

        except Exception as e:
            print_event(f"[Screenshot Error] {e}")
        finally:
            screenshot_queue.task_done()

# --- Printer Worker Thread ---
def printer_thread_worker(printer_queue):
    if not PRINTER_ENABLED:
        print_event("[Printer] Real-time printing is disabled in config.")
        return

    while True:
        try:
            text_to_print = printer_queue.get()
            if text_to_print is None:
                break
            send_to_printer(text_to_print)
        except Exception as e:
            print_event(f"[Printer Error] {e}")
        finally:
            printer_queue.task_done()

# --- Siren Worker Thread ---
def siren_thread_worker():
    global SIREN_ACTIVE
    print_event("[SIREN] Audio system activated.")
    while SIREN_ACTIVE:
        winsound.Beep(800, 200)
        winsound.Beep(1200, 200)
        time.sleep(0.1)
    print_event("[SIREN] Audio system deactivated.")

# --- Hardware Monitor Thread ---
def device_monitor_thread():
    global DEVICE_UNPLUGGED_FLAG
    print("[Device Monitor] Starting hardware monitor thread...")
    try:
        pythoncom.CoInitializeEx(0)
        c = wmi.WMI()
        keyboard_watcher = c.watch_for(
            notification_type="Deletion",
            wmi_class="Win32_Keyboard"
        )
        mouse_watcher = c.watch_for(
            notification_type="Deletion",
            wmi_class="Win32_PointingDevice"
        )
        print("[Device Monitor] ...Listening for USB device removal.")
        
        while True:
            try:
                keyboard_watcher(timeout_ms=500)
                print_event("[Device Monitor] ...Keyboard unplugged!")
                DEVICE_UNPLUGGED_FLAG = True
            except wmi.x_wmi_timed_out:
                pass
            
            try:
                mouse_watcher(timeout_ms=500)
                print_event("[Device Monitor] ...Pointing device unplugged!")
                DEVICE_UNPLUGGED_FLAG = True
            except wmi.x_wmi_timed_out:
                pass
            
            time.sleep(0.5) 
            
    except Exception as e:
        print_event(f"\n[Device Monitor ERROR] Hardware monitoring failed: {e}")
        print_event("[Device Monitor ERROR] This likely requires Admin rights.")
    finally:
        pythoncom.CoUninitialize()
