import time
import keyboard
from modules.config import *
from modules.utils import DEVICE_UNPLUGGED_FLAG

def check_manual_input_violations(telemetry, is_driving):
    """Checks for violations based on manual keyboard inputs."""
    global DEVICE_UNPLUGGED_FLAG
    violations = []
    speed_limit_val = telemetry.get('navigation', {}).get('speedLimit', 0)
    
    try:
        if is_driving and keyboard.is_pressed('h'):
            if speed_limit_val > 0 and speed_limit_val <= 60:
                context = f"{{input.key: 'h', navigation.speedLimit: {speed_limit_val}}}"
                violations.append(("IMPROPER HORN USE: Horn used in a city area!", "VIOLATION_HORN", context))
        
        if is_driving and keyboard.is_pressed('t') and telemetry.get('trailer', {}).get('attached', False):
            context = "{{input.key: 't', trailer.attached: true, is_driving: true}}"
            violations.append(("SAFETY VIOLATION: Attempted trailer detach while moving!", "VIOLATION_TRAILER_DETACH_ATTEMPT", context))
    except Exception:
        pass
    
    if DEVICE_UNPLUGGED_FLAG:
        context = "{device.unplugged: true}"
        violations.append(("SAFETY VIOLATION: Control device unplugged while driving!", "VIOLATION_DEVICE_REMOVAL", context))
        DEVICE_UNPLUGGED_FLAG = False

    return violations

def check_event_violations(telemetry, state, current_time):
    """Checks for event-driven violations like spamming controls or hit-and-run."""
    violations = []
    
    # --- Blinker Spam ---
    current_blinker_left = telemetry.get('truck', {}).get('blinkerLeftOn', False)
    current_blinker_right = telemetry.get('truck', {}).get('blinkerRightOn', False)
    if (current_blinker_left and not state.prev_blinker_left) or \
       (current_blinker_right and not state.prev_blinker_right):
        state.blinker_event_history.append(current_time)
    state.prev_blinker_left = current_blinker_left
    state.prev_blinker_right = current_blinker_right
    if len(state.blinker_event_history) == ERRATIC_BLINKER_EVENTS:
        time_span = state.blinker_event_history[-1] - state.blinker_event_history[0]
        if time_span < ERRATIC_BLINKER_TIME:
            context = f"{{event_count: {ERRATIC_BLINKER_EVENTS}, time_span: {time_span:.2f}s, threshold: {ERRATIC_BLINKER_TIME}s}}"
            violations.append(("ERRATIC SIGNALLING: Improper use of indicators!", "VIOLATION_BLINKER_SPAM", context))
            state.blinker_history.clear(); state.blinker_event_history.clear()

    # --- Wiper Spam ---
    current_wipers = telemetry.get('truck', {}).get('wipersOn', False)
    if current_wipers != state.prev_wipers:
        state.wiper_event_history.append(current_time)
    state.prev_wipers = current_wipers
    if len(state.wiper_event_history) == ERRATIC_WIPER_EVENTS:
        time_span = state.wiper_event_history[-1] - state.wiper_event_history[0]
        if time_span < ERRATIC_WIPER_TIME:
            context = f"{{event_count: {ERRATIC_WIPER_EVENTS}, time_span: {time_span:.2f}s, threshold: {ERRATIC_WIPER_TIME}s}}"
            violations.append(("ERRATIC BEHAVIOUR: Improper use of wipers!", "VIOLATION_WIPER_SPAM", context))
            state.wiper_event_history.clear()

    # --- High Beam Spam ---
    current_high_beams = telemetry.get('truck', {}).get('lightsBeamHighOn', False)
    if current_high_beams != state.prev_high_beams:
        state.high_beam_event_history.append(current_time)
    state.prev_high_beams = current_high_beams
    if len(state.high_beam_event_history) == ERRATIC_HIGH_BEAM_EVENTS:
        time_span = state.high_beam_event_history[-1] - state.high_beam_event_history[0]
        if time_span < ERRATIC_HIGH_BEAM_TIME:
            context = f"{{event_count: {ERRATIC_HIGH_BEAM_EVENTS}, time_span: {time_span:.2f}s, threshold: {ERRATIC_HIGH_BEAM_TIME}s}}"
            violations.append(("ERRATIC SIGNALLING: Improper use of high beams!", "VIOLATION_HIGH_BEAM_SPAM", context))
            state.high_beam_event_history.clear()

    # --- Erratic Steering Spam ---
    current_steer = telemetry.get('truck', {}).get('gameSteer', 0)
    if (current_steer > ERRATIC_STEER_SWERVE_THRESHOLD and state.prev_steer < -ERRATIC_STEER_SWERVE_THRESHOLD) or \
       (current_steer < -ERRATIC_STEER_SWERVE_THRESHOLD and state.prev_steer > ERRATIC_STEER_SWERVE_THRESHOLD):
        state.steer_event_history.append(current_time)
    state.prev_steer = current_steer
    if len(state.steer_event_history) == ERRATIC_STEER_EVENTS:
        time_span = state.steer_event_history[-1] - state.steer_event_history[0]
        if time_span < ERRATIC_STEER_TIME:
            context = f"{{event_count: {ERRATIC_STEER_EVENTS}, time_span: {time_span:.2f}s, threshold: {ERRATIC_STEER_TIME}s}}"
            violations.append(("ERRATIC DRIVING: Rapidly swerving wheel!", "VIOLATION_ERRATIC_STEERING", context))
            state.steer_event_history.clear()
            
    # --- Hit-and-Run ---
    current_truck_damage = max(telemetry.get('truck', {}).get('wearEngine', 0),
                                 telemetry.get('truck', {}).get('wearTransmission', 0),
                                 telemetry.get('truck', {}).get('wearCabin', 0),
                                 telemetry.get('truck', {}).get('wearChassis', 0),
                                 telemetry.get('truck', {}).get('wearWheels', 0))
    if state.last_known_truck_damage == 0.0: state.last_known_truck_damage = current_truck_damage
    damage_increase = current_truck_damage - state.last_known_truck_damage
    
    if damage_increase > HIT_AND_RUN_DAMAGE_JUMP:
        is_driving = any(s > 0.1 for s in state.speed_history)
        if is_driving:
            pct = int(damage_increase * 100)
            context = f"{{damage.increase: {damage_increase:.3f}, damage.current: {current_truck_damage:.3f}, damage.previous: {state.last_known_truck_damage:.3f}}}"
            violations.append((f"HIT AND RUN: New {pct}% damage detected! (We saw that.)", "VIOLATION_HIT_AND_RUN", context))
    state.last_known_truck_damage = current_truck_damage

    return violations

def check_stateful_violations(telemetry, state, is_driving, is_stopped):
    """Checks for violations that depend on state over time."""
    violations = []
    
    # --- Forgotten Blinker ---
    current_blinker_left = telemetry.get('truck', {}).get('blinkerLeftOn', False)
    current_blinker_right = telemetry.get('truck', {}).get('blinkerRightOn', False)
    current_steer = telemetry.get('truck', {}).get('gameSteer', 0)
    
    blinker_on = current_blinker_left or current_blinker_right
    steer_centered = abs(current_steer) < 0.05
    if is_driving and blinker_on and steer_centered:
        state.blinker_history.append(True)
    else:
        state.blinker_history.clear() 
    if len(state.blinker_history) == state.blinker_history.maxlen:
        context = f"{{duration: {FORGOTTEN_BLINKER_TIME}s, truck.gameSteer: {current_steer:.2f}, truck.blinkerOn: true}}"
        violations.append(("TRAFFIC VIOLATION: Blinker left on!", "VIOLATION_FORGOTTEN_BLINKER", context))
        state.blinker_history.clear()
        
    # --- Dangerous Parking ---
    speed_limit_val = telemetry.get('navigation', {}).get('speedLimit', 0)
    park_brake_on = telemetry.get('truck', {}).get('parkBrakeOn', False)
    
    if park_brake_on and speed_limit_val > 0 and is_stopped:
        state.parking_history.append(True)
    else:
        state.parking_history.clear()
    if len(state.parking_history) == state.parking_history.maxlen:
        context = f"{{duration: {DANGEROUS_PARKING_TIME}s, navigation.speedLimit: {speed_limit_val}, truck.parkBrakeOn: true}}"
        violations.append(("DANGEROUS PARKING: Vehicle stopped in active roadway!", "VIOLATION_DANGEROUS_PARK", context))
        state.parking_history.clear()
        
    return violations

def check_cleared_faults(telemetry, state, speech_queue):
    """Checks if any persistent faults have been cleared."""
    cleared_messages = []
    current_truck_damage = max(telemetry.get('truck', {}).get('wearEngine', 0),
                                 telemetry.get('truck', {}).get('wearTransmission', 0),
                                 telemetry.get('truck', {}).get('wearCabin', 0),
                                 telemetry.get('truck', {}).get('wearChassis', 0),
                                 telemetry.get('truck', {}).get('wearWheels', 0))

    for fault_code, is_active in list(state.persistent_fault_states.items()):
        if is_active:
            is_clear = False
            try:
                if fault_code == "FAULT_FLIPPED" and abs(telemetry['truck']['placement']['roll']) < ROLL_THRESHOLD:
                   is_clear = True
                elif fault_code == "FAULT_JACKKNIFE":
                    angle_diff = abs(telemetry['truck']['placement']['heading'] - telemetry['trailer']['placement']['heading'])
                    if angle_diff > 3.14: angle_diff = (6.28) - angle_diff
                    if angle_diff < JACKKNIFE_THRESHOLD: is_clear = True
                elif fault_code == "FAULT_LATE_DELIVERY" and telemetry['job']['income'] == 0:
                    is_clear = True
                elif fault_code == "FAULT_TRUCK_DAMAGE" and current_truck_damage < DAMAGE_THRESHOLD:
                   is_clear = True
                elif fault_code == "FAULT_TRAILER_DAMAGE" and telemetry['trailer']['wear'] < DAMAGE_THRESHOLD:
                     is_clear = True
                elif fault_code == "FAULT_AIR" and not telemetry['truck']['airPressureWarningOn']:
                     is_clear = True
                elif fault_code == "FAULT_WATER" and not telemetry['truck']['waterTemperatureWarningOn']:
                     is_clear = True
                elif fault_code == "FAULT_OIL" and not telemetry['truck']['oilPressureWarningOn']:
                     is_clear = True
                elif fault_code == "FAULT_BRAKE_HOT" and telemetry['truck']['brakeTemperature'] < BRAKE_TEMP_THRESHOLD:
                     is_clear = True
                elif fault_code == "FAULT_ADBLUE" and not telemetry['truck']['adblueWarningOn']:
                     is_clear = True
                elif fault_code == "FAULT_BATTERY" and not telemetry['truck']['batteryVoltageWarningOn']:
                     is_clear = True
                elif fault_code == "FAULT_LOW_FUEL" and not telemetry['truck']['fuelWarningOn']:
                     is_clear = True
            except (KeyError, TypeError):
                # Telemetry data might be missing, skip this check
                continue
            
            if is_clear:
                state.persistent_fault_states[fault_code] = False 
                clear_msg = fault_code.replace('_', ' ').replace('FAULT', '').strip()
                if fault_code == "FAULT_FLIPPED": clear_msg = "Truck is upright. Accident cleared."
                elif fault_code == "FAULT_LATE_DELIVERY": clear_msg = "Job finished. Late delivery cleared."
                else: clear_msg = f"{clear_msg} fault cleared."
                speech_queue.put(clear_msg)
                cleared_messages.append(clear_msg)
    
    return cleared_messages
