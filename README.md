# API_checkAuto_security16

Dự án kiểm thử tự động chức năng và bảo mật cho hệ thống API 
Thành viên nhóm :
  + Dương Ngọc Hiếu : (lead) Kiến trúc Framework, Core API Client, Tổng hợp báo cáo, Phát triển các chức năng Tools
  + Vũ Duy Điệp : Phát triển Target API (FastAPI) & Vulnerabilities ( dựa theo khung Framework )
  + Nguyễn Quang Đạt : Phát triển Functional Test Sctipts (CRUD operations)
  + Nguyễn Trung Duy : Phát triển Security Test Scripts ( SQLi, BOLA, Broken Auth).
  + Phạm Văn Qúy: Tài liệu kĩ thuật & Allure Report, Phân tích kết quả kịch bản kiểm thử

Cấu trúc thư mục 
  - core/ : chứa API Client dùng chung cho toàn dự án.
  - target_api/ : mã nguồn của API giả lập dùng để kiểm thử.
  - tests/ : chứa các kịch bản kiểm thử Chức năng và Bảo mật.
  - data/ : chứa dữ liệu kiểm thử (JSON/Excel).
  - reports/ " Nơi xuất báo cáo Allure sau khi thực thi .

Công nghệ sử dụng 
  - Ngôn ngữ : Python 3.x , Framework : Pytest , Thư viện : Request, Pydantic
  - Báo cáo : Allure Report

Một số note cài đặt
  - Clone dự án: https://github.com/HIEU131538/API_checkAuto_security16.git
  - Cài đặt thư viện: pip install -r requirements.txt
  - Chạy API mẫu: uvicorn target_api.api:app --reload
  - Chạy kiểm thử: pytest --alluredir=reports/
