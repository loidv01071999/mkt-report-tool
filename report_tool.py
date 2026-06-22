import customtkinter as ctk
from tkinter import filedialog, messagebox
import os
import pandas as pd
import datetime

# --- CONFIG ---
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

def process_reports(bcfb_files, crm_file, output_dir):
    try:
        # 1. Đọc và gộp các file BCFB
        bcfb_dfs = []
        for file in bcfb_files:
            try:
                try:
                    df = pd.read_csv(file, encoding='utf-8')
                except UnicodeDecodeError:
                    df = pd.read_csv(file, encoding='utf-16')
                
                cols = ["Tên chiến dịch", "Kết quả", "Số tiền đã chi tiêu (VND)"]
                missing_cols = [c for c in cols if c not in df.columns]
                if missing_cols:
                    raise ValueError(f"File '{os.path.basename(file)}' thiếu các cột: {', '.join(missing_cols)}")
                
                df = df[cols].copy()
                bcfb_dfs.append(df)
            except Exception as e:
                raise Exception(f"Lỗi khi đọc file BCFB '{os.path.basename(file)}': {str(e)}")
        
        if not bcfb_dfs:
            raise ValueError("Chưa có dữ liệu BCFB.")
            
        bcfb_full = pd.concat(bcfb_dfs, ignore_index=True)
        
        # Clean numeric columns
        bcfb_full['Kết quả'] = pd.to_numeric(bcfb_full['Kết quả'], errors='coerce').fillna(0)
        bcfb_full['Số tiền đã chi tiêu (VND)'] = pd.to_numeric(bcfb_full['Số tiền đã chi tiêu (VND)'], errors='coerce').fillna(0)
        
        # Gom nhóm theo Tên chiến dịch
        bcfb_grouped = bcfb_full.groupby('Tên chiến dịch', as_index=False).agg({
            'Kết quả': 'sum',
            'Số tiền đã chi tiêu (VND)': 'sum'
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
            
        crm_df['Số contact'] = pd.to_numeric(crm_df['Số contact'], errors='coerce').fillna(0)
        
        # 3. Mapping
        output_rows = []
        matched_campaigns = set()
        
        for idx, row in crm_df.iterrows():
            ma = str(row['Mã']).strip()
            crm_contact = row['Số contact']
            
            # Find matching campaigns in bcfb_grouped
            matched_mask = bcfb_grouped['Tên chiến dịch'].str.contains(ma, regex=False, na=False)
            matching_rows = bcfb_grouped[matched_mask]
            
            sum_ket_qua = 0
            sum_so_tien = 0
            
            for _, m_row in matching_rows.iterrows():
                camp_name = m_row['Tên chiến dịch']
                if camp_name not in matched_campaigns:
                    sum_ket_qua += m_row['Kết quả']
                    sum_so_tien += m_row['Số tiền đã chi tiêu (VND)']
                    matched_campaigns.add(camp_name)
            
            max_contact = max(crm_contact, sum_ket_qua)
            
            output_rows.append({
                "Mã": ma,
                "Số contact": max_contact,
                "Số tiền đã chi tiêu (VND)": sum_so_tien
            })
            
        # 4. Các chiến dịch chưa được match trong BCFB
        unmatched_mask = ~bcfb_grouped['Tên chiến dịch'].isin(matched_campaigns)
        unmatched_rows = bcfb_grouped[unmatched_mask]
        
        for _, row in unmatched_rows.iterrows():
            output_rows.append({
                "Mã": row['Tên chiến dịch'],
                "Số contact": row['Kết quả'],
                "Số tiền đã chi tiêu (VND)": row['Số tiền đã chi tiêu (VND)']
            })
            
        # 5. Xuất Excel
        output_df = pd.DataFrame(output_rows)
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = os.path.join(output_dir, f"Bao_Cao_Marketing_{timestamp}.xlsx")
        
        output_df.to_excel(output_path, index=False)
        return True, output_path
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return False, str(e)


class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Tool Báo Cáo Marketing")
        self.geometry("600x400")
        
        self.bcfb_files = []
        self.crm_file = ""
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

        # Output Dir
        self.out_btn = ctk.CTkButton(self.input_frame, text="3. Chọn thư mục lưu Output", command=self.select_output)
        self.out_btn.grid(row=2, column=0, padx=20, pady=15, sticky="w")
        self.out_lbl = ctk.CTkLabel(self.input_frame, text="Chưa chọn thư mục", text_color="gray")
        self.out_lbl.grid(row=2, column=1, padx=20, pady=15, sticky="w")

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

        success, msg = process_reports(self.bcfb_files, self.crm_file, self.output_dir)
        if success:
            messagebox.showinfo("Thành công", f"Đã xuất báo cáo thành công tại:\n{msg}")
        else:
            messagebox.showerror("Lỗi xử lý", f"Có lỗi xảy ra:\n{msg}")
            
        self.run_btn.configure(text="XỬ LÝ & XUẤT BÁO CÁO", state="normal")

if __name__ == "__main__":
    app = App()
    app.mainloop()
