# vim: set ts=4 sw=4 et: -*- coding: utf-8 -*-

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

EVENT_BASE_URL = "http://www.rsroc.org.tw"
CALENDAR_ID = "primary"
KEY_FILE = '_client_secret.json'
SCOPES = 'https://www.googleapis.com/auth/calendar'

credentials = ServiceAccountCredentials.from_json_keyfile_name(KEY_FILE, scopes=SCOPES)
http = credentials.authorize(httplib2.Http())
service = discovery.build('calendar', 'v3', http=http)

conn = sqlite3.connect('trs-events.db')
c = conn.cursor()


def add_gcal_event(title, description, start_date, end_date):
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
  g_event = service.events().insert(calendarId=CALENDAR_ID, body=g_event).execute()
  print('Event created: %s' % (g_event.get('htmlLink')))


def add_db_event(id, title, description, start_date, end_date):
  c.execute("INSERT INTO events VALUES (?,?,?,?,?)", (id, title, description, start_date, end_date))
  conn.commit()


def exist_event(id):
  c.execute("SELECT * FROM events WHERE event_id=" + id)
  row = c.fetchone()
  return False if row is None else True


def fetch_event_month(year, month):
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
      print event_id

      event_url = EVENT_BASE_URL + event.attrib['href']
      r_event = requests.get(event_url)
      r_event.encoding = 'big5'
      #print r_event.text

      event_tree = html.fromstring(r_event.text)
      title = event_tree.xpath('//h4[1]/text()')[0].replace(u'研討會】', u'】')
      print title
      print event_url

      date_row = event_tree.xpath('//table[@class="annual_table1"]/tr[1]/td[1]/text()')
      date = re.findall(r"\b\d{4}\/\d{2}\/\d{2}\b", date_row[0])
      start_date = date[0].replace('/', '-')
      if len(date) > 1:
        end_date = (datetime.strptime(date[1], "%Y/%m/%d") + relativedelta(days=1)).strftime("%Y-%m-%d")
      else:
        end_date = (datetime.strptime(date[0], "%Y/%m/%d") + relativedelta(days=1)).strftime("%Y-%m-%d")
      print start_date
      print end_date

      if not exist_event(event_id):
        add_db_event(event_id, title, event_url, start_date, end_date)
        add_gcal_event(title, event_url, start_date, end_date)
      else:
        print "exists"

#      if index > 3:
#        break
    else:
      print "No ID found. Probably not an avalable event."


def main():
  today = datetime.today()
  print 'Current date: ', today
  i = 0
  while i < 3:
    date = today + relativedelta(months=i)
    year = date.year
    month = date.month
    print 'Fetching year: ', year, ' month: ', month
    fetch_event_month(year, month)
    i += 1
  conn.close()


if __name__ == '__main__':
  main()