import sys
import requests
from utils.decorators import singleton


# API 호출 클래스
@singleton
class ApiClient:
    def __init__(self):
        self.base_url = 'http://127.0.0.1:'
        if "--be_port" in sys.argv:
            index = sys.argv.index("--be_port") + 1
            self.port = sys.argv[index]
    
    def get(self, endpoint: str, params=None):
        if not self.port: return False
        url = self.base_url + self.port + '/' + endpoint
        response = requests.get(url, params=params)

        return response.json()
    
    def post(self, endpoint: str, data: dict):
        url = self.base_url + self.port + '/' + endpoint
        response = requests.post(url, json=data)
        try:
            return response.json()
        except requests.exceptions.JSONDecodeError:
            print(f"[JSONDecodeError] The response is not of JSON type. \nResponse: {response.text}")
            raise
        


        
        


    