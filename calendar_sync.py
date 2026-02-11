
import datetime
import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import json

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CREDENTIALS_FILE = os.path.join(BASE_DIR, 'credentials.json')
TOKEN_FILE = os.path.join(BASE_DIR, 'token.json')

def get_calendar_service():
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(CREDENTIALS_FILE):
                raise FileNotFoundError(f"Credentials file not found at {CREDENTIALS_FILE}")
            flow = InstalledAppFlow.from_client_secrets_file(
                CREDENTIALS_FILE, SCOPES)
            # Manual flow for remote/headless setup
            # We use a fixed redirect_uri that matches the console config (usually http://localhost:<port> is allowed for Desktop apps)
            # We'll use a random port or just http://localhost depending on what works. 
            # run_local_server uses random ports, suggesting wildcard port matching is enabled.
            # Match credentials.json exactly
            flow.redirect_uri = 'http://localhost'
            
            auth_url, _ = flow.authorization_url(prompt='consent', access_type='offline')
            
            print('-' * 80)
            print('Please visit this URL to authorize this application:\n')
            print(auth_url)
            print('\n' + '-' * 80)
            print('After giving consent, you will be redirected to a localhost URL (e.g. http://localhost/?code=...)')
            print('It might fail to load. This is EXPECTED.')
            print('Please copy the ENTIRE URL from your browser address bar and paste it here.')
            
            code = input('Paste the full redirect URL here: ').strip()
            
            # Handle if user pastes just the code or the full url
            # fetch_token(authorization_response=...) handles the URL parsing
            # If protocol is missing, it might complain, so ensure http is there if it looks like a url
            
            # Since https is required by some libs, but localhost is http, we allow http
            os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
            
            flow.fetch_token(authorization_response=code)
            creds = flow.credentials
        # Save the credentials for the next run
        with open(TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())

    service = build('calendar', 'v3', credentials=creds)
    return service

def get_busy_slots():
    """Fetches events for the current day (or next available workday) and returns busy time slots."""
    service = get_calendar_service()

    # Define time range: Now to End of Day
    now = datetime.datetime.now()
    # If it's late, maybe look at tomorrow? For now, stick to "Rest of Today" or "Tomorrow" logic matching scheduler
    # We should align with scheduler.py logic which defaults to tomorrow if late
    start_time = now.replace(hour=9, minute=0, second=0, microsecond=0)
    if start_time < now:
         start_time += datetime.timedelta(days=1) # Tomorrow
    
    end_time = start_time.replace(hour=17, minute=0, second=0)
    
    # ISO format needed by API
    timeMin = start_time.isoformat() + 'Z' # 'Z' indicates UTC time
    timeMax = end_time.isoformat() + 'Z'
    
    # Note: The above naive ISO format assumes UTC but datetime.now() is local. 
    # Proper time zone handling is complex. For simplicity in this script, we'll ask the API for 'primary' calendar
    # and let it handle timeMin/Max best effort, but properly we should localize.
    # Let's use simple local execution time for the scheduler and assume the user runs this in their timezone.
    
    # Better approach: Get events for the full "scheduler day"
    # Scheduler logic: 
    # start_time = datetime.datetime.now().replace(hour=9, minute=0, second=0, microsecond=0)
    # if start_time < datetime.datetime.now(): start_time += datetime.timedelta(days=1)
    
    # We need to construct the query window
    start_dt = start_time
    end_dt = start_time.replace(hour=23, minute=59)
    
    print(f"Fetching calendar events for {start_dt.date()}...")
    
    events_result = service.events().list(calendarId='primary', timeMin=start_dt.isoformat() + 'Z',
                                          timeMax=end_dt.isoformat() + 'Z', singleEvents=True,
                                          orderBy='startTime').execute()
    events = events_result.get('items', [])
    
    busy_slots = []
    
    if not events:
        print('No upcoming events found.')
    else:
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            end = event['end'].get('dateTime', event['end'].get('date'))
            summary = event.get('summary', 'Busy')
            
            # Simple parsing of ISO strings roughly
            # 2026-02-04T10:00:00-05:00
            # We just need the time part for the scheduler
            
            # Helper to convert ISO string to datetime object
            # Removing timezone info for simple local comparison
            try:
                s_dt = datetime.datetime.fromisoformat(start)
                e_dt = datetime.datetime.fromisoformat(end)
                
                # Make offset-naive for comparison with scheduler's naive objects
                s_dt = s_dt.replace(tzinfo=None)
                e_dt = e_dt.replace(tzinfo=None)
                
                busy_slots.append({
                    'start': s_dt,
                    'end': e_dt,
                    'summary': summary
                })
                print(f"  Found event: {summary} ({s_dt.strftime('%H:%M')} - {e_dt.strftime('%H:%M')})")
                
            except ValueError:
                pass # All-day events might format differently (YYYY-MM-DD), skipping for now or treat as blocking?
                # skipping for simplicity of the prompt
                
    return busy_slots

if __name__ == '__main__':
    try:
        slots = get_busy_slots()
        print("Busy Slots:", slots)
    except Exception as e:
        print(f"Error: {e}")
