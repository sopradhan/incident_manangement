import os
from dotenv import load_dotenv

# Load the .env file once during startup
load_dotenv()

# Access variables
APP_ENV = os.getenv("APP_ENV", "production")
LOG_LEVEL = os.getenv("LOG_LEVEL", "info")
APP_NAME = os.getenv("APP_NAME", "incident_iq")

def show_config():
    print(f"App Name: {APP_NAME}")
    print(f"Environment: {APP_ENV}")
    print(f"Log Level: {LOG_LEVEL}")
