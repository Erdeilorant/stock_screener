from flask import Flask, render_template, request, redirect, url_for, jsonify
import yfinance as yfin
import plotly.graph_objs as go
from plotly.subplots import make_subplots
import pandas as pd
from bs4 import BeautifulSoup
import requests
import re
import smtplib
from email.message import EmailMessage
from string import Template
from pathlib import Path
import json


app = Flask(__name__)


def daily_losers_json():
    url = "https://stockanalysis.com/api/screener/s/f"

    querystring = {"m": "change", "s": "asc", "c": "no,s,n,change,price,volume,marketCap,sector,industry", "cn": "20",
                   "f": "close-over-1,change-under-0,volume-over-10000,marketCap-over-1000000", "i": "stocks"}

    payload = ""
    headers = {
        "authority": "stockanalysis.com",
        "accept": "*/*",
        "accept-language": "ro-RO,ro;q=0.9,en-US;q=0.8,en;q=0.7,hu;q=0.6",
        "cookie": "_ga=GA1.1.479379106.1679762692; _ga_C83MWM65QF=GS1.1.1680195034.9.1.1680195784.0.0.0",
        "referer": "https://stockanalysis.com/markets/losers/",
        "sec-ch-ua": "^\^Google",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "^\^Windows^^",
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36"
    }

    response = requests.request(
        "GET", url, data=payload, headers=headers, params=querystring)

    data = json.loads(response.content)
    return data


def daily_gainers_json():
    url = "https://stockanalysis.com/api/screener/s/f"

    querystring = {"m": "change", "s": "desc", "c": "no,s,n,change,price,volume,marketCap,industry,sector", "cn": "20",
                   "f": "close-over-1,change-over-0,volume-over-10000,marketCap-over-1000000", "i": "stocks"}

    payload = ""
    headers = {
        "authority": "stockanalysis.com",
        "accept": "*/*",
        "accept-language": "en-US,en;q=0.9,ro;q=0.8",
        "cookie": "_ga=GA1.1.787001417.1679762889; _ga_C83MWM65QF=GS1.1.1680195213.10.1.1680196318.0.0.0",
        "referer": "https://stockanalysis.com/markets/gainers/",
        "sec-ch-ua": "^\^Microsoft",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "^\^Windows^^",
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36 Edg/111.0.1661.54"
    }

    response = requests.request(
        "GET", url, data=payload, headers=headers, params=querystring)

    data = json.loads(response.content)
    return data


def get_news_headlines():
    header = {
        'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36"}
    url = f"https://finviz.com/news.ashx"
    response = requests.get(url, headers=header)
    soup = BeautifulSoup(response.text, 'html.parser')
    links = soup.find_all('a', class_='nn-tab-link')
    time = soup.find_all('td', class_='nn-date')
    news_articles = []
    for i in range(1, len(links)):
        headline = {
            'title': links[i].text,
            'links': links[i]['href'],
            'time': time[i-1].text
        }
        news_articles.append(headline)
    return news_articles


def get_stock_price(instrument):

    ticker_symbol = instrument
    header = {
        'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36"}
    url = f"https://finance.yahoo.com/quote/{ticker_symbol}"
    response = requests.get(url, headers=header)
    soup = BeautifulSoup(response.text, 'html.parser')
    price = soup.find('div', class_='D(ib) Mend(20px)').find_all(
        'fin-streamer')[0].text
    change = soup.find(
        'div', class_='D(ib) Mend(20px)').find_all('span')[0].text
    change2 = soup.find(
        'div', class_='D(ib) Mend(20px)').find_all('span')[1].text
    header = soup.find('h1', class_="D(ib) Fz(18px)").text
    stock = {
        'Symbol': header,
        'Price': float(price),
        'Change': float(change),
        'Percentage': float(change2.strip('()%')),
    }
    return stock


def get_profile(symbol):
    header = {
        'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36"}
    url = f"https://stockanalysis.com/stocks/{symbol}/company/"
    response = requests.get(url, headers=header)
    soup = BeautifulSoup(response.text, 'html.parser')
    profile = soup.find_all(
        'div', class_='mb-5 text-base md:text-lg [&>p]:mb-5')
    return profile


def daily_gainers_df():
    header = {
        'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36"}
    url = "https://finance.yahoo.com/gainers/"
    response = requests.get(url, headers=header)
    soup = BeautifulSoup(response.text, 'html.parser')
    symbol = soup.find_all('a', class_='Fw(600) C($linkColor)')
    name = soup.find_all('td', class_='Va(m) Ta(start) Px(10px) Fz(s)')
    price = soup.find_all("td", {"aria-label": "Price (Intraday)"})
    change = soup.find_all("td", {"aria-label": "Change"})
    percent = soup.find_all("td", {"aria-label": "% Change"})
    volume = soup.find_all("td", {"aria-label": "Volume"})
    avg_vol = soup.find_all("td", {"aria-label": "Avg Vol (3 month)"})
    pe_ttm = soup.find_all("td", {"aria-label": "PE Ratio (TTM)"})
    # Define the column headers
    headers = ["Symbol", "Name", "Price", "Change", "Percentage",
               "Volume", 'Avg Vol (3 month)', 'PE Ratio (TTM)']
    table = []
    for i in range(len(symbol))[:5]:
        table.append([symbol[i].text, name[i].text, price[i].text, change[i].text, percent[i].text, volume[i].text,
                      avg_vol[i].text, pe_ttm[i].text])
    df = pd.DataFrame(table, columns=headers)
    return df


def daily_losers_df():
    header = {
        'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36"}
    url = "https://finance.yahoo.com/losers"
    response = requests.get(url, headers=header)
    soup = BeautifulSoup(response.text, 'html.parser')
    symbol = soup.find_all('a', class_='Fw(600) C($linkColor)')
    name = soup.find_all('td', class_='Va(m) Ta(start) Px(10px) Fz(s)')
    price = soup.find_all("td", {"aria-label": "Price (Intraday)"})
    change = soup.find_all("td", {"aria-label": "Change"})
    percent = soup.find_all("td", {"aria-label": "% Change"})
    volume = soup.find_all("td", {"aria-label": "Volume"})
    avg_vol = soup.find_all("td", {"aria-label": "Avg Vol (3 month)"})
    pe_ttm = soup.find_all("td", {"aria-label": "PE Ratio (TTM)"})
    # Headers of the df
    headers = ["Symbol", "Name", "Price", "Change", "Percentage",
               "Volume", 'Avg Vol (3 month)', 'PE Ratio (TTM)']
    table = []
    for i in range(len(symbol))[:5]:
        # Convertim % Change in float
        percent_change = float(percent[i].text.strip('%'))
        table.append([symbol[i].text, name[i].text, price[i].text, change[i].text, percent_change, volume[i].text,
                      avg_vol[i].text, pe_ttm[i].text])
    df = pd.DataFrame(table, columns=headers)
    return df


@app.route('/')
@app.route('/home')
def home():
    return render_template('index.html')


@app.route('/stock/<string:name>', methods=['GET', 'POST'])
def stock_detail(name):
    ticker = yfin.Ticker(name)
    stock_data = yfin.Ticker(name).history(period="1y")
    stock = ticker.ticker
    profile_data = get_profile(name)
    with open('ticker_list.txt') as tl:
        ticker_list = tl.read()

    stock_price_data = get_stock_price(name)
    news_articles = []
    for i in ticker.news:
        if 'thumbnail' in i:
            news = {'article_title': i['title'],
                    'article_url': i['link'],
                    'image': i['thumbnail']}
            news_articles.append(news)
    # Convertim in Df
    df = pd.DataFrame(stock_data)

   # Calculate the 14-day RSI using Pandas
    delta = df['Close'].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(window=14).mean()
    avg_loss = loss.rolling(window=14).mean()
    rs = avg_gain / avg_loss.abs()
    rsi = 100 - (100 / (1 + rs))

    # Create the subplots with 2 rows and 1 column
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
                        vertical_spacing=0.05)

    # Add the candlestick trace to the first row
    fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'],
                  low=df['Low'], close=df['Close'], name='Candlestick'), row=1, col=1)

    # Add the 50-day SMA trace to the first row
    fig.add_trace(go.Scatter(x=df.index, y=df['Close'].rolling(window=50).mean(
    ), line=dict(color='orange', width=2), name='50-day SMA'), row=1, col=1)

    # Add the RSI trace to the second row
    fig.add_trace(go.Scatter(x=df.index, y=rsi, name='RSI'), row=2, col=1)

    # Add the 30 and 70 levels as horizontal lines to the RSI chart
    fig.add_shape(type="line", x0=df.index[0], x1=df.index[-1],
                  y0=30, y1=30, line=dict(color="red", width=2), row=2, col=1)
    fig.add_shape(type="line", x0=df.index[0], x1=df.index[-1],
                  y0=70, y1=70, line=dict(color="red", width=2), row=2, col=1)

    # Set the size of the chart
    fig.update_layout(height=800, width=1200)

    # Add price levels to the chart
    fig.update_yaxes(showticklabels=True, tickmode='auto',
                     nticks=20, row=1, col=1)

    # Set the RSI chart range
    fig.update_yaxes(range=[0, 100], row=2, col=1)

    # Convert the chart to HTML
    chart_html = fig.to_html(full_html=False)

    header = {
        'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36"}
    url = f"https://stockanalysis.com/stocks/{name}/financials/balance-sheet/"
    response = requests.get(url, headers=header)
    try:
        df2 = pd.read_html(response.text)[0]
    except ValueError:
        df2 = pd.DataFrame()  # Daca nu se gaseste un tabel returneaza un DF gol
    if df2.empty:
        html_table = None
    else:
        df2 = df2.iloc[:, :-1]
    # Converteaza Df in tabel in HTML
    html_table = df2.to_html(classes='table table-bordered', index=False)
    if request.method == 'POST':
        ticker = request.form['ticker'].upper()
        if ticker not in ticker_list:
            return redirect(url_for('stocks'))
        return redirect(url_for('stock_detail', name=ticker))

    return render_template('stock_detail.html', stock_price_data=stock_price_data, profile_data=profile_data, stock=stock, news_articles=news_articles, chart_html=chart_html, table=html_table)


@app.route('/contact', methods=['GET', 'POST'])
def contact():
    with open('email_passw.txt') as p:
        pw = p.readlines()

    if request.method == 'POST':
        name = request.form['name']
        address = request.form['email']
        message = request.form['message']

        # Verificam daca s-a completat formula
        if name == "" or address == "" or message == "":
            return "All fields are required!"

        # Verificam validitatea adresei de email
        emailPattern = r'^\w+@[a-zA-Z_]+?\.[a-zA-Z]{2,3}$'
        if not re.match(emailPattern, address):
            return "Invalid email address!"

        # Formulam emailul
        html = Template(Path('email.html').read_text())
        email = EmailMessage()
        email['from'] = 'Stock Screener'
        email['to'] = address
        email['subject'] = 'Contact support'

        # continut email, variabile inlocuite, in format html
        email.set_content(html.substitute(name=name), 'html')

        # Trimitem emailul
        with smtplib.SMTP(host='smtp.gmail.com', port=587) as smtp:
            smtp.ehlo()
            smtp.starttls()
            smtp.login('myeducation1231@gmail.com', pw[0])
            smtp.send_message(email)

        return "Thank you for your message!"
    else:
        return render_template('contact.html')


@app.route("/stocks")
def test():
    losers = daily_losers_json()
    gainers = daily_gainers_json()
    return render_template('/stocks.html', gainers=gainers, losers=losers)


@app.route("/news")
def news():
    news_articles = get_news_headlines()
    return render_template('news.html', articles=news_articles)


if __name__ == "__main__":
    app.run(debug=True)
