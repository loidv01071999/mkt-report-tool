# Hướng Dẫn Sử Dụng Tool Báo Cáo Marketing

Tool Báo Cáo Marketing đã được phát triển và đóng gói hoàn thiện. Dưới đây là kết quả và hướng dẫn sử dụng chi tiết dành cho bạn.

## 1. Hướng dẫn sử dụng

1. **Khởi động:** Click đúp vào file `report_tool.exe` để mở giao diện.
2. **Giao diện App:** Màn hình của App sẽ hiện ra gồm 3 bước đơn giản:
   - **Bước 1 (Chọn file BCFB):** Bấm nút và chọn 1 hoặc nhiều file báo cáo Facebook (ví dụ các file CSV của từng ngày hoặc từng chiến dịch). Bạn có thể giữ Ctrl (hoặc kéo chuột) để chọn nhiều file cùng lúc.
   - **Bước 2 (Chọn file CRM):** Bấm nút và trỏ đến file báo cáo CRM (.csv) mới nhất của bạn.
   - **Bước 3 (Thư mục lưu):** Chọn thư mục mà bạn muốn xuất báo cáo kết quả ra đó.
3. **Chạy Báo Cáo:** 
   - Nhấn nút xanh lá cây **"XỬ LÝ & XUẤT BÁO CÁO"**.
   - Chờ trong giây lát, ứng dụng sẽ có thông báo **"Đã xuất báo cáo thành công"**.

## 2. Logic xử lý

Chức năng tool:
- **Tự động cộng dồn (Sum)**: Nếu 1 Mã trong CRM khớp với nhiều Tên chiến dịch bên BCFB, Tool sẽ tự động tính tổng Số tiền và Kết quả của tất cả các chiến dịch đó.
- **Tự động đẩy cuối file**: Nếu có những chiến dịch bên BCFB không match với bất kỳ mã nào của CRM, chúng sẽ được chèn tự động ở cuối file Excel output, giữ nguyên giá trị để bạn dễ đối soát.
- **Giữ vị trí gốc**: Các mã CRM chưa chạy BCFB vẫn sẽ giữ nguyên thứ tự ban đầu trong danh sách, chỉ hiện thị `Số contact` tương ứng trong CRM.
- **Tính MAX**: Cột `Số contact` ở Output đã được tự động lấy giá trị cao nhất (MAX) giữa `Số contact` của CRM và `Kết quả` từ Facebook trả về.

*Chúc bạn xuất báo cáo và đối soát hiệu quả!*
