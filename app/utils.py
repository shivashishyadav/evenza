# QR gen, PDF cert, email helpers
import qrcode #generate QR codes from text/data
import os
import threading

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
def send_async_email(app, msg):
    with app.app_context():
        try:
            mail.send(msg)
        except Exception as e:
            print(f'Email error: {e}')

def send_confirmation_email(student, event, qr_filename):
    from flask import current_app
    app = current_app._get_current_object()

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

         # send in background thread
        thread = threading.Thread(target=send_async_email, args=(app, msg))
        thread.start()

    except Exception as e:
        print(f'Email error: {e}')


# =======================================Reminder=========================================
def send_reminder_email(student, event):
    from flask import current_app
    app = current_app._get_current_object()

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

        thread = threading.Thread(target=send_async_email, args=(app, msg))
        thread.start()

    except Exception as e:
        print(f'Email error: {e}')


# ----------------------------------Certificate Generation-------------------------------------
# reportlab is a library to create PDFs
from reportlab.pdfgen import canvas as pdf_canvas # canvas is something like a drawing board, we can draw something on this
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors # used for styling

def generate_certificate(student_name, event_name, event_date, reg_id):
    """Create PDF -> Design layout -> Add text -> Save file -> Return filename"""

    filename = f"cert_{reg_id}.pdf"  # create filename (cert_12.pdf) (why unique? because one registration one certificate name)
    folder = os.path.join('app', 'static', 'certificates') # define folder (app/static/certificates/)
    os.makedirs(folder, exist_ok=True)  # if folder exists okay, if not then create it
    filepath = os.path.join(folder, filename) # final path (app/static/certificates/cert_12.pdf)

    # page setup
    width, height = landscape(A4) # page size
    c = pdf_canvas.Canvas(filepath, pagesize=landscape(A4)) #create drawing surface c

    # background color
    c.setFillColor(colors.HexColor('#f0f4ff'))
    c.rect(0, 0, width, height, fill=True, stroke=False)

    # border
    c.setStrokeColor(colors.HexColor('#1a56db'))
    c.setLineWidth(6)
    c.rect(20, 20, width - 40, height - 40, fill=False, stroke=True)

    # inner border
    c.setStrokeColor(colors.HexColor('#93c5fd'))
    c.setLineWidth(2)
    c.rect(30, 30, width - 60, height - 60, fill=False, stroke=True)

    # title
    c.setFillColor(colors.HexColor('#1a56db'))
    c.setFont('Helvetica-Bold', 42)
    c.drawCentredString(width / 2, height - 110, 'Certificate of Participation')

    # divider line
    c.setStrokeColor(colors.HexColor('#1a56db'))
    c.setLineWidth(1.5)
    c.line(100, height - 130, width - 100, height - 130)

    # body text
    c.setFillColor(colors.HexColor('#374151'))
    c.setFont('Helvetica', 20)
    c.drawCentredString(width / 2, height - 180, 'This is to certify that')

    # student name
    c.setFillColor(colors.HexColor('#1a56db'))
    c.setFont('Helvetica-Bold', 36)
    c.drawCentredString(width / 2, height - 240, student_name)

    # underline student name
    name_width = c.stringWidth(student_name, 'Helvetica-Bold', 36)
    c.setStrokeColor(colors.HexColor('#1a56db'))
    c.setLineWidth(1)
    c.line(width/2 - name_width/2, height - 248, width/2 + name_width/2, height - 248)
    
    # participated text
    c.setFillColor(colors.HexColor('#374151'))
    c.setFont('Helvetica', 20)
    c.drawCentredString(width / 2, height - 290, 'has successfully participated in')

    # event name
    c.setFillColor(colors.HexColor('#1a56db'))
    c.setFont('Helvetica-Bold', 28)
    c.drawCentredString(width / 2, height - 340, event_name)

    # event date
    c.setFillColor(colors.HexColor('#6b7280'))
    c.setFont('Helvetica', 16)
    c.drawCentredString(width / 2, height - 380, f'held on {event_date}')

    # divider
    c.setStrokeColor(colors.HexColor('#93c5fd'))
    c.setLineWidth(1)
    c.line(100, height - 420, width - 100, height - 420)

    # footer
    c.setFillColor(colors.HexColor('#6b7280'))
    c.setFont('Helvetica', 13)
    c.drawCentredString(width / 2, height - 450, 'Evenza — College Event Management System')

    c.save() #Writes everything to disk
    return filename #store in DB, send via email, show in UI


# -----------------------------Send Certificate on Mail------------------------------------
def send_certificate_email(student, event, cert_filename):
    from flask import current_app
    app = current_app._get_current_object()

    try:
        msg = Message(
            subject=f'Your Certificate — {event.title}',
            recipients=[student.email]
        )
        msg.body = f'''Hi {student.name},

            Congratulations on attending {event.title}!

            Your participation certificate is attached to this email.

            Thank you for being part of the event!
            Team Evenza
            '''
        msg.html = f"""
            <p>Hi {student.name},</p>
            <p>Congratulations on attending <b>{event.title}</b>!</p>
            <p>Your participation certificate is attached to this email.</p>
            <p>Thank you for being part of the event!<br>Team Evenza</p>
        """

        # attach PDF
        from flask import current_app
        filepath = os.path.join(current_app.root_path, 'static', 'certificates', cert_filename)
        with open(filepath, 'rb') as f:
            msg.attach(
                f"{event.title}_certificate.pdf",
                "application/pdf",
                f.read()
            )

        thread = threading.Thread(target=send_async_email, args=(app, msg))
        thread.start()

    except Exception as e:
        print(f'Certificate email error: {e}')


from datetime import datetime, timezone

def make_aware(dt):
    """Make datetime timezone-aware if it isn't already"""
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt