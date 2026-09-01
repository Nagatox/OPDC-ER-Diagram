import json
import pandas as pd
from sqlalchemy import create_engine

import ast

from datetime import datetime
import time

from google_sheet import openGSheet
from google_sheet import getNextEmptyRowNo
from google_sheet import getUpdateRowNumber


if __name__ == "__main__":

    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"Current Time: {current_time}")
    start_time = time.perf_counter()

    worksheet, spreadsheet = openGSheet(filename="OPDC-Database", worksheet_number=0)
    
    headers = worksheet.row_values(1)

    col0_index = headers.index('id') + 1
    col0_values = worksheet.col_values(col0_index)[1:]
    col1_index = headers.index('pks') + 1
    col1_values = worksheet.col_values(col1_index)[1:]
    col2_index = headers.index('join potential') + 1
    col2_values = worksheet.col_values(col2_index)[1:]
    col3_index = headers.index('join potential2') + 1
    col3_values = worksheet.col_values(col3_index)[1:]

    # แก้ไขบรรทัดนี้เพื่อทำ List Comprehension ให้ถูกต้อง
    #all_values = [{"id": c1} for c1 in col1_values]
    all_values = [{"id": c0, "pks": c1, "potential": c2, "potential2": c3} for c0, c1, c2, c3 in zip(col0_values, col1_values, col2_values, col3_values)]

    #print ((str(all_values[0]['id'])))
    row_no = 1
    for row in all_values:
        row_no += 1
        id = row['id']
        pks = row['pks'].strip()
        if pks != "":
            pks_list = ast.literal_eval(pks)
            if len(pks_list) > 0:
            
                potential = row['potential']
                potential2 = row['potential2']
                potential += potential2

                try:
                    data_list = ast.literal_eval(potential)
                except Exception as e:
                    pass

                dfx = pd.DataFrame(data_list)

                #if id == 'hdfs_2565-cgd-contract-7':
                
                # dfx.columns = ['from_table', 'from_col', 'to_table', 'to_col', 'match_ratio']
                if len(dfx)>0:
                    pks_list = ast.literal_eval(pks)
                    dfx = dfx[dfx['to_col'].isin(pks_list)]
                    print(f"{id} {pks} {len(dfx['to_col'])}")
                    if len(dfx['to_col'])>0:
                        worksheet.update_acell(f"H{row_no}", len(dfx['to_col']))
                        time.sleep(2)
    
    end_time = time.perf_counter()
    execution_time = end_time - start_time
    print(f"Execution time: {execution_time:.4f} seconds")
