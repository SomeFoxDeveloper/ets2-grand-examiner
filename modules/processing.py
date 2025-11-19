from datetime import datetime
import os
from modules.config import (
    VIOLATION_POINTS, VIOLATION_COOLDOWNS, PERSISTENT_FAULT_COOLDOWN,
    CHASE_TRIGGER_VIOLATIONS, PRINTER_ENABLED, REALTIME_TICKET_HTML_TEMPLATE, TEMP_IMAGE_FOLDER, SELENIUM_WEBDRIVER_PATH, FIREFOX_BINARY_PATH
)
from modules.utils import print_event
from modules.chase_logic import start_chase

# Selenium imports
from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options

# Ensure the temporary image folder exists
os.makedirs(TEMP_IMAGE_FOLDER, exist_ok=True)

def handle_violation_event(log_file, violation, points, printer_queue, context=None):
    """
    Handles all actions for a violation: console print, logging, and printing.
    """
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # 1. Print to console
    print_event(f"[VIOLATION] {ts} | {violation} (+{points})")
    if context:
        print_event(f"    L> Telemetry: {context}")
    
    # 2. Log to file
    context_log = context if context else 'N/A'
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(f"{ts} | {violation} | {points} | {context_log}\n")

    # 3. Generate HTML, take screenshot, and send image to printer queue
    if PRINTER_ENABLED:
        telemetry_html = f"<p><span class='label'>Telemetry:</span> {context}</p>" if context and context != 'N/A' else ""
        
        html_content = REALTIME_TICKET_HTML_TEMPLATE.format(
            timestamp=ts,
            violation=violation,
            points=points,
            telemetry_context=telemetry_html
        )
        
        # Create a temporary HTML file for Selenium to load
        temp_html_path = os.path.join(TEMP_IMAGE_FOLDER, f"temp_ticket_{datetime.now().timestamp()}.html")
        with open(temp_html_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        # Create a temporary image file
        temp_image_path = os.path.join(TEMP_IMAGE_FOLDER, f"temp_ticket_{datetime.now().timestamp()}.png")
        
        try:
            # Setup Firefox options for headless mode
            firefox_options = Options()
            firefox_options.add_argument("--headless")
            firefox_options.add_argument("--window-size=4000,3000") # Extreme window size for maximum resolution screenshot
            firefox_options.binary_location = FIREFOX_BINARY_PATH # Specify Firefox binary location


            # Setup WebDriver service
            service = Service(executable_path=SELENIUM_WEBDRIVER_PATH)
            
            driver = webdriver.Firefox(service=service, options=firefox_options)
            
            # Load the HTML content
            driver.get(f"file:///{os.path.abspath(temp_html_path)}")
            
            # Take screenshot
            driver.save_screenshot(temp_image_path)
            
            driver.quit() # Close the browser
            
            print_event(f"[Printer] Generated image ticket: {temp_image_path}")
            printer_queue.put(temp_image_path) # Put image path into queue
            
        except Exception as e:
            print_event(f"[Printer] ERROR: Failed to generate image for violation '{violation}': {e}")
        finally:
            if os.path.exists(temp_html_path):
                os.remove(temp_html_path) # Clean up temporary HTML file


def process_violations(state, violations, current_time, violation_timestamps, total_points, speech_queue, screenshot_queue, printer_queue, log_file):
    if not violations:
        return total_points
        
    processed_this_tick = set()
    
    # Now expects a 3-element tuple: (violation_msg, code, context)
    for violation_data in violations:
        violation_msg, code, context = violation_data
        
        if code in processed_this_tick:
            continue
            
        points = VIOLATION_POINTS.get(code, VIOLATION_POINTS.get("DEFAULT", 0))

        # Check if this violation should trigger a police chase
        if code in CHASE_TRIGGER_VIOLATIONS and not state.is_chase_active:
            # The chase logic will handle its own logging/printing via callbacks
            initial_points = start_chase(state, violation_data, speech_queue)
            total_points += initial_points
            processed_this_tick.add(code)
            continue 

        if code in state.persistent_fault_states:
            if not state.persistent_fault_states[code]:
                state.persistent_fault_states[code] = True
                global_last_time = violation_timestamps.get("GLOBAL", 0)
                if (current_time - global_last_time) > PERSISTENT_FAULT_COOLDOWN:
                    violation_timestamps["GLOBAL"] = current_time
                    total_points += points
                    speech_queue.put((1200, 300, violation_msg))
                    handle_violation_event(log_file, violation_msg, points, printer_queue, context=context)
                    processed_this_tick.add(code)
        else:
            cooldown_duration = VIOLATION_COOLDOWNS.get(code, VIOLATION_COOLDOWNS["DEFAULT"])
            last_triggered_time = violation_timestamps.get(code, 0)
            if (current_time - last_triggered_time) > cooldown_duration:
                violation_timestamps[code] = current_time
                total_points += points
                speech_queue.put((1200, 300, violation_msg))
                handle_violation_event(log_file, violation_msg, points, printer_queue, context=context)
                processed_this_tick.add(code)
    return total_points