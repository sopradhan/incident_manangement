import sys,os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__),'..','src')))

from incident_iq.api.controllers.user_controller import handle_user_request
from incident_iq.core.config import show_config

if __name__ == "__main__":
    # Display loaded configuration
    show_config()

    result = handle_user_request("Sourav")
    print(result)