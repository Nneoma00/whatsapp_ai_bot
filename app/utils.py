# Standard library import
import logging

# Third-party imports
from twilio.rest import Client
from decouple import config

# import gspread
# from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime


# Find your Account SID and Auth Token at twilio.com/console
# and set the environment variables. See http://twil.io/secure
account_sid = config("TWILIO_ACCOUNT_SID")
auth_token = config("TWILIO_AUTH_TOKEN")
# Use an explicit name to avoid colliding with other `client` variables.
twilio_client = Client(account_sid, auth_token)
twilio_number = config('TWILIO_NUMBER')
to_number = config('TO_NUMBER')

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# #SETUP GOOGLE SHEETS API
# gc = gspread.service_account(filename="whatsapp-bot-credentials.json") # JSON file path
# sh = gc.open("RealtorAppointments")  # Exact sheet name
# worksheet = sh.worksheet("Sheet1")  # Select the specific worksheet
# data = worksheet.get_all_records()

# Sending message logic through Twilio Messaging API
def send_message(to_number, body_text):
    try:
        message = twilio_client.messages.create(
            from_=f"whatsapp:{twilio_number}",
            body=body_text,
            to=f"whatsapp:{to_number}"
        )
        logger.info(f"Message sent to {to_number}: {message.body}")
    except Exception as e:
        logger.error(f"Error sending message to {to_number}: {e}")



