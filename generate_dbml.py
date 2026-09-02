import json
import pandas as pd
import numpy as np
from sqlalchemy import create_engine

import re
import ast

from datetime import datetime
import time

from google_sheet import openGSheet
from google_sheet import getNextEmptyRowNo
from google_sheet import getUpdateRowNumber

def safe_parse_list(val):
    try:
        # ถ้าเป็น string ให้แปลงเป็น list แต่ถ้าเป็น list อยู่แล้วหรือเป็นค่าว่างให้ข้าม
        return ast.literal_eval(val) if isinstance(val, str) else val
    except (ValueError, SyntaxError):
        return val # กรณีที่แปลงไม่ได้ ให้คืนค่าเดิมป้องกันโค้ดพัง

def remove_word_from_list(column_list, target_word):
    if not isinstance(column_list, list):
        return column_list
        
    clean_list = column_list.copy()
    
    # ลบคำตามที่ระบุในตัวแปร target_word
    if target_word in clean_list:
        clean_list.remove(target_word)
        
    return clean_list

df_all_values = ""

if __name__ == "__main__":

    group_name = 'fs'

    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"Current Time: {current_time}")
    start_time = time.perf_counter()

    worksheet, spreadsheet = openGSheet(filename="OPDC-Database", worksheet_number=5)
    
    #rows = worksheet.get_values('A:L')
    all_values = worksheet.get_all_records(expected_headers=['No','id','Name', 'Group','column_list', 'data_type_list'])

    all_values = [row for row in all_values if row.get('Group').strip() == group_name]

    df_all_values = pd.DataFrame(all_values[0:], columns=all_values[0])

    target_columns = ['No', 'id', 'pks', 'Name','Group', 'potential', 'potential2', 'schema_similar', 'table_similar', 'column_list', 'data_type_list']
    df_all_values = df_all_values[target_columns]

    print(df_all_values.shape[0])
    #print(df_all_values)
    #df_all_values = df_all_values[df_all_values['count'] != ""]
    #df_all_values['pks'] = df_all_values['pks'].apply(lambda x: [item for item in x if item != 'id'])
    df_all_values['pks'] = df_all_values['pks'].apply(remove_word_from_list, args=("id",))
    df_all_values['pks'] = df_all_values['pks'].apply(remove_word_from_list, args=("ลำดับ",))
    df_all_values['pks'] = df_all_values['pks'].apply(remove_word_from_list, args=("ที่",))
    df_all_values['pks'] = df_all_values['pks'].apply(remove_word_from_list, args=("คะแนน",))
    df_all_values['pks'] = df_all_values['pks'].apply(remove_word_from_list, args=("อันดับ",))
    df_all_values['pks'] = df_all_values['pks'].apply(remove_word_from_list, args=("timestamp",))

    #df_all_values['column_list'] = df_all_values['column_list'].apply(remove_word_from_list, args=("_id",))

    #df_all_values = df_all_values[df_all_values['pks'] != "[]"]

    row_no = 1
    dbml = ""
    table_name_list = []
    table_list = df_all_values['id'].unique().tolist()

    df_all_values['column_list_x'] = None
    df_all_values['column_list_x'] = df_all_values['column_list_x'].astype(object)

    table_remove_list = []
    for index, row in df_all_values.iterrows():
        row_no += 1
        id = row['id']
        table_name = row['id']
        table_similar = row['table_similar']

        cleaned_table_similar = re.sub(r'np\.float64\(([^)]+)\)', r'\1', table_similar)
        table_similar_list = ast.literal_eval(cleaned_table_similar)
        for ts in table_similar_list:
            if ts['schema_similarity'] == 1 and ts['data_similarity'] == 1 and table_name not in table_remove_list:
                table_remove_list.append(ts['table_name'])
        
                
    print(f"len(table_remove_list:{len(table_remove_list)}")
    print(f"table_remove_list:{table_remove_list}")
    table_remove_list = list(dict.fromkeys(table_remove_list))
    print(f"len(table_remove_list:{len(table_remove_list)}")

    print(f"df_all_values.shape[0]:{df_all_values.shape[0]}")
    df_all_values = df_all_values[~df_all_values['id'].isin(table_remove_list)]
    print(f"df_all_values.shape[0]:{df_all_values.shape[0]}")
    print(df_all_values)


    dbml_list = []
    relationship_string_list = []
    table_name_in_ref_list = []
    for index, row in df_all_values.iterrows():
        row_no += 1
        id = row['id']
        pks_list = row['pks']
        table_name = row['Name']
        description = row['id']
        
        potential = row['potential'] + row['potential2']
        potential = potential.strip()

        #print(f"row_no:{row_no} potential:{potential}")

        potential_list = ast.literal_eval(potential)

        #print(f"row_no:{row_no} type(potential_list):{type(potential_list)}")
        #print (f"---{potential_list}---")
        if potential_list != []:
            df_potential = pd.DataFrame(potential_list)
            # df_potential.columns = ['from_col', 'to_table', 'to_col', 'match_ratio']

            #print (df_potential.columns)
            column_list_x = df_potential['fc'].str.replace('\r\n', '_', regex=False).replace('\n', '_', regex=False).unique()
        else:
            column_list_x = []  
        #print(column_list)
        #column_list = ast.literal_eval(row['column_list'])
        column_list = [col.replace('\r\n', '') for col in ast.literal_eval(row['column_list'])]
        #data_type_list = ast.literal_eval(row['data_type_list'])
        data_type_list = [dtype.replace('without time zone', '') for dtype in ast.literal_eval(row['data_type_list'])]
        column_string_list = "  ".join([f"\"{col}\" {dtype} \n" for col, dtype in zip(column_list, data_type_list)])  

        print(f"ID:{id} TABLE_NAME:{table_name}")
        #print(column_string_list)
        
        df_all_values.at[index, 'column_list_x'] = column_list

        if not table_name  in table_name_list and column_string_list.strip() != "":
            dbml_list.append ({'table_name':table_name, 'note': description, 'column_string_list': column_string_list})
            """ dbml += (
                f"Table \"{table_name}\" {{\n"
                f"  Note: '{description}'\n"
                f"  {column_string_list} "
                f"}}\n\n"
            ) """
            table_name_list += [table_name]

        #if table_name == '7fd938c5-ea4d-4903-b533-3bd8e883c55c':
        #    with open('column_list.txt', 'w', encoding='utf-8') as f:
        #        f.write(str(column_list))
    print(f"len(dbml_list):{len(dbml_list)}")
    #print(df_all_values.shape[0])
    #print (df_all_values['column_list'] )
    print(df_all_values)


    df_all_ref = pd.DataFrame()
    if True:
        for index, row in df_all_values.iterrows():
            row_no += 1
            id = row['id']
            pks_list = row['pks']
            table_name = row['Name']
            description = row['id']

            potential = row['potential'] + row['potential2']

            #with open('potential.txt', 'w', encoding='utf-8') as f:
            #    f.write(potential)

            potential_list = ast.literal_eval(potential)
            df_potential = pd.DataFrame(potential_list)
            print(f"df_potential.shape[1]:{df_potential.shape[1]}")
            if df_potential.shape[1] > 0:

                #print(f"{id} {pks_list} {len(df_to_col['to_col'])}")

                print(f"index:{index}")
                df_potential = df_potential[df_potential['tt'].isin(table_name_list)]
                df_potential = df_potential[df_potential['mr'] == 1]

                keep_rows = []
                for index, row in df_potential.iterrows():
                    matched_rows = df_all_values[df_all_values['Name'] == row['tt']]
                    if not matched_rows.empty:
                        column_list = matched_rows['column_list'].iloc[0]
                        #print(f"type(column_list):{type(column_list)} type(matched_rows):{type(matched_rows)} {matched_rows['id'].iloc[0]}")
                        
                        #print (f"{row['from_table']} : {row['from_col']} \n {column_list}")
                        #if isinstance(column_list, list) and (row['from_col'] in column_list):
                        if hasattr(column_list, 'tolist'):
                            column_list = column_list.tolist()
                        # หรือถ้ามันเป็น string ของ array ให้แปลงชัวร์ๆ
                        
                        if isinstance(column_list, np.ndarray):
                            column_list = list(column_list)

                        from_col=row['fc']
                        to_col=row['tc']
                        if df_all_ref.empty:
                            condition = False
                        else:
                            ret = df_all_ref.apply(lambda row: {from_col, to_col}.issubset({row['fc'], row['tc']}), axis=1)
                            condition = ret.any()
                        #print(f"type(condition:{type(condition)}")
                        if from_col in column_list and to_col in column_list:
                            if not condition:
                                keep_rows.append(row)

                df_relationship = pd.DataFrame(keep_rows).reset_index(drop=True)
                df_relationship = df_relationship.drop_duplicates()

                # Remove Duplicates Cross from and to
                if df_all_ref.empty:
                    df_all_ref = df_relationship
                else: 
                    df_all_ref = pd.concat([df_all_ref, df_relationship], axis=0, ignore_index=True)    

                
                #print (df_relationship)
                #print (f"df_relationship.shape: {df_relationship.shape}")


                #if df_relationship.shape[0] > 0:
                if True:
                    relationship_string = "\n".join([
                        f"Ref: \"{table_name}\".\"{row['fc']}\" > \"{row['tt']}\".\"{row['tc']}\" "
                        for _, row in df_relationship.iterrows()
                    ])
                    for _,r in df_relationship.iterrows():
                        table_name_in_ref_list.append(r['tt'])
                        table_name_in_ref_list.append(table_name)
                    
                    #if not table_name in table_name_list:
                    relationship_string_list.append(relationship_string)
                    if False:
                        dbml += (
                            f"{relationship_string} \n\n"
                        )
        print(f"df_all_ref.shape:{df_all_ref.shape}")

    print(f"len(relationship_string_list):{len(relationship_string_list)}")
    print(f"len(table_name_in_ref_list):{len(table_name_in_ref_list)}")
    table_name_in_ref_list = list(dict.fromkeys(table_name_in_ref_list))
    print(f"len(table_name_in_ref_list):{len(table_name_in_ref_list)}")

    print(f"len(dbml_list):{len(dbml_list)}")
    #dbml_list = [item for item in dbml_list if item["table_name"] in table_name_in_ref_list]
    #print(f"len(dbml_list):{len(dbml_list)}")

    for data in dbml_list:
        dbml += (
            f"Table \"{data['table_name']}\" {{\n"
            f"  Note: '{data['note']}'\n"
            f"  {data['column_string_list']} "
            f"}}\n\n"
        )
    
    for relationship_string in relationship_string_list:
        if relationship_string != "":
            dbml += (
                f"{relationship_string} \n\n"
            )
                
    with open('DBML/dbml.txt', 'w', encoding='utf-8') as f:
        f.write(dbml)
    
    with open('temp/table_name_list.txt', 'w', encoding='utf-8') as f:
        for item in table_name_list:
            # สั่งเขียนข้อมูลตามด้วย \n เพื่อบังคับขึ้นบรรทัดใหม่
            f.write(f"{item}\n")

    with open('temp/table_list.txt', 'w', encoding='utf-8') as f:
        for item in table_list:
            # สั่งเขียนข้อมูลตามด้วย \n เพื่อบังคับขึ้นบรรทัดใหม่
            f.write(f"{item}\n")
    
    end_time = time.perf_counter()
    execution_time = end_time - start_time
    print(f"Execution time: {execution_time:.4f} seconds")
