import io
import requests

@st.cache_data(ttl=30)
def load_data():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    
    df_temp = pd.read_csv(io.BytesIO(response.content), header=None)
    header_row = 0
    for i in range(len(df_temp)):
        row_str = str(df_temp.iloc[i].values)
        if '출하처' in row_str or 'SHIPMENT' in row_str or '제품명' in row_str:
            header_row = i
            break
            
    df = pd.read_csv(io.BytesIO(response.content), header=header_row)
    df.columns = df.columns.astype(str).str.strip()
    return df
