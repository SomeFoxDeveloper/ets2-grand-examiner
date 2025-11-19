from datetime import datetime
from modules.config import (
    ROLL_THRESHOLD, BRAKE_TEMP_THRESHOLD, JACKKNIFE_THRESHOLD, DAMAGE_THRESHOLD,
    NIGHT_END, NIGHT_START, RAIN_THRESHOLD, STEER_THRESHOLD,
    RECKLESS_SPEED_FLAT_KPH, RECKLESS_SPEED_PERCENT, SPEEDING_TOLERANCE,
    HARSH_BRAKE_THRESHOLD, HARSH_SWERVE_THRESHOLD, HARSH_LANDING_THRESHOLD
)

def check_critical_faults(telemetry):
    violations_found = []
    truck = telemetry.get('truck', {})
    
    roll = truck.get('placement', {}).get('roll', 0)
    if abs(roll) > ROLL_THRESHOLD:
        context = f"{{truck.placement.roll: {abs(roll):.1f}, threshold: {ROLL_THRESHOLD}}}"
        violations_found.append(("CRITICAL ACCIDENT: Truck is flipped! Shut down engine!", "FAULT_FLIPPED", context))

    # --- Faults with Grace Period ---
    # Only trigger these if the engine is running under load (not just at startup idle)
    is_under_load = truck.get('engineRpm', 0) > 900 or abs(truck.get('speed', 0)) > 1

    if truck.get('airPressureWarningOn', False) and is_under_load:
        context = f"{{truck.airPressureWarningOn: true, engine.rpm: {truck.get('engineRpm', 0)}, truck.speed: {abs(truck.get('speed', 0)):.1f}}}"
        violations_found.append(("CRITICAL FAULT: LOW AIR PRESSURE! STOP IMMEDIATELY!", "FAULT_AIR", context))
    if truck.get('waterTemperatureWarningOn', False) and is_under_load:
        context = f"{{truck.waterTemperatureWarningOn: true, engine.rpm: {truck.get('engineRpm', 0)}, truck.speed: {abs(truck.get('speed', 0)):.1f}}}"
        violations_found.append(("CRITICAL FAULT: ENGINE OVERHEATING! STOP IMMEDIATELY!", "FAULT_WATER", context))
    if truck.get('oilPressureWarningOn', False) and is_under_load:
        context = f"{{truck.oilPressureWarningOn: true, engine.rpm: {truck.get('engineRpm', 0)}, truck.speed: {abs(truck.get('speed', 0)):.1f}}}"
        violations_found.append(("CRITICAL FAULT: LOW OIL PRESSURE! STOP ENGINE NOW!", "FAULT_OIL", context))
    
    return violations_found


def check_driving_violations(telemetry):
    if not telemetry or not telemetry.get('game', {}).get('connected'):
        return []
    violations_found = []
    truck = telemetry.get('truck', {})
    nav = telemetry.get('navigation', {})
    game = telemetry.get('game', {})
    trailer = telemetry.get('trailer', {})
    job = telemetry.get('job', {})
    speed_kmh = abs(truck.get('speed', 0))
    speed_limit = nav.get('speedLimit', 0)
    engine_on = truck.get('engineOn', False)
    game_brake = truck.get('gameBrake', 0)
    park_brake = truck.get('parkBrakeOn', False)
    engine_rpm = truck.get('engineRpm', 0)
    engine_rpm_max = truck.get('engineRpmMax', 2500)
    steer = truck.get('gameSteer', 0)
    cruise_control = truck.get('cruiseControlOn', False)
    motor_brake = truck.get('motorBrakeOn', False)
    retarder = truck.get('retarderBrake', 0)
    truck_heading = truck.get('placement', {}).get('heading', 0)
    accel = truck.get('acceleration', {})
    accel_x = accel.get('x', 0)
    accel_y = accel.get('y', 0)
    accel_z = accel.get('z', 0)
    adblue_warning = truck.get('adblueWarningOn', False)
    battery_warning = truck.get('batteryVoltageWarningOn', False)
    brake_temp = truck.get('brakeTemperature', 0)
    fuel_warning = truck.get('fuelWarningOn', False)
    game_time_str = game.get('time', '')
    is_night = False
    if game_time_str and 'T' in game_time_str:
        try:
            hour = int(game_time_str.split('T')[1].split(':')[0])
            if hour < NIGHT_END or hour >= NIGHT_START:
                is_night = True
        except: pass
    is_raining = game.get('raining', 0) > RAIN_THRESHOLD
    wipers_on = truck.get('wipersOn', False)
    lights_high = truck.get('lightsBeamHighOn', False)
    lights_low = truck.get('lightsBeamLowOn', False)
    blinker_left = truck.get('blinkerLeftOn', False)
    blinker_right = truck.get('blinkerRightOn', False)
    hazard_lights = truck.get('lightsHazardOn', False)
    beacon_on = truck.get('lightsBeaconOn', False)
    truck_damage = max(truck.get('wearEngine', 0), truck.get('wearTransmission', 0), 
                         truck.get('wearCabin', 0), truck.get('wearChassis', 0), 
                         truck.get('wearWheels', 0))
    trailer_wear = trailer.get('wear', 0)
    trailer_attached = trailer.get('attached', False)
    job_income = job.get('income', 0)
    deadline_time_str = job.get('deadlineTime', '')
    trailer_heading = trailer.get('placement', {}).get('heading', 0)

    # --- Start checking laws ---
    
    if brake_temp > BRAKE_TEMP_THRESHOLD:
        context = f"{{truck.brakeTemperature: {int(brake_temp)}, threshold: {BRAKE_TEMP_THRESHOLD}}}"
        violations_found.append((f"BRAKE OVERHEAT: Brakes at {int(brake_temp)}C! Use retarder.", "FAULT_BRAKE_HOT", context))
    if trailer_attached:
        angle_diff = abs(truck_heading - trailer_heading)
        if angle_diff > 3.14: angle_diff = (6.28) - angle_diff
        if angle_diff > JACKKNIFE_THRESHOLD:
            context = f"{{trailer.angle_difference: {angle_diff:.2f}, threshold: {JACKKNIFE_THRESHOLD:.2f}}}"
            violations_found.append(("JACKKNIFE WARNING: Trailer angle is critical!", "FAULT_JACKKNIFE", context))
    if job_income > 0 and not trailer_attached and speed_kmh > 5:
        context = f"{{job.income: {job_income}, trailer.attached: false, truck.speed: {speed_kmh:.1f}}}"
        violations_found.append(("TRAILER DETACHED: The trailer has been lost mid-job!", "FAULT_TRAILER_LOST", context))
    if trailer_wear > DAMAGE_THRESHOLD:
        pct = int(trailer_wear * 100)
        context = f"{{trailer.wear: {pct}%, threshold: {int(DAMAGE_THRESHOLD*100)}%}}"
        violations_found.append((f"TRAILER UNROADWORTHY: Trailer damage at {pct}%!", "FAULT_TRAILER_DAMAGE", context))
    if job_income > 0 and game_time_str and deadline_time_str:
        try:
            game_dt = datetime.fromisoformat(game_time_str.replace('Z', ''))
            deadline_dt = datetime.fromisoformat(deadline_time_str.replace('Z', ''))
            if game_dt > deadline_dt:
                context = f"{{game.time: {game_dt.strftime('%H:%M')}, job.deadlineTime: {deadline_dt.strftime('%H:%M')}}}"
                violations_found.append(("PROFESSIONAL FAULT: Late for delivery!", "FAULT_LATE_DELIVERY", context))
        except: pass
    if truck_damage > DAMAGE_THRESHOLD: 
        pct = int(truck_damage * 100)
        context = f"{{truck.wear: {pct}%, threshold: {int(DAMAGE_THRESHOLD*100)}%}}"
        violations_found.append((f"VEHICLE UNROADWORTHY: Truck damage at {pct}%. Vehicle is illegal!", "FAULT_TRUCK_DAMAGE", context))
    if is_night and engine_on and speed_kmh > 5 and not (lights_low or lights_high):
        context = f"{{game.is_night: true, truck.speed: {speed_kmh:.1f}, truck.lightsBeamLowOn: false, truck.lightsBeamHighOn: false}}"
        violations_found.append(("LIGHTING VIOLATION: Headlights required after dark!", "VIOLATION_LIGHTS", context))
    if is_raining and speed_kmh > 5 and not wipers_on:
        context = f"{{game.is_raining: true, truck.speed: {speed_kmh:.1f}, truck.wipersOn: false}}"
        violations_found.append(("POOR VISIBILITY: Wipers required in rain!", "VIOLATION_WIPERS", context))
    if is_night and speed_limit > 0 and speed_limit <= 60 and lights_high:
        context = f"{{game.is_night: true, navigation.speedLimit: {speed_limit}, truck.lightsBeamHighOn: true}}"
        violations_found.append(("LIGHTING VIOLATION: Improper use of high beams in city!", "VIOLATION_HIGH_BEAMS", context))
    
    # --- TIERED SPEEDING LOGIC ---
    if speed_limit > 0:
        speed_over = speed_kmh - speed_limit
        is_reckless = (speed_over > RECKLESS_SPEED_FLAT_KPH) or \
                      (speed_limit > 0 and (speed_kmh / speed_limit) > RECKLESS_SPEED_PERCENT)
        is_speeding = speed_over > SPEEDING_TOLERANCE

        if is_reckless:
            context = f"{{truck.speed: {speed_kmh:.1f}, navigation.speedLimit: {speed_limit}, reckless_threshold_percent: {RECKLESS_SPEED_PERCENT}}}"
            violations_found.append((f"RECKLESS DRIVING: {int(speed_kmh)} in a {speed_limit} zone!", "VIOLATION_RECKLESS_SPEEDING", context))
        elif is_speeding:
            context = f"{{truck.speed: {speed_kmh:.1f}, navigation.speedLimit: {speed_limit}, tolerance: {SPEEDING_TOLERANCE}}}"
            violations_found.append((f"SPEEDING: {int(speed_kmh)} in a {speed_limit} zone!", "VIOLATION_SPEEDING", context))

    if is_raining and cruise_control and speed_kmh > 30:
        context = "{game.is_raining: true, truck.cruiseControlOn: true}"
        violations_found.append(("POOR JUDGEMENT: Cruise control is unsafe in the rain!", "VIOLATION_CRUISE_RAIN", context))
    if speed_limit > 0 and speed_limit <= 60 and speed_kmh > 20 and (motor_brake or retarder > 0):
        context = f"{{navigation.speedLimit: {speed_limit}, truck.motorBrakeOn: {motor_brake}, truck.retarderBrake: {retarder}}}"
        violations_found.append(("NOISE VIOLATION: Engine brake in city!", "VIOLATION_NOISE", context))
    if not engine_on and speed_kmh > 10:
        context = f"{{truck.engineOn: false, truck.speed: {speed_kmh:.1f}}}"
        violations_found.append(("DANGEROUS DRIVING: Coasting with engine off!", "VIOLATION_COASTING", context))
    if hazard_lights and speed_kmh > 30:
        context = f"{{truck.lightsHazardOn: true, truck.speed: {speed_kmh:.1f}}}"
        violations_found.append(("LIGHTING VIOLATION: Improper use of hazard lights!", "VIOLATION_HAZARDS", context))
    if beacon_on and speed_kmh > 80:
        context = f"{{truck.lightsBeaconOn: true, truck.speed: {speed_kmh:.1f}}}"
        violations_found.append(("SAFETY VIOLATION: Improper use of warning beacon!", "VIOLATION_BEACON_MISUSE", context))
    if abs(accel_z) > HARSH_BRAKE_THRESHOLD:
        context = f"{{truck.acceleration.z: {accel_z:.2f}, threshold: {HARSH_BRAKE_THRESHOLD}}}"
        violations_found.append(("HARSH DRIVING: Harsh braking detected!", "VIOLATION_HARSH_BRAKE", context))
    if abs(accel_x) > HARSH_SWERVE_THRESHOLD:
        context = f"{{truck.acceleration.x: {accel_x:.2f}, threshold: {HARSH_SWERVE_THRESHOLD}}}"
        violations_found.append(("HARSH DRIVING: Harsh swerving detected!", "VIOLATION_HARSH_SWERVE", context))
    if abs(accel_y) > HARSH_LANDING_THRESHOLD:
        context = f"{{truck.acceleration.y: {accel_y:.2f}, threshold: {HARSH_LANDING_THRESHOLD}}}"
        violations_found.append(("HARSH DRIVING: Hard landing on curb/bump!", "VIOLATION_HARSH_LANDING", context))
    if engine_on and speed_kmh > 5 and engine_rpm > (engine_rpm_max * 0.95):
        context = f"{{truck.engineRpm: {int(engine_rpm)}, max_rpm_threshold: {int(engine_rpm_max * 0.95)}}}"
        violations_found.append(("MECHANICAL ABUSE: Engine over-revving!", "VIOLATION_OVER_REV", context))
    
    if speed_kmh > 11.0: # Turn signal violations only trigger above ~7 mph (11 km/h)
        if steer < -STEER_THRESHOLD and not blinker_left:
            context = f"{{truck.gameSteer: {steer:.2f}, truck.blinkerLeftOn: false, threshold: {-STEER_THRESHOLD}}}"
            violations_found.append(("TRAFFIC VIOLATION: Failure to indicate left turn!", "VIOLATION_NO_BLINKER_L", context))
        elif steer > STEER_THRESHOLD and not blinker_right:
            context = f"{{truck.gameSteer: {steer:.2f}, truck.blinkerRightOn: false, threshold: {STEER_THRESHOLD}}}"
            violations_found.append(("TRAFFIC VIOLATION: Failure to indicate right turn!", "VIOLATION_NO_BLINKER_R", context))
    if speed_limit > 30 and speed_kmh < 10 and not park_brake and game_brake < 0.1:
         context = f"{{truck.speed: {speed_kmh:.1f}, navigation.speedLimit: {speed_limit}}}"
         violations_found.append((f"IMPEDING TRAFFIC: Crawling at {int(speed_kmh)} in a {speed_limit} zone!", "VIOLATION_CRAWLING", context))
    if speed_limit >= 80 and speed_kmh < 5 and game_brake < 0.1 and not park_brake:
         context = f"{{truck.speed: {speed_kmh:.1f}, navigation.speedLimit: {speed_limit}}}"
         violations_found.append((f"DANGEROUS OBSTRUCTION: Stopped on a high-speed road!", "VIOLATION_OBSTRUCTION", context))
    if park_brake and speed_kmh > 5:
        context = f"{{truck.parkBrakeOn: true, truck.speed: {speed_kmh:.1f}}}"
        violations_found.append(("MECHANICAL ABUSE: Driving with park brake on!", "VIOLATION_PARK_BRAKE", context))
    if engine_on and speed_kmh < 1 and engine_rpm > 1800:
        context = f"{{truck.speed: {speed_kmh:.1f}, truck.engineRpm: {int(engine_rpm)}}}"
        violations_found.append(("EXCESSIVE IDLING: Engine revving while stationary!", "VIOLATION_IDLING", context))
    if adblue_warning:
        context = "{truck.adblueWarningOn: true}"
        violations_found.append(("EMISSIONS FAULT: AdBlue level critical.", "FAULT_ADBLUE", context))
    if battery_warning:
        context = "{truck.batteryVoltageWarningOn: true}"
        violations_found.append(("MECHANICAL FAULT: Low battery.", "FAULT_BATTERY", context))
    if fuel_warning:
        context = "{truck.fuelWarningOn: true}"
        violations_found.append(("LOW FUEL: Fuel level is critical.", "FAULT_LOW_FUEL", context))
        
    return violations_found