import requests
import os
from datetime import datetime, timedelta
from PyQt6.QtWidgets import (
    QApplication,
    QVBoxLayout,
    QHBoxLayout,
    QCheckBox,
    QPushButton,
    QMainWindow,
    QWidget,
    QLineEdit,
    QLabel,
    QDateEdit,
    QMessageBox,
)
import json

# Dictionary with explorers' links
explorers = {
    "Ethereum": "api.etherscan.io",
}


# Calculates how mush was spent on fees for a certain time interval
def calculate_fees(
    network: str, api_key: str, wallet: str, start_date: datetime, end_date: datetime
):
    total_fees = 0
    start_date = datetime.timestamp(start_date)
    end_date = datetime.timestamp(end_date)

    transactions = requests.get(
        "https://"
        + explorers[network]
        + "/api?module=account&action=txlist&address="
        + wallet
        + "&sort=desc&offset=1000&apikey="
        + api_key,
        headers={"User-Agent": "Custom"},
    )
    transactions = json.loads(transactions.text)
    current_price = [0, 0]  # 0 - timestamp, 1 - price
    for transaction in transactions["result"]:
        tx_date = int(transaction["timeStamp"])
        if tx_date > end_date:
            continue
        if tx_date < start_date:
            break
        if tx_date > current_price[0] + 3599 or tx_date < current_price[0]:
            price_data = requests.get(
                "https://min-api.cryptocompare.com/data/v2/histohour?fsym=ETH&tsym=USD&limit=1&toTs="
                + str(tx_date)
            )
            price_data = json.loads(price_data.text)["Data"]["Data"][1]
            current_price[0] = int(price_data["time"])
            current_price[1] = float(price_data["high"])
        current_fee = int(transaction["gasPrice"]) * int(transaction["gasUsed"])
        current_fee = current_fee * 10 ** (-18) * current_price[1]
        total_fees += current_fee

    return total_fees


# Just a console clear
def clear():
    if os.name == "nt":
        os.system("cls")
    else:
        os.system("clear")


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Fees Checker")
        self.setGeometry(10, 10, 400, 150)

        widget = QWidget()

        api_key_layout = QHBoxLayout()
        api_key_lbl = QLabel("API Key:")
        self.api_key = QLineEdit()
        self.api_key.setMaximumWidth(310)
        api_key_layout.addWidget(api_key_lbl)
        api_key_layout.addWidget(self.api_key)

        wallet_layout = QHBoxLayout()
        wallet_lbl = QLabel("Wallet")
        self.wallet = QLineEdit()
        self.wallet.setMaximumWidth(310)
        wallet_layout.addWidget(wallet_lbl)
        wallet_layout.addWidget(self.wallet)

        self.ethereum = QCheckBox("Ethereum")
        self.bsc = QCheckBox("BSC")

        start_date_layout = QHBoxLayout()
        start_date_lbl = QLabel("Start Date")
        self.start_date = QDateEdit(calendarPopup=True)
        self.start_date.setDate(datetime.today() - timedelta(days=1))
        start_date_layout.addWidget(start_date_lbl)
        start_date_layout.addWidget(self.start_date)

        end_date_layout = QHBoxLayout()
        end_date_lbl = QLabel("End Date")
        self.end_date = QDateEdit(calendarPopup=True)
        self.end_date.setDate(datetime.today())
        end_date_layout.addWidget(end_date_lbl)
        end_date_layout.addWidget(self.end_date)

        self.confirm_button = QPushButton("Confirm")
        self.confirm_button.clicked.connect(self.btn_confirm_pushed)

        layout = QVBoxLayout()
        layout.addLayout(api_key_layout)
        layout.addLayout(wallet_layout)
        layout.addWidget(self.ethereum)
        layout.addLayout(start_date_layout)
        layout.addLayout(end_date_layout)
        layout.addWidget(self.confirm_button)
        widget.setLayout(layout)
        self.setCentralWidget(widget)

    def btn_confirm_pushed(self):
        total_fees = 0
        if self.ethereum.isChecked():
            total_fees += calculate_fees(
                self.ethereum.text(),
                self.api_key.text(),
                self.wallet.text(),
                self.start_date.dateTime().toPyDateTime(),
                self.end_date.dateTime().toPyDateTime(),
            )
        msg = QMessageBox()
        msg.setWindowTitle("Total fees")
        msg.setText(f"${total_fees:.2f}")
        msg.exec()


if __name__ == "__main__":
    app = QApplication([])
    ex = MainWindow()
    ex.show()
    app.exec()
