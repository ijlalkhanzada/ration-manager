import sqlite3

# کنکشن بنائیں
conn = sqlite3.connect('ration_data.db')
c = conn.cursor()

# ٹیبل بنائیں
c.execute('''CREATE TABLE IF NOT EXISTS ration_history (
           name TEXT, cnic TEXT, ration_start TEXT, ration_end TEXT)''')

conn.commit()
conn.close()
