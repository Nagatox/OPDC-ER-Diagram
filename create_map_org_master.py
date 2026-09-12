import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import gspread
from google.oauth2.service_account import Credentials

# 1. เชื่อมต่อ Google Sheets API
scopes = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

creds = Credentials.from_service_account_file('credentials.json', scopes=scopes)
gc = gspread.authorize(creds)

# 2. เปิด Google Sheet และอ่านข้อมูล
spreadsheet = gc.open('ORG_MASTER_FROM_PAS')  # หรือใช้ gc.open_by_key('SPREADSHEET_ID')

ws1 = spreadsheet.worksheet('MASTER')
ws2 = spreadsheet.worksheet('INPUT')

data1 = ws1.get_all_values()
data2 = ws2.get_all_values()

df1 = pd.DataFrame(data1)
df2 = pd.DataFrame(data2)

# ดึงชื่อหน่วยงานจาก Sheet PAS (คอลัมน์ D / index 3)
sheet1_names = df1[3].fillna('').astype(str).tolist()

# 3. เทรน TF-IDF Vectorizer
vectorizer = TfidfVectorizer(analyzer='char_wb', ngram_range=(2, 4))
tfidf_matrix_s1 = vectorizer.fit_transform(sheet1_names)

# สร้าง DataFrame ขนาดเท่ากับ df1 สำหรับเก็บเฉพาะผลลัพธ์ใน Column E และ Column F
# Index 0 -> Column E (ชื่อหน่วยงานใกล้เคียงจาก Sheet 2)
# Index 1 -> Column F (ค่า best_score)
#output_df = pd.DataFrame("", index=range(len(df1)), columns=[0, 1])
output_df = pd.DataFrame("", index=range(len(df1)), columns=[0])

unmatched_list = []

# 4. วนลูปอ่าน Sheet 2 ทีละ Row
for idx, row in df2.iterrows():
    s2_name = str(row[0]).strip()
    if not s2_name or s2_name == 'nan':
        continue
    
    s2_name_clean = s2_name.replace('\n', ' ')
    tfidf_s2 = vectorizer.transform([s2_name_clean])
    similarities = cosine_similarity(tfidf_s2, tfidf_matrix_s1)[0]
    
    best_match_idx = similarities.argmax()
    best_score = similarities[best_match_idx]
    best_matched_s1_name = sheet1_names[best_match_idx]
    
    # 5. จัดเก็บข้อมูลเฉพาะผลลัพธ์
    if best_score > 0.85:
        output_df.at[best_match_idx, 0] = s2_name                      # ใส่ชื่อลงใน Column E
        #output_df.at[best_match_idx, 1] = round(float(best_score), 4)  # ใส่ best_score ลงใน Column F
    else:
        unmatched_list.append({
            'Sheet 2 Name': s2_name,
            'Closest Match in Sheet 1': best_matched_s1_name,
            'Similarity Score': round(float(best_score), 4)
        })

# 6. อัปเดตเฉพาะคอลัมน์ E และ F บน Google Sheets (เริ่มที่ช่อง E1)
ws1.update(output_df.values.tolist(), 'E1')

# 7. บันทึก/อัปเดต Sheet 'Unmatched'
df_unmatched = pd.DataFrame(unmatched_list)

try:
    ws_unmatched = spreadsheet.worksheet('Unmatched')
    ws_unmatched.clear()
except gspread.WorksheetNotFound:
    ws_unmatched = spreadsheet.add_worksheet(title='Unmatched', rows='100', cols='10')

if not df_unmatched.empty:
    unmatched_data = [df_unmatched.columns.tolist()] + df_unmatched.values.tolist()
    ws_unmatched.update(unmatched_data, 'A1')

print("อัปเดตเฉพาะ Column E และ F เรียบร้อยแล้ว!")
print(f"จำนวนรายการที่ไม่ผ่านเกณฑ์ (> 0.5): {len(df_unmatched)} รายการ")