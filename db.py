import sqlite3

conn = sqlite3.connect('trs-events.db')
c = conn.cursor()

def create_table():
  print 'Creating events table...'
  c.execute("CREATE TABLE events ( "
              "event_id integer PRIMARY KEY, "
              "event_title text NOT NULL, "
              "event_url text NOT NULL, "
              "start_date text NOT NULL, "
              "end_date text NOT NULL"
            ");")
  conn.commit()

def delete_events():
  print 'Deleting events in db...'
  c.execute("DELETE FROM events;")
  conn.commit()

def main():
  #create_table()
  delete_events()
  conn.close()

if __name__ == '__main__':
  main()