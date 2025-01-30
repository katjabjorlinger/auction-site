""" ansvarar för kategorierna till föremål """
import sqlite3

#skapar categoryrepository
class CategoryRepository:
    def __init__(self, file_name: str):
        self.file_name = file_name
        self.create_category_table()

    #skapar taballen
    def create_category_table(self):
        conn = sqlite3.connect(self.file_name)
        cursor = conn.cursor()
        #skapa tabell
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL
            )
        ''')
        # insert för kategorier
        cursor.executemany('''
            INSERT OR IGNORE INTO categories (name) VALUES (?)
        ''', [('Konst',), ('Musik & Instrument',), ('Möbler',), ('Elektronik & Teknik',), ('Smycken',), ('Mode & Accessoarer',), ('Klockor',),('Böcker',)])

        #coomit och stänger databasen
        conn.commit()
        conn.close()

    #hämtar alla kategorier
    def get_all_categories(self) -> list:

        conn = sqlite3.connect(self.file_name)
        cursor = conn.cursor()
        cursor.execute('SELECT id, name FROM categories')
        categories = cursor.fetchall()
        conn.close()
        return categories
