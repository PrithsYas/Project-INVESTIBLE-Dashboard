from flask import Flask, render_template, request
import pandas as pd
import difflib
from datetime import datetime
import feedparser
from textblob import TextBlob
from pytrends.request import TrendReq
import numpy as np
import requests
from bs4 import BeautifulSoup
import webbrowser
import os
import sys

def resource_path(relative_path):
    """Get absolute path to resource for PyInstaller executable or script"""
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)


app = Flask(__name__)
stock_df = pd.read_csv(resource_path("nse_stock_list.csv"))
stock_df.columns = stock_df.columns.str.strip().str.lower()

sector_pe_df = pd.read_csv(resource_path("sector_pe_data.csv"))
sector_pe_df["sector"] = sector_pe_df["sector"].str.strip().str.lower()

def resolve_ticker(user_input):
    user_input = user_input.lower().strip()
    matches = difflib.get_close_matches(user_input, stock_df["name"].str.lower(), n=1, cutoff=0.6)
    if matches:
        return stock_df[stock_df["name"].str.lower() == matches[0]].iloc[0]
    return None

def get_valuation(pe_ratio):
    try:
        pe = float(pe_ratio)
        if pe < 15:
            return "Undervalued"
        elif pe < 30:
            return "Fair"
        else:
            return "Overvalued"
    except:
        return "N/A"

def fetch_headlines(stock_name):
    try:
        query = stock_name.replace(" ", "+")
        url = f"https://news.google.com/rss/search?q={query}+stock+india"
        feed = feedparser.parse(url)
        return [entry.title for entry in feed.entries][:4] or ["No news found."]
    except Exception as e:
        print("[News Fetch Error]", e)
        return ["News unavailable."]

def analyze_sentiment(headlines):
    try:
        score = sum(TextBlob(head).sentiment.polarity for head in headlines)
        if score > 0.3: return "Positive"
        elif score < -0.3: return "Negative"
        return "Neutral"
    except:
        return "Neutral"

def compute_score_from_sentiment(sentiment):
    return {"Positive": 8.5, "Neutral": 6.0, "Negative": 3.0}.get(sentiment, 5.0)

def get_trend_momentum(stock_name):
    try:
        pytrends = TrendReq(hl='en-US', tz=330)
        query = stock_name.lower().replace("&", "and").replace(" ", "+")
        pytrends.build_payload([query], cat=0, timeframe='now 7-d', geo='IN')
        data = pytrends.interest_over_time()
        if data.empty or query not in data.columns:
            return "Unavailable"
        scores = data[query].dropna().values
        avg, start, end = np.mean(scores), np.mean(scores[:3]), np.mean(scores[-3:])
        if avg > 70 and end > start * 1.2:
            return "📈 Strong Uptrend — Retail Interest Surging"
        elif avg > 70 and end < start * 0.8:
            return "⚠️ Recent Peak — Trend Cooling Off"
        elif avg > 40:
            return "🔁 Steady Public Attention — No Strong Moves"
        elif avg < 30 and end < start:
            return "💤 Very Low Interest — Off Radar"
        else:
            return "🪨 Flat — No Buzz, No Moves"
    except Exception as e:
        print("[Trend Fetch Error]", e)
        return "Unavailable"

def get_financials_growth(ticker):
    try:
        url = f"https://www.screener.in/company/{ticker.upper().replace('.NS', '')}/consolidated/"
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(r.text, "html.parser")
        tables = soup.find_all("table")
        income_table = next((t for t in tables if "Sales" in t.text and "Profit before tax" in t.text), None)
        if not income_table:
            return "Data Unavailable", "Data Unavailable"
        rows = income_table.find_all("tr")
        sales = [td.text.strip().replace(",", "") for td in rows[1].find_all("td")]
        profits = [td.text.strip().replace(",", "") for td in rows[-2].find_all("td")]
        if len(sales) < 2 or len(profits) < 2:
            return "Insufficient Data", "Insufficient Data"
        q = [th.text.strip() for th in rows[0].find_all("th")][1:]
        s1, s0 = float(sales[-1]), float(sales[-2])
        p1, p0 = float(profits[-1]), float(profits[-2])
        return f"{(s1-s0)/s0*100:+.1f}% QoQ ({q[-1]})", f"{(p1-p0)/p0*100:+.1f}% QoQ ({q[-1]})"
    except Exception as e:
        print("[Financials Error]", e)
        return "Unavailable", "Unavailable"

def get_sector_pe(ticker, name):
    static_sector_pe = {
        "banking": 18.2,
        "information technology": 26.4,
        "oil ": 12.9,
        "Pharma": 28.1,
        "auto": 22.5,
        "metals & mining": 9.7,
        "Fmcg": 41.1,
        "paints": 52.3,
        "cement": 34.0,
        "real estate": 19.5,
        "insurance": 42.2,
        "financial services": 33.0,
        "chemicals": 31.2,
        "others": 22.0
    }

    # Try to get sector from stock_df
    try:
        row = stock_df[(stock_df["ticker"].str.lower() == ticker.lower())].iloc[0]
        sector = str(row.get("sector", "others")).strip().lower()
        sector_pe = static_sector_pe.get(sector, static_sector_pe["others"])
        return sector.title(), str(sector_pe)
    except Exception as e:
        print("[Hardcoded Sector PE Error]", e)
        return "Others", str(static_sector_pe["others"])

@app.route("/")
def search():
    return render_template("search.html")

@app.route("/dashboard")
def dashboard_view():
    row = resolve_ticker(request.args.get("ticker", ""))
    if row is None:
        return render_template("dashboard.html", error="Stock not found.")
    try:
        name = row["name"]
        ticker = row["ticker"]
        pe = row.get("pe ratio", "N/A")
        valuation = get_valuation(pe)
        headlines = fetch_headlines(name)
        sentiment = analyze_sentiment(headlines)
        score_val = compute_score_from_sentiment(sentiment)
        momentum = get_trend_momentum(name)
        rev_growth, prof_growth = get_financials_growth(ticker)
        sector_name, sector_pe = get_sector_pe(ticker, name)

        return render_template("dashboard.html",
            name=name, pe=pe, valuation=valuation, sentiment=sentiment,
            score=f"{score_val}/10", score_value=score_val,
            momentum=momentum, revenue_growth=rev_growth, profit_growth=prof_growth,
            sector_name=sector_name, sector_pe=sector_pe,
            news=headlines, last_updated=datetime.now().strftime("%d %b, %I:%M %p")
        )
    except Exception as e:
        print("[ERROR] Failed to fetch stock data:", e)
        return render_template("dashboard.html", error="Something went wrong.")

if __name__ == "__main__":
    app.run(debug=True, port=5001)
