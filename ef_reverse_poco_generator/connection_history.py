# connection_history.py
import json
import os
import logging

logger = logging.getLogger(__name__)

class ConnectionHistory:
    def __init__(self, filename='connection_history.json'):
        self.filename = filename
        self.history = self.load_history()

    def load_history(self):
        if os.path.exists(self.filename):
            with open(self.filename, 'r') as f:
                return json.load(f)
        return []

    def save_history(self):
        with open(self.filename, 'w') as f:
            json.dump(self.history, f)

    def add_connection(self, connection_info):
        required_fields = ['db_type', 'host', 'port', 'user', 'password', 'database']
        for field in required_fields:
            if field not in connection_info:
                logger.warning(f"Missing field '{field}' in connection info. Using default value.")
                connection_info[field] = 'Unknown'
        
        if connection_info not in self.history:
            self.history.append(connection_info)
            self.save_history()
        logger.info("Connection added to history successfully.")

    def get_history(self):
        return self.history

    def clear_history(self):
        self.history = []
        self.save_history()