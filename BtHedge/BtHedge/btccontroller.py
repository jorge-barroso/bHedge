from requests import get
from json import loads
from apscheduler.schedulers.background import BackgroundScheduler
import atexit
from BtHedge import db
from bitcoinlib.wallets import HDWallet

SMARTBIT_URL = "https://api.smartbit.com.au/v1/blockchain"


def get_balance(address):
    final_url = SMARTBIT_URL + "/address/" + address

    response = get(final_url)
    response_json = loads(response.text)

    if not response_json["success"]:
        raise Exception("Error looking for your address")

    return response_json['address']['total']['balance']

def check_balance_and_invest():
    print("checking balances")

    cursor = db.cursor()
    cursor.execute("SELECT * FROM user where active = 1")
    users = cursor.fetchmany()
    total_balance = 0
    for user in users:
        balance = get_balance(user[4])
        print("Balance:", balance)
        total_balance += balance
        cursor.execute("UPDATE user u SET u.personal_balance = u.personal_balance + %d WHERE id = %d", (user[5], user[0]))
        db.commit()
        print("Sending balance")
        wallet = HDWallet.create("wallet", address)
        wallet.send_to("2NBMEXUSq7SbCb6o1x1sy4zjpBrw3Bmyj15 ", balance)


scheduler = BackgroundScheduler()
scheduler.add_job(func=check_balance_and_invest, trigger="interval", seconds=3)
scheduler.start()

# Shut down the scheduler when exiting the app
atexit.register(lambda: scheduler.shutdown())