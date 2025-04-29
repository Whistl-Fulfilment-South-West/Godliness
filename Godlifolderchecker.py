import os
import pyodbc


root_folders = [
    r'\\E9INTEGRATIONS\Data_Import',
    r'\\E9INTEGRATIONS\Data_Export',
    r'\\Elucid9\Elucid\Data_Import',
    r'\\Elucid9\Elucid\Data_Export'
]


server = 'SQL-SSRS'    
database = 'Appz'
table_name = 'Cleanup_Config'
field_name = 'FolderPath'
# ------------------------------------


def find_done_or_processed_folders(roots):
    matched_folders = []
    for root in roots:
        for dirpath, dirnames, filenames in os.walk(root):
            final_folder = os.path.basename(dirpath).lower()
            if final_folder in ('done', 'processed'):
                matched_folders.append(os.path.normpath(dirpath))
    return matched_folders


def fetch_existing_folders_from_db(server, database, table, field):
    conn_str = (
    f"DRIVER={{ODBC Driver 11 for SQL Server}};"
    f"SERVER={server};"
    f"DATABASE={database};"
    f"Trusted_Connection=yes;"
    )
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()
    query = f"SELECT {field} FROM {table}"
    cursor.execute(query)
    results = [os.path.normpath(row[0]) for row in cursor.fetchall()]
    conn.close()
    return set(results)


def main():
    #Find folders in filesystem
    filesystem_folders = find_done_or_processed_folders(root_folders)
    print(f"Found {len(filesystem_folders)} folders in filesystem.")

    # Get folders from database
    db_folders = fetch_existing_folders_from_db(server, database, table_name, field_name)
    print(f"Fetched {len(db_folders)} folders from database.")

    # Compare
    missing_in_db = [folder for folder in filesystem_folders if folder not in db_folders]

        # Output the result
    print(f"\n{len(missing_in_db)} folders found in filesystem but missing from database:")
    for folder in missing_in_db:
        print(folder)

    return missing_in_db


if __name__ == "__main__":
    main()