import json
import pandas as pd
from sqlalchemy import create_engine

from datetime import datetime
import time

from google_sheet import openGSheet
from google_sheet import getNextEmptyRowNo
from google_sheet import getUpdateRowNumber

from database import engine, is_Table_in_public

from check_person_name import is_thai_name_column
from check_primary_key import find_candidate_primary_keys, find_potential_joins, calculate_schema_similarity, analyze_table_similarity

def scan_is_thai_name_column(worksheet):
    all_values = worksheet.get_all_records()
    #print(all_values)
    start_row = 545-2
    row_no = start_row + 2
    for row in all_values[start_row:]:
        tablename = row['id']
        print (f"{row_no} {tablename} ", end="")
        
        #tablename = '2925f26a-3b62-443a-98c6-3d321bbedd7d'
        max_confidence = 0
        if is_Table_in_public(tablename):
            query = f'SELECT * FROM PUBLIC."{tablename}" LIMIT 5000'

            #print("กำลังดึงข้อมูลจาก PostgreSQL...")
            # ดึงข้อมูลจากฐานข้อมูลมาแปลงเป็น Pandas DataFrame
            df = pd.read_sql(query, con=engine)
            try:
                df.drop(columns=['_id', '_full_text'], inplace=True)
            except Exception as e:
                pass

            for col_name in df:
                is_person, confidence = is_thai_name_column(df[col_name])
                if confidence > max_confidence:
                    max_confidence = confidence
                #print(f"{col_name} เป็นคอลัมน์ชื่อคนใช่ไหม: {is_person} (ความมั่นใจ {confidence*100}%)")

            print (f"{max_confidence}")
            worksheet.update_acell(f"F{row_no}", max_confidence*100)
            time.sleep(2)
        else:
            print (f"-")

        row_no += 1

def scan_primary_key(worksheet):
    
    #all_values = worksheet.get_all_records()
    current_last_row = len(worksheet.get_all_values())
    last_row_values = worksheet.row_values(current_last_row)

    #all_values = worksheet.get_all_records()
    # 1. ดึงเฉพาะแถวแรกมาหาตำแหน่งคอลัมน์ (ใช้ RAM น้อยมาก)
    headers = worksheet.row_values(1)

    col1_index = headers.index('id') + 1
    col1_values = worksheet.col_values(col1_index)[1:]

    # แก้ไขบรรทัดนี้เพื่อทำ List Comprehension ให้ถูกต้อง
    all_values = [{"id": c1} for c1 in col1_values]

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
            worksheet.update_acell(f"G{row_no}", str(pks))
            time.sleep(2)
        else:
            print (f"-")

        row_no += 1

def scan_find_potential_joins(worksheet):
    current_last_row = len(worksheet.get_all_values())
    last_row_values = worksheet.row_values(current_last_row)

    #all_values = worksheet.get_all_records()
    # 1. ดึงเฉพาะแถวแรกมาหาตำแหน่งคอลัมน์ (ใช้ RAM น้อยมาก)
    headers = worksheet.row_values(1)

    col1_index = headers.index('id') + 1
    col1_values = worksheet.col_values(col1_index)[1:]

    # แก้ไขบรรทัดนี้เพื่อทำ List Comprehension ให้ถูกต้อง
    all_values = [{"id": c1} for c1 in col1_values]

    start_row = 644 - 2 # 694
    row_no = start_row + 2

    for row in all_values[start_row:]:
        row2_no = 2
        concat_potential = []
        
        for row2 in all_values[0:]:
            
            if row != row2:
                tablename1 = row['id']
                tablename2 = row2['id']
                print (f"{row_no} {tablename1} {row2_no} {tablename2} ", end="")
        
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

                    potential =find_potential_joins(df1, df2, df1_name=tablename1, df2_name=tablename2)
                    print(f"{potential}")
                    concat_potential += potential
                else:
                    print (f"-")

            row2_no += 1
        s_concat_potential = str(concat_potential)

        worksheet.update_acell(f"L{row_no}", s_concat_potential[0:49999])
        if len(s_concat_potential) > 50000:
            worksheet.update_acell(f"M{row_no}", s_concat_potential[50000:])
        #time.sleep(2)
        row_no += 1

def scan_similar(worksheet):
    current_last_row = len(worksheet.get_all_values())
    last_row_values = worksheet.row_values(current_last_row)

    #all_values = worksheet.get_all_records()
    # 1. ดึงเฉพาะแถวแรกมาหาตำแหน่งคอลัมน์ (ใช้ RAM น้อยมาก)
    headers = worksheet.row_values(1)

    col1_index = headers.index('id') + 1
    col1_values = worksheet.col_values(col1_index)[1:]

    # แก้ไขบรรทัดนี้เพื่อทำ List Comprehension ให้ถูกต้อง
    all_values = [{"id": c1} for c1 in col1_values]

    start_row = 883 - 2 # 694
    row_no = start_row + 2

    for row in all_values[start_row:]:
        row2_no = 2
        similarity_results_I = []
        similarity_results_J = []
        
        for row2 in all_values[0:]:
            
            if row != row2:
                tablename1 = row['id']
                tablename2 = row2['id']
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

        #df_results_I = pd.DataFrame(similarity_results_I)
        #df_results_J = pd.DataFrame(similarity_results_J)
        #print(df_results_I)
        #print(df_results_J)
        #print(similarity_results_I)
        #print(similarity_results_J)
        top_5_native_I = sorted(similarity_results_I, key=lambda x: x['similarity'], reverse=True)[:5]
        top_5_native_J = sorted(similarity_results_J, key=lambda x: x['total_similarity'], reverse=True)[:5]
        #top_5_similarity_I = df_results_I.nlargest(5, 'similarity')
        #top_5_similarity_J = df_results_J.nlargest(5, 'total_similarity')
        

        s_top_5_similarity_I = str(top_5_native_I)
        s_top_5_similarity_J = str(top_5_native_J)

        worksheet.update_acell(f"I{row_no}", s_top_5_similarity_I)
        worksheet.update_acell(f"J{row_no}", s_top_5_similarity_J)
        #time.sleep(2)
        row_no += 1


if __name__ == "__main__":

    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"Current Time: {current_time}")
    start_time = time.perf_counter()

    worksheet, spreadsheet = openGSheet(filename="OPDC-Database", worksheet_number=0)
    #scan_is_thai_name_column (worksheet)
    #scan_primary_key (worksheet)
    scan_find_potential_joins(worksheet)
    #scan_similar (worksheet)
    
    end_time = time.perf_counter()
    execution_time = end_time - start_time
    print(f"Execution time: {execution_time:.4f} seconds")
