# AI-Powered WhatsApp Appointment Bot for Realtors

An intelligent, real-time appointment booking system that uses Gemini AI to handle natural conversations via WhatsApp, automatically detects scheduling conflicts, and syncs with Google Sheets for seamless schedule management.

## Features

- **Natural Language Processing**: Powered by Gemini AI for conversational appointment booking
- **Intelligent Conflict Detection**: Automatically checks for scheduling conflicts with ±30 minute buffer
- **Dual Database Architecture**: Separate tables for conversations and appointments for data integrity
- **Smart Routing**: Differentiates between cancellations and consultations
- **Real-time Sync**: Bidirectional integration with Google Sheets
- **Sub-5 Second Response**: Lightning-fast conflict resolution and booking confirmation
- **Auto Cleanup**: Automatically removes completed appointments when marked as "DONE"

## Demo
![Chat Sample](https://cdn.jsdelivr.net/gh/Nneoma00/whatsapp_ai_bot@main/images/chat-w-twilio.jpg)




## 🏗️ System Architecture

```
User WhatsApp Message
        ↓
   Twilio Webhook
        ↓
    Gemini AI (Natural conversation, data extraction)
        ↓
  Database Write (Conversations + Appointments)
        ↓
 Python Logic (Conflict check in <5s)
        ↓
    Conflict Found? 
    ├─ YES → Ask user for different time (loop back)
    └─ NO → Route by type (Cancel/Consult)
              ↓
        Confirm to User
              ↓
     Google Sheets Sync
```

## 📁 Project Structure

```
whatsapp_ai_bot/
├── main.py                          # FastAPI application, webhook handler
├── requirements.txt                 # Python dependencies
├── .env                            # Environment variables (API keys, credentials)
├── whatsapp-bot-credentials.json   # Google Sheets API credentials
└── app/
    ├── __init__.py                 # Package initializer
    ├── models.py                   # Database models (Conversations, Appointments)
    ├── utils.py                    # Gemini AI integration, business logic
    └── sheets_sync.py              # Google Sheets sync functionality
```

## Getting Started

### Prerequisites

- Python 3.8+
- Twilio account with WhatsApp enabled
- Google Cloud account (for Gemini AI and Sheets API)
- PostgreSQL/MySQL database (or your preferred DB)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/Nneoma00/whatsapp_ai_bot.git
   cd whatsapp_ai_bot
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   
   Create a `.env` file in the root directory:
   ```env
   # Twilio Configuration
   TWILIO_ACCOUNT_SID=your_account_sid
   TWILIO_AUTH_TOKEN=your_auth_token
   TWILIO_WHATSAPP_NUMBER=whatsapp:+14155238886
   
   # Gemini AI Configuration
   GOOGLE_API_KEY=your_gemini_api_key
   
   # Database Configuration
   DATABASE_URL=postgresql://user:password@localhost:5432/appointments_db
   ```

4. **Set up Google Sheets API**
   
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select existing
   - Enable Google Sheets API
   - Create service account credentials
   - Download JSON and save as `whatsapp-bot-credentials.json`
   - Share your Google Sheet with the service account email

5.  **Run the application**
   ```bash
   uvicorn main:app --reload 
   ```

7. **Configure Twilio Webhook**
   
   - Go to your Twilio Console
   - Navigate to WhatsApp Sandbox settings
   - Set webhook URL to: `https://your-domain.com/webhook` (use ngrok for local testing)
   - Method: POST


## 🔄 How It Works

1. **User Interaction**: User sends a WhatsApp message (e.g., "Is Sherri available on Friday at 2pm")

2. **AI Processing**: Gemini AI:
   - Engages in natural conversation
   - Prompts for missing information (name, time, date)
   - Extracts structured data
   - Returns JSON with `user_text` and `appointmentinfo`

3. **Data Storage**: 
   - Saves complete conversation to `Conversations` table
   - Extracts and saves appointment details to `Appointments` table

4. **Conflict Detection**: Python logic:
   - Queries existing appointments
   - Checks for conflicts with ±30 minute buffer
   - Returns conflict status in under 5 seconds

5. **Smart Routing**:
   - **If conflict found**: Ask user to pick a different time
   - **If no conflict**: Route by appointment type
     - Cancellation → Acknowledge
     - Consultation → Confirm booking

6. **Sync to Sheets**: Update Google Sheets with new appointment

7. **Auto Cleanup**: When realtor marks status as "DONE", row is deleted on next sync

## 🛠️ Key Components

### `main.py`
- FastAPI application setup
- Webhook endpoint for Twilio
- Request/response handling

### `app/utils.py`
- Gemini AI integration
- Appointment conflict detection logic
- Business logic for routing and validation
- Message formatting

### `app/models.py`
- SQLAlchemy database models
- Database connection setup
- CRUD operations

### `app/sheets_sync.py`
- Google Sheets API integration
- Bidirectional sync functionality
- Auto-delete logic for DONE status

## 📝 Example Conversation Flow

```
User: "Hi, I need to book an appointment"
Bot: "Hello! I'd be happy to help you book an appointment. 
     Could you please provide your name?"

User: "John Smith"
Bot: "Thank you, John! What type of appointment would you like?"

User: "Consultation"
Bot: "Great! What date and time works best for you?"

User: "This Friday at 2pm"
Bot: "Perfect! Let me check availability... 
     ✅ Your consultation is confirmed for Friday, Jan 17 at 2:00 PM. 
     See you then!"
```

## 🔐 Security Considerations

- Store all sensitive credentials in `.env` file
- Never commit `.env` or `whatsapp-bot-credentials.json` to version control
- Add them to `.gitignore`:
  ```
  .env
  whatsapp-bot-credentials.json
  __pycache__/
  *.pyc
  ```
- Use environment variables for production deployment
- Implement rate limiting for webhook endpoint
- Validate and sanitize all user inputs


⭐ If you find this project useful, please consider giving it a star!
