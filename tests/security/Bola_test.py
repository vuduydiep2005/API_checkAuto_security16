import requests
import re
from security_function import SecurityFunction


url = "http://127.0.0.1:8000"
open_api = "http://127.0.0.1:8000/openapi.json"

login_admin = {
    "username":"admin",
    "password":"password"
}

#Yeu cau tao user truoc, vi sqllite chay tren ram nen la moi lan tat server se mat het du lieu
login_user_1 = {
    "username":"duynt",
    "password":"duynt"
}

class MyTester(SecurityFunction):

    
    #hpp là http parameter pollution thêm các tham số rác trên request để backend lỗi
    #mục tiêu là để server đọc 1 tham số và truy vấn 1 tham số khác
    #Ví dụ: 101?user_id=104 -> Lúc đầu đọc thấy id 101 ok chuẩn với token xong thấy id 104 ok truy vấn data của id 104 --> bola thành công 
    def BOLA_hpp(self):
        data_test = self.doc_file_json("data/test_data.json")
        lo_hong = False
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
                                    lo_hong = True
                                else:
                                    print("Failed! Can't access the target_id ")
                            else:
                                print("Failed! System is against bola with hpp method")
                        except Exception as e:
                            print(f"Loi roi {e}")
        return lo_hong



    def BOLA_classic(self):
        data_test = self.doc_file_json("data/test_data.json")
        lo_hong = False
        for part in data_test:
            if part["id"] != 13:
                continue

            test_case = part["payloads"]
            token_u1 = self.login(login_user_1)
            for case in test_case:
                target_id = case["target_id"]
                my_id = case["my_id"]
                print(f"Dang test {case['description']}")


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
                                    lo_hong = True
                                else:
                                    print("Failed! System is immune to bola with classic way")
                            else:
                                print("Failed! System is immune to bola with classic way")
                        except Exception as e:
                            print(f"Co loi {e}")
        return lo_hong



def test_bola_hpp():
    print("Testing kịch bản Bola hpp")
    tool = MyTester(url)
    res = tool.BOLA_hpp()

    assert res,"API không có lỗ hổng Bola HPP"

def test_bola_classic():
    print("Testing kịch bản bola classic")
    tool = MyTester(url)
    res = tool.BOLA_classic()

    assert res,"API không có lỗ hổng BOLA"
    
    
