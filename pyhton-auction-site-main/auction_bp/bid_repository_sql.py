""" ansvarar för att lagra bud i datasbasen """

import sqlite3
from datetime import datetime

#skapar klassen för bidrepositry
class BidRepository:
    def __init__(self, file_name: str):
        self.file_name = file_name
        self.create_bids_table()
    # Skapar tabell
    def create_bids_table(self):
    # Lagrara information om bud ink id, belopp, objekt, användare
    # Anslut till sqlite-databas
         conn = sqlite3.connect(self.file_name)
         cursor = conn.cursor()
    # Kör sql fråga för att skapa tabell om den inte finns
         cursor.execute('''
            CREATE TABLE IF NOT EXISTS bids (
               id INTEGER PRIMARY KEY AUTOINCREMENT,
               item_id TEXT,
               user TEXT,
               amount REAL,
               timestamp TEXT,
               email TEXT,
               notify_outbid INTEGER DEFAULT 0,
               FOREIGN KEY(item_id) REFERENCES items(id)
           )
         ''')
         # Bekräftar ändringar, stäng databas
         conn.commit()
         conn.close()

    # Lägger till nytt bud i tabellen
    def place_bid(self, item_id: str, user: str, amount: float, timestamp: str, email: str, notify_outbid: bool):
        #Sql-fråga
        conn = sqlite3.connect(self.file_name)
        cursor = conn.cursor()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute('''
             INSERT INTO bids (item_id, user, amount, timestamp, email, notify_outbid)
             VALUES (?, ?, ?, ?, ?, ?)
        ''', (item_id, user, amount, timestamp, email, int(notify_outbid)))
        # Bekräftar ändringar, stäng databas
        conn.commit()
        conn.close()
        print(f"✅ Bid placed by {user} on item {item_id} with notify_outbid={notify_outbid}")

    #markerade användare som vill ha notis om bud
    def mark_user_for_outbid_notification(self, item_id: str, user: str, email: str):
        conn = sqlite3.connect(self.file_name)
        cursor = conn.cursor()
        cursor.execute('''
           UPDATE bids
           SET notify_outbid = 1, email = ?
           WHERE item_id = ? AND user = ?
        ''', (email, item_id, user))
        conn.commit()
        conn.close()


    # Hämta notifierade användare
    def get_users_to_notify(self, item_id: str):
        conn = sqlite3.connect(self.file_name)
        cursor = conn.cursor()
        cursor.execute('''
           SELECT user, email FROM bids
           WHERE item_id = ? AND notify_outbid = 1
        ''', (item_id,))
        users = cursor.fetchall()
        conn.close()
        return users

    #tar bort bud 
    def delete_bid(self, bid_id: int) -> bool:
        conn = sqlite3.connect(self.file_name)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM bids WHERE id = ?', (bid_id,))
        conn.commit()
        conn.close()
        return True

    #hämtar bud för föremål
    def get_bids_for_item(self, item_id: str) -> list:
        conn = sqlite3.connect(self.file_name)
        cursor = conn.cursor()

        cursor.execute('SELECT id, user, amount, timestamp FROM bids WHERE item_id = ? ORDER BY amount DESC', (item_id,))
        bids = cursor.fetchall()

        conn.close()

        return [{"id": bid[0], "user": bid[1], "amount": bid[2], "timestamp": bid[3]} for bid in bids]

    #hämtar det högsta budet för ett föremål
    def get_highest_bid_for_item(self, item_id: str) -> float:
        conn = sqlite3.connect(self.file_name)
        cursor = conn.cursor()

        cursor.execute('SELECT amount FROM bids WHERE item_id = ? ORDER BY amount DESC LIMIT 1', (item_id,))
        highest_bid = cursor.fetchone()

        conn.close()

        return highest_bid[0] if highest_bid else None
