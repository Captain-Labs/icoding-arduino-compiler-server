# config.py
# Configuration constants for the Arduino CLI Compilation Server - Hardened Production Version

# Path to arduino-cli. If in PATH, just the executable name works.
ARDUINO_CLI_PATH = 'arduino-cli'

import os
# Self-contained configuration paths
ARDUINO_CLI_CONFIG_FILE = os.path.join(os.path.dirname(__file__), 'arduino-cli.yaml')
ARDUINO_CLI_CMD = [ARDUINO_CLI_PATH, '--config-file', ARDUINO_CLI_CONFIG_FILE]

# Default and supported boards (Arduino Uno only as requested)
DEFAULT_BOARD_FQBN = 'arduino:avr:uno'
SUPPORTED_BOARDS = {
    'uno': 'arduino:avr:uno'
}

# Maximum flash storage size (in bytes) for supported boards
BOARD_FLASH_LIMITS = {
    'arduino:avr:uno': 32256
}

# Limits and Timeouts
COMPILE_TIMEOUT_SEC = 60
MAX_QUEUE_SIZE = 20
MAX_CODE_LENGTH = 50000  # maximum sketch characters
CACHE_MAX_ENTRIES = 500

# Server Binding
SERVER_HOST = '0.0.0.0'
SERVER_PORT = 5000

# Prefix for temporary compilation directories
TEMP_DIR_PREFIX = 'arduino_compile_'

# ═══════════════════════════════════════
# PRODUCTION SECURITY ADDITIONS
# ═══════════════════════════════════════

# Request Size Limit (100KB)
MAX_CONTENT_LENGTH = 100 * 1024

# Security Hardening Blocked Patterns (restricted dangerous keywords)
BLOCKED_PATTERNS = [
    'system(',
    'exec(',
    'popen(',
    'fork(',
    '__asm',
    '#include "/etc',
    '#include "/proc',
    '#include "/sys',
    'FILE *',
    'fopen(',
]

# ═══════════════════════════════════════
# AUTO LIBRARY INSTALLER MAPPINGS
# ═══════════════════════════════════════

# Map header filenames to Arduino Library names
HEADER_TO_LIBRARY = {
    'Servo.h':                  'Servo',
    'DHT.h':                    'DHT sensor library',
    'DHT20.h':                  'DHT20',
    'Adafruit_NeoPixel.h':      'Adafruit NeoPixel',
    'Adafruit_SSD1306.h':       'Adafruit SSD1306',
    'Adafruit_GFX.h':           'Adafruit GFX Library',
    'Adafruit_TCS34725.h':      'Adafruit TCS34725',
    'Adafruit_VL53L0X.h':       'Adafruit VL53L0X',
    'Adafruit_NeoMatrix.h':     'Adafruit NeoMatrix',
    'NewPing.h':                'NewPing',
    'Encoder.h':                'Encoder',
    'RTClib.h':                 'RTClib',
    'AccelStepper.h':           'AccelStepper',
    'MPU6050_tockn.h':          'MPU6050_tockn',
    'RunningAverage.h':         'RunningAverage',
    'Wire.h':                   'Wire',
    'SPI.h':                    'SPI',
    'Stepper.h':                'Stepper',
    'LiquidCrystal_I2C.h':      'LiquidCrystal I2C',
    'LiquidCrystal.h':          'LiquidCrystal',
}

# Essential startup library lists used by the 16 block categories
ESSENTIAL_LIBRARIES = list(set(HEADER_TO_LIBRARY.values()))

# ═══════════════════════════════════════
# INTELLIGENT CACHING COMMON SKETCHES
# ═══════════════════════════════════════

COMMON_SKETCHES = [
    {
        "name": "blink_250",
        "board": "arduino:avr:uno",
        "code": "void setup() { pinMode(13, OUTPUT); }\nvoid loop() {\n  digitalWrite(13, HIGH); delay(250);\n  digitalWrite(13, LOW);  delay(250);\n}"
    },
    {
        "name": "blink_500",
        "board": "arduino:avr:uno",
        "code": "void setup() { pinMode(13, OUTPUT); }\nvoid loop() {\n  digitalWrite(13, HIGH); delay(500);\n  digitalWrite(13, LOW);  delay(500);\n}"
    },
    {
        "name": "blink_1000",
        "board": "arduino:avr:uno",
        "code": "void setup() { pinMode(13, OUTPUT); }\nvoid loop() {\n  digitalWrite(13, HIGH); delay(1000);\n  digitalWrite(13, LOW);  delay(1000);\n}"
    },
    {
        "name": "blink_2000",
        "board": "arduino:avr:uno",
        "code": "void setup() { pinMode(13, OUTPUT); }\nvoid loop() {\n  digitalWrite(13, HIGH); delay(2000);\n  digitalWrite(13, LOW);  delay(2000);\n}"
    },
    {
        "name": "empty_sketch",
        "board": "arduino:avr:uno",
        "code": "void setup(){} void loop(){}"
    }
]
