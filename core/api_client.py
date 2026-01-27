import requests
import json
import os

# Cái Class này tôi dựng làm cái khung chung, mấy ông (người 3,4) cứ thế mà gọi dùng nhé
class APIClient:
    def __init__(self, base_url):
        # Lưu cái link API tổng vào đây, ví dụ: http://127.0.0.1:8000
        self.base_url = base_url
        # Tạo cái session để giữ kết nối cho mượt, khỏi phải login đi login lại nhiều lần
        self.session = requests.Session() 

    def show_log(self, method, url, response):
        # Hàm này tôi viết thêm để lúc chạy nó in ra màn hình cho đẹp thôi
        # Để mình biết là code đang chạy đến đâu, API trả về cái gì cho dễ debug
        print(f"\n>>> ĐANG CHẠY: {method} - {url}")
        print(f">>> MÃ TRẢ VỀ: {response.status_code}")
        try:
            # Nếu nó trả về dạng json thì mình in ra cho dễ nhìn
            print(f">>> DỮ LIỆU: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        except:
            # Nếu lỗi server hay gì đó ko có json thì in tạm text thô ra
            print(f">>> TEXT: {response.text[:100]}")

    # --- Mấy hàm GET, POST, PUT, DELETE bên dưới các ông cứ truyền endpoint vào là xong ---

    def get(self, endpoint, params=None, headers=None):
        full_url = f"{self.base_url}{endpoint}"
        res = self.session.get(full_url, params=params, headers=headers)
        self._show_log("GET", full_url, res) # In log ra xem cho sướng
        return res

    def post(self, endpoint, data_json=None, headers=None):
        full_url = f"{self.base_url}{endpoint}"
        res = self.session.post(full_url, json=data_json, headers=headers)
        self._show_log("POST", full_url, res)
        return res

    def put(self, endpoint, data_json=None, headers=None):
        full_url = f"{self.base_url}{endpoint}"
        res = self.session.put(full_url, json=data_json, headers=headers)
        self._show_log("PUT", full_url, res)
        return res

    def delete(self, endpoint, headers=None):
        full_url = f"{self.base_url}{endpoint}"
        res = self.session.delete(full_url, headers=headers)
        self._show_log("DELETE", full_url, res)
        return res

    # --- Phần này tôi viết hộ ông 3, ông 4 để đọc dữ liệu từ file JSON trong folder data ---

    @staticmethod
    def doc_du_lieu_json(duong_dan_file):
        # Kiểm tra xem file có nằm đúng chỗ không, ko lại báo lỗi văng code
        if not os.path.exists(duong_dan_file):
            print(f"Báo lỗi: Không tìm thấy file tại {duong_dan_file}")
            return []

        try:
            with open(duong_dan_file, 'r', encoding='utf-8') as f:
                data_list = json.load(f)
            print(f"Đã nạp thành công {len(data_list)} kịch bản test. Chuẩn bị chạy thôi!")
            return data_list
        except Exception as e:
            print(f"Lỗi rồi ông ơi, check lại file JSON nhé: {e}")
            return []
