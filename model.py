import yfinance as yf
import pandas as pd
import pandas_datareader.data as web
import datetime
import bs4 as bs
import requests
from AVapikey import get_AVapikey

AV_apikey = get_AVapikey()
risk_free_rate = yf.Ticker("^TNX").info.get("previousClose") / 100
sp500 = yf.download("^GSPC", start = "1996-11-22", end = datetime.datetime.now().strftime("%Y-%m-%d"))
market_return = ((1 + sp500["Adj Close"].pct_change().dropna().mean()) ** 252) - 1

# Sustained growth rate
def find_SGR(ticker):
    try:
        stock = yf.Ticker(ticker)
        ROE = stock.info.get("returnOnEquity")
        dividends_paid = abs(stock.cashflow.loc["Cash Dividends Paid"].head(1).values[0])
        net_income = stock.incomestmt.loc["Net Income"].head(1).values[0]
        retention_rate = 1 - (dividends_paid / net_income)
        
        return ROE * retention_rate
    
    except:
        return 100 # arbitrary maximum

# Long-term growth rate (nominal interest rate)
def find_LTGR():
    data = web.DataReader('DGS10', 'fred', datetime.datetime(2023, 1, 1), datetime.datetime.now())
    return data.iloc[-1]["DGS10"] / 100

def find_WACC(ticker):
    stock = yf.Ticker(ticker)
    beta = stock.info.get("beta")
    cost_of_equity = risk_free_rate + beta * (market_return - risk_free_rate)

    interest_expense = stock.financials.loc["Interest Expense"].head(1).values[0]
    total_debt = stock.balancesheet.loc["Total Debt"].head(1).values[0]
    cost_of_debt = interest_expense / total_debt

    market_cap = stock.info.get("marketCap")
    equity_weight = market_cap / (market_cap + total_debt)
    debt_weight = 1 - equity_weight
    tax_rate = stock.financials.loc["Tax Rate For Calcs"].head(1).values[0]

    wacc = (cost_of_equity * equity_weight) + (cost_of_debt * debt_weight * (1 - tax_rate))
    """print("Risk-Free Rate:", risk_free_rate)
    print("Market Return:", market_return)
    print("Equity Market Risk Premium:", (market_return - risk_free_rate))
    print("Beta:", beta)
    print("Cost of Equity:", cost_of_equity)
    print("Equity Weight:", equity_weight)
    print("Cost of Debt:", cost_of_debt)
    print("Debt Weight:", debt_weight)
    print("Tax Rate:", tax_rate)"""
    return wacc

def DCF(ticker: str, years_to_project: int = 5) -> float:
    try:
        stock = yf.Ticker(ticker)
        url = f'https://www.alphavantage.co/query?function=CASH_FLOW&symbol={ticker}&apikey={AV_apikey}'
        r = requests.get(url)
        data = r.json()
        
        fcf = pd.DataFrame({"Year": [],
                        "FreeCashFlow": []})
        
        for dict in data["annualReports"]:
            year = int(dict["fiscalDateEnding"][:4])
            ocf = int(dict["operatingCashflow"])
            capex = int(dict["capitalExpenditures"])
            cashflow = ocf - capex
            entry = [year, cashflow]
            fcf.loc[len(fcf.index)] = entry

        fcf = fcf.sort_values(by = "Year")
        avg_growth = fcf["FreeCashFlow"].pct_change().mean()

        latest_historical_info = fcf.iloc[-1]
        future_years = [i for i in range(latest_historical_info["Year"] + 1, latest_historical_info["Year"] + years_to_project + 1)]

        for yr in future_years:
            proj_fcf = (latest_historical_info["FreeCashFlow"] * (1 + avg_growth) ** (yr - latest_historical_info["Year"]))
            fcf.loc[len(fcf.index)] = [yr, proj_fcf]
        
        perpetual_growth_rate = min(find_SGR(ticker), find_LTGR())
        discount_rate = find_WACC(ticker)

        terminal_value = fcf.iloc[-1]["FreeCashFlow"] * (1 + perpetual_growth_rate) / (discount_rate - perpetual_growth_rate)
        future_fcf_sum = fcf.tail(years_to_project)["FreeCashFlow"].sum() + terminal_value

        balance_sheet = stock.quarterly_balance_sheet
        cash_casheq = balance_sheet.loc["Cash Cash Equivalents And Short Term Investments"].iloc[0]
        total_debt = balance_sheet.loc["Total Debt"].iloc[0]
        equity_value = future_fcf_sum + cash_casheq - total_debt
        shares_outstanding = balance_sheet.loc["Share Issued"].iloc[0]
        
        dcf_pps = (equity_value / shares_outstanding)
        return round(dcf_pps, 2)
    except Exception as e:
        return e

def compare(ticker, years_to_project = 5):
    comp_stock = yf.Ticker(ticker)
    curr_price = comp_stock.info.get("previousClose")
    DCF_price = DCF(ticker, years_to_project)
    comp_name = comp_stock.info.get("shortName")
    return comp_name + " is currently at $" + str(curr_price) + ", and its DCF projection is $" + str(DCF_price)

def get_sp500_dict():
    resp = requests.get("https://en.wikipedia.org/wiki/List_of_S%26P_500_companies")
    soup = bs.BeautifulSoup(resp.text, 'lxml')
    table = soup.find('table', {'class': 'wikitable sortable'})
    tickers = {}
    for row in table.findAll('tr')[1:]:
        elems = row.findAll('td')
        ticker = elems[0].text.replace("\n", "")
        name = elems[1].text.replace("\n", "")
        tickers[ticker] = name
    return tickers

def get_sp500_list():
    tickers_dict = get_sp500_dict()
    tickers = []
    for key, value in tickers_dict.items():
        # entry = value + " (" + key + ")"
        entry = key + " — " + value
        tickers.append(entry)
    return tickers

def get_sp500_ticker_list():
    tickers_dict = get_sp500_dict()
    tickers = []
    for key, value in tickers_dict.items():
        tickers.append(key)
    return tickers

# print(compare("AAPL"))
# print("\n".join(get_sp500_ticker_list()))