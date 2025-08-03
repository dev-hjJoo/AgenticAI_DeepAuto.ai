import sys
import requests

class ApiClient:
    def __init__(self):
        self.base_url = 'http://127.0.0.1:'
        if "--be_port" in sys.argv:
            index = sys.argv.index("--be_port") + 1
            self.port = sys.argv[index]
    
    def getData(self, endpoint: str, params=None):
        if not self.port: return False
        url = self.base_url + self.port + '/' + endpoint
        response = requests.get(url, params=params)

        return response.json()

        
        


    