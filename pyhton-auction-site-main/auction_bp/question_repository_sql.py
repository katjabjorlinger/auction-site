""" ansvarar för frågor och svar för föremål """
import sqlite3

#skapar questionsrepository klassen
class QuestionRepository:
    def __init__(self, file_name: str):
        self.file_name = file_name
        self.create_questions_table()

    #skapar tabellen questions
    def create_questions_table(self):
        conn = sqlite3.connect(self.file_name)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_id TEXT,
                user TEXT,
                question TEXT,
                answer TEXT,
                answered_by TEXT,
                FOREIGN KEY(item_id) REFERENCES items(id)
            )
        ''')
        #commit och stänger databas
        conn.commit()
        conn.close()

    #skapar nya frågor 
    def add_question(self, item_id: str, user: str, question: str):
        conn = sqlite3.connect(self.file_name)
        cursor = conn.cursor()
        cursor.execute('INSERT INTO questions (item_id, user, question) VALUES (?, ?, ?)', (item_id, user, question))
        conn.commit()
        conn.close()

    #hämtar frågor för ett föremål som matchar id 
    def get_questions_for_item(self, item_id: str):
        conn = sqlite3.connect(self.file_name)
        cursor = conn.cursor()
        cursor.execute('SELECT id, user, question, answer, answered_by FROM questions WHERE item_id = ?', (item_id,))
        questions = cursor.fetchall()
        conn.close()
        return [{"id": q[0], "user": q[1], "question": q[2], "answer": q[3], "answered_by": q[4]} for q in questions]

    #skapar ett svar på frågan
    def answer_question(self, question_id: int, answer: str, answered_by: str):
        conn = sqlite3.connect(self.file_name)
        cursor = conn.cursor()
        cursor.execute('UPDATE questions SET answer = ?, answered_by = ? WHERE id = ?', (answer, answered_by, question_id))
        conn.commit()
        conn.close()
