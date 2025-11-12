from incident_iq.api.controllers.user_controller import handle_user_request
from incident_iq.core.config import show_config

if __name__ == "__main__":
    # Display loaded configuration
    show_config()

    result = handle_user_request("Alice")
    print(result)