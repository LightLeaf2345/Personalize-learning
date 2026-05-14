import pyodbc
from environ import Env
import os

env = Env()
Env.read_env()  # đọc file .env

# Thông tin kết nối của bạn
conn_string = (
    f"DRIVER={{{env('DB_DRIVER')}}};"
    f"SERVER={env('DB_HOST')};"
    f"DATABASE={env('DB_NAME')};"
    f"UID={env('DB_USER')};"
    f"PWD={env('DB_PASSWORD')};"
    "TrustServerCertificate=yes;"
)

try:
    print("--- ĐANG KIỂM TRA KẾT NỐI SQL SERVER ---")
    conn = pyodbc.connect(conn_string)
    cursor = conn.cursor()

    # Thử lấy câu hỏi "I bought ___ apple..." để xem phần giải thích
    cursor.execute("SELECT explanation FROM AppGrammar WHERE correct_answer = 'an'")
    row = cursor.fetchone()

    if row:
        print("Kết quả lấy được từ Database là:")
        print(f">>> {row[0]}")
        
        # Kiểm tra xem có phải dấu hỏi không
        if "?" in row[0]:
            print("\n❌ CẢNH BÁO: Dữ liệu TRONG SQL Server đang bị lỗi dấu hỏi.")
            print("Giải pháp: Bạn cần chạy lại file SQL và nhớ thêm chữ N trước các chuỗi tiếng Việt.")
        else:
            print("\n✅ THÀNH CÔNG: SQL Server trả về tiếng Việt chuẩn!")
            print("Giải pháp: Lỗi nằm ở cách Django hiển thị hoặc Cache trình duyệt.")
    else:
        print("Không tìm thấy dữ liệu mẫu!")

except Exception as e:
    print(f"Lỗi kết nối: {e}")