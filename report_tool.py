import customtkinter as ctk
from tkinter import filedialog, messagebox
import os
import pandas as pd
import datetime
from tkcalendar import DateEntry

# --- CONFIG ---
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

def process_reports(bcfb_files, crm_file, content_file, output_dir, start_date="", end_date="", crm_prefixes=None):
    if crm_prefixes is None:
        crm_prefixes = ["P", "PH"]
        
    try:
        # 1. Đọc và gộp các file BCFB
        bcfb_dfs = []
        for file in bcfb_files:
            try:
                try:
                    df = pd.read_csv(file, encoding='utf-8')
                except UnicodeDecodeError:
                    df = pd.read_csv(file, encoding='utf-16')
                
                # Hỗ trợ linh hoạt các cột Tên chiến dịch hoặc Tên nhóm quảng cáo
                name_col = None
                for possible_name in ["Tên chiến dịch", "Tên nhóm quảng cáo", "Tên quảng cáo"]:
                    if possible_name in df.columns:
                        name_col = possible_name
                        break
                
                if not name_col:
                    raise ValueError(f"File '{os.path.basename(file)}' thiếu cột Tên chiến dịch/Tên nhóm quảng cáo.")
                
                # Đổi tên cột về chuẩn chung để xử lý
                df = df.rename(columns={name_col: "Tên chiến dịch"})
                
                cols = ["Tên chiến dịch", "Kết quả", "Số tiền đã chi tiêu (VND)", "Ngày tạo"]
                missing_cols = [c for c in cols if c not in df.columns]
                if missing_cols:
                    raise ValueError(f"File '{os.path.basename(file)}' thiếu các cột (bạn cần xuất báo cáo Chiến dịch/Nhóm có chứa Ngày tạo): {', '.join(missing_cols)}")
                
                df = df[cols].copy()
                bcfb_dfs.append(df)
            except Exception as e:
                raise Exception(f"Lỗi khi đọc file BCFB '{os.path.basename(file)}': {str(e)}")
        
        if not bcfb_dfs:
            raise ValueError("Chưa có dữ liệu BCFB.")
            
        bcfb_full = pd.concat(bcfb_dfs, ignore_index=True)
        
        # Clean numeric columns - sử dụng Regex để giữ lại số và dấu trừ
        for col in ['Kết quả', 'Số tiền đã chi tiêu (VND)']:
            if bcfb_full[col].dtype == 'object':
                bcfb_full[col] = bcfb_full[col].astype(str).str.replace(r'[^\d-]', '', regex=True)
            bcfb_full[col] = pd.to_numeric(bcfb_full[col], errors='coerce').fillna(0)
        
        # Lọc bỏ các record có Số tiền đã chi tiêu (VND) = 0
        bcfb_full = bcfb_full[bcfb_full['Số tiền đã chi tiêu (VND)'] != 0]
        
        # Convert Ngày tạo to datetime.date
        bcfb_full['Ngày tạo'] = pd.to_datetime(bcfb_full['Ngày tạo'], format='%Y-%m-%d', errors='coerce').dt.date
        
        # Gom nhóm theo Tên chiến dịch
        bcfb_grouped = bcfb_full.groupby('Tên chiến dịch', as_index=False).agg({
            'Kết quả': 'sum',
            'Số tiền đã chi tiêu (VND)': 'sum',
            'Ngày tạo': 'first'
        })
        
        # 2. Đọc file CRM
        try:
            try:
                crm_df = pd.read_csv(crm_file, encoding='utf-8')
            except UnicodeDecodeError:
                crm_df = pd.read_csv(crm_file, encoding='utf-16')
        except Exception as e:
            raise Exception(f"Lỗi khi đọc file CRM: {str(e)}")
            
        crm_cols = ["Mã", "Số contact"]
        missing_crm_cols = [c for c in crm_cols if c not in crm_df.columns]
        if missing_crm_cols:
            raise ValueError(f"File CRM thiếu các cột: {', '.join(missing_crm_cols)}")
            
        for col in ['Số contact', 'Số đơn', 'DT khởi tạo']:
            if col in crm_df.columns:
                if crm_df[col].dtype == 'object':
                    crm_df[col] = crm_df[col].astype(str).str.replace(r'[^\d-]', '', regex=True)
                crm_df[col] = pd.to_numeric(crm_df[col], errors='coerce').fillna(0)
        
        # Đọc file Content (nếu có)
        content_dict = {}
        if content_file:
            try:
                try:
                    content_df = pd.read_csv(content_file, encoding='utf-8')
                except UnicodeDecodeError:
                    content_df = pd.read_csv(content_file, encoding='utf-16', errors='replace')
                except Exception:
                    content_df = pd.read_csv(content_file, encoding='latin1')
                
                # Bỏ qua kiểm tra tên cột do file csv có thể bị lỗi font chữ (VD: M CONTENT)
                # Lấy trực tiếp cột 1 làm Mã Content, cột 2 làm Link Content
                if len(content_df.columns) >= 2:
                    col1, col2 = content_df.columns[0], content_df.columns[1]
                    for _, row in content_df.iterrows():
                        ma_c = str(row[col1]).strip()
                        link_c = str(row[col2]).strip()
                        if ma_c and ma_c.lower() != 'nan':
                            content_dict[ma_c] = link_c if link_c.lower() != 'nan' else ""
            except Exception as e:
                raise Exception(f"Lỗi khi đọc file Content: {str(e)}")
                
        # 3. Mapping thông minh (Ưu tiên chuỗi Mã dài nhất nếu có nhiều Mã trùng lặp)
        crm_codes = []
        for idx, row in crm_df.iterrows():
            ma = str(row['Mã']).strip()
            crm_codes.append(ma)
        crm_df['Mã'] = crm_codes
        
        mapped_campaigns = {ma: [] for ma in crm_codes}
        unmatched_campaigns = []
        
        for _, camp_row in bcfb_grouped.iterrows():
            camp_name = str(camp_row['Tên chiến dịch'])
            
            matches = [ma for ma in crm_codes if ma in camp_name]
            
            if matches:
                # Chọn mã dài nhất để map (VD: PHYNV212YNC454L8i2 sẽ ưu tiên hơn PHYNV212YNC454L8)
                best_match = max(matches, key=len)
                mapped_campaigns[best_match].append(camp_row)
            else:
                unmatched_campaigns.append(camp_row)
                
        # Parse Dates
        start_dt = None
        end_dt = None
        if start_date and end_date:
            try:
                start_dt = datetime.datetime.strptime(start_date, "%d_%m_%Y").date()
                end_dt = datetime.datetime.strptime(end_date, "%d_%m_%Y").date()
            except Exception:
                pass
                
        output_new = []
        output_old = []
        output_anomaly = []
        
        for idx, row in crm_df.iterrows():
            ma = row['Mã']
            crm_contact = row['Số contact']
            
            camps = mapped_campaigns[ma]
            
            sum_ket_qua = sum([c['Kết quả'] for c in camps])
            sum_so_tien = sum([c['Số tiền đã chi tiêu (VND)'] for c in camps])
            max_contact = max(crm_contact, sum_ket_qua)
            
            row_dict = {
                "Mã": ma,
                "Số contact": max_contact,
                "Số đơn": row.get('Số đơn', 0),
                "DT khởi tạo": row.get('DT khởi tạo', 0),
                "Số tiền đã chi tiêu (VND)": sum_so_tien,
                "Link content": content_dict.get(ma, "")
            }
            
            has_new_valid = False
            has_old = False
            
            if start_dt and end_dt:
                for c in camps:
                    c_date = c['Ngày tạo']
                    c_name = str(c['Tên chiến dịch'])
                    if pd.notnull(c_date):
                        if c_date < start_dt:
                            has_old = True
                        elif start_dt <= c_date <= end_dt and "bản sao" not in c_name.lower():
                            has_new_valid = True
            
            if has_new_valid and not has_old:
                output_new.append(row_dict)
            elif has_new_valid and has_old:
                output_old.append(row_dict)
                output_anomaly.append(row_dict)
            else:
                output_old.append(row_dict)
                
        # Helper function to clean campaign name
        import re
        
        # Sắp xếp tiền tố theo chiều dài giảm dần để ưu tiên match tiền tố dài trước (VD: PH trước P)
        sorted_prefixes = sorted(crm_prefixes, key=len, reverse=True)
        escaped_prefixes = [re.escape(p) for p in sorted_prefixes]
        prefix_pattern = "|".join(escaped_prefixes)
        
        # Chuỗi Regex động dựa trên mảng tiền tố
        regex_str = rf'(?:^|[^A-Za-z0-9])(({prefix_pattern})[A-Z0-9]+[a-z0-9]*)(?:[^A-Za-z0-9]|$)'
        
        def extract_crm_code(name):
            m = re.search(regex_str, str(name))
            if m:
                extracted = m.group(1)
                if len(extracted) >= 6:
                    return extracted
            return name

        # 4. Các chiến dịch chưa được match trong BCFB
        unmatched_grouped = {}
        for camp_row in unmatched_campaigns:
            clean_code = extract_crm_code(camp_row['Tên chiến dịch'])
            if clean_code not in unmatched_grouped:
                unmatched_grouped[clean_code] = []
            unmatched_grouped[clean_code].append(camp_row)
            
        for clean_code, camps in unmatched_grouped.items():
            sum_ket_qua = sum([c['Kết quả'] for c in camps])
            sum_so_tien = sum([c['Số tiền đã chi tiêu (VND)'] for c in camps])
            
            row_dict = {
                "Mã": clean_code,
                "Số contact": sum_ket_qua,
                "Số đơn": 0,
                "DT khởi tạo": 0,
                "Số tiền đã chi tiêu (VND)": sum_so_tien,
                "Link content": content_dict.get(clean_code, "")
            }
            
            has_new_valid = False
            has_old = False
            
            if start_dt and end_dt:
                for c in camps:
                    c_date = c['Ngày tạo']
                    c_name = str(c['Tên chiến dịch'])
                    if pd.notnull(c_date):
                        if c_date < start_dt:
                            has_old = True
                        elif start_dt <= c_date <= end_dt and "bản sao" not in c_name.lower():
                            has_new_valid = True
                            
            if has_new_valid and not has_old:
                output_new.append(row_dict)
            elif has_new_valid and has_old:
                output_old.append(row_dict)
                output_anomaly.append(row_dict)
            else:
                output_old.append(row_dict)
                
        # 5. Xuất Excel
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        date_str = ""
        if start_date or end_date:
            s = start_date if start_date else "..."
            e = end_date if end_date else "..."
            date_str = f"_Từ_{s}_Đến_{e}"
            
        msgs = []
        if start_dt and end_dt:
            # Chế độ tách 2 file (Content Mới và Ads Cũ)
            if output_new:
                df_new = pd.DataFrame(output_new)
                path_new = os.path.join(output_dir, f"File_1_CONTENT_MOI{date_str}_{timestamp}.xlsx")
                df_new.to_excel(path_new, index=False)
                msgs.append(f"- {path_new}")
                
            path_old = os.path.join(output_dir, f"File_2_ADS_CU{date_str}_{timestamp}.xlsx")
            with pd.ExcelWriter(path_old, engine='openpyxl') as writer:
                df_old = pd.DataFrame(output_old) if output_old else pd.DataFrame(columns=["Mã", "Số contact", "Số đơn", "DT khởi tạo", "Số tiền đã chi tiêu (VND)", "Link content"])
                df_old.to_excel(writer, sheet_name="ADS CU", index=False)
                
                if output_anomaly:
                    df_anomaly = pd.DataFrame(output_anomaly)
                    df_anomaly.to_excel(writer, sheet_name="Ma Can Kiem Tra", index=False)
            msgs.append(f"- {path_old}")
        else:
            # Chế độ bình thường (không kích hoạt lọc)
            path_regular = os.path.join(output_dir, f"Bao_Cao_Marketing_{timestamp}.xlsx")
            df_regular = pd.DataFrame(output_old) if output_old else pd.DataFrame(columns=["Mã", "Số contact", "Số đơn", "DT khởi tạo", "Số tiền đã chi tiêu (VND)", "Link content"])
            df_regular.to_excel(path_regular, index=False)
            msgs.append(f"- {path_regular}")
        
        return True, "\n".join(msgs)
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return False, str(e)


class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Tool Báo Cáo Marketing")
        self.geometry("700x650")
        
        self.bcfb_files = []
        self.crm_file = ""
        self.content_file = ""
        self.output_dir = ""

        self.title_label = ctk.CTkLabel(self, text="TỔNG HỢP BÁO CÁO MARKETING", font=ctk.CTkFont(size=20, weight="bold"))
        self.title_label.pack(pady=20)

        self.input_frame = ctk.CTkFrame(self)
        self.input_frame.pack(pady=10, padx=20, fill="both", expand=True)

        # BCFB Input
        self.bcfb_btn = ctk.CTkButton(self.input_frame, text="1. Chọn các file BCFB (.csv)", command=self.select_bcfb)
        self.bcfb_btn.grid(row=0, column=0, padx=20, pady=15, sticky="w")
        self.bcfb_lbl = ctk.CTkLabel(self.input_frame, text="Chưa chọn file nào", text_color="gray")
        self.bcfb_lbl.grid(row=0, column=1, padx=20, pady=15, sticky="w")

        # CRM Input
        self.crm_btn = ctk.CTkButton(self.input_frame, text="2. Chọn file CRM (.csv)", command=self.select_crm)
        self.crm_btn.grid(row=1, column=0, padx=20, pady=15, sticky="w")
        self.crm_lbl = ctk.CTkLabel(self.input_frame, text="Chưa chọn file nào", text_color="gray")
        self.crm_lbl.grid(row=1, column=1, padx=20, pady=15, sticky="w")

        # Content Input
        self.content_btn = ctk.CTkButton(self.input_frame, text="3. Chọn file Content (.csv) (Tuỳ chọn)", command=self.select_content)
        self.content_btn.grid(row=2, column=0, padx=20, pady=15, sticky="w")
        self.content_lbl = ctk.CTkLabel(self.input_frame, text="Chưa chọn file nào", text_color="gray")
        self.content_lbl.grid(row=2, column=1, padx=20, pady=15, sticky="w")

        # Output Dir
        self.out_btn = ctk.CTkButton(self.input_frame, text="4. Chọn thư mục lưu Output", command=self.select_output)
        self.out_btn.grid(row=3, column=0, padx=20, pady=15, sticky="w")
        self.out_lbl = ctk.CTkLabel(self.input_frame, text="Chưa chọn thư mục", text_color="gray")
        self.out_lbl.grid(row=3, column=1, padx=20, pady=15, sticky="w")
        
        # Prefixes Input
        self.prefix_lbl = ctk.CTkLabel(self.input_frame, text="Ký hiệu đầu của Mã CRM (cách nhau bởi dấu phẩy):")
        self.prefix_lbl.grid(row=4, column=0, padx=20, pady=15, sticky="w")
        self.prefix_var = ctk.StringVar(value="P, PH")
        self.prefix_entry = ctk.CTkEntry(self.input_frame, textvariable=self.prefix_var, width=200)
        self.prefix_entry.grid(row=4, column=1, padx=20, pady=15, sticky="w")

        # Date Frame
        self.date_frame = ctk.CTkFrame(self)
        self.date_frame.pack(pady=5, padx=20, fill="x")
        
        self.use_date_var = ctk.BooleanVar(value=False)
        self.use_date_chk = ctk.CTkCheckBox(self.date_frame, text="Kích hoạt bộ lọc phân tách CONTENT MỚI (chọn khoảng Ngày tạo bên dưới)", variable=self.use_date_var)
        self.use_date_chk.grid(row=0, column=0, columnspan=4, padx=15, pady=5, sticky="w")
        
        self.start_date_lbl = ctk.CTkLabel(self.date_frame, text="Từ ngày:")
        self.start_date_lbl.grid(row=1, column=0, padx=15, pady=10, sticky="w")
        self.start_date_entry = DateEntry(self.date_frame, width=12, background='darkblue', foreground='white', borderwidth=2, date_pattern='dd_mm_yyyy')
        self.start_date_entry.grid(row=1, column=1, padx=5, pady=10, sticky="w")
        
        self.end_date_lbl = ctk.CTkLabel(self.date_frame, text="Đến ngày:")
        self.end_date_lbl.grid(row=1, column=2, padx=15, pady=10, sticky="w")
        self.end_date_entry = DateEntry(self.date_frame, width=12, background='darkblue', foreground='white', borderwidth=2, date_pattern='dd_mm_yyyy')
        self.end_date_entry.grid(row=1, column=3, padx=5, pady=10, sticky="w")

        # Run Button
        self.run_btn = ctk.CTkButton(self, text="XỬ LÝ & XUẤT BÁO CÁO", command=self.run_process, height=40, font=ctk.CTkFont(size=15, weight="bold"), fg_color="green", hover_color="darkgreen")
        self.run_btn.pack(pady=20)

    def select_bcfb(self):
        files = filedialog.askopenfilenames(title="Chọn file BCFB", filetypes=(("CSV files", "*.csv"), ("All files", "*.*")))
        if files:
            self.bcfb_files = list(files)
            self.bcfb_lbl.configure(text=f"Đã chọn {len(files)} file(s)", text_color=("black", "white"))

    def select_crm(self):
        file = filedialog.askopenfilename(title="Chọn file CRM", filetypes=(("CSV files", "*.csv"), ("All files", "*.*")))
        if file:
            self.crm_file = file
            self.crm_lbl.configure(text=os.path.basename(file), text_color=("black", "white"))

    def select_content(self):
        file = filedialog.askopenfilename(title="Chọn file Content", filetypes=(("CSV files", "*.csv"), ("All files", "*.*")))
        if file:
            self.content_file = file
            self.content_lbl.configure(text=os.path.basename(file), text_color=("black", "white"))

    def select_output(self):
        directory = filedialog.askdirectory(title="Chọn thư mục lưu file")
        if directory:
            self.output_dir = directory
            self.out_lbl.configure(text=directory, text_color=("black", "white"))

    def run_process(self):
        if not self.bcfb_files:
            messagebox.showerror("Lỗi", "Vui lòng chọn ít nhất 1 file BCFB.")
            return
        if not self.crm_file:
            messagebox.showerror("Lỗi", "Vui lòng chọn file CRM.")
            return
        if not self.output_dir:
            messagebox.showerror("Lỗi", "Vui lòng chọn thư mục lưu Output.")
            return
            
        self.run_btn.configure(text="ĐANG XỬ LÝ...", state="disabled")
        self.update()

        start_d = self.start_date_entry.get().strip() if self.use_date_var.get() else ""
        end_d = self.end_date_entry.get().strip() if self.use_date_var.get() else ""
        
        # Parse CRM prefixes
        raw_prefixes = self.prefix_var.get().split(',')
        crm_prefixes = [p.strip() for p in raw_prefixes if p.strip()]
        if not crm_prefixes:
            crm_prefixes = ["P", "PH"]

        success, msg = process_reports(self.bcfb_files, self.crm_file, self.content_file, self.output_dir, start_d, end_d, crm_prefixes)
        if success:
            messagebox.showinfo("Thành công", f"Đã xuất báo cáo thành công tại:\n{msg}")
        else:
            messagebox.showerror("Lỗi xử lý", f"Có lỗi xảy ra:\n{msg}")
            
        self.run_btn.configure(text="XỬ LÝ & XUẤT BÁO CÁO", state="normal")

if __name__ == "__main__":
    app = App()
    app.mainloop()
