import time
import threading
from modules.utils import print_event
from modules.workers import siren_thread_worker
import modules.workers as workers 
from modules.config import (
    VIOLATION_POINTS, CHASE_PENALTY_INTERVAL, CHASE_FLEEING_PENALTY,
    CHASE_PULL_OVER_DURATION
)

def start_chase(state, violation, speech_queue):
    """Initiates the chase sequence."""
    if state.is_chase_active:
        return # A chase is already active

    msg, code, context = violation
    
    state.is_chase_active = True
    state.chase_start_time = time.time()
    state.chase_last_penalty_time = state.chase_start_time
    state.chase_initial_violation = violation

    dispatch_msg = f"[DISPATCH] Unit 7, we have a report of a {code.replace('VIOLATION_', '').replace('_', ' ').lower()}... Engaging."
    print_event(dispatch_msg)
    speech_queue.put("Police dispatch, a unit is in pursuit.")

    # Start the siren
    workers.SIREN_ACTIVE = True
    siren_thread = threading.Thread(target=siren_thread_worker, daemon=True)
    siren_thread.start()
    
    return VIOLATION_POINTS.get(code, 0) # Return initial points

def manage_chase(state, is_stopped, current_time, speech_queue, handle_event_func, log_file, printer_queue):
    """Manages the chase logic while it's active."""
    if not state.is_chase_active:
        return 0

    # Check if user is trying to pull over
    if is_stopped:
        if state.time_stopped_start == 0:
            state.time_stopped_start = current_time
        
        time_stopped = current_time - state.time_stopped_start
        if time_stopped >= CHASE_PULL_OVER_DURATION:
            return end_chase(state, speech_queue, handle_event_func, log_file, printer_queue)
    else:
        # Reset the stopped timer if the truck moves
        state.time_stopped_start = 0

    # Check if it's time to add a fleeing penalty
    if (current_time - state.chase_last_penalty_time) > CHASE_PENALTY_INTERVAL:
        state.chase_last_penalty_time = current_time
        
        fleeing_msg = "EVADING POLICE: Failure to yield for a police unit!"
        fleeing_context = f"{{chase_duration: {current_time - state.chase_start_time:.1f}s}}"
        
        handle_event_func(log_file, fleeing_msg, CHASE_FLEEING_PENALTY, printer_queue, context=fleeing_context)
        # Send a more urgent beep with the speech
        speech_queue.put((1500, 500, "Suspect is evading, repeat, suspect is evading!"))
        
        return CHASE_FLEEING_PENALTY

    return 0 # No points added in this tick

def end_chase(state, speech_queue, handle_event_func, log_file, printer_queue):
    """Ends the chase sequence."""
    if not state.is_chase_active:
        return 0

    print_event("[DISPATCH] Suspect has pulled over. Unit 7, issue citation.")
    speech_queue.put("Suspect has complied. Issuing citation.")

    # Stop the siren
    workers.SIREN_ACTIVE = False
    
    # Calculate final penalty
    initial_msg, code, context = state.chase_initial_violation
    initial_points = VIOLATION_POINTS.get(code, 0)
    
    # Log the initial violation that started the chase
    handle_event_func(log_file, initial_msg, initial_points, printer_queue, context=context)

    # Reset state
    state.is_chase_active = False
    state.chase_start_time = 0.0
    state.chase_last_penalty_time = 0.0
    state.chase_initial_violation = None
    state.time_stopped_start = 0.0
    
    return initial_points # Return the points for the initial violation
