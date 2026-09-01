import os
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.types import INTEGER, TEXT

from pathlib import Path

from database import connection_string, is_Table_in_public

def upload_file_to_postgres(file_path, table_name, db_url):
    # 1. เช็กนามสกุลไฟล์เพื่อเลือกฟังก์ชันอ่านให้ถูกต้อง (ตามสไตล์ที่เราเคยคุยกัน)
    file_ext = os.path.splitext(file_path)[1].lower()
    
    try:
        print(f"📦 กำลังอ่านไฟล์: {file_path}")
        if file_ext == '.csv':
            df = pd.read_csv(file_path)
        elif file_ext in ['.xlsx', '.xls']:
            df = pd.read_excel(file_path, engine='openpyxl')
        else:
            print("❌ ไม่รองรับไฟล์ประเภทนี้")
            return

        # 2. ทำความสะอาดชื่อคอลัมน์ (Header) เบื้องต้น
        # PostgreSQL ไม่ชอบชื่อคอลัมน์ที่มีเว้นวรรคหรืออักขระพิเศษ จึงควรแปลงให้เป็นตัวพิมพ์เล็กและแทนที่เว้นวรรคด้วย '_'
        df.columns = [col.strip().lower().replace(" ", "_").replace("-", "_") for col in df.columns]

        # 3. สร้าง Map Data Type อัตโนมัติ (สแกนประเภทข้อมูลจาก DataFrame)
        # คอลัมน์ไหนเป็นตัวเลขให้เป็น INTEGER นอกนั้นให้เป็น TEXT
        data_type_mapping = {}
        for col_name in df.columns:
            # เช็กว่าคอลัมน์นั้นเป็นประเภทตัวเลข (Integer) หรือไม่
            if pd.api.types.is_integer_dtype(df[col_name]):
                data_type_mapping[col_name] = INTEGER()
                #print(f"📊 คอลัมน์ [{col_name}] -> กำหนดเป็น INTEGER")
            else:
                data_type_mapping[col_name] = TEXT()
                #print(f"🔤 คอลัมน์ [{col_name}] -> กำหนดเป็น TEXT")

        # 4. เชื่อมต่อฐานข้อมูล PostgreSQL และสั่งสร้างตาราง
    
        engine = create_engine(db_url)
        
        # ยิงข้อมูลเข้า Postgres
        # if_exists='replace' หมายถึง ถ้ามีตารางชื่อนี้อยู่แล้ว ให้ลบแล้วสร้างใหม่
        # if_exists='fail' หมายถึง ถ้ามีตารางอยู่แล้ว ให้หยุดทำงาน
        # if_exists='append' หมายถึง ถ้ามีตารางอยู่แล้ว ให้เพิ่มข้อมูลต่อท้าย
        df.to_sql(
            name=table_name,
            con=engine,
            if_exists='replace', 
            index=False,          # ไม่เอา Index ของ Pandas ไปสร้างเป็นคอลัมน์ใน DB
            dtype=data_type_mapping # ส่ง Map Data Type ที่เราเซ็ตไว้ไปบังคับโครงสร้างตาราง
        )
        print(f"🎯 สำเร็จ! สร้างตาราง '{table_name}' ใน PostgreSQL เรียบร้อยแล้ว\n")
        
    except Exception as e:
        print(f"❌ เกิดข้อผิดพลาดในการนำข้อมูลเข้า Database: {e}\n")


def upload_heavy_csv_in_chunks(file_path, table_name, db_url, chunk_rows=20000):
    engine = create_engine(db_url)
    
    print(f"🚀 กำลังเริ่มโหลดไฟล์ขนาดใหญ่แบบ Chunksize ({chunk_rows} แถวต่อรอบ)...")
    
    # ใส่ chunksize=... จะทำให้ Pandas คืนค่ากลับมาเป็น TextFileReader (Iterator) แทนการโหลดทั้งไฟล์
    chunks = pd.read_csv(file_path, chunksize=chunk_rows)
    
    for i, df_chunk in enumerate(chunks):
        # จัดการชื่อคอลัมน์เหมือนเดิม
        df_chunk.columns = [col.strip().lower().replace(" ", "_").replace("-", "_") for col in df_chunk.columns]
        
        # รอบแรกสุด (i == 0) ให้สร้างตารางใหม่แทนที่ของเก่า ('replace')
        # รอบถัดไป ให้เอาข้อมูลไปต่อท้ายตารางเดิม ('append')
        if_exists_mode = 'replace' if i == 0 else 'append'
        
        # ตรวจประเภทข้อมูลเฉพาะรอบแรกเพื่อความชัวร์
        data_type_mapping = {}
        if i == 0:
            for col_name in df_chunk.columns:
                if pd.api.types.is_integer_dtype(df_chunk[col_name]):
                    data_type_mapping[col_name] = TEXT()
                else:
                    data_type_mapping[col_name] = TEXT()
        
        # ยิงข้อมูลเข้า Postgresทีละ Chunk
        df_chunk.to_sql(
            name=table_name,
            con=engine,
            if_exists=if_exists_mode,
            index=False,
            dtype=data_type_mapping if i == 0 else None # รอบหลังไม่ต้องใส่คู่มือประเภทแล้ว
        )
        print(f"✅ ยิงข้อมูลสำเร็จไปแล้ว {(i+1) * chunk_rows} แถว...")

    print("🎯 จบการทำงาน! โหลดข้อมูลขนาดใหญ่เข้า Postgres เรียบร้อยอย่างปลอดภัย")

# เรียกใช้งาน
# upload_heavy_csv_in_chunks("huge_data.csv", "t_huge_sales", POSTGRES_URL)

if __name__ == "__main__":
    # --- 🚀 วิธีใช้งานจริง ---

    # 1. ตั้งค่า URL ของ Postgres ของคุณ
    # โครงสร้าง: postgresql://[user]:[password]@[host]:[port]/[database_name]
    print ("start import_file_to_database")
    POSTGRES_URL = connection_string

    # 2. เรียกใช้งานฟังก์ชัน (ใส่พาธไฟล์ และ ชื่อตารางที่อยากได้ใน DB)
    #target_dir = "/media/nagato/NAS-SHARED-2/OPDC_2569/data/"
    target_dir = "/media/nagato/NAS-SHARED-2/OPDC_2569/data/data-20260831/"

    target_path = Path(target_dir)

    for path in target_path.iterdir():
        #print(f"[Folder] {path} {path.name} {path.is_dir()}")
        if path.is_dir():
            #print(f"[Folder] {path} {path.name}")
            #new_sheet = spreadsheet.add_worksheet(title='HDFS_' + path.name, rows=1000, cols=20)
            row_no = 1
            for root, dirs, files in os.walk(path):
                print(f"files: {files}")
                for file in files:
                    try:
                        full_path = os.path.join(root, file)
                        filename, file_ext = os.path.splitext(file)
                        file_ext = file_ext.lower()

                        print(f"{filename} {file_ext}")
                        table_name = 'hdfs_' + filename

                        if file_ext in ['.csv']:
                            if not is_Table_in_public(table_name):
                                upload_heavy_csv_in_chunks(full_path, table_name, POSTGRES_URL)
                        elif file_ext in ['.xlsx', '.xls']:

                            if not is_Table_in_public(table_name):
                                upload_file_to_postgres(full_path, table_name, POSTGRES_URL)

                    except Exception as e:
                        print(f"Unexpected error: {e}")

    #upload_file_to_postgres(target_dir, "384_4_010_score_eva_12m68_govpro_p", POSTGRES_URL)