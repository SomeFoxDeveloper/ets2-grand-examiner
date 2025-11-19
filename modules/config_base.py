# --- Configuration ---
TELEMETRY_URL = "http://localhost:25555/api/ets2/telemetry"
CHECK_INTERVAL = 0.5
LOG_FILE = "violations_log.txt"
SCREENSHOT_FOLDER = "violations_screenshots" 
SESSIONS_FOLDER = "court_sessions"

# --- Printer Configuration ---
PRINTER_ENABLED = True # Set to False to disable printing
TEMP_IMAGE_FOLDER = "temp_tickets" # Folder to save temporary image files for printing
SELENIUM_WEBDRIVER_PATH = r"C:\path\to\geckodriver.exe" # !!! IMPORTANT: Update this path to your WebDriver executable (e.g., geckodriver.exe) !!!
FIREFOX_BINARY_PATH = r"C:\path\to\firefox.exe" # !!! IMPORTANT: Update this path to your Firefox browser executable !!!
