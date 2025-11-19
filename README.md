# ETS2 Grand Examiner - Traffic Violation Detection System

A comprehensive traffic violation detection system for Euro Truck Simulator 2 that monitors driving behavior, detects violations, and generates official court citations.

![ETS2 Traffic Enforcement](https://img.shields.io/badge/ETS2-Traffic%20Enforcement-blue)
![Python](https://img.shields.io/badge/Python-3.7%2B-green)
![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey)

## 🚛 Features

### Real-Time Violation Detection
- **Critical Faults**: Engine failures, air pressure issues, overheating
- **Traffic Violations**: Speeding, failure to indicate, illegal parking
- **Driving Violations**: Harsh driving, dangerous maneuvers
- **Equipment Violations**: Lighting, wipers, horn misuse
- **Stateful Violations**: Erratic behavior patterns

### Smart Detection System
- **Tiered Speeding**: Regular speeding vs reckless driving
- **Weather Awareness**: Rain, night conditions affecting rules
- **Context Awareness**: Speed limits, road types, traffic density
- **Behavioral Analysis**: Erratic steering, blinker spam, horn abuse

### Enforcement Features
- **Chase System**: Active pursuit for serious violations
- **Court Citations**: Professional HTML tickets with evidence
- **Hardware Integration**: Device tampering detection
- **Screenshot Evidence**: Automatic violation documentation

## 📋 Violation Types & Fines

| Violation Type | Points | Description |
|----------------|---------|-------------|
| **Critical Faults** | 20-50 | Engine failure, flipping, critical systems |
| **Major Violations** | 10-25 | Reckless driving, trailer issues |
| **Traffic Violations** | 3-10 | Speeding, parking, signaling |
| **Equipment Violations** | 1-5 | Lighting, wipers, horn misuse |
| **Behavioral Violations** | 2-30 | Erratic patterns, tampering |

## 🛠️ Installation

### Prerequisites
1. **Euro Truck Simulator 2** with telemetry server enabled
2. **Python 3.7 or higher**
3. **Mozilla Firefox** (for ticket printing)
4. **Administrator privileges** (required for device monitoring)

### Setup Steps

1. **Clone/Download the project**
   ```bash
   git clone <repository-url>
   cd ets2-grand-examiner
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Paths** (Edit `modules/config.py`)
   ```python
   # Update these paths for your system:
   SELENIUM_WEBDRIVER_PATH = r"C:\path\to\geckodriver.exe"
   FIREFOX_BINARY_PATH = r"C:\Program Files\Mozilla Firefox\firefox.exe"
   ```

4. **Enable ETS2 Telemetry**
   - Start ETS2 with telemetry server enabled
   - Ensure telemetry is running on `localhost:25555`

5. **Run as Administrator**
   ```bash
   python main.py
   ```

## ⚙️ Configuration

### Violation Thresholds
Edit `modules/config.py` to customize:
```python
SPEEDING_TOLERANCE = 1          # km/h tolerance
RECKLESS_SPEED_PERCENT = 1.30   # 130% = reckless
BRAKE_TEMP_THRESHOLD = 220      # Celsius
HARSH_BRAKE_THRESHOLD = 12.0    # m/s²
```

### Fine Structure
Adjust points in `VIOLATION_POINTS` dictionary:
```python
VIOLATION_POINTS = {
    "VIOLATION_SPEEDING": 5,        # Regular speeding
    "VIOLATION_RECKLESS_SPEEDING": 20,  # Extreme speeding
    "FAULT_FLIPPED": 50,            # Most severe violation
    # ... other violations
}
```

### Cooldown Settings
Prevent violation spam with cooldown periods:
```python
VIOLATION_COOLDOWNS = {
    "VIOLATION_SPEEDING": 5,  # 5 second cooldown
    "VIOLATION_LIGHTS": 5,    # 5 second cooldown
    # ... other cooldowns
}
```

## 🎮 Usage

### Starting the System
1. Run `python main.py` as Administrator
2. Start ETS2 with telemetry enabled
3. Begin driving - system auto-detects violations

### Violation Handling
- **Critical Faults**: Immediate shutdown required
- **Standard Violations**: Points accumulated
- **Chase Events**: Active pursuit mode activated

### Court Sessions
- Automatic HTML ticket generation
- Screenshot evidence collection
- Professional citation format
- Contest submission system

### Output Files
```
├── violations_log.txt              # Detailed violation log
├── court_sessions/                 # HTML court citations
├── violations_screenshots/         # Evidence screenshots
├── temp_tickets/                   # Temporary ticket files
└── temp_videos/                    # Recorded chase events
```

## 🔧 Advanced Features

### Chase System
- Triggered by serious violations
- Automatic penalty escalation
- Flee detection and enforcement
- Professional pursuit protocols

### AI Examiner Remarks
- Automated violation commentary
- Professional legal language
- Humorous but authoritative tone
- Court-ready documentation

### Hardware Integration
- Device tampering detection
- USB device monitoring
- Anti-evasion measures
- Professional enforcement protocols

## 📊 System Requirements

### Minimum
- Windows 10/11
- Python 3.7+
- 4GB RAM
- ETS2 with telemetry
- Mozilla Firefox

### Recommended
- Administrator privileges
- SSD storage for screenshots
- Dedicated graphics card
- High-speed internet for updates

## 🔒 Security & Privacy

### Local Operation
- All data processed locally
- No cloud transmission
- Local screenshot storage
- Privacy-first design

### File Management
- Automatic log rotation
- Secure ticket generation
- Local evidence storage
- User-controlled data

## 📝 Logging & Monitoring

### Real-Time Monitoring
```bash
[Status] Speed: 85 / 100 km/h | Total Points: 15
[VIOLATION] SPEEDING: 85 in a 80 zone! (5 Points)
[INFO] BRAKE OVERHEAT cleared
```

### Log Files
- **violations_log.txt**: Complete violation history
- **Court Sessions**: Professional citation documents
- **Screenshots**: Visual evidence collection

## 🚨 Legal Disclaimer

This system is designed for entertainment and educational purposes within ETS2. It simulates law enforcement behavior but:

- Does not connect to real legal systems
- Functions only within the game environment
- Should not be used to violate actual traffic laws
- Maintains appropriate separation from reality

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

### Development Setup
```bash
pip install -r requirements-dev.txt
python -m pytest tests/
```

## 📄 License

This project is open source. See LICENSE file for details.

## ⚠️ Important Notes

- **Must run as Administrator** for full functionality
- **ETS2 telemetry server** must be enabled
- **Firefox browser** required for ticket printing
- **Hardware monitoring** requires elevated privileges
- **Personal configurations** should not be committed to git

## 🆘 Troubleshooting

### Common Issues
1. **Telemetry Connection**: Ensure ETS2 telemetry server is running
2. **Permission Errors**: Run as Administrator
3. **Printing Issues**: Verify Firefox path in config
4. **Device Monitoring**: Check antivirus exceptions

### Debug Mode
Enable verbose logging:
```python
LOG_FILE = "debug_violations.log"
# Set higher log level in code
```

## 📧 Support

For issues and support:
- Check the troubleshooting section
- Review configuration files
- Ensure all prerequisites are met
- Verify Administrator privileges

---

**Enjoy safe and legal driving in ETS2!** 🚛⚖️
