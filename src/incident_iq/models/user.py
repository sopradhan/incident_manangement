class User:
    def __init__(self, username: str):
        self.username = username

    def greet(self):
        return f"Hello, {self.username}!"
