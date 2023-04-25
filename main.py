from bs4 import BeautifulSoup, NavigableString
import requests
import re
import multiprocessing.dummy as mp
import os
import datetime

# Dictionary with explorers' links
explorers = {
    "Arbitrum": "arbiscan.io",
    "BSC": "bscscan.com",
    "Ethereum": "etherscan.io",
    "Polygon": "polygonscan.com",
}

def get_date(row):
    date = row.find("td", class_="showAge").span.get("title") # Arb, BSC
    if date is None:
        date = row.find("td", class_="showAge").span.get("data-bs-title") # ETH
    if date is None:
        date = row.find("td", class_="showAge").span.get("data-original-title") # Polygon

    date = re.search(r"\d+\-\d+-\d+", date)[0]
    date = datetime.datetime.strptime(date, "%Y-%m-%d")
    return date

# Getting fee of transaction in $
# It takes tuple with row : bs4.Tag, month : int, network : str
def get_fee_from_tx_page(input_tuple):
    row, network, start_date, end_date = input_tuple
    date = get_date(row)
    if not (start_date <= date and date <= end_date):
        return 0
    transaction_page_href = row.find("span", class_="hash-tag").a["href"]
    transaction_page = requests.get(
        "https://" + explorers[network] + transaction_page_href,
        headers={"User-Agent": "Custom"},
    )
    transaction_page_soup = BeautifulSoup(transaction_page.text, "lxml")
    fee = transaction_page_soup.find("button", {"id": "txfeebutton"})  # Arb, BSC
    if fee is None:
        fee = transaction_page_soup.find("a", {"id": "txfeebutton"})  # ETH
    if fee is None:
        fee = transaction_page_soup.find(
            "span", {"id": "ContentPlaceHolder1_spanTxFee"}
        )  # Polygon
    if fee is None:
        return 0
    fee = fee.get_text()
    fee = re.search(r"\$[0-9\.]+", fee)[0][1:]
    return fee


# Calculates how mush was spent on fees for a certain month
def calculate_fees_multiprocs(network: str, wallet: str, start_date: datetime, end_date: datetime):
    total_fees = 0

    for i in range(1, 100):
        html = requests.get(
            "https://" + explorers[network] + "/txs?a=" + wallet + "&ps=10&p=" + str(i),
            headers={"User-Agent": "Custom"},
        )
        soup = BeautifulSoup(html.text, "lxml")
        table = soup.find("table", class_="table").tbody
        rows = []
        for row in table.children:
            if not isinstance(row, NavigableString):
                rows.append(row)
        # check to skip unnecessary data
        if get_date(rows[-1]) > end_date:
            continue
        if get_date(rows[0]) < start_date:
            break
        with mp.Pool() as p:
            page_fees = p.map(
                get_fee_from_tx_page, [(row, network, start_date, end_date) for row in rows]
            )
        fees_on_page = sum([float(val) for val in page_fees])
        total_fees += fees_on_page 

    return total_fees

# Just a console clear
def clear():
    if os.name == "nt":
        os.system("cls")
    else:
        os.system("clear")


# Interface function
def interface():
    networks_list = []
    while 1:
        clear()
        for i, network in enumerate(explorers.keys(), 1):
            print(f"{i}. {network}")
            networks_list.append(network)
        try:
            network = input("Choose network (q for exit): ")
            if network == "q":
                break
            network = int(network)
        except:
            print("You should write number of network!")
            wait = input()
            continue
        try:
            start_date = input("Write start date (Y-M-D): ")
            start_date = datetime.datetime.strptime(start_date, "%Y-%m-%d")
        except:
            print("You should write date in format Y-M-D!")
            wait = input()
            continue
        try:
            end_date = input("Write end date (Y-M-D): ")
            end_date = datetime.datetime.strptime(end_date, "%Y-%m-%d")
        except:
            print("You should write date in format Y-M-D!")
            wait = input()
            continue
        wallet = input("Write wallet address: ")
        print(
            f"Total fees: ${calculate_fees_multiprocs(networks_list[network-1], wallet, start_date, end_date)}"
        )
        wait = input()


if __name__ == "__main__":
    interface()
