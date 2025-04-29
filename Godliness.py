import os
import time
import logging
import pyodbc

from datetime import datetime

SERVER = 'SQL-SSRS'
DATABASE = 'Appz'
if os.getenv("username") == 'james.trimble':
    LOG_FOLDER = 'C:/Development/python/Godliness'
else:
    LOG_FOLDER = 'C:/Scripts/Cleardowns/Logs'
LOG_FILE = f'cleanup{datetime.now().strftime("%Y%m%dT%H%M%S")}.log'
LOG_DEST = os.path.join(LOG_FOLDER,LOG_FILE)

logging.basicConfig(filename=LOG_DEST,
                    level=logging.INFO,
                    format="%(asctime)s - %(levelname)s - %(message)s")
logging.info(f"Program Start - {os.getenv("username")}")
try:
    def get_config():
        conn_str = (
            f'DRIVER={{ODBC Driver 11 for SQL Server}};'
            f'SERVER={SERVER};DATABASE={DATABASE};Trusted_Connection=yes;'
        )
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
        cursor.execute(f"""
            SELECT FolderPath, RetentionDays, FileExtensions, ExcludedFilenames
            FROM Cleanup_Config WHERE Enabled = 1
        """)
        rows = cursor.fetchall()
        conn.close()
        return rows

    def delete_old_files(folder_path, retention_days, extensions=None, excluded_files=None):
        now = time.time()
        cutoff = now - (retention_days * 86400)
        log_cutoff = datetime.fromtimestamp(cutoff).strftime('%Y-%m-%d %H:%M:%S')
        extensions = [ext.strip().lower() for ext in extensions.split(',')] if extensions else []
        excluded = [f.strip().lower() for f in excluded_files.split(',')] if excluded_files else []
        if extensions:
            if excluded:
                logging.info(f"Deleting files from before {log_cutoff} with extensions - {extensions}. Excluding {excluded}")
            else:
                logging.info(f"Deleting files from before {log_cutoff} with extensions - {extensions}")
        else:
            logging.info(f"Deleting files from before {log_cutoff}")

        if not extensions:
            filenames = os.listdir(folder_path)
        else:
            fullnames = os.listdir(folder_path)
            filenames = []
            for ext in extensions:
                filenames.extend([fullname for fullname in fullnames if fullname.endswith(ext)])
        if len(filenames) == 0:
            logging.info(f"No files in {folder_path}")
            return
        try:
            count = 0
            for filename in os.listdir(folder_path):
                filepath = os.path.join(folder_path, filename)
                if not os.path.isfile(filepath):
                    continue

                if extensions and not any(filename.lower().endswith(ext) for ext in extensions):
                    continue  # skip files that don’t match extension filter

                if filename.lower() in excluded:
                    continue  # skip explicitly excluded files

                if os.path.getmtime(filepath) < cutoff:
                    try:
                        os.remove(filepath)
                        logging.info(f"Deleted: {filepath}")
                        count += 1
                    except Exception as e:
                        logging.error(f"Failed to delete {filepath}: {e}")
            logging.info(f"{count} files deleted from {folder_path}")
        except Exception as e:
            logging.error(f"Error in folder {folder_path}: {e}")

# Main
    if __name__ == "__main__":
        configs = get_config()
        for row in configs:
            path, days, exts, excluded = row
            if os.path.exists(path):
                logging.info(f"Checking {path}")
                delete_old_files(path, days, exts, excluded)
            else:
                logging.warning(f"Folder not found: {path}")
except Exception as e:
    logging.error(f"General Error - {e}")