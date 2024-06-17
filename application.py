from flask import Flask, request, jsonify, render_template
from firstdraft import DCF, get_sp500_ticker_list
import json

app = Flask(__name__)

# comp_list = get_sp500_ticker_list()
# print(comp_list)
# with open('companies.json') as f:
#     companies = json.load(f)

@app.route('/')
def home():
    # return "Welcome to the DCF Analysis App!"
    return render_template("index.html")

@app.route('/get_companies')
def get_companies():
    companies = get_sp500_ticker_list()
    return jsonify(companies)

@app.route('/calculate', methods = ["POST", "GET"])
def predict():
    # try:
    # data = request.get_json()
    ticker = request.form['ticker']
    price_prediction = DCF(ticker)
    # return jsonify({"ticker": ticker, "predicted_price": price_prediction})
    return render_template('index.html', ticker = ticker, dcf_value = price_prediction)
    
    # except Exception as e:
    #     return jsonify({"error": str(e)}), 500

# @app.route('/autoc', methods = ["POST", "GET"])
# def autoc():
#     query = request.args.get('q')
#     suggestions = [company for company in companies if company.lower().contains(query.lower())]
#     return jsonify(suggestions)

if __name__ == '__main__':
    app.run(debug = True)