import pandas as pd
import numpy as np


def find_candidate_primary_keys(df):
    candidate_keys = []
    total_rows = len(df)
    
    if total_rows == 0:
        return "ตารางไม่มีข้อมูล"

    for col in df.columns:
        # ข้อที่ 1: เช็กว่ามีค่าว่างไหม
        has_nulls = df[col].isnull().any()
        
        # ข้อที่ 2: เช็กสัดส่วนความไม่ซ้ำกัน (Uniqueness)
        unique_values = df[col].nunique()

        null_values = df[col].notnull().all() 
        
        # ถ้าไม่มีค่าว่าง และจำนวนคอลัมน์ที่ซ้ำเท่ากับจำนวนแถวทั้งหมด
        if not has_nulls and null_values and unique_values == total_rows:
            candidate_keys.append(col)
            
    return candidate_keys

def find_potential_joins(df1, df2, df1_name="Table1", df2_name="Table2"):
    potential_joins = []
    
    for col1 in df1.columns:
        for col2 in df2.columns:
            # ถ้าชื่อคอลัมน์ตรงกัน (หรือปรับให้เป็นตัวเล็กแล้วตรงกัน)
            #if col1.lower() == col2.lower():
            set1 = set(df1[col1].dropna().unique())
            set2 = set(df2[col2].dropna().unique())
            try:
                # เช็กสัดส่วนว่าข้อมูลในตารางที่ 2 วิ่งไปจับคู่ในตารางที่ 1 ได้มากน้อยแค่ไหน
                if set2.issubset(set1) or len(set2.intersection(set1)) / len(set2) > 0.7:
                    potential_joins.append({
                        'fc': col1,
                        'tt': df2_name, 'tc': col2,
                        'mr': round(len(set2.intersection(set1)) / len(set2),3)
                    })
            except Exception as e:
                print(f"Unexpected error: {e}")
                    
    return potential_joins

def calculate_schema_similarity(df1, df2, df1_name="Table1", df2_name="Table2"):
    cols1 = set(df1.columns)
    cols2 = set(df2.columns)
    
    # หาคอลัมน์ที่อินเตอร์เซกชัน (ซ้ำกัน) และยูเนียน (รวมกัน)
    intersection = cols1.intersection(cols2)
    union = cols1.union(cols2)
    
    # คำนวณเปอร์เซ็นต์ความคล้าย (0 ถึง 1)
    similarity = len(intersection) / len(union) if len(union) > 0 else 0
    return {
        'table_name':df2_name,
        'similarity': similarity,
        'intersection': intersection,
    }

def analyze_table_similarity(df1, df2, df1_name="Table1", df2_name="Table2"):
    """
    ฟังก์ชันคำนวณความคล้ายระหว่าง 2 ตาราง ทั้งชื่อคอลัมน์และข้อมูลด้านใน
    """
    # ==========================================
    # ส่วนที่ 1: ตรวจสอบความคล้ายของชื่อคอลัมน์ (Schema Similarity)
    # ==========================================
    cols1 = set(df1.columns)
    cols2 = set(df2.columns)
    
    col_intersection = cols1.intersection(cols2)
    col_union = cols1.union(cols2)
    
    schema_score = len(col_intersection) / len(col_union) if len(col_union) > 0 else 0
    
    # ==========================================
    # ส่วนที่ 2: ตรวจสอบความคล้ายของข้อมูลภายใน (Data Content Similarity)
    # ==========================================
    # แปลงข้อมูลในแต่ละคอลัมน์ให้เป็น Set ของ Unique Values (แปลงเป็น string เพื่อให้เทียบข้าม Type ได้ง่ายขึ้น)
    dict_set1 = {col: set(df1[col].dropna().astype(str).unique()) for col in df1.columns}
    dict_set2 = {col: set(df2[col].dropna().astype(str).unique()) for col in df2.columns}
    
    match_scores = []
    
    # วนลูปเปรียบเทียบข้อมูลแบบไขว้ทุกคอลัมน์
    for col1, set1 in dict_set1.items():
        if not set1: continue
        best_match_for_col1 = 0
        
        for col2, set2 in dict_set2.items():
            if not set2: continue
            
            # คำนวณ Jaccard ของตัวข้อมูลด้านใน
            data_intersection = set1.intersection(set2)
            data_union = set1.union(set2)
            data_sim = len(data_intersection) / len(data_union) if len(data_union) > 0 else 0
            
            # เก็บค่าความคล้ายที่สูงที่สุดที่คอลัมน์นี้ไปตรงกับตารางที่ 2
            if data_sim > best_match_for_col1:
                best_match_for_col1 = data_sim
                
        match_scores.append(best_match_for_col1)
        
    # ค่าเฉลี่ยความคล้ายของข้อมูลภายในตาราง (ถ้าไม่มีข้อมูลเลยให้เป็น 0)
    data_score = np.mean(match_scores) if match_scores else 0
    
    # ==========================================
    # ส่วนที่ 3: คำนวณคะแนนรวม (Total Score)
    # ==========================================
    # ถ้าน้ำหนักเท่ากัน (Schema 50% + Data 50%)
    total_score = (schema_score * 0.5) + (data_score * 0.5)
    
    return {
        'table_name':df2_name,
        'schema_similarity': schema_score,
        'data_similarity': data_score,
        'total_similarity': total_score,
        'shared_column_names': list(col_intersection),
    }

if __name__ == "__main__":
    # --- วิธีใช้งาน ---
    # df = pd.read_csv("your_file.csv")
    df_example = pd.DataFrame({
        'customer_id': [101, 102, 103],  # Unique + No Null -> น่าจะเป็น PK
        'name': ['Somchai', 'Somsri', 'Somchai'], 
        'phone': ['081', None, '083']     # มี Null -> ไม่ใช่ PK
    })

    pks = find_candidate_primary_keys(df_example)
    print(f"🔑 คอลัมน์ที่สามารถเป็น Primary Key ได้คือ: {pks}")