# Third-party imports
from google import genai
from google.genai import types
from fastapi import FastAPI, Form, Depends
from decouple import config
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from datetime import datetime, timedelta 
import json

# Internal imports
from app.models import Conversation, Appointment, SessionLocal
from app.utils import send_message, logger
from app.sheets_sync import sync_appt_to_sheet


app = FastAPI()

# Initialize Google GenAI client
genai_client = genai.Client(api_key=config("GEMINI_API_KEY"))  


# Database Dependency
def get_db():
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()


@app.post("/message")
async def reply(Body: str = Form(), From: str = Form(), db: Session = Depends(get_db)):
    whatsapp_number = From.replace('whatsapp:', '')

    # 1. Fetch last 3 messages from user (optional context)
    last_msgs = db.query(Conversation).filter_by(sender=whatsapp_number)\
        .order_by(Conversation.id.desc()).limit(3).all()
    context_text = "\n".join(msg.message for msg in reversed(last_msgs)) if last_msgs else ""

    # 2. Prepare system instruction for AI
    SYSTEM_INSTRUCTION = f"""
    You are Sherri's real estate assistant. Extract appointment details and respond naturally.

    Always return valid JSON in this EXACT format:
    {{
      "user_text": "your response to user here",
      "appointmentinfo": {{
        "name": "full name",
        "type": "showing|consultation|cancellation",
        "date": "YYYY-MM-DD",
        "time": "HH:MM"
      }}
    }}

    Instructions:
    - Use the recent conversation context to remember user details (name, preferences, previous requests)
    - If user provides complete appointment details (name, type, date, time), say: "Let me check Sherri's availability for that time..." NEVER confirm the appointment - that's handled separately.
    - If info is missing but you know it from context (like their name), use it. Only ask for what's truly missing.
    - If info is missing and not in context, ask naturally: "I'd be happy to help! Could you provide your name, appointment type (showing/consultation/cancellation), date and time?"
    - If just chatting (not booking), set appointmentinfo to null and respond naturally
    - Keep user_text brief (under 200 characters)
    - NEVER say "confirmed" or "booked" - Python will send a separate confirmation message
    - THE YEAR IS ALWAYS 2026. aLL DATES MUST BE IN 2026.
    
    CRITICAL FORMATTING:
    - date: "YYYY-MM-DD" (e.g., "2026-01-14")
    - time: "HH:MM" 24-hour format (e.g., "14:30")
    - type: "showing", "consultation", or "cancellation"
    
    Recent context: {context_text}
    """

    # 3. AI call
    try:
        response = genai_client.models.generate_content(
            model="gemini-2.5-flash",
            contents=Body,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
                max_output_tokens=1000,
                temperature=0.5,
            ),
        )

        # Debug logging
        print("=== FULL RESPONSE ===")
        print(response.text)
        print("=== END RESPONSE ===")
    except Exception:
        logger.exception("AI call failed")
        raise

    # 4. PARSE JSON PAYLOAD with proper error handling
    appt_info = None
    chat_response = "I'm having trouble processing that right now. Please try again."

    try:
        # Remove markdown code blocks if AI includes them
        response_text = response.text.strip()
        if response_text.startswith("```"):
            lines = response_text.split("\n")
            response_text = "\n".join(lines[1:-1])
            if response_text.startswith("json"):
                response_text = response_text[4:].strip()
        
        data = json.loads(response_text)
        chat_response = data.get("user_text", "I'm here to help with your real estate needs!")
        appt_info = data.get("appointmentinfo")
        
        # Validate appointmentinfo has all required fields and no nulls
        if appt_info:
            required_fields = ["name", "type", "date", "time"]
            if not all(appt_info.get(field) for field in required_fields):
                appt_info = None  # Incomplete data
                logger.info("Appointment info incomplete, not saving")
        
    except Exception as e:
        logger.error(f"Error parsing AI response: {e}. Response was: {response.text}")

    # 5. Store conversation
    try:
        conversation = Conversation(
            sender=whatsapp_number,
            message=Body,
            response=chat_response
        )
        db.add(conversation)
        db.commit()
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Error storing conversation: {e}")

    # 6. Send AI-generated message first (always)
    if len(chat_response) > 1600:
        chat_response = chat_response[:1597] + "..."
    send_message(whatsapp_number, chat_response)

    # 7. Process appointment if valid data was extracted
    if appt_info:
        try:
            # Convert date/time strings to datetime objects
            appt_dt = datetime.strptime(f"{appt_info['date']} {appt_info['time']}", "%Y-%m-%d %H:%M")
            appt_date = appt_dt.date()
            appt_time = appt_dt.time()

            # Cancellations skip conflict check - always save them
            if appt_info['type'] == 'cancellation':
                appt = Appointment(
                    phone=whatsapp_number,
                    name=appt_info['name'],
                    type=appt_info['type'],
                    date=appt_date,
                    time=appt_time,
                )
                db.add(appt)
                db.commit()
                logger.info(f"Cancellation saved: {appt_info}")
                
                confirmation_msg = f"✓ Cancellation noted. {appt_info['name']}'s appointment on {appt_info['date']} at {appt_info['time']} has been cancelled."
                send_message(whatsapp_number, confirmation_msg)
            
            else:
                # For bookings (showing/consultation), check for conflicts
                start_time = (appt_dt - timedelta(minutes=30)).time()
                end_time = (appt_dt + timedelta(minutes=30)).time()
                
                conflict = db.query(Appointment).filter(
                    Appointment.date == appt_date,
                    Appointment.time >= start_time,
                    Appointment.time <= end_time
                ).first()

                if not conflict:
                    # No conflict - save and confirm
                    appt = Appointment(
                        phone=whatsapp_number,
                        name=appt_info['name'],
                        type=appt_info['type'],
                        date=appt_date,
                        time=appt_time,
                    )
                    db.add(appt)
                    db.commit()
                    logger.info(f"Appointment saved: {appt_info}")
                    # Sync to Google Sheet
                    sync_appt_to_sheet()
                    
                    confirmation_msg = f"✓ Confirmed! {appt_info['name']}'s {appt_info['type']} on {appt_info['date']} at {appt_info['time']}."
                    send_message(whatsapp_number, confirmation_msg)
                else:
                    logger.warning(f"Appointment conflict detected for {appt_date} at {appt_time}")
                    # Send conflict message
                    conflict_msg = f"Sorry, Sherri already has an appointment at that time. Could you choose another time?"
                    send_message(whatsapp_number, conflict_msg)
                
        except ValueError as e:
            logger.error(f"Invalid date/time format: {e}")
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Error storing appointment: {e}")
        except Exception as e:
            logger.error(f"Unexpected error saving appointment: {e}")

    return ""


@app.get("/")
async def index():
    return {"msg": "up & running"}


@app.get("/sync-sheets")
def sync_sheets():
    sync_all_appointments_to_sheet()
    return {"status": "ok"}
