import time
import datetime
import requests

def detection():
    url = 'http://140.112.183.138:3000/monitor/updated/'
    r = requests.post(url)
    print(r.text)


if __name__ == "__main__":
    detection()
