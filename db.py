import sqlite3
import argparse

def connect(sqlite_file):
    conn = sqlite3.connect(sqlite_file)
    c = conn.cursor()
    return conn, c

def create_table(c):
    print 'Creating events table...'
    c.execute("CREATE TABLE events ( "
                            "event_id integer PRIMARY KEY, "
                            "event_title text NOT NULL, "
                            "event_url text NOT NULL, "
                            "start_date text NOT NULL, "
                            "end_date text NOT NULL"
                        ");")

def delete_events(c):
    print 'Deleting events in db...'
    c.execute("DELETE FROM events;")

def main():
    sqlite_file = 'trs-events.db'
    parser = argparse.ArgumentParser(description='Local db manipulation utility.')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("-c", help="create event table", action="store_true")
    group.add_argument("-d", help="delete events in db", action="store_true")
    args = parser.parse_args()

    conn, c = connect(sqlite_file)
    if args.c:
        create_table(c)
    elif args.d:
        delete_events(c)

    conn.commit()
    conn.close()

if __name__ == '__main__':
    main()