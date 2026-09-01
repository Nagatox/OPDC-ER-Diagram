import os
import pandas as pd
import numpy as np
import time
from pathlib import Path

from google_sheet import openGSheet
from google_sheet import getNextEmptyRowNo
from google_sheet import getUpdateRowNumber

from database import connection_string, is_Table_in_public

if __name__ == "__main__":
    worksheet, spreadsheet = openGSheet(filename="OPDC-Database", worksheet_number=6)

    target_dir = "/media/nagato/NAS-SHARED-2/OPDC_2569/data/data-20260831/"

    target_path = Path(target_dir)

    for path in target_path.iterdir():
        if path.is_dir():
            #print(f"[Folder] {path} {path.name}")
            #new_sheet = spreadsheet.add_worksheet(title='HDFS_' + path.name, rows=1000, cols=20)
            row_no = 1
            for root, dirs, files in os.walk(path):
                for file in files:
                    try:
                        full_path = os.path.join(root, file)
                        filename, file_ext = os.path.splitext(file)
                        file_ext = file_ext.lower()

                        print(f"{filename} {file_ext}")
                        table_name = 'hdfs_' + filename

                        if file_ext in ['.csv', '.xlsx', '.xls']:
                            if is_Table_in_public(table_name):
                                new_row = [filename]
                                new_row += [file_ext]
                                new_row += [full_path]
                                new_row += [table_name]
                                worksheet.append_row(new_row)
                                time.sleep(2)

                    except Exception as e:
                        print(f"Unexpected error: {e}")