""" !!! ONLY WORKS WITH FIREFOX !!!
This script will fetch the required Metallum cookies from your personal browser profile. If your cookies expires, complete the captcha in your browser and re-run this script.
"""

import sqlite3
import json
from Env import Env
env = Env.get_instance()

## Set firefox profile sqlite database path in Config.json
cookie_db = env.fire
conn = sqlite3.connect(cookie_db)
cursor = conn.cursor()

def metallum():
    config_file = 'Config.json'
    with open(config_file, "r") as f:
        config = json.load(f)

    domain = '.metal-archives.com'
    cursor.execute("""
        SELECT name, value
        FROM moz_cookies
        WHERE host LIKE ?
        """, (domain,))
    cookies = dict(cursor.fetchall())
    conn.close()

    for cookie_name, cookie_value in cookies.items():
        if cookie_name in config["cookies"]:
            config["cookies"][cookie_name] = cookie_value

    with open(config_file, "w") as f:
        json.dump(config, f, indent=4)

if __name__ == '__main__':
    metallum()
    