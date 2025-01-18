import os
import base64
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# Your Zoom API credentials
CLIENT_ID = os.getenv('ZOOM_CLIENT_ID', '0Uxt5PNBQQOle9SziFj35Q')
CLIENT_SECRET = os.getenv('ZOOM_CLIENT_SECRET', 'mvbN90eulvZ3kDXw1eIW1LhxS7Grh6z6')
REDIRECT_URI = os.getenv('ZOOM_REDIRECT_URI', 'http://localhost:5000/callback')

# Discord Webhook URL
DISCORD_WEBHOOK_URL = 'https://discord.com/api/webhooks/1329160606955208775/LLpKWCKgJCZc9DrRO_29Mse_buujvvfPsVJ_wrNDOuqB5xiaZismcCC-cbGl6sg_nl8K'


def send_discord_notification(meeting_details):
    """Send a message to Discord using a webhook."""
    payload = {
        "content": (
            f"**📢 New Trading Group Session Scheduled!**\n\n"
            f"**🆔 Meeting ID:** {meeting_details['id']}\n"
            f"**📝 Topic:** {meeting_details['topic']}\n"
            f"**🕒 Start Time:** {meeting_details['start_time']} (UTC)\n"
            f"**🔗 Join Link:** [Click here to join the session]({meeting_details['join_url']})\n\n"
            f"💡 **Note for Students:** Use the above link to join the session at the scheduled time. "
            f"Make sure your device is ready and you're logged into your Zoom account!"
        )
    }
    headers = {
        'Content-Type': 'application/json'
    }

    try:
        response = requests.post(DISCORD_WEBHOOK_URL, json=payload, headers=headers)
        if response.status_code == 204:
            print("Discord notification sent successfully.")
        else:
            print(f"Failed to send Discord notification. Status code: {response.status_code}")
            print(f"Response: {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"Error sending Discord notification: {e}")



def create_zoom_meeting(access_token):
    """Create a Zoom meeting using the Zoom API."""
    meeting_url = 'https://api.zoom.us/v2/users/me/meetings'
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    payload = {
        "topic": "Test Meeting",
        "type": 2,  # Scheduled meeting
        "start_time": "2025-01-16T10:00:00Z",
        "duration": 30,
        "timezone": "UTC"
    }

    try:
        response = requests.post(meeting_url, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error creating Zoom meeting: {e}")
        return None


@app.route('/callback')
def callback():
    # Step 1: Get the authorization code from the query string
    code = request.args.get('code')
    if not code:
        return jsonify({'error': 'Authorization code not found'}), 400

    # Step 2: Exchange the authorization code for an access token
    token_url = 'https://zoom.us/oauth/token'
    payload = {
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': REDIRECT_URI
    }
    headers = {
        'Authorization': f'Basic {base64.b64encode(f"{CLIENT_ID}:{CLIENT_SECRET}".encode()).decode()}'
    }

    try:
        response = requests.post(token_url, data=payload, headers=headers)
        response.raise_for_status()
        tokens = response.json()

        # Step 3: Create a Zoom meeting
        access_token = tokens.get('access_token')
        if not access_token:
            return jsonify({'error': 'Access token not found'}), 400

        meeting_details = create_zoom_meeting(access_token)
        if not meeting_details:
            return jsonify({'error': 'Failed to create Zoom meeting'}), 400

        # Step 4: Send the meeting details to Discord
        send_discord_notification(meeting_details)

        return jsonify({
            'message': 'Zoom meeting created and notification sent to Discord',
            'meeting_details': meeting_details
        })
    except requests.exceptions.RequestException as e:
        return jsonify({'error': str(e)}), 400


if __name__ == '__main__':
    app.run(debug=True)
