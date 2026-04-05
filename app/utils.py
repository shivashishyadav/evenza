# QR gen, PDF cert, email helpers
import qrcode #generate QR codes from text/data
import os

from flask_mail import Message
from app import mail

# One user can register for multiple events,So combination ensures uniqueness
def generate_qr(registration_id, user_id, event_id):
    # unique data string for this registration (EVENZA-REG-12-5-3)
    data = f"EVENZA-REG-{registration_id}-{user_id}-{event_id}"

    # create QR code(object)
    qr = qrcode.QRCode(
        version=1, #Controls QR size (1 = smallest), version 1=21x21grid, higher version more data capacity
        error_correction=qrcode.constants.ERROR_CORRECT_H, #Allows QR to still work even if damaged
        box_size=10, #Size of each pixel block, Bigger = larger image
        border=4  #White margin around QR
    )
    qr.add_data(data=data)
    qr.make(fit=True)

    # readable QR with black dot/pattern and white background
    img = qr.make_image(fill_color="black", back_color="white")

    # save to static/qrcodes/ 
    filename = f"qr_{registration_id}_{user_id}_{event_id}.png" # create filename(Standard readable QR)
    folder = os.path.join('app','static','qrcodes') #folder path
    os.makedirs(folder, exist_ok=True) #create folder if missing, doesn’t crash if already exists

    # full file path
    filepath = os.path.join(folder,filename) #app/static/qrcodes/qr_12_5_3.png
    img.save(filepath) #QR image is now stored on disk

    return filename #so that we can store it in DB, use in UI


# ============================== Verification Mail==========================================
def send_confirmation_email(student, event, qr_filename):
    try:
        msg = Message(subject=f'Registration Confirmed - {event.title}', recipients=[student.email])
        msg.body= f'''Hi {student.name},
                Your registration for {event.title} is confirmed!
                
                Event Details:
                - Venue: {event.venue}
                - Date: {event.date.strftime('%d %b %Y, %I:%M %p')}

                Please carry your QR code for check-in.
                Login to Evenza to view your QR code.
                
                Your QR code is attached to this email.

                See you there!
                Team Evenza
            '''
        # HTML VERSION WITH QR CODE  
        msg.html = f"""
                <p>Hi {student.name},</p>

                <p>Your registration for <b>{event.title}</b> is confirmed!</p>

                <p><b>Event Details:</b></p>
                <ul>
                <li>Venue: {event.venue}</li>
                <li>Date: {event.date.strftime('%d %b %Y, %I:%M %p')}</li>
                </ul>

                <p><b>Scan this QR at entry:</b></p>
                <img src="cid:qr_code" width="200">

                <p>See you there!<br>Team Evenza</p>
            """

        
        # Attach QR
        filepath = os.path.join('app', 'static', 'qrcodes', qr_filename)

        with open(filepath, 'rb') as f:
            msg.attach(
                qr_filename,
                "image/png",
                f.read(),
                headers={'Content-ID': '<qr_code>'}
            )

        mail.send(msg)

    except Exception as e:
        print(f'Email error: {e}')


# ==============================Reminder===================================
def send_reminder_email(student, event):
    try:
        msg = Message(
            subject=f'Reminder — {event.title} is on {event.date.strftime("%d %b %Y")}!',
            recipients=[student.email]
        )
        msg.body = f'''Hi {student.name},

            Just a reminder that {event.title} is on {event.date.strftime("%d %b %Y")}!

            Event Details:
            - Venue: {event.venue}
            - Date: {event.date.strftime('%d %b %Y, %I:%M %p')}

            Don't forget to carry your QR code for check-in.
            Login to Evenza to view your QR code.

            See you there!
            Team Evenza
        '''
        mail.send(msg)
    except Exception as e:
        print(f'Email error: {e}')
    