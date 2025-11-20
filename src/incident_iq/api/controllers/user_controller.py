from incident_iq.ml.user import User
from incident_iq.core.logger import log

def handle_user_request(username: str):
    user = User(username)
    log(f"Handling user: {username}")
    return user.greet()
