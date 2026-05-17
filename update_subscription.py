import datetime
import sqlite3
import sys

# Connect to the database (replace 'your_database.db' with your actual database file)
conn = sqlite3.connect('instance/sigmund.db')

# Create a cursor object
cur = conn.cursor()

# Define the user_id for which you want to update the to_date
user_id = int(sys.argv[-1])  # Replace with the actual user_id
print(f'Extending subscription for user {user_id}')


# Calculate the date three years in the future
to_date = datetime.datetime.now() + datetime.timedelta(days=1000)
# Calculate the date now
from_date = datetime.datetime.now() - datetime.timedelta(days=1)

# Check if the user_id exists in the subscription table
cur.execute("""SELECT 1 FROM subscription WHERE user_id = ?""", (user_id,))
if cur.fetchone():
    # Update the to_date and from_date for the specific user_id
    cur.execute("""UPDATE subscription SET to_date = ?, from_date = ? WHERE user_id = ?""", (to_date, from_date, user_id))
else:
    # Insert a new record for the user_id with the calculated to_date and current from_date
    cur.execute("""INSERT INTO subscription (user_id, to_date, from_date) VALUES (?, ?, ?)""", (user_id, to_date, from_date))


# Commit the changes and close the connection
conn.commit()
conn.close()
