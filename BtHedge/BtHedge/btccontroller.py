from requests import get
from json import loads
from apscheduler.schedulers.background import BackgroundScheduler
import atexit
from BtHedge import db

SMARTBIT_URL = "https://api.smartbit.com.au/v1/blockchain"


def get_balance(address):
    final_url = SMARTBIT_URL + "/address/" + address

    response = get(final_url)
    response_json = loads(response.text)

    if not response_json["success"]:
        raise Exception("Error looking for your address")

    return response_json['address']['total']['balance']

def check_balance_and_invest():
    cursor = db.cursor()
    cursor.execute("SELECT * FROM user where active = 1")
    users = cursor.fetchmany()
    for user in users:
        balance = get_balance(user[4])
        cursor.execute("UPDATE user SET personal_balance = personal_balance + %s WHERE id = %s", (balance, user[0]))
        db.commit()


scheduler = BackgroundScheduler()
scheduler.add_job(func=check_balance_and_invest, trigger="interval", seconds=10)
scheduler.start()

# Shut down the scheduler when exiting the app
#atexit.register(lambda: scheduler.shutdown())