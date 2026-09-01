import os
import pandas as pd
import numpy as np
import time
from pathlib import Path

from google_sheet import openGSheet
from google_sheet import getNextEmptyRowNo
from google_sheet import getUpdateRowNumber

from check_person_name import is_thai_name_column


def deep_scan_dataframe(df):
    print("=== [1] โครงสร้างข้อมูลพื้นฐาน (Shape & Types) ===")
    print(f"จำนวนแถวทั้งหมด: {df.shape[0]} | จำนวนคอลัมน์: {df.shape[1]}\n")
    
    # สร้างตารางวิเคราะห์คุณภาพข้อมูล
    profile_df = pd.DataFrame({
        'Data Type': df.dtypes,
        'Non-Null Count': df.count(),
        'Missing Values': df.isnull().sum(),
        'Missing %': (df.isnull().sum() / len(df) * 100).round(2),
        'Unique Values': df.nunique()
    })
    
    print(profile_df)
    print("\n" + "="*50 + "\n")
    
    print("=== [2] สถิติเชิงลึกสำหรับข้อมูลตัวเลข (Numeric Summary) ===")
    # ดูค่าเฉลี่ย, ส่วนเบี่ยงเบน, ค่าสูงสุด-ต่ำสุด, และ Percentile
    numeric_cols = df.select_dtypes(include=[np.number])
    if not numeric_cols.empty:
        print(numeric_cols.describe().T)
    else:
        print("ไม่มีข้อมูลที่เป็นตัวเลข")
        
    print("\n" + "="*50 + "\n")
    
    print("=== [3] ตรวจสอบแถวที่ข้อมูลซ้ำ (Duplicate Rows) ===")
    duplicate_count = df.duplicated().sum()
    print(f"จำนวนแถวที่ซ้ำกันทั้งแถว: {duplicate_count} แถว ({ (duplicate_count/len(df)*100):.2f}%)")

# สั่งใช้งาน (ใช้ได้ทั้งคู่)
# df = pd.read_csv('data.csv') 
# deep_scan_dataframe(df)

def proceefile (worksheet, row_no, filename, df):
    #worksheet.update_acell(f"B{row_no}", filename)
    try:
        new_row = [row_no, filename]
        max_confidence = 0
        for col_name in df:
            is_person, confidence = is_thai_name_column(df[col_name])
            if confidence > max_confidence:
                max_confidence = confidence
            #print(f"{col_name} เป็นคอลัมน์ชื่อคนใช่ไหม: {is_person} (ความมั่นใจ {confidence*100}%)")

        #print (f"{max_confidence}")
        #worksheet.update_acell(f"F{row_no}", max_confidence*100)    
        new_row += [max_confidence*100]

        worksheet.append_row(new_row)

        time.sleep(2)
    except Exception as e:
        print(f"Unexpected error: {e}")

if __name__ == "__main__":
    worksheet, spreadsheet = openGSheet(filename="OPDC-Database", worksheet_number=1)

    target_dir = "/media/nagato/NAS-SHARED-2/OPDC_2569/data"

    target_path = Path(target_dir)

    for path in target_path.iterdir():
        if path.is_dir():
            print(f"[Folder] {path} {path.name}")
            new_sheet = spreadsheet.add_worksheet(title='HDFS_' + path.name, rows=1000, cols=20)
            row_no = 1
            for root, dirs, files in os.walk(path):
                for file in files:
                    try:
                        full_path = os.path.join(root, file)
                        filename, file_ext = os.path.splitext(file)
                        file_ext = file_ext.lower()
                        
                        # แยกจำแนกเพื่อส่งเข้าฟังก์ชันสแกนให้ถูกต้อง
                        if file_ext == '.csv':
                            print(f"[พบไฟล์ CSV]: {file}")
                            df = pd.read_csv(full_path)
                            proceefile (new_sheet, row_no, full_path, df)
                            #deep_scan_dataframe(df)
                            row_no += 1
                            
                        elif file_ext in ['.xlsx', '.xls']:
                            print(f"[พบไฟล์ Excel]: {file}")
                            df = pd.read_excel(full_path, engine='openpyxl')
                            proceefile (new_sheet, row_no, full_path, df)
                            #deep_scan_dataframe(df)
                            row_no += 1
                            
                        elif file_ext == '.py':
                            print(f"[พบไฟล์ Python Source Code]: {file}")
                            # ส่งไปทำ Static / Line Profiling ของโค้ด
                            
                        else:
                            # ไฟล์ประเภทอื่นๆ ที่ไม่อยู่ในเงื่อนไข
                            continue

                    except Exception as e:
                        print(f"Unexpected error: {e}")
            

    #row_no = 1
    #for root, dirs, files in os.walk(target_dir):
    #    pass
        #print(dirs)
        # for file in files:
        #     try:
        #         full_path = os.path.join(root, file)
        #         filename, file_ext = os.path.splitext(file)
        #         file_ext = file_ext.lower()
                
        #         # แยกจำแนกเพื่อส่งเข้าฟังก์ชันสแกนให้ถูกต้อง
        #         if file_ext == '.csv':
        #             print(f"[พบไฟล์ CSV]: {file}")
        #             df = pd.read_csv(full_path)
        #             proceefile (worksheet, row_no, full_path, df)
        #             #deep_scan_dataframe(df)
        #             row_no += 1
                    
        #         elif file_ext in ['.xlsx', '.xls']:
        #             print(f"[พบไฟล์ Excel]: {file}")
        #             df = pd.read_excel(full_path, engine='openpyxl')
        #             proceefile (worksheet, row_no, full_path, df)
        #             #deep_scan_dataframe(df)
        #             row_no += 1
                    
        #         elif file_ext == '.py':
        #             print(f"[พบไฟล์ Python Source Code]: {file}")
        #             # ส่งไปทำ Static / Line Profiling ของโค้ด
                    
        #         else:
        #             # ไฟล์ประเภทอื่นๆ ที่ไม่อยู่ในเงื่อนไข
        #             continue

        #     except Exception as e:
        #         print(f"Unexpected error: {e}")
            
