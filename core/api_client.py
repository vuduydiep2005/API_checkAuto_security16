import requests
import json
import os

class APIClient:
    """
    [LƯU Ý CHO CẢ NHÓM]
    - Đây là file xương sống của dự án. Mọi người tuyệt đối không tự ý sửa các hàm _xu_ly_yeu_cau.
    - Ông 3, 4 khi viết script test chỉ cần gọi các hàm get(), post()... là xong.
    - Mọi thắc mắc liên hệ Lead Hiếu.
    """

    def __init__(self, base_url, timeout=10):
        # Base_url là cái link gốc, ví dụ: http://localhost:8000
        self.base_url = base_url
        self.timeout = timeout
        # Dùng Session để giữ kết nối liên tục, giúp tốc độ test nhanh hơn và quản lý Token dễ hơn
        self.session = requests.Session()
        # Header mặc định để API hiểu mình đang gửi dữ liệu dạng JSON
        self.session.headers.update({"Content-Type": "application/json"})

    # --- PHẦN DÀNH CHO ÔNG 3 & 4 (XỬ LÝ ĐĂNG NHẬP) ---
    
    def gan_token(self, token):
        """ 
        [HƯỚNG DẪN]: Sau khi ông 3 viết xong case Login, lấy được Token thì ném vào đây.
        Sau đó các lệnh test phía sau sẽ tự động có quyền truy cập mà không cần làm gì thêm.
        """
        self.session.headers.update({
            "Authorization": f"Bearer {token}"
        })
        print(f">>> [HỆ THỐNG]: Đã nhận Token từ Lead Hiếu, anh em yên tâm test tiếp.")

    def xoa_token(self):
        """ 
        [HƯỚNG DẪN]: Ông 4 dùng hàm này khi muốn test xem "Nếu không có Token thì có hack được không".
        Nó sẽ xóa sạch dấu vết đăng nhập trong Header.
        """
        if "Authorization" in self.session.headers:
            self.session.headers.pop("Authorization")
            print(">>> [HỆ THỐNG]: Đã xóa sạch Token. Đang ở chế độ ẩn danh (Unauthenticated).")

    # --- PHẦN DÀNH CHO ÔNG 5 (LÀM BÁO CÁO) ---

    def hien_thi_log(self, method, url, response):
        """
        [HƯỚNG DẪN]: Ông 5 chú ý, những gì in ra ở đây chính là bằng chứng để ông dán vào file Word.
        Nó sẽ hiện rõ: Gửi lệnh gì, API trả về mã bao nhiêu và dữ liệu là gì.
        """
        print(f"\n{'='*30} [NHẬT KÝ KIỂM THỬ] {'='*30}")
        print(f"[*] HÀNH ĐỘNG: {method} {url}")
        print(f"[*] KẾT QUẢ (Status Code): {response.status_code}")
        try:
            print("[*] DỮ LIỆU PHẢN HỒI:")
            print(json.dumps(response.json(), indent=2, ensure_ascii=False))
        except:
            print(f"[*] NỘI DUNG PHẢN HỒI: {response.text[:200]}...")
        print(f"{'='*70}\n")

    # --- BỘ MÁY XỬ LÝ CHÍNH (CẤM SỬA) ---

    def _xu_ly_yeu_cau(self, method, endpoint, **kwargs):
        """ 
        Hàm trung tâm để xử lý lỗi hệ thống (Timeout, sập Server).
        Dùng **kwargs để anh em có thể truyền thêm params hay body thoải mái.
        """
        full_url = f"{self.base_url}{endpoint}"

        try:
            # Gọi API thực tế thông qua thư viện requests
            response = self.session.request(
                method=method,
                url=full_url,
                timeout=self.timeout,
                **kwargs
            )
            # Tự động in Log mỗi khi chạy xong
            self.hien_thi_log(method, full_url, response)
            return response

        except requests.exceptions.Timeout:
            raise Exception(f"LỖI THỜI GIAN: API {full_url} chậm quá, treo máy rồi!")
        except requests.exceptions.ConnectionError:
            raise Exception(f"LỖI KẾT NỐI: Ông số 2 xem lại xem đã bật Server chưa nhé.")
        except requests.exceptions.RequestException as e:
            raise Exception(f"LỖI KHÔNG XÁC ĐỊNH: {e}")

    # --- CÁC HÀM TIỆN ÍCH CHO ANH EM ---

    def get(self, endpoint, params=None):
        """ Dùng để lấy thông tin (ví dụ: Xem danh sách user, xem profile) """
        return self._xu_ly_yeu_cau("GET", endpoint, params=params)

    def post(self, endpoint, data_json=None):
        """ Dùng để gửi dữ liệu lên (ví dụ: Đăng nhập, Đăng ký, Gửi mã độc SQLi) """
        return self._xu_ly_yeu_cau("POST", endpoint, json=data_json)

    def put(self, endpoint, data_json=None):
        """ Dùng để cập nhật dữ liệu (ví dụ: Đổi mật khẩu, sửa thông tin user) """
        return self._xu_ly_yeu_cau("PUT", endpoint, json=data_json)

    def delete(self, endpoint):
        """ Dùng để xóa dữ liệu (ví dụ: Xóa user, xóa bài viết) """
        return self._xu_ly_yeu_cau("DELETE", endpoint)

    # --- PHẦN ĐỌC DỮ LIỆU TEST ---

    @staticmethod
    def doc_file_json(duong_dan):
        """ 
        [HƯỚNG DẪN]: Ông 3, 4 chuẩn bị 20 kịch bản trong file JSON rồi gọi hàm này.
        Nó sẽ bốc toàn bộ dữ liệu ra để nạp vào máy chạy tự động.
        """
        if not os.path.exists(duong_dan):
            print(f"LỖI: Đường dẫn {duong_dan} không tồn tại. Xem lại folder data/ nhé.")
            return []

        try:
            with open(duong_dan, "r", encoding="utf-8") as f:
                data = json.load(f)
            print(f">>> Đã nạp thành công {len(data)} kịch bản từ file của anh em.")
            return data
        except Exception as e:
            print(f"LỖI ĐỊNH DẠNG: File JSON viết sai cú pháp rồi ông ơi: {e}")
            return []
