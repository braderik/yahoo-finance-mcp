"""
Yahoo Finance MCP Server (FastMCP version for ChatGPT compatibility)
Wraps yfinance in FastMCP with SSE transport
"""
from fastmcp import FastMCP
import yfinance as yf
import json
from typing import Optional
from datetime import datetime

mcp = FastMCP("Yahoo Finance")

@mcp.tool()
def get_stock_info(symbol: str) -> str:
    """Get comprehensive stock data including price, volume, and company info."""
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        return json.dumps({
            "symbol": symbol.upper(),
            "name": info.get("longName"),
            "price": info.get("currentPrice") or info.get("regularMarketPrice"),
            "currency": info.get("currency"),
            "marketCap": info.get("marketCap"),
            "peRatio": info.get("trailingPE"),
            "52WeekHigh": info.get("fiftyTwoWeekHigh"),
            "52WeekLow": info.get("fiftyTwoWeekLow"),
            "volume": info.get("volume"),
            "avgVolume": info.get("averageVolume"),
            "dividendYield": info.get("dividendYield"),
            "sector": info.get("sector"),
            "industry": info.get("industry"),
            "summary": info.get("longBusinessSummary", "")[:500]
        }, indent=2)
    except Exception as e:
        return f"Error: {str(e)}"

@mcp.tool()
def get_historical_prices(symbol: str, period: str = "1mo", interval: str = "1d") -> str:
    """
    Get historical OHLCV data.
    period: 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max
    interval: 1m, 5m, 15m, 30m, 60m, 1d, 1wk, 1mo
    """
    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period=period, interval=interval)
        if hist.empty:
            return f"No data found for {symbol}"
        hist = hist.reset_index()
        hist['Date'] = hist['Date'].astype(str)
        return hist.tail(20).to_json(orient="records", date_format="iso")
    except Exception as e:
        return f"Error: {str(e)}"

@mcp.tool()
def get_stock_news(symbol: str) -> str:
    """Get latest news articles for a stock."""
    try:
        ticker = yf.Ticker(symbol)
        news = ticker.news
        if not news:
            return f"No news found for {symbol}"
        articles = []
        for item in news[:5]:
            articles.append({
                "title": item.get("content", {}).get("title", item.get("title", "No title")),
                "publisher": item.get("content", {}).get("provider", {}).get("displayName", "Unknown"),
                "link": item.get("content", {}).get("canonicalUrl", {}).get("url", "")
            })
        return json.dumps(articles, indent=2)
    except Exception as e:
        return f"Error: {str(e)}"

@mcp.tool()
def get_financial_statement(symbol: str, statement_type: str = "income") -> str:
    """
    Get financial statements.
    statement_type: income, balance, cashflow
    """
    try:
        ticker = yf.Ticker(symbol)
        if statement_type == "income":
            data = ticker.financials
        elif statement_type == "balance":
            data = ticker.balance_sheet
        elif statement_type == "cashflow":
            data = ticker.cashflow
        else:
            return "Invalid statement_type. Use: income, balance, or cashflow"
        
        if data.empty:
            return f"No {statement_type} data for {symbol}"
        data.columns = data.columns.astype(str)
        return data.head(10).to_json(orient="index", indent=2)
    except Exception as e:
        return f"Error: {str(e)}"

@mcp.tool()
def get_recommendations(symbol: str) -> str:
    """Get analyst recommendations."""
    try:
        ticker = yf.Ticker(symbol)
        recs = ticker.recommendations
        if recs is None or recs.empty:
            return f"No recommendations for {symbol}"
        recs = recs.reset_index()
        recs['Date'] = recs['Date'].astype(str) if 'Date' in recs.columns else ""
        return recs.tail(10).to_json(orient="records")
    except Exception as e:
        return f"Error: {str(e)}"

if __name__ == "__main__":
    mcp.run(transport="sse", host="0.0.0.0", port=8000)
