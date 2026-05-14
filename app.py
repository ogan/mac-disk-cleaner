# pyrefly: ignore [missing-import]
import customtkinter as ctk
from scanner import Scanner, format_size
import threading

class MacCleanerApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Mac Cleaner")
        self.geometry("700x700")
        self.resizable(False, False)
        
        # Appearance
        ctk.set_appearance_mode("system")
        ctk.set_default_color_theme("blue")

        self.scanner = Scanner()
        self.scan_results = {}
        
        self.create_widgets()

    def create_widgets(self):
        # Header
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.pack(pady=20, padx=20, fill="x")

        self.title_label = ctk.CTkLabel(self.header_frame, text="Disk Space Cleaner", font=ctk.CTkFont(size=24, weight="bold"))
        self.title_label.pack(side="left")

        self.scan_btn = ctk.CTkButton(self.header_frame, text="Scan Now", command=self.start_scan)
        self.scan_btn.pack(side="right")

        # Footer
        self.footer_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.footer_frame.pack(side="bottom", pady=20, padx=20, fill="x")

        self.status_label = ctk.CTkLabel(self.footer_frame, text="Ready", font=ctk.CTkFont(size=14))
        self.status_label.pack(side="left")

        self.clean_btn = ctk.CTkButton(self.footer_frame, text="CLEAN / DELETE", command=self.start_clean, fg_color="#D32F2F", hover_color="#B71C1C", state="normal", font=ctk.CTkFont(size=16, weight="bold"))
        self.clean_btn.pack(side="right")

        # Main Body
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.pack(side="top", pady=10, padx=20, fill="both", expand=True)

        self.category_vars = {}
        self.category_labels = {}
        
        row_idx = 0
        for category in self.scanner.categories:
            default_val = "off" if category in ["App Leftovers", "System Caches"] else "on"
            var = ctk.StringVar(value=default_val)
            self.category_vars[category] = var
            
            display_text = category
            if category == "System Caches":
                display_text += " (Warning: Apps may lose state)"
                
            chk = ctk.CTkCheckBox(self.main_frame, text=display_text, variable=var, onvalue="on", offvalue="off", font=ctk.CTkFont(size=14))
            chk.grid(row=row_idx, column=0, padx=20, pady=15, sticky="w")
            
            lbl = ctk.CTkLabel(self.main_frame, text="Not scanned", font=ctk.CTkFont(size=14))
            lbl.grid(row=row_idx, column=1, padx=20, pady=15, sticky="e")
            self.category_labels[category] = lbl
            
            self.main_frame.grid_columnconfigure(0, weight=1)
            self.main_frame.grid_columnconfigure(1, weight=1)
            
            row_idx += 1

        self.total_size_label = ctk.CTkLabel(self.main_frame, text="Total Space Can Be Freed: 0.00 B", font=ctk.CTkFont(size=16, weight="bold"))
        self.total_size_label.grid(row=row_idx, column=0, columnspan=2, pady=20)


    def start_scan(self):
        self.scan_btn.configure(state="disabled")
        self.clean_btn.configure(state="disabled")
        self.status_label.configure(text="Scanning...")
        
        threading.Thread(target=self.run_scan, daemon=True).start()

    def run_scan(self):
        self.scan_results, total_size = self.scanner.scan()
        self.after(0, self.update_ui_after_scan, total_size)

    def update_ui_after_scan(self, total_size):
        for category, data in self.scan_results.items():
            if category in self.category_labels:
                self.category_labels[category].configure(text=data['formatted'])
        
        self.total_size_label.configure(text=f"Total Space Can Be Freed: {format_size(total_size)}")
        self.status_label.configure(text="Scan Complete")
        self.scan_btn.configure(state="normal")
        self.clean_btn.configure(state="normal")
        if total_size == 0:
            self.clean_btn.configure(text="Nothing to Clean")
        else:
            self.clean_btn.configure(text="CLEAN / DELETE")

    def start_clean(self):
        selected_categories = [cat for cat, var in self.category_vars.items() if var.get() == "on"]
        if not selected_categories:
            self.status_label.configure(text="No categories selected.")
            return

        self.scan_btn.configure(state="disabled")
        self.clean_btn.configure(state="disabled")
        self.status_label.configure(text="Cleaning...")
        
        threading.Thread(target=self.run_clean, args=(selected_categories,), daemon=True).start()

    def run_clean(self, selected_categories):
        freed_space, errors = self.scanner.clean(selected_categories)
        self.after(0, self.update_ui_after_clean, freed_space, errors)

    def update_ui_after_clean(self, freed_space, errors):
        if errors:
            self.status_label.configure(text=f"Cleaned {format_size(freed_space)}. Some errors occurred.")
        else:
            self.status_label.configure(text=f"Successfully freed {format_size(freed_space)}!")
        
        # Rescan to reflect changes visually
        self.start_scan()

if __name__ == "__main__":
    app = MacCleanerApp()
    app.mainloop()
