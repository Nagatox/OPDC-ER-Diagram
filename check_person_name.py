#import spacy
import pandas as pd
from pythainlp.tag import NER

import ast
import random
import re

# โหลดโมเดลภาษาอังกฤษขนาดเล็ก (เร็วและเบา)
""" nlp = spacy.load("en_core_web_sm")

def is_person_column(series, threshold=0.8, sample_size=100):
    # สุ่มตรวจ sample_size แถวเพื่อความรวดเร็ว
    samples = series.dropna().sample(min(sample_size, len(series))).astype(str)
    
    person_count = 0
    for text in samples:
        doc = nlp(text)
        # ตรวจสอบว่า AI มองคำนี้เป็น "PERSON" หรือไม่
        if any(ent.label_ == "PERSON" for ent in doc.ents):
            person_count += 1
            
    # คำนวณเปอร์เซ็นต์ความมั่นใจ
    match_ratio = person_count / len(samples) if len(samples) > 0 else 0
    return match_ratio >= threshold, match_ratio """


# 1. ประกาศตัว NER ให้ถูกต้อง
""" thai_ner = NER(engine="thainer")

def check_if_thai_name_column(col_data, threshold=0.7, sample_size=50):
    # สุ่มตรวจเพื่อความรวดเร็ว ไม่ให้บอทค้าง
    samples = col_data.dropna().sample(min(sample_size, len(col_data))).astype(str)
    
    person_count = 0
    for text in samples:
        tags = thai_ner.tag(text)
        # ตรวจสอบว่าในคำที่ตัดมา มีแท็กที่เป็น 'PERSON' หรือไม่
        if any("PERSON" in tag[1] for tag in tags):
            person_count += 1
            
    match_ratio = person_count / len(samples) if len(samples) > 0 else 0
    return match_ratio >= threshold, match_ratio """




import re
import pandas as pd
from pythainlp.tag.named_entity import NER

# โหลด NER engine="thainer"
thai_ner = NER(engine="thainer")

# 1. กำหนดเซตของชื่อคอลัมน์ที่เป็น "ชื่อบุคคล" แบบเป๊ะๆ เท่านั้น (Exact Match)
ALLOWED_EXACT_PERSON_NAMES = {
    "name",
    "fullname",
    "firstname",
    "lastname",
    "first_name",
    "last_name",
    "fname",
    "lname",
    "surname",
    "ชื่อ",
    "นามสกุล",
    "ชื่อจริง",
    "ชื่อผู้เสียภาษี",
    "ผู้ประกอบการ",
    "ผู้ขอ",
    "ผู้ยื่น",
}

# 2. คลังคำ Blacklist คัดออกสำหรับข้อมูลในแถว (Data)
NON_PERSON_KEYWORDS = {
    "ภาษี",
    "ค่าธรรมเนียม",
    "อากร",
    "ทรัพย์สิน",
    "สาธารณูปโภค",
    "เบ็ดเตล็ด",
    "รายได้",
    "ดอกเบี้ย",
    "ค่าปรับ",
    "อบจ",
    "เทศบาล",
    "บริษัท",
    "ห้างหุ้นส่วน",
}


def check_column_name_score(col_name: str) -> float:
    """คำนวณคะแนนชื่อคอลัมน์ (Exact Match 100%)

    ถ้าไม่ใช่คำเป๊ะๆ ใน ALLOWED_EXACT_PERSON_NAMES ให้คืนค่า 0.0 ทันที
    """
    if not col_name:
        return 0.0

    # แปลงเป็นตัวพิมพ์เล็กและตัดช่องว่าง
    clean_col = str(col_name).strip().lower()

    # เช็กเงื่อนไขแบบ Exact Match 100%
    if clean_col in ALLOWED_EXACT_PERSON_NAMES:
        return 0.60

    return 0.0  # สำหรับ agc_name, min_name, name_en, project_name ฯลฯ จะได้ 0.00 ทันที


def is_thai_name_column(
    col_data: pd.Series,
    col_name: str = "",
    threshold: float = 0.35,
    sample_size: int = 30,
):
    """ฟังก์ชันสแกนคอลัมน์เพื่อตรวจว่าเป็นชื่อคนไทยหรือไม่"""

    # -------------------------------------------------------------
    # ส่วนที่ 1: ตรวจสอบชื่อคอลัมน์ (Column Score - Max 0.60)
    # -------------------------------------------------------------
    col_score = check_column_name_score(col_name)

    # -------------------------------------------------------------
    # ส่วนที่ 2: ตรวจสอบข้อมูลในแถวด้วย NER (Data Score - Max 0.40)
    # -------------------------------------------------------------
    data_score = 0.0
    cleaned_data = col_data.dropna().astype(str)

    if not cleaned_data.empty:
        samples = cleaned_data.sample(
            min(sample_size, len(cleaned_data)), random_state=42
        )
        person_match_count = 0

        for text in samples:
            tags = thai_ner.tag(text)

            has_person = False
            for tag in tags:
                word = tag[0]
                ner_tag = tag[-1]  # NER Tag

                if "PERSON" in ner_tag:
                    # คัดคำใน Blacklist ออก
                    if not any(kw in word for kw in NON_PERSON_KEYWORDS):
                        has_person = True
                        break

            if has_person:
                person_match_count += 1

        match_ratio = person_match_count / len(samples)
        data_score = match_ratio

    # -------------------------------------------------------------
    # ส่วนที่ 3: เลือกค่าที่มากที่สุด (MAX Score Selection)
    # -------------------------------------------------------------
    col_score = round(col_score, 4)
    data_score = round(data_score, 4)

    max_score = round(max(col_score, data_score), 4)
    is_name_col = max_score >= threshold

    #print(
    #    f"Column: '{col_name}' | Col Score: {col_score:.2f} | Data Score:"
    #    f" {data_score:.2f} | Max Score: {max_score:.2f}"
    #)

    return is_name_col, max_score



if __name__ == "__main__":
    # --- วิธีใช้งาน ---
    #df = pd.DataFrame({"col1": ["John Doe", "Jane Smith", "Robert"], "col2": [25, 30, 35]})
    #is_person, confidence = is_person_column(df["col1"])
    #print(f"เป็นคอลัมน์ชื่อคนใช่ไหม: {is_person} (ความมั่นใจ {confidence*100}%)")
    # --- ตัวอย่างตอนเอาไปวนลูปใน DataFrame ---
    #for col_name, col_data in df.items():
    #    is_name, confidence = check_if_thai_name_column(col_data)
    #    if is_name:
    #        print(f"📌 คอลัมน์ [{col_name}] น่าจะเป็น 'ชื่อคนไทย' (ความมั่นใจ {confidence*100:.2f}%)")

    #from pythainlp.tag import NER
    # ทดสอบเรียกใหม่อีกครั้ง หลังติดตั้ง python-crfsuite
    #thai_ner = NER(engine="thainer")
    #print(thai_ner.tag("สมชาย มั่นคง")) 
    # ผลลัพธ์ที่ควรได้: [('สมชาย', 'B-PERSON'), (' ', 'O'), ('มั่นคง', 'I-PERSON')]

    # --- 🚀 ทดสอบใช้งานจริงกับ DataFrame ของคุณ ---
    # สมมติตารางข้อมูลของคุณ
    # data = {
    #     "customer_id": [101, 102, 103],
    #     "full_name": ["สมชาย มั่นคง", "สมศรี มีชัย", "กนกวรรณ นามดี"],
    #     "city": ["กรุงเทพ", "เชียงใหม่", "ภูเก็ต"]
    # }
    # df = pd.DataFrame(data)

    # print("=== เริ่มการสแกนหาคอลัมน์ 'ชื่อคน' เชิงลึก ===\n")

    # # ลูปผ่านชื่อคอลัมน์และข้อมูลด้านใน (ใช้ .items() ตามที่คุยกันก่อนหน้านี้)
    # for col_name, col_data in df.items():
    #     is_name, confidence = is_thai_name_column(col_data)
        
    #     if is_name:
    #         print(f"🎯 เจอแล้ว! คอลัมน์ [{col_name}] -> เป็น 'ชื่อคนไทย' แน่นอน")
    #         print(f"   (ความมั่นใจจากการสุ่มตรวจ: {confidence * 100:.2f}%)\n")
    #     else:
    #         print(f"❌ คอลัมน์ [{col_name}] -> ไม่ใช่ชื่อคน (ความมั่นใจ: {confidence * 100:.2f}%)")

    db_string = "[{'name': 'ภาษีที่ดินและสิ่งปลูกสร้าง', 'amount': '779.476306'}, {'name': 'ภาษีบำรุงท้องที่', 'amount': '0.047141'}, {'name': 'ภาษีป้าย', 'amount': '74.065213'}, {'name': 'ภาษีบำรุง อบจ. จากสถานค้าปลีกยาสูบ', 'amount': 0}, {'name': 'ภาษีบำรุง อบจ. จากสถานค้าปลีกน้ำมัน', 'amount': 0}, {'name': 'ค่าธรรมเนียมบำรุง อบจ. จากผู้เข้าพักโรงแรม', 'amount': 0}, {'name': 'อากรการฆ่าสัตว์', 'amount': 0}, {'name': 'อากรรังนกอีแอ่น', 'amount': 0}, {'name': 'ทรัพย์สิน', 'amount': '105.884499'}, {'name': 'สาธารณูปโภค', 'amount': '4.746032'}, {'name': 'เบ็ดเตล็ด', 'amount': '8.330361'}, {'name': 'ภาษีโรงเรือนและที่ดิน', 'amount': '47.263030'}]"
    
    db_data = ast.literal_eval(db_string)

    # ดึงเฉพาะคอลัมน์ 'name' ออกมาเป็น List
    df['column'] = pd.DataFrame(db_data)
    x, y = is_thai_name_column (df['column'])
    print (x)
    print (y)