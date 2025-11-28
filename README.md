# HỆ THỐNG ĐIỂM DANH HỌC SINH BẰNG NHẬN DIỆN KHUÔN MẶT "FACE-ID"

## 📋 TỔNG QUAN DỰ ÁN

Hệ thống điểm danh học sinh THCS sử dụng công nghệ nhận diện khuôn mặt (Face Recognition) AI để tự động hóa quy trình điểm danh, giúp tiết kiệm thời gian, tăng tính chính xác và hiện đại hóa quản lý giáo dục.

## 🎯 CHỨC NĂNG CHÍNH

### 1. 🎥 Module Nhận Diện Khuôn Mặt & Điểm Danh
**Chức năng cốt lõi:**
- ✅ Nhận diện khuôn mặt học sinh qua camera thời gian thực
- ✅ Hiển thị thông tin học sinh ngay lập tức (Họ tên, Lớp, Ảnh, Trạng thái)
- ✅ Tự động lưu kết quả điểm danh với timestamp chính xác
- ✅ Cảnh báo học sinh không nhận diện được hoặc chưa đăng ký
- ✅ Hiển thị độ tin cậy nhận diện (confidence score)
- ✅ Ngăn chặn điểm danh trùng lặp trong cùng buổi học

**Quy tắc nghiệp vụ:**
- Mỗi học sinh chỉ điểm danh 1 lần/buổi (sáng/chiều)
- Độ tin cậy tối thiểu: 80% để xác nhận
- Lưu ảnh chụp tại thời điểm điểm danh để kiểm tra
- Tự động đánh dấu "Vắng" cho học sinh chưa điểm danh sau giờ quy định

---

### 2. 📚 Module Quản Lý Niên Khóa
**Chức năng:**
- ✅ Thêm niên khóa mới (VD: 2024-2025, 2025-2026)
- ✅ Chỉnh sửa thông tin niên khóa (ngày bắt đầu, kết thúc)
- ✅ Kích hoạt/Vô hiệu hóa niên khóa
- ✅ Chỉ có 1 niên khóa đang hoạt động tại một thời điểm
- ✅ Xem danh sách tất cả niên khóa
- ✅ **Không cho phép xóa** niên khóa đã có dữ liệu lớp học hoặc điểm danh

**Quy tắc nghiệp vụ:**
- Niên khóa có định dạng: "YYYY-YYYY" (VD: 2024-2025)
- Ngày kết thúc phải sau ngày bắt đầu
- Khi chuyển niên khóa mới, hệ thống tự động lưu trữ dữ liệu cũ
- Chỉ admin mới có quyền thêm/sửa/xóa niên khóa

---

### 3. 🏫 Module Quản Lý Lớp Học
**Chức năng:**
- ✅ Thêm lớp học mới (6A1, 7B2, 8C3, 9A1)
- ✅ Chỉnh sửa thông tin lớp (tên lớp, GVCN, phòng học)
- ✅ Gán lớp học vào niên khóa cụ thể
- ✅ Chuyển lớp sang niên khóa mới (lên lớp hàng năm)
- ✅ Xem danh sách lớp học theo niên khóa
- ✅ Xem danh sách học sinh trong lớp
- ✅ Thống kê số lượng học sinh hiện tại
- ✅ **Không cho phép xóa** lớp đã có học sinh hoặc dữ liệu điểm danh

**Quy tắc nghiệp vụ:**
- Tên lớp không trùng lặp trong cùng niên khóa
- Mỗi lớp phải thuộc 1 khối (6, 7, 8, 9)
- Mỗi lớp có 1 GVCN
- Số lượng học sinh tối đa: 45 học sinh/lớp

---

### 4. 👨‍🎓 Module Quản Lý Học Sinh
**Chức năng:**
- ✅ Thêm học sinh mới (thủ công hoặc import Excel)
- ✅ Chỉnh sửa thông tin cá nhân (Họ tên, Mã số, Giới tính, Ngày sinh, Địa chỉ)
- ✅ Phân công học sinh vào lớp học
- ✅ Chuyển lớp học sinh (trong niên khóa hoặc lên lớp)
- ✅ **Upload ảnh khuôn mặt** (3-5 ảnh/học sinh)
- ✅ Xem trước danh sách ảnh đã upload
- ✅ Xóa ảnh khuôn mặt không phù hợp
- ✅ Tự động train/update model khi có ảnh mới
- ✅ Xem lịch sử điểm danh của học sinh
- ✅ Xuất danh sách học sinh ra Excel
- ✅ **Vô hiệu hóa** học sinh (nghỉ học, chuyển trường) thay vì xóa

**Quy tắc nghiệp vụ:**
- Mã học sinh là duy nhất (unique), không trùng lặp
- Mỗi học sinh chỉ thuộc 1 lớp tại một thời điểm
- Yêu cầu ít nhất 3 ảnh khuôn mặt để kích hoạt điểm danh
- Ảnh phải đạt chất lượng (rõ nét, đủ sáng, nhìn thẳng)
- Không cho phép xóa học sinh đã có dữ liệu điểm danh (chỉ vô hiệu hóa)

**Upload ảnh khuôn mặt:**
- Định dạng: JPG, PNG
- Kích thước tối đa: 5MB/ảnh
- Số lượng: 3-5 ảnh (tối ưu 5 ảnh)
- Góc chụp: Thẳng, nghiêng trái 15°, nghiêng phải 15°, hơi ngẩng, hơi cúi
- Hệ thống tự động detect face và crop

---

### 5. 📊 Module Xem & Quản Lý Kết Quả Điểm Danh
**Chức năng:**
- ✅ Xem điểm danh theo lớp học và ngày cụ thể
- ✅ Xem điểm danh theo khoảng thời gian (tuần, tháng)
- ✅ Hiển thị danh sách học sinh: Có mặt / Vắng / Muộn / Có phép
- ✅ Hiển thị thời gian điểm danh chi tiết (giờ:phút:giây)
- ✅ Hiển thị ảnh chụp tại thời điểm điểm danh
- ✅ **Chỉnh sửa thủ công** kết quả điểm danh (nếu có sai sót)
- ✅ Thêm ghi chú cho từng lần điểm danh
- ✅ Xuất báo cáo Excel theo ngày/tuần/tháng
- ✅ Tìm kiếm học sinh theo tên, mã số
- ✅ Lọc theo trạng thái (Có mặt, Vắng, Muộn)

**Quy tắc nghiệp vụ:**
- Chỉ giáo viên chủ nhiệm và admin mới chỉnh sửa được điểm danh
- Mọi chỉnh sửa đều được log lại (ai sửa, sửa gì, khi nào)
- Không cho phép xóa lịch sử điểm danh (chỉ chỉnh sửa)
- Báo cáo Excel bao gồm: Tên, Mã số, Lớp, Ngày, Giờ, Trạng thái

---

### 6. 📈 Module Thống Kê & Báo Cáo
**Chức năng:**
- ✅ Thống kê tỷ lệ đi học theo lớp (theo ngày, tuần, tháng, học kỳ)
- ✅ Thống kê tỷ lệ đi học theo từng học sinh
- ✅ Biểu đồ tỷ lệ điểm danh (Line chart, Bar chart)
- ✅ Top 10 học sinh chuyên cần nhất
- ✅ Danh sách học sinh hay vắng (>3 lần/tuần)
- ✅ So sánh tỷ lệ điểm danh giữa các lớp
- ✅ Báo cáo tổng hợp theo niên khóa
- ✅ Xuất báo cáo PDF/Excel chi tiết

**Quy tắc nghiệp vụ:**
- Công thức tỷ lệ đi học: (Số buổi có mặt / Tổng số buổi học) × 100%
- Học sinh được xếp loại: Chuyên cần (≥95%), Đạt (≥90%), Cảnh báo (<90%)
- Báo cáo được tạo tự động vào cuối mỗi tuần/tháng

---

### 7. 🔐 Module Quản Trị Hệ Thống & Bảo Mật
**Chức năng:**
- ✅ Đăng nhập bảo mật (JWT Authentication)
- ✅ Đăng xuất và xóa session
- ✅ Phân quyền người dùng: Admin, Giáo viên, Nhân viên
- ✅ Quản lý tài khoản (Thêm/Sửa/Vô hiệu hóa)
- ✅ Đổi mật khẩu (bắt buộc hash)
- ✅ Log hoạt động hệ thống
- ✅ Backup/Restore database

**Phân quyền:**
| Chức năng               | Admin   | Giáo viên               |
|-------------------------|---------|-------------------------|
| Quản lý niên khóa       |   ✅    |           ❌            |
| Quản lý lớp học         |   ✅    | ✅ (lớp mình phụ trách) |
| Quản lý học sinh        |   ✅    |     ✅ (lớp mình)       |
| Upload ảnh khuôn mặt    |   ✅    |           ✅            |
| Điểm danh               |   ✅    |           ✅            |
| Xem kết quả             |   ✅    |     ✅ (lớp mình)       |
| Chỉnh sửa điểm danh     |   ✅    |     ✅ (lớp mình)       |
| Thống kê                |   ✅    |     ✅ (lớp mình)       |
| Quản lý user            |   ✅    |           ❌            |


**Quy tắc bảo mật:**
- Mật khẩu tối thiểu 8 ký tự, hash bằng bcrypt
- Session timeout: 8 giờ
- JWT token refresh mỗi 1 giờ
- Log mọi thao tác nhạy cảm (thêm/sửa/xóa)
- Giới hạn số lần đăng nhập sai: 5 lần (lock 15 phút)
