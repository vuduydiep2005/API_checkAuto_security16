import requests
import json

class APIClient:
    def __init__(self, base_url):
        self.base_url = base_url
        self.session = requests.Session() # Dùng session để giữ kết nối và token

    def _log_request(self, method, url, response):
        """Hàm nội bộ để in ra nhật ký mỗi khi gọi API"""
        print(f"\n--- [REQUEST] {method}: {url}")
        print(f"--- [STATUS]: {response.status_code}")
        try:
            print(f"--- [RESPONSE]: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        except:
            print(f"--- [RESPONSE]: {response.text}")

    def get(self, endpoint, params=None, headers=None):
        url = f"{self.base_url}{endpoint}"
        response = self.session.get(url, params=params, headers=headers)
        self._log_request("GET", url, response)
        return response

    def post(self, endpoint, data=None, json_data=None, headers=None):
        url = f"{self.base_url}{endpoint}"
        response = self.session.post(url, data=data, json=json_data, headers=headers)
        self._log_request("POST", url, response)
        return response

    def put(self, endpoint, data=None, json_data=None, headers=None):
        url = f"{self.base_url}{endpoint}"
        response = self.session.put(url, data=data, json=json_data, headers=headers)
        self._log_request("PUT", url, response)
        return response

    def delete(self, endpoint, headers=None):
        url = f"{self.base_url}{endpoint}"
        response = self.session.delete(url, headers=headers)
        self._log_request("DELETE", url, response)
        return response
