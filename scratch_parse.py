import re
import pandas as pd
from pathlib import Path

def parse_euros(s):
    if pd.isna(s) or not isinstance(s, str):
        return s
    s = s.replace('€', '').replace(' ', '').replace('\xa0', '').replace('\u202f', '').strip()
    try:
        return float(s.replace(',', '.'))
    except:
        return None

def parse_pct(s):
    if pd.isna(s) or not isinstance(s, str):
        return s
    s = s.replace('%', '').replace('pts', '').replace(' ', '').replace('\xa0', '').replace('\u202f', '').strip()
    try:
        return float(s.replace(',', '.'))
    except:
        return None

def parse_int(s):
    if pd.isna(s) or not isinstance(s, str):
        return s
    s = s.replace('clts', '').replace(' ', '').replace('\xa0', '').replace('\u202f', '').strip()
    try:
        return int(s)
    except:
        return None

def extract_tables(filepath):
    content = Path(filepath).read_text()
    
    # Extract tables
    tables = re.findall(r'(\|[^\n]+\|\n)((?:\|[-:]+)+\|\n)((\|[^\n]+\|\n)+)', content)
    
    extracted = []
    for header, sep, body in tables:
        lines = [header.strip()] + [b.strip() for b in body.strip().split('\n')]
        
        data = []
        for line in lines:
            row = [cell.strip() for cell in line.split('|')[1:-1]]
            data.append(row)
        
        df = pd.DataFrame(data[1:], columns=data[0])
        extracted.append(df)
        print("TABLE COLS:", df.columns.tolist())
    
    return extracted

tables = extract_tables("Rapport hebdomadaire/rapport hebdomadaire semaine 19.md")
for i, df in enumerate(tables):
    print(f"--- Table {i} ---")
    print(df.head(2))
