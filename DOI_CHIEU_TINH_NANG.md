# Đối chiếu chức năng và danh sách chạy thử

Tài liệu ghi nhận chức năng từ mã nguồn, không thay thế biên bản kiểm thử thực tế.

| Nhóm | Chức năng được giữ | Kiểm tra trên máy thử nghiệm |
|---|---|---|
| Đăng nhập | Kiểm tra tài khoản/mật khẩu | Đúng/sai thông tin đăng nhập |
| Phiên làm việc | Ghi nhớ qua query token; đăng xuất xóa query | Đăng nhập lại và đăng xuất |
| Khởi tạo | Tạo ba hồ sơ khi CSV chưa tồn tại | Chạy thư mục chưa có CSV |
| Khách hàng | Tìm theo mã/tên, tạo mới, nạp hồ sơ cũ | Chọn hai khách hàng liên tiếp |
| Trạm biến áp | Chọn trạm cũ hoặc tạo mã/tên mới | Mã trạm có số 0 ở đầu |
| Hồ sơ | Mã/tên KH, số công tơ, vị trí treo, số trụ, địa chỉ | Đủ các trường sau lưu |
| Ảnh | Hai bộ tải ảnh JPG/JPEG/PNG và xem trước | Ảnh trụ, ảnh mặt, một ảnh và hai ảnh |
| Xử lý ảnh | Thu nhỏ 1024 px, JPEG 85, mã hóa Base64 | Đọc lại ảnh đã lưu |
| Tọa độ | EXIF ưu tiên, OCR dự phòng | Ảnh GPS, ảnh đóng dấu tọa độ, ảnh không GPS |
| Địa chỉ | Tra địa chỉ theo tọa độ; giữ địa chỉ cũ khi tra không được | Có mạng và mất mạng |
| Tên trạm | Bổ sung xã/tỉnh khi tạo mới và tra được địa chỉ | Tạo trạm mới |
| Kiểm tra đầu vào | Bắt buộc mã/tên KH, trạm, tối thiểu một ảnh | Bỏ trống từng mục |
| Ghi đè | Yêu cầu tích xác nhận; thay dòng cùng mã KH | Kiểm tra không sinh dòng trùng |
| Lưu | CSV gồm tọa độ, ảnh, nguồn và thời gian | Mở lại ứng dụng sau lưu |
| Bản đồ | Tìm KH với khóa widget ổn định; định vị và toàn cảnh | Tìm và đổi khách hàng |
| Cụm điểm | MarkerCluster | Thu/phóng bản đồ |
| Marker | Ảnh mặt công tơ hoặc biểu tượng | Chuyển hai kiểu hiển thị |
| Popup | Đủ thông tin trạm, KH, công tơ, địa chỉ, tọa độ, trụ | Đối chiếu CSV |
| Xem ảnh | Hai ảnh và phóng to/thu lại | Bấm từng ảnh trong popup |
| Chỉ đường | Google Maps đến tọa độ công tơ | Mở liên kết trên thiết bị |
| Bảng dữ liệu | Hiển thị dữ liệu, ẩn Base64 | So sánh số dòng CSV |
| Xuất | CSV UTF-8 BOM mở trong Excel | Tiếng Việt và mã định danh |

## Điều chỉnh hỗ trợ dữ liệu

- Đọc các mã định danh dưới dạng chuỗi để giữ số 0 đầu mã trạm, số công tơ.
- Tọa độ được chuyển riêng sang số; hồ sơ tọa độ không hợp lệ được thông báo và bỏ qua trên bản đồ, vẫn giữ trong CSV/bảng dữ liệu.
- Chỉ tải mô hình OCR khi thật sự cần OCR.
- Escape trường văn bản trước khi đưa vào HTML popup.
- Không tải ảnh logo trên mạng để tạo dữ liệu giả, giúp ứng dụng khởi tạo khi chưa có mạng.

Mã gốc được lưu nguyên bản trong `ma_nguon_goc.txt` để đối chiếu đầy đủ.
