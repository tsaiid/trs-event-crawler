# coding=UTF-8
import requests
from lxml import html
import re
import httplib2
import os
import sqlite3

from apiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage
from oauth2client.service_account import ServiceAccountCredentials

from datetime import datetime
from dateutil.relativedelta import relativedelta
import argparse


EVENT_BASE_URL = "http://www.rsroc.org.tw"
CALENDAR_ID = "primary"
KEY_FILE = '_client_secret.json'
SCOPES = 'https://www.googleapis.com/auth/calendar'
SQL_FILE = 'trs-events.db'

class TrsEventCrawler:
  def __init__(self, **kwargs):
    self.conn, self.c = self.connect_db()
    self.service = self.service_init()
    self.verbose = kwargs['verbose']
    self.test = kwargs['test']
    self.dry_run = kwargs['dry_run']

  def __del__(self):
    self.conn.commit()
    self.conn.close()

  def connect_db(self):
    conn = sqlite3.connect(SQL_FILE)
    c = conn.cursor()
    return conn, c

  def service_init(self):
    credentials = ServiceAccountCredentials.from_json_keyfile_name(KEY_FILE, scopes=SCOPES)
    http = credentials.authorize(httplib2.Http())
    service = discovery.build('calendar', 'v3', http=http)
    return service


  def add_gcal_event(self, title, description, start_date, end_date):
    g_event = {
      'summary': title,
      'description': description,
      'start': {
        'date': start_date,
      },
      'end': {
        'date': end_date,
      },
    }
    g_event = self.service.events().insert(calendarId=CALENDAR_ID, body=g_event).execute()
    if g_event is not None and self.verbose > 0:
      print('Event created: %s' % (g_event.get('htmlLink')))
    return g_event


  def add_db_event(self, id, title, description, start_date, end_date):
    self.c.execute("INSERT INTO events VALUES (?,?,?,?,?)", (id, title, description, start_date, end_date))
    if self.verbose > 0:
      print "added to db"


  def db_exist_event(self, id):
    self.c.execute("SELECT * FROM events WHERE event_id=" + id)
    row = self.c.fetchone()
    return False if row is None else True


  def fetch_event_month(self, year, month):
    r = requests.get(EVENT_BASE_URL + '/action/index.asp?EType=&YEARNOW=' + str(year) + '&MONTHNOW=' + str(month))
    r.encoding = 'big5'
    #print r.text
    tree = html.fromstring(r.text)
    events = tree.xpath('//table[@class="cal_table"]/tr/td/div/a')
    #urls = tree.xpath('//table[@class="cal_table"]/tr/td/div/a/@href')
    #print 'Events: ', events[0].attrib['href']
    #print 'Urls: ', urls

    for index, event in enumerate(events):
      match = re.search(r"id=(\d+)$", event.attrib['href'])
      if match:
        event_id = match.group(1)
        if self.verbose > 0:
          print "event_id: " + event_id

        event_url = EVENT_BASE_URL + event.attrib['href']
        r_event = requests.get(event_url)
        r_event.encoding = 'big5'
        #print r_event.text

        event_tree = html.fromstring(r_event.text)
        title = event_tree.xpath('//h4[1]/text()')[0].replace(u'研討會】', u'】')
        if self.verbose > 1:
          print "title: " + title
        if self.verbose > 2:
          print "event_url: " + event_url

        date_row = event_tree.xpath('//table[@class="annual_table1"]/tr[1]/td[1]/text()')
        date = re.findall(r"\b\d{4}\/\d{2}\/\d{2}\b", date_row[0])
        start_date = date[0].replace('/', '-')
        if len(date) > 1:
          end_date = (datetime.strptime(date[1], "%Y/%m/%d") + relativedelta(days=1)).strftime("%Y-%m-%d")
        else:
          end_date = (datetime.strptime(date[0], "%Y/%m/%d") + relativedelta(days=1)).strftime("%Y-%m-%d")
        if self.verbose > 1:
          print "start_date: " + start_date + "\tend_date: " + end_date

        if not self.db_exist_event(event_id):
          not_exists_str = "not exists in local db"
          if not self.verbose:
            not_exists_str += ": " + start_date + " " + title
          print not_exists_str
          if not self.dry_run:
            g_event = self.add_gcal_event(title, event_url, start_date, end_date)
            if g_event is not None:
              self.add_db_event(event_id, title, event_url, start_date, end_date)
          else:
            print "not added to db and gcal in dry-run mode"
        else:
          if self.verbose > 0:
            print "exists in local db"

        if self.test and index > 3:
          break
      else:
        print "No ID found. Probably not an avalable event."


def check_positive(value):
  ivalue = int(value)
  if ivalue <= 0:
   raise argparse.ArgumentTypeError("%s is an invalid positive int value" % value)
  return ivalue


def main():
  parser = argparse.ArgumentParser(description='Google Calendar manipulation utility.')
  parser.add_argument("-t", "--test", help="fetch only first few events", action="store_true")
  parser.add_argument("-d", "--dry-run", help="dry run", action="store_true")
  parser.add_argument("-m", "--months", type=check_positive, default=3)
  parser.add_argument("-v", "--verbose", help="increase output verbosity", action="count")
  args = parser.parse_args()

  crawler = TrsEventCrawler(**vars(args))

  today = datetime.today()
  if args.dry_run:
    print 'Dry run mode.'
  print 'Current date: ', today
  i = 0
  while i < args.months:
    date = today + relativedelta(months=i)
    year = date.year
    month = date.month
    print 'Fetching year: ', year, ' month: ', month
    crawler.fetch_event_month(year, month)
    i += 1


if __name__ == '__main__':
  main()