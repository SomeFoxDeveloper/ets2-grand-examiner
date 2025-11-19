from collections import deque
from modules.config import (
    FORGOTTEN_BLINKER_TIME, DANGEROUS_PARKING_TIME, ERRATIC_BLINKER_EVENTS,
    ERRATIC_WIPER_EVENTS, ERRATIC_HIGH_BEAM_EVENTS, ERRATIC_STEER_EVENTS,
    CHECK_INTERVAL
)

class AppState:
    def __init__(self):
        self.total_points = 0
        self.speed_history = deque(maxlen=10)
        self.blinker_history = deque(maxlen=int(FORGOTTEN_BLINKER_TIME / CHECK_INTERVAL))
        self.parking_history = deque(maxlen=int(DANGEROUS_PARKING_TIME / CHECK_INTERVAL))
        
        self.blinker_event_history = deque(maxlen=ERRATIC_BLINKER_EVENTS)
        self.prev_blinker_left = False
        self.prev_blinker_right = False
        
        self.prev_wipers = False
        self.wiper_event_history = deque(maxlen=ERRATIC_WIPER_EVENTS)
        
        self.prev_high_beams = False
        self.high_beam_event_history = deque(maxlen=ERRATIC_HIGH_BEAM_EVENTS)
        
        self.prev_steer = 0.0
        self.steer_event_history = deque(maxlen=ERRATIC_STEER_EVENTS)
        
        self.last_known_truck_damage = 0.0
        
        self.violation_timestamps = {"GLOBAL": 0.0}
        self.persistent_fault_states = {
            "FAULT_FLIPPED": False, "FAULT_AIR": False, "FAULT_WATER": False, 
            "FAULT_OIL": False, "FAULT_BRAKE_HOT": False, "FAULT_JACKKNIFE": False,
            "FAULT_TRAILER_LOST": False, "FAULT_TRAILER_DAMAGE": False, 
            "FAULT_TRUCK_DAMAGE": False, "FAULT_ADBLUE": False, "FAULT_BATTERY": False,
            "FAULT_LATE_DELIVERY": False, "FAULT_LOW_FUEL": False
        }

        # --- Chase State ---
        self.is_chase_active = False
        self.chase_start_time = 0.0
        self.chase_last_penalty_time = 0.0
        self.chase_initial_violation = None
        self.time_stopped_start = 0.0
