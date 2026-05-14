# utils/helpers.py
import pandas as pd
import os

def mixing_faq_data(file_name="e_learning_faq.csv"):
    """
    Logic trộn dữ liệu từ file untitled0.py của Bảo
    """
    # Đường dẫn động dựa trên thư mục project
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_path = os.path.join(base_dir, 'data', file_name) # Giả sử bạn để file trong thư mục data
    
    if not os.path.exists(data_path):
        return None

    df_qa = pd.read_csv(data_path, sep=';', encoding='utf-8-sig')
    
    # Xóa cột rác
    df_qa = df_qa.loc[:, ~df_qa.columns.str.contains('^Unnamed')]
    
    # Trộn Câu hỏi + Câu trả lời + Phân loại (Logic gốc của Bảo)
    df_qa['combined_text'] = (
        "Question: " + df_qa['Question (Người học hỏi)'].astype(str) + ". " +
        "Answer: " + df_qa['Answer (Quản gia phản hồi)'].astype(str) + ". " +
        "Class: " + df_qa['Class (Phân loại)'].astype(str) + ". "
    )
    return df_qa