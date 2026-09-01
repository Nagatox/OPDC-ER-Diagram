import re

from sentence_transformers import SentenceTransformer, util

model = SentenceTransformer('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')

def clean_text(text: str) -> str:
    """แยกคำด้วย _ และตัวอักษรพิเศษ แล้วแปลงเป็นตัวพิมพ์เล็ก"""
    return re.sub(r'[^a-zA-Z0-9ก-๙/]', ' ', text.lower()).strip()

def check_similar_word_hybrid_max_score(column_names: list, word_list: list):
    # 1. เช็ก Exact Match / Sub-word Match ก่อน (ได้คะแนน 1.0 ทันที)
    cleaned_words = [clean_text(w) for w in word_list]
    
    # 1. Exact Match & Sub-string Match Check (ภาษาไทย + อังกฤษ)
    for col in column_names:
        cleaned_col = clean_text(col)
        col_no_space = cleaned_col.replace(' ', '') # ลบช่องว่างออกเผื่อเปรียบเทียบคำไทยติดกัน
        col_tokens = cleaned_col.split()            # แยกคำด้วยช่องว่าง/อักขระพิเศษ
        
        for word in cleaned_words:
            word_no_space = word.replace(' ', '')
            
            # เช็ก 3 เงื่อนไขที่ถือว่าคล้ายกันมากๆ (ได้ 1.00 ทันที):
            # 1) ตรงกันแบบ 100%
            # 2) คำอยู่ใน tokens (เช่น 'kpi' ใน ['kpi', 'description'])
            # 3) มีคำซ้อนอยู่ข้างในภาษาไทย (เช่น 'ผลงาน' ซ้อนอยู่ใน 'ชื่อผลงาน')
            if (word_no_space == col_no_space) or \
               (word_no_space in col_tokens) or \
               (word_no_space in col_no_space) or \
               (col_no_space in word_no_space):
                return True, 1.00

    # 2. Semantic NLP Vector (กรณีความหมายคล้ายกันแต่คนละคำ)
    col_embeddings = model.encode(column_names, convert_to_tensor=True)
    word_embeddings = model.encode(word_list, convert_to_tensor=True)
    
    cosine_scores = util.cos_sim(col_embeddings, word_embeddings)
    max_score = cosine_scores.max().item()
    
    
    # ถ้าคะแนน NLP เกิน 0.45 ถือว่ามีการจับคู่สำเร็จ
    has_match = max_score >= 0.45
    return has_match, round(max_score, 4)

def get_multi_group_max_score(column_names: list, group1: list, group2: list) -> float:
    """
    ต้องพบคำจากทั้ง group1 และ group2 ใน list of columns จึงจะคำนวณคะแนน
    """
    matched1, score1 = check_similar_word_hybrid_max_score(column_names, group1)
    matched2, score2 = check_similar_word_hybrid_max_score(column_names, group2)
    
    # เงื่อนไขสำคัญ: ต้องมีคำจากทั้ง 2 กลุ่ม
    if matched1 and matched2:
        # คืนค่าคะแนนเฉลี่ย หรือค่าเฉลี่ยถ่วงน้ำหนักของทั้ง 2 กลุ่ม
        return round((score1 + score2) / 2, 4)
    
    return 0.0

def x_check_similar_word(words, column_names):
    # โหลด Model ภาษาไทย/Multi-language
    

    # แปลงคำเป็น Vector
    word_embeddings = model.encode(words, convert_to_tensor=True)
    col_embeddings = model.encode(column_names, convert_to_tensor=True)

    """ # วนลูปหาคู่ที่มีความหมายใกล้เคียงกัน (Threshold เช่น > 0.4 หรือ 0.5)
    threshold = 0.45

    for i, col in enumerate(column_names):
        # คำนวณ Cosine Similarity ระหว่าง col ปัจจุบันกับทุกคำใน words
        cosine_scores = util.cos_sim(col_embeddings[i], word_embeddings)[0]
        
        for j, word in enumerate(words):
            score = cosine_scores[j].item()
            if score >= threshold:
                print(f"Column: '{col}' <---> Word: '{word}' (Score: {score:.4f})") """

    cosine_scores = util.cos_sim(col_embeddings, word_embeddings)
    max_score = cosine_scores.max().item()
    
    return round(max_score, 4)

if __name__ == "__main__":

    words = ['ตัวชี้วัด', 'ยอดขาย', 'ชื่อลูกค้า', 'kpi']
    column_names = ['kpi', 'target', 'customer_name', 'sales_amount', 'id']
    column_name = 'kpi'

    max_score = check_similar_word(words, column_names)
    print(max_score)

    max_score = check_similar_word(words, column_names)
    print(max_score)