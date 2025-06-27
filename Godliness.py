import os
import time
import logging
import pyodbc

from datetime import datetime

#Setup global variables
SERVER = 'SQL-SSRS'
DATABASE = 'Appz'
#Log folder inside development environement if I am the one running it. Otherwise, in the cleardowns folder.
if os.getenv("username") == 'james.trimble':
    LOG_FOLDER = 'C:/Development/python/Godliness'
else:
    LOG_FOLDER = 'C:/Scripts/Cleardowns/Logs'
LOG_FILE = f'cleanup{datetime.now().strftime("%Y%m%dT%H%M%S")}.log'
LOG_DEST = os.path.join(LOG_FOLDER,LOG_FILE)

#Setup logging
logging.basicConfig(filename=LOG_DEST,
                    level=logging.INFO,
                    format="%(asctime)s - %(levelname)s - %(message)s")
logging.info(f"Program Start - {os.getenv("username")}")
try:
    def get_config():
        #Connect to database, get configurations from table, return them.
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
        #calculate cutoff (and create string version of it for the log)
        now = time.time()
        cutoff = now - (retention_days * 86400)
        log_cutoff = datetime.fromtimestamp(cutoff).strftime('%Y-%m-%d %H:%M:%S')
        #set extensions and excluded files to lower case lists (if they exist)
        extensions = [ext.strip().lower() for ext in extensions.split(',')] if extensions else []
        excluded = [f.strip().lower() for f in excluded_files.split(',')] if excluded_files else []
        #log above
        if extensions:
            if excluded:
                logging.info(f"Deleting files from before {log_cutoff} with extensions - {extensions}. Excluding {excluded}")
            else:
                logging.info(f"Deleting files from before {log_cutoff} with extensions - {extensions}")
        else:
            logging.info(f"Deleting files from before {log_cutoff}")

        #get list of files to check - if extensions are specified, only get files with extensions
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
                
                #Skip files that do not have file extension/s specified, if file extension exists (should never come up due to how file list is created, but works as a second check)
                if extensions and not any(filename.lower().endswith(ext) for ext in extensions):
                    continue  
                
                #skip any explicitly excluded files
                if filename.lower() in excluded:
                    continue
                
                #if the file was last updated before the cutoff, delete.
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
        #get the configurations from the table
        configs = get_config()
        #per row in the configurations, go through the delete process (as long as the filepath exists)
        for row in configs:
            path, days, exts, excluded = row
            if os.path.exists(path):
                logging.info(f"Checking {path}")
                delete_old_files(path, days, exts, excluded)
            else:
                logging.warning(f"Folder not found: {path}")
except Exception as e:
    logging.error(f"General Error - {e}")