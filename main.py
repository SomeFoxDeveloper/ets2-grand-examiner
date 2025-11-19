import time
import threading
import queue

from modules.config import *
from modules.utils import (
    setup, get_telemetry, get_game_window, print_event
)
from modules.workers import (
    speech_thread_worker, screenshot_thread_worker, device_monitor_thread,
    printer_thread_worker
)
from modules.violations import (
    check_critical_faults, check_driving_violations
)
from modules.processing import process_violations, handle_violation_event
from modules.ticket_generator import generate_html_ticket
from modules.state import AppState
from modules.checks import (
    check_manual_input_violations, check_event_violations,
    check_stateful_violations, check_cleared_faults
)
from modules.chase_logic import manage_chase
import modules.workers as workers

def main():
    setup(LOG_FILE, SCREENSHOT_FOLDER, SESSIONS_FOLDER)
    
    speech_queue = queue.Queue()
    screenshot_queue = queue.Queue()
    printer_queue = queue.Queue()
    
    state = AppState()
    
    print("="*60)
    print("      ETS2 GRAND EXAMINER (Hardware Detection Enabled)")
    print("="*60)
    print("Monitoring for ALL violations... (Reckless Speed, Erratic Steering)")
    print(f"Screenshots will be saved to: {SCREENSHOT_FOLDER}")
    print(f"Court Sessions will be saved to: {SESSIONS_FOLDER}")
    print("REMINDER: This script must be run as Administrator.")
    print("="*60)

    # Start background threads
    threading.Thread(target=device_monitor_thread, daemon=True).start()
    threading.Thread(target=speech_thread_worker, args=(speech_queue,), daemon=True).start()
    threading.Thread(target=screenshot_thread_worker, args=(screenshot_queue, SCREENSHOT_FOLDER), daemon=True).start()
    threading.Thread(target=printer_thread_worker, args=(printer_queue,), daemon=True).start()

    try:
        while True:
            current_time = time.time()
            
            telemetry = get_telemetry(TELEMETRY_URL)
            
            if not telemetry or not telemetry.get('game', {}).get('connected'):
                status = "Waiting for Telemetry Server..." if not telemetry else "Game Paused / Not Connected..."
                print_event(f"[Status] {status}")
                time.sleep(1)
                continue

            speed_val = abs(telemetry.get('truck', {}).get('speed', 0))
            is_stopped = speed_val < 1

            # --- CHASE LOGIC ---
            if state.is_chase_active:
                points_added = manage_chase(state, is_stopped, current_time, speech_queue, handle_violation_event, LOG_FILE, printer_queue)
                state.total_points += points_added
                time.sleep(CHECK_INTERVAL)
                continue # Skip all other checks during a chase

            # If the game is backgrounded, only process critical faults and then skip the rest
            if not get_game_window():
                print_event("[Status] ETS2 is backgrounded...")
                # We still process critical faults even if backgrounded
                crit_violations = check_critical_faults(telemetry)
                if crit_violations:
                    state.total_points = process_violations(
                        state, crit_violations, current_time, state.violation_timestamps, 
                        state.total_points, speech_queue, screenshot_queue, printer_queue, LOG_FILE
                    )
                time.sleep(1)
                continue

            # --- NORMAL VIOLATION CHECKING ---
            current_violations = []
            current_violations.extend(check_critical_faults(telemetry))
            
            # Determine driving status
            speed_limit_val = telemetry.get('navigation', {}).get('speedLimit', 0)
            state.speed_history.append(speed_val)
            is_driving = any(s > 0.1 for s in state.speed_history)
            
            # Gather all violations
            current_violations.extend(check_manual_input_violations(telemetry, is_driving))
            current_violations.extend(check_event_violations(telemetry, state, current_time))
            current_violations.extend(check_stateful_violations(telemetry, state, is_driving, is_stopped))
            
            stateless_violations = check_driving_violations(telemetry)
            if stateless_violations:
                for violation_data in stateless_violations:
                    if "VIOLATION" in violation_data[1]: 
                        if is_driving or (is_stopped and violation_data[1] == "VIOLATION_IDLING"):
                            current_violations.append(violation_data)
                    else:
                        current_violations.append(violation_data)

            cleared_messages = check_cleared_faults(telemetry, state, speech_queue)
            for msg in cleared_messages:
                print_event(f"[INFO] {msg}")

            if current_violations:
                state.total_points = process_violations(
                    state,
                    current_violations, 
                    current_time, 
                    state.violation_timestamps, 
                    state.total_points,
                    speech_queue,
                    screenshot_queue,
                    printer_queue,
                    LOG_FILE
                )
            
            if not current_violations and not cleared_messages:
                print_event(f"[Monitoring] Speed: {int(speed_val)} / {speed_limit_val} km/h | Total Points: {state.total_points}    ")
                
            time.sleep(CHECK_INTERVAL)

    except KeyboardInterrupt:
        print_event(f"\n[STOPPING] Session ended. Total Points: {state.total_points}")
        # Ensure siren stops on exit
        workers.SIREN_ACTIVE = False
        print_event("[Info] Generating final court session ticket...")
        
        generate_html_ticket(state.total_points, SESSIONS_FOLDER, LOG_FILE) 
        
        print_event("[Info] Shutting down worker threads...")
        speech_queue.put(None)
        screenshot_queue.put(None) 
        printer_queue.put(None)
        
        speech_queue.join()
        screenshot_queue.join()
        printer_queue.join()
        print_event("[Info] Shutdown complete. Goodbye.")
        
    except Exception as e:
        print_event(f"\nA CRITICAL ERROR OCCURRED: {e}")
        # Ensure siren stops on error
        workers.SIREN_ACTIVE = False
        print_event("This may be due to not running as Administrator.")
        speech_queue.put(None)
        screenshot_queue.put(None) 
        printer_queue.put(None)
        
        speech_queue.join()
        screenshot_queue.join()
        printer_queue.join()

if __name__ == "__main__":
    main()