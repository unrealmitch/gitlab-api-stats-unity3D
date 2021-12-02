from __future__ import print_function
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

# The ID and range of a sample spreadsheet.
SPREADSHEET_ID = '1uJkfCcGOZvfZUEtx-JtfVlTIlFRhJJeM9qaEKknV318'
RANGE = 'Datos!A:A'
START_CELL = 'Datos!A3'

def login():
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    service = build('sheets', 'v4', credentials=creds)
    return service

def appendCommitsGoogleSheet(values):
    service = login()

    body = {
        "majorDimension": "ROWS",
        'values': values
    }
    result = service.spreadsheets().values().append(
        spreadsheetId=SPREADSHEET_ID, range=RANGE,
        valueInputOption="USER_ENTERED", body=body).execute()
    print('{0} rows appended.'.format(result.get('updates').get('updatedRows')))


def replaceCommitsGoogleSheet(values):
    service = login()

    data = [
        {
            'range': START_CELL,
            'values': values
        },
    ]
    body = {
        'valueInputOption': "USER_ENTERED",
        'data': data
    }
    result = service.spreadsheets().values().batchUpdate(
        spreadsheetId=SPREADSHEET_ID, body=body).execute()
    print('{0} rows updated.'.format(result.get('totalUpdatedRows')))

    