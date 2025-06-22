import pandas as pd
import requests
from bs4 import BeautifulSoup
import time

def fetch_pe_from_screener(ticker):
    try:
        url = f"https://www.screener.in/company/{ticker}/"
        headers = {"User-Agent": "Mozilla/5.0"}
        resp = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(resp.text, "html.parser")

        pe = "N/A"
        ratios = soup.select("ul#top-ratios li")
        for r in ratios:
            if "P/E" in r.text or "Stock P/E" in r.text:
                pe_span = r.find("span", class_="number")
                if pe_span:
                    pe = pe_span.text.strip()
                    break
        return pe
    except Exception as e:
        print(f"[Error fetching {ticker}]:", e)
        return "N/A"

# 🔁 Load existing CSV
df = pd.read_csv("nse_stock_list.csv")

# 🔄 Update PE ratios
for i, row in df.iterrows():
    name = row['name']
    print(f"Fetching PE for {name}...")
    pe = fetch_pe_from_screener(name)
    df.at[i, "pe ratio"] = pe
    time.sleep(1.2)  # avoid getting blocked

# 💾 Save updated file
df.to_csv("nse_stock_list.csv", index=False)
print("✅ PE values updated in nse_stock_list.csv")
