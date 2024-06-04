import re
import pandas as pd
import google.generativeai as genai
import os
from dotenv import load_dotenv
import time
import json

load_dotenv()

GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY', None)

genai.configure(api_key=GOOGLE_API_KEY)

model = genai.GenerativeModel('gemini-1.5-flash')

# 讀取 CSV 文件
df = pd.read_csv('result.csv')

# 添加新的欄位以儲存生成的內容
df['generated_content'] = ''

# 遍歷每一行
for index, row in df.iterrows():
    # 處理每一行的數據
    response = model.generate_content(
        '''```''' + str(row) + '''```''' + '''
        1.請統計出留言已最適當的方式評論店家。
        2.請嚴格以json格式輸出，除了json格式以外，不要有其他說明。
        3.json只包含 pros、cons 欄位。
        4.pros、cons 1-3個且盡量具體，避免適用好、佳等模糊用詞，太通用的內容，就不用列出。
        5.cons 盡量不要提及店家等待時間長等，太通用的內容，就不用列出。''')

    text = re.sub(r'```json|```', '', response.text).strip()

    # 驗證生成的內容是否為 JSON 格式
    try:
        json_data = json.loads(text)
        if not isinstance(json_data, dict) or 'pros' not in json_data or 'cons' not in json_data:
            raise ValueError("生成的內容缺少必要的 'pros' 和 'cons' 欄位")
    except json.JSONDecodeError:
        raise ValueError(f"生成的內容不是有效的 JSON 格式: {text}")

    print(json.dumps(json_data, ensure_ascii=False, indent=2))

    df.at[index, 'generated_content'] = text

    df.to_csv('result.csv', index=False)

    time.sleep(5)
