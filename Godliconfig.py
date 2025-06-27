import tkinter as tk
from tkinter import ttk, messagebox
import pyodbc
import pathlib
import os

class CleanupConfigApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Godliness Config Manager")

        self.create_widgets()
        self.load_data()

    def get_connection(self):
        conn_str = (
            'DRIVER={ODBC Driver 11 for SQL Server};'
            'SERVER=SQL-SSRS;'
            'DATABASE=Appz;'
            'Trusted_Connection=yes;'
        )
        return pyodbc.connect(conn_str)

    def create_widgets(self):
        self.tree = ttk.Treeview(self.root, columns=("ID", "FolderPath", "RetentionDays", "FileExtensions", "ExcludedFilenames", "Client", "Enabled"), show="headings")

        # Set dynamic column widths
        column_widths = {
            "ID": 30,
            "FolderPath": 400,
            "RetentionDays": 90,
            "FileExtensions": 150,
            "ExcludedFilenames": 150,
            "Client": 100,
            "Enabled": 70
        }

        for col in self.tree["columns"]:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=column_widths.get(col, 100), anchor="w")  # default to 100 if not found

        self.tree.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        button_frame = tk.Frame(self.root)
        button_frame.pack(pady=10)

        tk.Button(button_frame, text="Add Record", command=self.add_record).grid(row=0, column=0, padx=5)
        tk.Button(button_frame, text="Edit Record", command=self.edit_record).grid(row=0, column=1, padx=5)
        tk.Button(button_frame, text="Delete Record", command=self.delete_record).grid(row=0, column=2, padx=5)
        tk.Button(button_frame, text="Refresh", command=self.load_data).grid(row=0, column=3, padx=5)

    def load_data(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT ID, FolderPath, RetentionDays, FileExtensions, ExcludedFilenames, Client, Enabled 
                FROM Cleanup_Config
            """)
            rows = cursor.fetchall()
            for row in rows:
                clean_row = [
                    str(row[0]),  #ID
                    row[1].strip() if row[1] else '', #FolderPath
                    str(row[2]) if row[2] is not None else '',  #RetentionDays
                    row[3].strip() if row[3] else '',  #FileExtensions
                    row[4].strip() if row[4] else '',  #ExcludedFilenames
                    row[5].strip() if row[5] else '',  #Client
                    str(row[6]) if row[6] is not None else '0'  #Enabled ('0' or '1')
                ]
                self.tree.insert("", tk.END, values=clean_row)
            conn.close()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load data:\n{e}")

    def add_record(self):
        RecordWindow(self, "Add New Record")

    def edit_record(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Select a record to edit.")
            return
        item = self.tree.item(selected)
        RecordWindow(self, "Edit Record", item["values"])

    def delete_record(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Select a record to delete.")
            return
        confirm = messagebox.askyesno("Confirm", "Are you sure you want to delete this record?")
        if confirm:
            item = self.tree.item(selected)
            id_to_delete = item["values"][0]
            try:
                conn = self.get_connection()
                cursor = conn.cursor()
                cursor.execute("DELETE FROM Cleanup_Config WHERE ID = ?", (id_to_delete,))
                conn.commit()
                conn.close()
                self.load_data()
                messagebox.showinfo("Success", "Record deleted successfully.")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete record:\n{e}")

class RecordWindow:
    def __init__(self, app, title, record=None):
        self.app = app
        self.record = record
        self.user = os.getenv("username")

        self.win = tk.Toplevel()
        self.win.title(title)

        self.win.transient(app.root)   # Tie it to the main window
        self.win.grab_set()            # Block input to other windows
        self.win.focus_force()

        labels = ["FolderPath", "RetentionDays", "FileExtensions", "ExcludedFilenames", "Client", "Enabled"]
        self.entries = {}
        self.vars = {} 

        for i, label in enumerate(labels):
            tk.Label(self.win, text=label).grid(row=i, column=0, padx=5, pady=5, sticky="w")
            if label == "Enabled":
                var = tk.IntVar(value=1) 
                chk = tk.Checkbutton(self.win, variable=var)
                chk.grid(row=i, column=1, padx=5, pady=5)
                self.vars[label] = var
                self.entries[label] = chk
            else:
                entry = tk.Entry(self.win, width=50)
                entry.grid(row=i, column=1, padx=5, pady=5)
                self.entries[label] = entry

        if record:
            self.entries["FolderPath"].insert(0, record[1])
            self.entries["RetentionDays"].insert(0, record[2])
            self.entries["FileExtensions"].insert(0, record[3])
            self.entries["ExcludedFilenames"].insert(0, record[4])
            self.entries["Client"].insert(0, record[5])
            self.vars["Enabled"].set(1 if record[6] else 0)

        save_btn_text = "Update" if record else "Add"
        tk.Button(self.win, text=save_btn_text, command=self.save_record).grid(row=len(labels), column=0, columnspan=2, pady=10)

    def save_record(self):
        
        for field, entry in self.entries.items():
            if isinstance(entry, tk.Entry):
                entry.config(bg="white")

        errors = []

        # Required fields
        required_fields = ["FolderPath", "RetentionDays"]

        for field in required_fields:
            val = self.entries[field].get().strip()
            if not val:
                errors.append(field)
                self.entries[field].config(bg="#ffcccc")

        # Additional checks
        try:
            int(self.entries["RetentionDays"].get())
        except ValueError:
            errors.append("RetentionDays")
            self.entries["RetentionDays"].config(bg="#ffcccc")
        
        if errors:
            msg = "Please correct the following field(s):\n" + ", ".join(errors)
            messagebox.showwarning("Missing or invalid data", msg)
            self.win.lift()
            self.win.focus_force()
            return  # Don't proceed to save
        
        folder_path = self.entries["FolderPath"].get().strip()

        # Normalize path for comparison
        p = pathlib.Path(folder_path).resolve()

        # Too shallow: only drive/root-level
        if p.drive and p == pathlib.Path(p.drive + "\\"):
            errors.append("FolderPath")
            self.entries["FolderPath"].config(bg="#ffcccc")

        # Too shallow: UNC root or single folder (e.g. \\server or \\server\share)
        if p.is_absolute() and len(p.parts) <= 2:
            errors.append("FolderPath")
            self.entries["FolderPath"].config(bg="#ffcccc")

        # Does path exist?
        if not p.exists():
            errors.append("FolderPath does not exist")
            self.entries["FolderPath"].config(bg="#ffcccc")

        if errors:
            msg = "FolderPath is either too broad or does not exist.\nPlease choose a specific subdirectory (e.g., ...\\logs\\app1)."
            messagebox.showwarning("Invalid FolderPath", msg)
            self.win.lift()
            self.win.focus_force()
            return

        try:
            conn = self.app.get_connection()
            cursor = conn.cursor()

            values = (
                self.entries["FolderPath"].get(),
                int(self.entries["RetentionDays"].get()),
                self.entries["FileExtensions"].get(),
                self.entries["ExcludedFilenames"].get(),
                self.entries["Client"].get(),
                self.vars["Enabled"].get(),
                self.user
            )

            if self.record:
                # Update existing
                cursor.execute("""
                    EXEC Godliness_Update ?,?,?,?,?,?,?,?
                """, values + (self.record[0],))
            else:
                # Insert new
                cursor.execute("""
                    EXEC Godliness_Insert ?,?,?,?,?,?,?
                """, values)

            conn.commit()
            conn.close()
            self.app.load_data()
            self.win.destroy()
            messagebox.showinfo("Success", "Record saved successfully.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save record:\n{e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = CleanupConfigApp(root)
    root.mainloop()