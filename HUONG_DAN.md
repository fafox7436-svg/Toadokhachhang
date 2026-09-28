# EVNSPC – Giao diện quản lý điểm đo

Bản nâng cấp giao diện từ mã được cung cấp ngày 28/09/2026. Giữ nền tảng Streamlit và các luồng nghiệp vụ đang có. Đây là bản mã nguồn cần chạy thử trong môi trường đơn vị, chưa phải bản nghiệm thu triển khai chính thức.

## Cài đặt và chạy

Dùng Python 3.11 hoặc 3.12. Giải nén, mở terminal tại thư mục `evnspc_pro`, thực hiện:

```bash
python -m venv .venv
```

Windows:

```powershell
.venv\Scripts\activate
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Linux/macOS:

```bash
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Danh sách thư viện là khoảng phiên bản đề xuất, chưa phải bộ phiên bản đã kiểm thử tích hợp. EasyOCR sẽ tải mô hình khi sử dụng OCR lần đầu; cần có kết nối phù hợp hoặc chuẩn bị mô hình trước.

## Dữ liệu và nhận diện

- Sao lưu CSV hiện có trước khi dùng. Đặt `database_congto_v8.csv` cạnh `app.py` để tiếp tục sử dụng dữ liệu cũ; không đổi tên cột.
- Khi không có CSV, ứng dụng tạo ba hồ sơ mẫu giống mã gốc, không gắn logo giả làm ảnh hiện trường.
- Đặt logo chính thức do đơn vị cung cấp tại `assets/evn_logo.png`. Nếu chưa có, thanh điều hướng hiển thị chữ EVNSPC. Bản này không tự vẽ lại logo hay khẳng định tuân thủ bộ quy chuẩn nhận diện chưa được cung cấp.
- Đăng nhập thử vẫn sử dụng tài khoản và cơ chế ghi nhớ trong mã gốc. Không đưa bản này lên môi trường chính thức với cơ chế đăng nhập hiện tại.

## Nâng cấp giao diện

- Tông xanh đậm, trắng và điểm nhấn đỏ; chữ và nhãn theo phong cách hành chính, hạn chế viết hoa.
- Bộ biểu tượng SVG đồng nhất, không phụ thuộc máy chủ icon bên ngoài.
- Header theo từng màn hình, thẻ thống kê tính trực tiếp từ CSV, ba bước nhập hồ sơ.
- Khung ảnh trụ điện và mặt công tơ; bố cục thích ứng màn hình hẹp.
- Hiệu ứng xuất hiện 300 ms, trạng thái hover 160 ms; hỗ trợ thiết bị yêu cầu giảm chuyển động.
- Điểm đánh dấu bản đồ mặc định dùng icon công tơ; vẫn chọn được ảnh công tơ như bản cũ.
- Popup bản đồ rõ ràng hơn, ảnh giữ tỷ lệ, vẫn có phóng to và liên kết chỉ đường.
- Bỏ hiệu ứng bóng bay; thay bằng thông báo lưu phù hợp công việc.

## Những điểm chưa có trong mã gốc

1. Google Sheets: chỉ có biến URL mẫu; không có lệnh gửi dữ liệu. Bản nâng cấp ghi đúng trạng thái lưu CSV cục bộ.
2. “Xem sản lượng”: chỉ là khối HTML, không có sự kiện hay nguồn dữ liệu. Bản nâng cấp đổi thành tiêu đề “Thông tin điểm đo”; không có chức năng sản lượng nào bị loại bỏ.
3. Xuất Excel: mã gốc chỉ xuất CSV. Bản nâng cấp ghi rõ “CSV (mở bằng Excel)”, không giả định đã có XLSX.
4. Bản đồ chỉ thể hiện các vị trí, không có đường dây hoặc cấu trúc đấu nối; đổi tiêu đề “sơ đồ đơn tuyến” thành “bản đồ điểm đo”.

## Giới hạn cần xử lý khi đưa vào vận hành

- Tài khoản/mật khẩu và token ghi nhớ đang ghi trực tiếp trong mã, token đi qua URL. Cần thay bằng cơ chế xác thực của đơn vị, phân quyền và quản lý phiên trước triển khai.
- CSV chưa xử lý xung đột ghi đồng thời của nhiều người dùng; chưa có nhật ký thao tác hay cơ chế sao lưu tự động.
- Bản đồ nền, tra địa chỉ OpenStreetMap và chỉ đường Google Maps cần mạng. Tra địa chỉ sẽ gửi tọa độ đến dịch vụ bên ngoài như mã gốc.
- OCR vẫn dùng quy tắc nhận dạng của bản gốc, không bảo đảm đọc được mọi định dạng tọa độ; cần kiểm tra bằng ảnh thực tế.
- Khi cập nhật chỉ cung cấp một ảnh, cột ảnh còn lại bị để trống như hành vi gốc. Nên lưu đủ hai ảnh nếu cần giữ hồ sơ đầy đủ.

## Kết quả kiểm tra

Đã kiểm tra biên dịch cú pháp Python, đối chiếu đủ các hàm nghiệp vụ và trường dữ liệu với bản gốc; kiểm tra đọc CSV bảo toàn số 0 đầu mã trạm. Môi trường thực hiện chưa có Streamlit, Folium, OpenCV và EasyOCR, vì vậy chưa chạy giao diện thực tế, OCR, dịch vụ tra địa chỉ hoặc kiểm thử đầu cuối. Cần xác nhận các mục trong `DOI_CHIEU_TINH_NANG.md` trên máy thử nghiệm trước sử dụng.
