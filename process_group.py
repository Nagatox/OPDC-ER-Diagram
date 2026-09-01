import json
import pandas as pd
from sqlalchemy import create_engine

from datetime import datetime
import time

from google_sheet import openGSheet
from google_sheet import getNextEmptyRowNo
from google_sheet import getUpdateRowNumber

from database import engine, is_Table_in_public, get_column_list

from check_primary_key import find_candidate_primary_keys, find_potential_joins, calculate_schema_similarity, analyze_table_similarity


def process_group(worksheet, group_name):
    all_values = worksheet.get_all_records(expected_headers=['No','id','Group','Name'])

    all_values = [row for row in all_values if row.get('Group').strip() == group_name]

    start_row = 2 - 2
    #row_no = start_row + 2
    for row in all_values[start_row:]:
        row2_no = 2
        concat_potential = []
        
        for row2 in all_values[0:]:
            
            if row != row2:
                tablename1 = row['id']
                tablename2 = row2['id']
                no = str(row['No'])
                print (f"{no} {tablename1} {row2_no} {tablename2} ", end="")
        
                #tablename = '2925f26a-3b62-443a-98c6-3d321bbedd7d'
                max_confidence = 0
                
                if is_Table_in_public(tablename1) and is_Table_in_public(tablename2):
                    query1 = f'SELECT * FROM PUBLIC."{tablename1}" LIMIT 10000'
                    query2 = f'SELECT * FROM PUBLIC."{tablename2}" LIMIT 10000'

                    # ดึงข้อมูลจากฐานข้อมูลมาแปลงเป็น Pandas DataFrame
                    df1 = pd.read_sql(query1, con=engine)
                    df2 = pd.read_sql(query2, con=engine)
                    try:
                        df1.drop(columns=['_id', '_full_text', 'idx_', 'unnamed:_0'], inplace=True, errors='ignore')
                        df2.drop(columns=['_id', '_full_text', 'idx_', 'unnamed:_0'], inplace=True, errors='ignore')
                    except Exception as e:
                        pass

                    potential =find_potential_joins(df1, df2, df1_name=row['Name'], df2_name=row2['Name'])
                    print(f"{potential}")
                    concat_potential += potential
                else:
                    print (f"-")

            row2_no += 1
        s_concat_potential = str(concat_potential)
        cell = worksheet.find(no, in_column=1)
        worksheet.update_acell(f"X{cell.row}", s_concat_potential[0:49998])
        if len(s_concat_potential) > 49998:
            worksheet.update_acell(f"Y{cell.row}", s_concat_potential[49998:])
        #time.sleep(2)
        #row_no += 1


def scan_similar(worksheet, group_name):
    current_last_row = len(worksheet.get_all_values())
    last_row_values = worksheet.row_values(current_last_row)

    all_values = worksheet.get_all_records(expected_headers=['No','id','Group','Name'])

    all_values = [row for row in all_values if row.get('Group').strip() == group_name]

    start_row = 2 - 2 # 694
    row_no = start_row + 2

    for row in all_values[start_row:]:
        row2_no = 2
        similarity_results_I = []
        similarity_results_J = []
        
        for row2 in all_values[0:]:
            
            if row != row2:
                tablename1 = row['id']
                tablename2 = row2['id']
                no = str(row['No'])
                print (f"{row_no} {tablename1} {row2_no} {tablename2} ", end="")

                if is_Table_in_public(tablename1) and is_Table_in_public(tablename2):
                    query1 = f'SELECT * FROM PUBLIC."{tablename1}" LIMIT 10000'
                    query2 = f'SELECT * FROM PUBLIC."{tablename2}" LIMIT 10000'

                    df1 = pd.read_sql(query1, con=engine)
                    df2 = pd.read_sql(query2, con=engine)
                    try:
                        df1.drop(columns=['_id', '_full_text'], inplace=True, errors='ignore')
                        df2.drop(columns=['_id', '_full_text'], inplace=True, errors='ignore')
                    except Exception as e:
                        pass

                    I =calculate_schema_similarity(df1, df2, df1_name=tablename1, df2_name=tablename2)
                    J =analyze_table_similarity(df1, df2, df1_name=tablename1, df2_name=tablename2)

                    #print(f"{I}, {J}")
                    print (f"-")
                    similarity_results_I.append(I)
                    similarity_results_J.append(J)
                else:
                    print (f"-")

            row2_no += 1

        top_5_native_I = sorted(similarity_results_I, key=lambda x: x['similarity'], reverse=True)[:5]
        top_5_native_J = sorted(similarity_results_J, key=lambda x: x['total_similarity'], reverse=True)[:5]

        s_top_5_similarity_I = str(top_5_native_I)
        s_top_5_similarity_J = str(top_5_native_J)

        cell = worksheet.find(no, in_column=1)
        worksheet.update_acell(f"U{cell.row}", s_top_5_similarity_I)
        worksheet.update_acell(f"V{cell.row}", s_top_5_similarity_J)
        #time.sleep(2)
        row_no += 1

def fill_column_tosheet (worksheet, group_name=""):
    all_values = worksheet.get_all_records(expected_headers=['No','id','Group','Name'])

    if group_name != "":
        all_values = [row for row in all_values if row.get('Group').strip() == group_name]

    start_row = 2 - 2
    #row_no = start_row + 2
    for row in all_values[start_row:]:
        tablename1 = row['id']
        no = str(row['No'])

        print(f"{no} {tablename1}")

        column_list, data_type_list = get_column_list(tablename1)

        s_column_list = str(column_list)
        s_data_type_list = str(data_type_list)

        cell = worksheet.find(no, in_column=1)
        worksheet.update_acell(f"H{cell.row}", s_column_list)
        worksheet.update_acell(f"I{cell.row}", s_data_type_list)
        time.sleep(2)

def scan_primary_key(worksheet, group_name=""):
    
    #all_values = worksheet.get_all_records()
    current_last_row = len(worksheet.get_all_values())
    last_row_values = worksheet.row_values(current_last_row)

    #all_values = worksheet.get_all_records()
    # 1. ดึงเฉพาะแถวแรกมาหาตำแหน่งคอลัมน์ (ใช้ RAM น้อยมาก)
    headers = worksheet.row_values(1)

    col1_index = headers.index('id') + 1
    col1_values = worksheet.col_values(col1_index)[1:]

    # แก้ไขบรรทัดนี้เพื่อทำ List Comprehension ให้ถูกต้อง
    #all_values = [{"id": c1} for c1 in col1_values]
    all_values = worksheet.get_all_records(expected_headers=['No','id','Group','Name'])

    if group_name != "":
        all_values = [row for row in all_values if row.get('Group').strip() == group_name]    

    #print(all_values)
    start_row = 2 - 2
    row_no = start_row + 2
    for row in all_values[start_row:]:
        tablename = row['id']
        print (f"{row_no} {tablename} ", end="")
        
        #tablename = '2925f26a-3b62-443a-98c6-3d321bbedd7d'
        max_confidence = 0
        if is_Table_in_public(tablename):
            query = f'SELECT * FROM PUBLIC."{tablename}" LIMIT 20000'

            #print("กำลังดึงข้อมูลจาก PostgreSQL...")
            # ดึงข้อมูลจากฐานข้อมูลมาแปลงเป็น Pandas DataFrame
            df = pd.read_sql(query, con=engine)
            try:
                df.drop(columns=['_id'], inplace=True, errors='ignore')
                df.drop(columns=['_full_text'], inplace=True, errors='ignore')
                df.drop(columns=['คะแนน'], inplace=True, errors='ignore')
                df.drop(columns=['ตัวชี้วัด'], inplace=True, errors='ignore')
                df.drop(columns=['ผลผลิต'], inplace=True, errors='ignore')
            except Exception as e:
                print(e)
                pass

            pks = find_candidate_primary_keys(df)

            print (f"{pks}")
            worksheet.update_acell(f"T{row_no}", str(pks))
            time.sleep(2)
        else:
            print (f"-")

        row_no += 1

if __name__ == "__main__":

    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"Current Time: {current_time}")
    start_time = time.perf_counter()

    worksheet, spreadsheet = openGSheet(filename="OPDC-Database", worksheet_number=5)
    scan_primary_key (worksheet, 'psdg')
    #fill_column_tosheet (worksheet, 'gence-lab')

    scan_similar(worksheet, 'psdg')
    process_group(worksheet, 'psdg')

    #column_list, data_type_list = get_column_list('3841669f-8398-4e92-b485-0293a9930ecc')
    #print("รายชื่อ column ใน List:", column_list)
    #print("รายชื่อ data type ใน List:", data_type_list)
    
    end_time = time.perf_counter()
    execution_time = end_time - start_time
    print(f"Execution time: {execution_time:.4f} seconds")
