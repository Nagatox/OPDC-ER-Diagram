
import gspread

def openGSheet(filename, worksheet_number):
    # Authenticate using your downloaded JSON credentials file
    gc = gspread.service_account(filename="credentials.json")

    # Open the spreadsheet by its exact name or URL key
    # Make sure you shared this sheet with your service account email!
    spreadsheet = gc.open(filename)

    # Select the first worksheet (tab)
    worksheet = spreadsheet.get_worksheet(worksheet_number)

    return worksheet, spreadsheet

def getNextEmptyRowNo(worksheet):
    row_no = 1
    col_no = 1  # colume A
    while worksheet.cell(row_no, col_no).value != None:
        row_no += 1
    return row_no


def getUpdateRowNumber(response):
    updated_range = response.get('updates', {}).get('updatedRange')
    updated_row_num = int(updated_range.split('!')[-1].split(':')[0][1:])
    return updated_row_num

if __name__ == "__main__":

    worksheet = openGSheet(filename="OPDC-Database", worksheet_number=0)
    #row_no = getNextEmptyRowNo(worksheet)
    #print(row_no)
    #worksheet.update_acell(f"A{row_no}","xxx")
    #worksheet.update(f"E{row_no}", ["Alice", 25, "Bob", 30])
    
    #new_row = ["Charlie", 35,'=SUM(A1:B1)',"Charlie", 35,"Charlie", 35]
    #a = 123.12
    #new_row += [a]
    #new_row += [a]
    
    #worksheet.append_row(new_row)
    #worksheet.update_acell("C1", "=SUM(A1:B1)")

    #current_last_row = len(worksheet.get_all_values())
    #row_values = worksheet.row_values(current_last_row)
    #print(row_values)
    #print(row_values[1])

    all_values = worksheet.get_all_records()
    #print(all_values)
    for row in all_values:
        print(row['id'])



""" # ---- EXAMPLES OF WRITING DATA ----

# 1. Update a single specific cell
worksheet.update_acell("A1", "Name")
worksheet.update_acell("B1", "Age")

# 2. Update a batch range of cells
# Pass a list of lists corresponding to rows and columns
worksheet.update("A2:B3", [["Alice", 25], ["Bob", 30]])

# 3. Append a new row to the bottom of the existing sheet
new_row = ["Charlie", 35]
worksheet.append_row(new_row)

print("Data successfully written to Google Sheets!") 


all_records = worksheet.get_all_records()
print("--- ข้อมูลรูปแบบ Dictionary ---")
print(all_records)
# ผลลัพธ์ที่ได้จะหน้าตาประมาณนี้: [{'Name': 'Alice', 'Age': 24}, {'Name': 'Bob', 'Age': 30}]


# --- ทางเลือกที่ 2: ดึงข้อมูลทั้งหมดออกมาเป็น List ของ List (Array 2 มิติ) ---
# เหมาะสำหรับตารางทั่วไปที่ไม่ได้เน้นชื่อหัวคอลัมน์
all_values = worksheet.get_all_values()
print("\n--- ข้อมูลรูปแบบ List ของ List ---")
print(all_values)
# ผลลัพธ์ที่ได้: [['Name', 'Age'], ['Alice', '24'], ['Bob', '30']]


# --- ทางเลือกที่ 3: ดึงข้อมูลเฉพาะเจาะจงบางแถว หรือ บางคอลัมน์ ---
row_2_values = worksheet.row_values(2)  # ดึงข้อมูลแถวที่ 2 ทั้งหมด
col_1_values = worksheet.col_values(1)  # ดึงข้อมูลคอลัมน์ที่ 1 (A) ทั้งหมด

print("\n--- ข้อมูลเฉพาะแถว/คอลัมน์ ---")
print(f"ข้อมูลแถวที่ 2: {row_2_values}")
print(f"ข้อมูลคอลัมน์ที่ 1: {col_1_values}")


# --- ทางเลือกที่ 4: ดึงข้อมูลเฉพาะเจาะจงบางช่อง (Cell) ---
cell_a2_value = worksheet.acell("A2").value  # ระบุชื่อช่องตรงๆ เช่น A2
cell_by_index = worksheet.cell(2, 1).value  # ระบุตำแหน่ง (แถวที่ 2, คอลัมน์ที่ 1)

print("\n--- ข้อมูลเฉพาะเจาะจงช่อง ---")
print(f"ข้อมูลช่อง A2: {cell_a2_value}")
print(f"ข้อมูลช่อง แถว 2 คอลัมน์ 1: {cell_by_index}")


"""