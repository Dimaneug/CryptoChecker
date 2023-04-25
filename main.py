from bs4 import BeautifulSoup, NavigableString
import requests
import re
import multiprocessing.dummy as mp
import time

explorers = {"Arbitrum": "arbiscan.io", "BSC" : "bscscan.com"}



def get_fee_from_tx_page(input_tuple):
    row, month, network = input_tuple
    date = row.find("td", class_="showAge").span["title"]
    if int(date[5:7]) != month:
        return 0
    transaction_page_href = row.find("span", class_="hash-tag").a["href"]
    transaction_page = requests.get("https://" + explorers[network] + transaction_page_href, headers={'User-Agent': 'Custom'})
    transaction_page_soup = BeautifulSoup(transaction_page.text, "lxml")
    fee = transaction_page_soup.find("button", {"id" : "txfeebutton"}).get_text()
    if fee is None:
        return 0
    fee = re.search(r"\$[0-9\.]+", fee)[0][1:]
    # fee = row.find("td", class_="showTxnFee").span.get_text() # Комиссия в токенах
    return fee


def check_fees(network: str, wallet: str, month: int):
    total_fees = 0

    for i in range(1,3):
        html = requests.get("https://" + explorers[network]+ "/txs?a=" + wallet+"&ps=10&p="+str(i), headers={'User-Agent': 'Custom'})
        soup = BeautifulSoup(html.text, "lxml")
        table = soup.find("table", class_="table table-hover").tbody
        for row in table.children:
            if isinstance(row, NavigableString):
                continue
            date = row.find("td", class_="showAge").span["title"]
            if int(date[5:7]) != month:
                break
            transaction_page_href = row.find("span", class_="hash-tag").a["href"]
            transaction_page = requests.get("https://" + explorers[network] + transaction_page_href, headers={'User-Agent': 'Custom'})
            transaction_page_soup = BeautifulSoup(transaction_page.text, "lxml")
            fee = transaction_page_soup.find("button", {"id" : "txfeebutton"}).get_text()
            fee = re.search(r"\$[0-9\.]+", fee)[0][1:]
            # fee = row.find("td", class_="showTxnFee").span.get_text() # Комиссия в токенах
            total_fees += float(fee)

        else:
            continue
        break
    
    print(total_fees)


def check_fees_multiprocs(network: str, wallet: str, month: int):
    total_fees = 0

    for i in range(1,3):
        html = requests.get("https://" + explorers[network]+ "/txs?a=" + wallet+"&ps=10&p="+str(i), headers={'User-Agent': 'Custom'})
        soup = BeautifulSoup(html.text, "lxml")
        table = soup.find("table", class_="table table-hover").tbody
        rows = []
        for row in table.children:
            if not isinstance(row, NavigableString):
                rows.append(row)
        with mp.Pool() as p:
            page_fees = p.map(get_fee_from_tx_page, [(row, month, network) for row in rows])
            
        total_fees += sum([float(val) for val in page_fees])
    
    print(total_fees)

start = time.time()
check_fees("BSC", "0x7da10ce8d5bd7abf0ee57433366bf1c2abbef02e", 4)
print("Without procs:", time.time() - start)

start = time.time()
check_fees_multiprocs("BSC", "0x7da10ce8d5bd7abf0ee57433366bf1c2abbef02e", 4)
print("With procs:", time.time() - start)


