import json
from django.http import HttpResponse, HttpResponseRedirect
from django.views import View
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from django.conf import settings


class GoogleCalendarInitView(View):
    def get(self, request):
        flow = Flow.from_client_secrets_file(
            'credentials.json',
            scopes=['https://www.googleapis.com/auth/calendar.readonly'],
            redirect_uri=settings.GOOGLE_CALENDAR_REDIRECT_URI
        )
        authorization_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true'
        )
        request.session['state'] = state
        return HttpResponseRedirect(authorization_url)


class GoogleCalendarRedirectView(View):
    def get(self, request):
        state = request.session.pop('state', None)
        if state is None or state != request.GET.get('state', ''):
            return HttpResponse('Invalid state parameter', status=400)

        flow = Flow.from_client_secrets_file(
            'credentials.json',
            scopes=['https://www.googleapis.com/auth/calendar.readonly'],
            redirect_uri=settings.GOOGLE_CALENDAR_REDIRECT_URI
        )

        try:
            flow.fetch_token(authorization_response=request.build_absolute_uri())
            credentials = flow.credentials
        except Exception as e:
            return HttpResponse(f'Failed to fetch token: {e}', status=400)

        try:
            service = build('calendar', 'v3', credentials=credentials)
            events_result = service.events().list(calendarId='primary', maxResults=10).execute()
            events = events_result.get('items', [])
            event_list = []
            for event in events:
                event_list.append(event['summary'])

            return HttpResponse(json.dumps(event_list), content_type='application/json')

        except HttpError as err:
            return HttpResponse(f'API request error: {err}', status=500)
