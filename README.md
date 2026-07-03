# Marketing Report Tool 📊

Chào bạn! Đây là công cụ **Marketing Report Tool** do tôi phát triển nhằm giúp tự động hóa quá trình đối soát và tổng hợp số liệu giữa **Facebook Ads (BCFB)** và **Hệ thống CRM**. 

Phần mềm được thiết kế với giao diện đồ họa (GUI) đơn giản, trực quan và cực kỳ dễ sử dụng cho mọi người, dù bạn không có kiến thức về lập trình.

---

## ✨ Tính năng nổi bật
- **Gộp dữ liệu thông minh**: Tự động nhận diện và gộp số liệu (Số tiền chi tiêu, Kết quả) của các chiến dịch Facebook có chung Mã CRM.
- **Phân tách Content Mới & Ads Cũ**: Hỗ trợ bộ lọc theo khoảng "Ngày tạo" của chiến dịch, tự động bóc tách các chiến dịch mới tinh (không chứa chữ "Bản sao" và chưa từng chạy trước đó) sang file `File_1_CONTENT_MOI`. Các mã còn lại được đưa vào `File_2_ADS_CU`.
- **Tự động làm sạch mã CRM (Auto-Extraction)**: Cung cấp tính năng tuỳ chỉnh Tiền tố mã CRM (VD: `P, PH, K`). Nếu chiến dịch không khớp mã CRM có sẵn, Tool tự động sử dụng sức mạnh Regex để quét và cắt gọt tên chiến dịch dài ngoằng thành các mã CRM tinh gọn (tối thiểu 6 ký tự), loại bỏ toàn bộ thông tin thừa.
- **Phát hiện Ngoại lệ (Anomaly Detection)**: Nếu phát hiện một mã CRM vừa có chiến dịch cũ, lại vừa có chiến dịch mới trong khoảng thời gian đang test, hệ thống sẽ tự động cách ly nó sang một sheet riêng biệt tên là `Ma Can Kiem Tra` để bạn dễ dàng rà soát lại lỗi từ đội chạy Ads.
- **Tích hợp Link Content**: Có khả năng đọc thêm file Content tùy chọn để ghép link bài quảng cáo vào báo cáo cuối cùng.
- **Chế độ Linh hoạt**: Bạn có quyền bỏ tick bộ lọc ngày để phần mềm hoạt động ở chế độ cơ bản (xuất gộp chung thành 1 file duy nhất như trước đây).

---

## 🚀 Hướng dẫn cài đặt và sử dụng cho từng Hệ Điều Hành

### 🪟 1. Dành cho Windows (Dễ nhất)
Nếu bạn đang dùng hệ điều hành Windows, bạn **KHÔNG CẦN** cài đặt bất kỳ phần mềm lập trình nào.

1. Truy cập vào mục **Releases** ở bên phải trang Github này (hoặc mục tải xuống do người phát triển cung cấp) để tải về máy file thực thi: `report_tool.exe`.
2. Click đúp chuột vào file `report_tool.exe` để mở phần mềm.
3. Làm theo các bước trên màn hình: 
   - Chọn các file báo cáo Facebook (`.csv`). (Lưu ý: Bắt buộc chọn báo cáo cấp độ Chiến dịch/Nhóm có chứa cột `Ngày tạo`).
   - Chọn file báo cáo CRM (`.csv`).
   - Chọn file báo cáo Content (`.csv` - Tùy chọn, dùng để lấy link content).
   - Chọn thư mục xuất file.
   - Nhập các Tiền tố Mã CRM (cách nhau bởi dấu phẩy, mặc định `P, PH`).
   - (Tùy chọn) Kích hoạt bộ lọc Ngày để phân tách Content Mới / Ads Cũ.
4. Bấm **"XỬ LÝ & XUẤT BÁO CÁO"** và nhận kết quả là file Excel chỉ sau vài giây.

*(Nếu muốn chạy bằng mã nguồn Python, bạn có thể tham khảo cách của Linux/macOS bên dưới).*

---

### 🍏 2. Dành cho macOS (Macbook)
Với macOS, phần mềm sẽ chạy trực tiếp từ mã nguồn Python. Cách làm như sau:

**Bước 1: Cài đặt Python**
- Mở ứng dụng **Terminal** (Nhấn `Cmd + Space`, gõ `Terminal` và Enter).
- Kiểm tra xem máy đã có Python 3 chưa bằng lệnh: `python3 --version`.
- Nếu chưa có, hãy tải và cài đặt Python từ trang chủ [python.org](https://www.python.org/downloads/macos/).

**Bước 2: Tải Source Code & Cài thư viện**
- Tải toàn bộ source code này về máy.
- Mở Terminal, dùng lệnh `cd` để di chuyển vào thư mục chứa code. VD: 
  ```bash
  cd Downloads/mkt-report-tool
  ```
- Cài đặt các công cụ cần thiết bằng lệnh sau:
  ```bash
  pip3 install -r requirements.txt
  ```

**Bước 3: Khởi động phần mềm**
- Gõ lệnh sau vào Terminal và nhấn Enter:
  ```bash
  python3 report_tool.py
  ```
- Giao diện phần mềm sẽ hiện ra, bạn thao tác chọn file như bình thường.

---

### 🐧 3. Dành cho Linux (Ubuntu, Fedora, v.v.)
Cũng tương tự như macOS, bạn sẽ chạy trực tiếp từ mã nguồn Python.

**Bước 1: Cài đặt Python3 và pip**
- Mở **Terminal** và chạy lệnh:
  ```bash
  sudo apt update
  sudo apt install python3 python3-pip python3-tk
  ```
  *(Lưu ý: `python3-tk` là thư viện bắt buộc trên Linux để có thể hiển thị giao diện phần mềm).*

**Bước 2: Cài đặt thư viện**
- Trỏ tới thư mục chứa code:
  ```bash
  cd path/to/mkt-report-tool
  ```
- Chạy lệnh cài đặt thư viện:
  ```bash
  pip3 install -r requirements.txt
  ```

**Bước 3: Khởi động phần mềm**
- Chạy lệnh:
  ```bash
  python3 report_tool.py
  ```

---

## 👨‍💻 Hướng dẫn dành cho Developer (Lập trình viên)

Nếu bạn muốn chỉnh sửa mã nguồn và đóng gói lại thành file `.exe` mới cho Windows, hãy chạy các lệnh sau (thực hiện trên máy Windows):

```bash
# Cài đặt công cụ đóng gói
pip install pyinstaller

# Lưu ý: Babel có thể cần import ẩn để DateEntry của tkcalendar hoạt động
pyinstaller --onefile --noconsole --icon=icon.ico --hidden-import babel.numbers report_tool.py
```
File `.exe` mới sẽ được tự động tạo ra và nằm bên trong thư mục `dist/`.

---
*Chúc bạn xuất báo cáo và đối soát số liệu nhanh chóng, chính xác! Nếu thấy phần mềm hữu ích, hãy để lại 1 Star ⭐ cho kho chứa này nhé.*
