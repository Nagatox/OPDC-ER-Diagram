import pandas as pd
from sqlalchemy import create_engine
from data_profiling import ProfileReport


# 1. ตั้งค่าการเชื่อมต่อฐานข้อมูล PostgreSQL
# รูปแบบ: postgresql://[user]:[password]@[host]:[port]/[database_name]
#DB_USER = "ckan_default"
#DB_PASSWORD = "ckan_default"
#DB_HOST = "10.35.23.43"  # หรือใส่เป็น IP Address ของ Server
#DB_PORT = "5432"  # Port มาตรฐานของ PostgreSQL
#DB_NAME = "datastore_default"

DB_USER = "postgres"
DB_PASSWORD = "nagatos"
DB_HOST = "127.0.0.1"  # หรือใส่เป็น IP Address ของ Server
DB_PORT = 5432  # Port มาตรฐานของ PostgreSQL
DB_NAME = "datastore_default"

# สร้าง Connection Engine ของ SQLAlchemy
connection_string = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
engine = create_engine(connection_string)

def is_Table_in_public (tablename):
    query = f"""
        SELECT count(*) as cnt
        FROM pg_catalog.pg_tables 
        WHERE schemaname = 'public' and tablename = '{tablename}'
        """

    # โหลดเข้า DataFrame 
    df = pd.read_sql(query, con=engine)

    # ดึงค่าในแถวที่ 0 คอลัมน์ที่ 0 ออกมา
    total_rows = df.iloc[0, 0]

    #print(f"จำนวนแถวทั้งหมดคือ: {total_rows}")
    return total_rows > 0

def getTableList (engine):
    query = """
    SELECT tablename 
    FROM pg_catalog.pg_tables 
    WHERE schemaname = 'public'
    ORDER BY tablename;
    """

    print("กำลังดึงรายชื่อตารางจาก PostgreSQL...")

    # 3. เปิด Connection และดึงข้อมูลออกมาเป็น DataFrame
    with engine.connect() as conn:
        df_tables = pd.read_sql(query, con=conn)

    # 4. แปลงคอลัมน์ tablename ใน DataFrame ให้กลายเป็น Python List
    table_list = df_tables["tablename"].tolist()

    # 5. แสดงผลลัพธ์
    print(f"พบตารางทั้งหมด {len(table_list)} ตารางในระบบ")
    print("รายชื่อตารางใน List:", table_list)
    return table_list

def get_column_list(talbe_name):
    query = f"""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = '{talbe_name}'
        AND COLUMN_NAME NOT IN ('_id','_full_text')
        ORDER BY ordinal_position;
        """

    # โหลดเข้า DataFrame 
    df = pd.read_sql(query, con=engine)

    column_list = df["column_name"].tolist()
    data_type_list = df["data_type"].tolist()

    # 5. แสดงผลลัพธ์
    #print("รายชื่อ column ใน List:", column_list)
    return column_list, data_type_list

if __name__ == "__main__":
    table_list = getTableList(engine)
    print(table_list)

    # 2. เขียนคำสั่ง SQL เพื่อดึงข้อมูลจากตารางที่ต้องการ
    # แนะนำ: ถ้าตารางใหญ่มาก ให้ใส่ LIMIT เพื่อทดสอบระบบก่อน เช่น "SELECT * FROM customers LIMIT 10000"
    for table in table_list:
        query = f'SELECT * FROM PUBLIC."{table}"'

        print("กำลังดึงข้อมูลจาก PostgreSQL...")
        # ดึงข้อมูลจากฐานข้อมูลมาแปลงเป็น Pandas DataFrame
        df = pd.read_sql(query, con=engine)
        print(f"ดึงข้อมูลเสร็จสิ้น! จำนวนข้อมูลที่พบ: {df.shape[0]} แถว, {df.shape[1]} คอลัมน์")

        # 3. สั่งทำ Data Profiling
        print("กำลังสร้างรายงาน Data Profiling...")
        # ใส่โหมด minimal=True หากตารางมีข้อมูลจำนวนมาก เพื่อป้องกันคอมพิวเตอร์ค้าง
        #report = ProfileReport(df, title="PostgreSQL Data Profiling Report", minimal=False)

        # 4. บันทึกรายงานออกมาเป็นไฟล์ HTML
        #output_filename = "postgres_data_profile.html"
        #report.to_file(output_filename)
        #print(f"สร้างรายงานสำเร็จ! บันทึกไฟล์ไว้ที่: {output_filename}")
        # สรุปสถิติพื้นฐานทุกคอลัมน์ให้ออกมาเป็นตาราง DataFrame
        summary_df = df.describe(include="all")

        # บันทึกตารางสรุปสถิตินี้ลงไฟล์ Excel
        summary_df.to_excel(f"data_summary/{table}.xlsx")