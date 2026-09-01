import os
import pandas as pd
import numpy as np
import time
from pathlib import Path

import ast

from google_sheet import openGSheet
from google_sheet import getNextEmptyRowNo
from google_sheet import getUpdateRowNumber

from database import engine, is_Table_in_public

from check_person_name import is_thai_name_column
#from check_similar_word import check_similar_word_hybrid_max_score, get_multi_group_max_score

def scan_is_thai_name_column(worksheet, group_name):
    all_values = worksheet.get_all_records(expected_headers=['No','id','Group','Name'])

    if group_name != "":
        all_values = [row for row in all_values if row.get('Group').strip() == group_name]

    start_row = 2 - 2
    row_no = start_row + 2
    for row in all_values[start_row:]:
        tablename = row['id']
        print (f"{row_no} {tablename} ", end="")
        
        #tablename = '2925f26a-3b62-443a-98c6-3d321bbedd7d'
        max_confidence = 0
        if is_Table_in_public(tablename):
        #if True:
            query = f'SELECT * FROM PUBLIC."{tablename}" LIMIT 5000'

            #print("กำลังดึงข้อมูลจาก PostgreSQL...")
            # ดึงข้อมูลจากฐานข้อมูลมาแปลงเป็น Pandas DataFrame
            df = pd.read_sql(query, con=engine)

            df.drop(columns=['_id', '_full_text'], inplace=True, errors='ignore')

            for col_name in df:
                is_person, confidence = is_thai_name_column(df[col_name], col_name)
                if confidence > max_confidence:
                    max_confidence = confidence
                #print(f"{col_name} เป็นคอลัมน์ชื่อคนใช่ไหม: {is_person} (ความมั่นใจ {confidence*100}%)")

            print (f"{max_confidence}")
            worksheet.update_acell(f"M{row_no}", round(max_confidence,4)*100)
            time.sleep(2)
        else:
            print (f"-")

        row_no += 1

def scan_find_word_list (worksheet, group_name, word_list, cell_prefix):
    all_values = worksheet.get_all_records(expected_headers=['No','id','Group','Name','column_list'])

    if group_name != "":
        all_values = [row for row in all_values if row.get('Group').strip() == group_name]
    
    start_row = 2 - 2
    row_no = start_row + 2
    for row in all_values[start_row:]:
        tablename = row['id']
        column_names = row['column_list']
        column_list = ast.literal_eval(column_names)

        print (f"{row_no} {tablename} ")
        if column_list:
            matched, max_score = check_similar_word_hybrid_max_score(column_list, word_list)

            worksheet.update_acell(f"{cell_prefix}{row_no}", max_score*100)
            time.sleep(2)

        row_no += 1

def scan_find_2_word_list (worksheet, group_name, word_list1, word_list2, cell_prefix):
    all_values = worksheet.get_all_records(expected_headers=['No','id','Group','Name','column_list'])

    if group_name != "":
        all_values = [row for row in all_values if row.get('Group').strip() == group_name]
    
    start_row = 2 - 2
    row_no = start_row + 2
    for row in all_values[start_row:]:
        tablename = row['id']
        column_names = row['column_list']
        column_list = ast.literal_eval(column_names)

        print (f"{row_no} {tablename} ")
        if column_list:
            #matched, max_score = check_similar_word_hybrid_max_score(column_list, word_list)
            max_score = get_multi_group_max_score (column_list, word_list1, word_list2)

            worksheet.update_acell(f"{cell_prefix}{row_no}", max_score*100)
            time.sleep(2)

        row_no += 1

if __name__ == "__main__":
    worksheet, spreadsheet = openGSheet(filename="OPDC-Database", worksheet_number=5)

    scan_is_thai_name_column (worksheet, '')
    #scan_find_word_list (worksheet, '', ['รางวัล','reward'], 'P')
    #scan_find_2_word_list (worksheet, '', ['รางวัล','reward'], ['ปี','year'], 'O')

