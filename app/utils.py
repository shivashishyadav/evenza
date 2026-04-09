import qrcode
import os
import io
import threading
import requests
import base64
from flask import current_app


# allowed image extensions
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png'}

def allowed_file(filename):
    if '.' not in filename:
        return False
    extension = filename.split('.')[-1].lower()
    if extension in ALLOWED_EXTENSIONS:
        return True
    else:
        return False


# --- QR GENERATION LOGIC ---

def generate_qr_image(registration_id, user_id, event_id):
    """Generate QR code and return as bytes in memory"""
    data = f"EVENZA-REG-{registration_id}-{user_id}-{event_id}"
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4
    )
    qr.add_data(data=data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    return buffer.getvalue()

def generate_qr(registration_id, user_id, event_id):
    """Saves QR to disk (for UI display) and returns filename"""
    data = f"EVENZA-REG-{registration_id}-{user_id}-{event_id}"
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4
    )
    qr.add_data(data=data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    filename = f"qr_{registration_id}_{user_id}_{event_id}.png"
    folder = os.path.join(current_app.root_path, 'static', 'qrcodes')
    os.makedirs(folder, exist_ok=True)
    
    filepath = os.path.join(folder, filename)
    img.save(filepath)
    return filename

# --- CORE EMAIL ENGINE (BREVO API) ---

def send_brevo_api_email(to_email, to_name, subject, html_content, attachment_name=None, attachment_content=None):
    """Universal helper to send email via Brevo HTTP API (Bypasses Port Blocks)"""
    api_key = os.environ.get('BREVO_API_KEY').strip()
    sender_email = os.environ.get('MAIL_DEFAULT_SENDER').strip()
    
    url = "https://api.brevo.com/v3/smtp/email"
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "api-key": api_key
    }
    
    payload = {
        "sender": {"name": "Evenza", "email": sender_email},
        "to": [{"email": to_email, "name": to_name}],
        "subject": subject,
        "htmlContent": html_content
    }

    if attachment_content:
        # API requires Base64 for attachments
        b64_content = base64.b64encode(attachment_content).decode('utf-8')
        payload["attachment"] = [{
            "name": attachment_name,
            "content": b64_content
        }]

    try:
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code not in [200, 201, 202]:
            print(f"Brevo Error: {response.text}")
        else:
            print(f"Email successfully sent to {to_email}")
    except Exception as e:
        print(f"Network error calling Brevo API: {e}")

# --- SPECIFIC EMAIL FUNCTIONS ---

def send_confirmation_email(student, event, registration_id, user_id, event_id):
    """Sends registration confirmation with QR code attached"""
    qr_bytes = generate_qr_image(registration_id, user_id, event_id)
    
    html = f"""
        <html><body>
            <p>Hi {student.name},</p>
            <p>Your registration for <b>{event.title}</b> is confirmed!</p>
            <p><b>Event Details:</b></p>
            <ul>
                <li>Venue: {event.venue}</li>
                <li>Date: {event.date.strftime('%d %b %Y, %I:%M %p')}</li>
            </ul>
            <p>Please find your QR code attached to this email. You can also view it in your dashboard.</p>
            <p>See you there!<br>Team Evenza</p>
        </body></html>
    """
    
    thread = threading.Thread(target=send_brevo_api_email, args=(
        student.email, 
        student.name, 
        f"Registration Confirmed - {event.title}",
        html,
        f"qr_event_{event_id}.png",
        qr_bytes
    ))
    thread.start()

def send_reminder_email(student, event):
    """Sends event reminder (No attachment)"""
    html = f"""
        <html><body>
            <p>Hi {student.name},</p>
            <p>Just a reminder that <b>{event.title}</b> is happening soon!</p>
            <p><b>Date:</b> {event.date.strftime('%d %b %Y, %I:%M %p')}<br>
               <b>Venue:</b> {event.venue}</p>
            <p>Don't forget your QR code!</p>
        </body></html>
    """
    thread = threading.Thread(target=send_brevo_api_email, args=(
        student.email,
        student.name,
        f"Reminder: {event.title} is coming up!",
        html
    ))
    thread.start()

def send_certificate_email(student, event, cert_filename, pdf_bytes=None):
    """Sends participation certificate as PDF attachment"""
    # If bytes aren't passed, try reading from disk
    if not pdf_bytes:
        folder = os.path.join(current_app.root_path, 'static', 'certificates')
        filepath = os.path.join(folder, cert_filename)
        if os.path.exists(filepath):
            with open(filepath, 'rb') as f:
                pdf_bytes = f.read()

    html = f"""
        <html><body>
            <p>Hi {student.name},</p>
            <p>Congratulations on attending <b>{event.title}</b>!</p>
            <p>Your participation certificate is attached to this email.</p>
            <p>Thank you for being part of Evenza!<br>Team Evenza</p>
        </body></html>
    """
    
    thread = threading.Thread(target=send_brevo_api_email, args=(
        student.email,
        student.name,
        f"Your Certificate — {event.title}",
        html,
        f"{event.title}_Certificate.pdf",
        pdf_bytes
    ))
    thread.start()

# --- HELPER LOGIC ---

from datetime import datetime, timezone
def make_aware(dt):
    if dt is None: return None
    if dt.tzinfo is None: return dt.replace(tzinfo=timezone.utc)
    return dt

# --- PDF GENERATION LOGIC ---
from reportlab.pdfgen import canvas as pdf_canvas
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors

def generate_certificate(student_name, event_name, event_date, reg_id):
    filename = f"cert_{reg_id}.pdf"
    folder = os.path.join(current_app.root_path, 'static', 'certificates')
    os.makedirs(folder, exist_ok=True)
    filepath = os.path.join(folder, filename)

    width, height = landscape(A4)
    c = pdf_canvas.Canvas(filepath, pagesize=landscape(A4))

    # Design
    c.setFillColor(colors.HexColor('#f0f4ff'))
    c.rect(0, 0, width, height, fill=True, stroke=False)
    c.setStrokeColor(colors.HexColor('#1a56db'))
    c.setLineWidth(6)
    c.rect(20, 20, width - 40, height - 40, fill=False, stroke=True)

    # Text
    c.setFillColor(colors.HexColor('#1a56db'))
    c.setFont('Helvetica-Bold', 42)
    c.drawCentredString(width / 2, height - 110, 'Certificate of Participation')
    
    c.setFillColor(colors.HexColor('#374151'))
    c.setFont('Helvetica', 20)
    c.drawCentredString(width / 2, height - 180, 'This is to certify that')

    c.setFillColor(colors.HexColor('#1a56db'))
    c.setFont('Helvetica-Bold', 36)
    c.drawCentredString(width / 2, height - 240, student_name)

    c.setFillColor(colors.HexColor('#374151'))
    c.setFont('Helvetica', 20)
    c.drawCentredString(width / 2, height - 290, 'has successfully participated in')

    c.setFillColor(colors.HexColor('#1a56db'))
    c.setFont('Helvetica-Bold', 28)
    c.drawCentredString(width / 2, height - 340, event_name)

    c.setFillColor(colors.HexColor('#6b7280'))
    c.setFont('Helvetica', 16)
    c.drawCentredString(width / 2, height - 380, f'held on {event_date}')

    c.save()
    
    with open(filepath, 'rb') as f:
        pdf_bytes = f.read()

    return filename, pdf_bytes


def send_otp_email(user_email, user_name, otp):
    """Sends a 6-digit OTP for account verification using Brevo API"""
    html = f"""
        <html><body style="font-family: Arial, sans-serif; color: #374151;">
            <div style="max-width: 600px; margin: auto; border: 1px solid #e5e7eb; padding: 20px; border-radius: 12px;">
                <h2 style="color: #1a56db; text-align: center;">Verify Your Evenza Account</h2>
                <p>Hi {user_name},</p>
                <p>Thank you for joining Evenza! To complete your registration, please use the following One-Time Password (OTP):</p>
                <div style="text-align: center; margin: 30px 0;">
                    <span style="font-size: 32px; font-weight: bold; letter-spacing: 8px; color: #1a56db; background: #f0f4ff; padding: 10px 20px; border-radius: 8px; border: 1px dashed #1a56db;">
                        {otp}
                    </span>
                </div>
                <p style="font-size: 14px; color: #6b7280;">This code will expire shortly. If you did not request this, please ignore this email.</p>
                <hr style="border: 0; border-top: 1px solid #e5e7eb; margin: 20px 0;">
                <p style="font-size: 12px; color: #9ca3af; text-align: center;">Team Evenza — Campus Event Management</p>
            </div>
        </body></html>
    """
    # Using a thread to keep the registration snappy
    thread = threading.Thread(target=send_brevo_api_email, args=(
        user_email, 
        user_name, 
        "Verify your Evenza Account", 
        html
    ))
    thread.start()


def send_reset_otp_email(user_email, user_name, otp):
    """Sends a 6-digit OTP for password reset using Brevo API"""
    html = f"""
        <html><body style="font-family: Arial, sans-serif; color: #374151;">
            <div style="max-width: 600px; margin: auto; border: 1px solid #e5e7eb; padding: 20px; border-radius: 12px;">
                <h2 style="color: #1a56db; text-align: center;">Reset Your Password</h2>
                <p>Hi {user_name},</p>
                <p>We received a request to reset your Evenza password. Use the following OTP to proceed:</p>
                <div style="text-align: center; margin: 30px 0;">
                    <span style="font-size: 32px; font-weight: bold; letter-spacing: 8px; color: #1a56db; background: #fef2f2; padding: 10px 20px; border-radius: 8px; border: 1px dashed #dc2626;">
                        {otp}
                    </span>
                </div>
                <p style="font-size: 14px; color: #6b7280;">If you didn't request this, you can safely ignore this email. Your password will not change until you verify this code.</p>
                <hr style="border: 0; border-top: 1px solid #e5e7eb; margin: 20px 0;">
                <p style="font-size: 12px; color: #9ca3af; text-align: center;">Team Evenza</p>
            </div>
        </body></html>
    """
    thread = threading.Thread(target=send_brevo_api_email, args=(
        user_email, user_name, "Password Reset OTP - Evenza", html
    ))
    thread.start()