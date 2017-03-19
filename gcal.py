from __future__ import print_function
import httplib2
import os

from apiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage
from oauth2client.service_account import ServiceAccountCredentials

import datetime

try:
    import argparse
    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    flags = None

# If modifying these scopes, delete your previously saved credentials
# at ~/.credentials/calendar-python-quickstart.json
SCOPES = 'https://www.googleapis.com/auth/calendar'
CLIENT_SECRET_FILE = 'client_secret.json'
KEY_FILE = '_client_secret.json'


# Functions
def get_credentials():
    credentials = ServiceAccountCredentials.from_json_keyfile_name(KEY_FILE, scopes=SCOPES)
    return credentials

def create_calendar():
  # Create a calendar for the Service Account
  calendar = {
    'summary': 'My Calendar',
  #  'timeZone': 'America/Los_Angeles'
  }

  created_calendar = service.calendars().insert(body=calendar).execute()

  print(created_calendar['id'])


def list_calendars():
  # List calendars
  print('Listing calendars')
  page_token = None
  while True:
    calendar_list = service.calendarList().list(pageToken=page_token).execute()
    for calendar_list_entry in calendar_list['items']:
      print(calendar_list_entry['summary'])
    page_token = calendar_list.get('nextPageToken')
    if not page_token:
      break


def set_calendar_owner():
  # Set calendar owner
  rule = {
      'scope': {
          'type': 'user',
          'value': 'ittsai@gmail.com',
      },
      'role': 'owner'
  }

  created_rule = service.acl().insert(calendarId='primary', body=rule).execute()

  print(created_rule['id'])


def insert_a_test_event():
  # Insert an event
  event = {
    'summary': 'Test Event',
    'start': {
      'date': '2017-03-18',
    },
    'end': {
      'date': '2017-03-18',
    },
  }

  event = service.events().insert(calendarId='primary', body=event).execute()
  print('Event created: %s' % (event.get('htmlLink')))


def clear_calendar():
  # clear calendar
  print('Clearing calendar...')
  eventsResult = service.events().list(calendarId='primary').execute()
  events = eventsResult.get('items', [])

  if not events:
    print('No events found.')
  for event in events:
    service.events().delete(calendarId='primary', eventId=event['id']).execute()


def print_events():
    now = datetime.datetime.utcnow().isoformat() + 'Z' # 'Z' indicates UTC time

    print('Getting the upcoming 10 events...')
    eventsResult = service.events().list(
        calendarId='primary', timeMin=now, maxResults=10, singleEvents=True,
        orderBy='startTime').execute()
    events = eventsResult.get('items', [])

    if not events:
        print('No upcoming events found.')
    for event in events:
        start = event['start'].get('dateTime', event['start'].get('date'))
        print(start, event['summary'])


# Global vars
credentials = get_credentials()
http = credentials.authorize(httplib2.Http())
service = discovery.build('calendar', 'v3', http=http)


def main():
    #create_calendar()
    #list_calendars()
    #set_calendar_owner()
    #insert_a_test_event()
    clear_calendar()
    #print_events()

if __name__ == '__main__':
    main()