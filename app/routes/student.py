# browse events, register, dashboard
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.decorators import role_required
from app.models import Event, Registration, Certificate, Attendance
from app import db
from datetime import datetime, timezone

from app.utils import generate_qr, send_confirmation_email, generate_certificate, send_certificate_email, make_aware

student = Blueprint('student', __name__)


# --------------------------DASHBOARD-----------------------------
@student.route('/student/dashboard')
@login_required #Only logged-in users can logout
@role_required('student')
def dashboard():
    regs = Registration.query.filter_by(user_id=current_user.id).all() #all registration of current user
    total = len(regs) # total number of events of current user
    confirmed = sum(1 for r in regs if r.status=='confirmed') #Count only those with status = confirmed
    waitlist = sum(1 for r in regs if r.status=='waitlist') #Events where user is not guaranteed a seat

    # # upcoming events only
    # from datetime import datetime, timezone
    # now = datetime.now(timezone.utc).replace(tzinfo=None)
    # # Only events that haven’t happened yet, Ignore waitlist events
    # upcoming = [r for r in regs if r.event.date>now and r.status=='confirmed']

    now = datetime.now(timezone.utc)
    upcoming = [
        r for r in regs
        if r.status == 'confirmed' and make_aware(r.event.date) > now
    ]

    # Send data to template & return template
    return render_template('student/dashboard.html',
        regs=regs,
        total=total,
        confirmed=confirmed,
        waitlist=waitlist,
        upcoming=upcoming
    )


# --------------------------My Events-------------------------------
@student.route('/student/my-events')
@login_required
@role_required('student')
def my_events():    
    regs = Registration.query.filter_by(user_id=current_user.id).all()
    total = len(regs)
    confirmed = sum(1 for r in regs if r.status == 'confirmed')
    waitlist = sum(1 for r in regs if r.status == 'waitlist')
    # now = datetime.now(timezone.utc).replace(tzinfo=None)
    # upcoming = [r for r in regs if r.event.date > now and r.status == 'confirmed']

    now = datetime.now(timezone.utc)
    upcoming = [
        r for r in regs
        if r.status == 'confirmed' and make_aware(r.event.date) > now
    ]

    return render_template('student/dashboard.html',
        regs=regs,
        total=total,
        confirmed=confirmed,
        waitlist=waitlist,
        upcoming=upcoming
    )   


# ------------------------Events Listing--------------------------------------
@student.route('/student/events')
@login_required
@role_required('student')
def events():
    search = request.args.get('search', '')
    query = Event.query.filter_by(status='approved')

    if search:
        query = query.filter(Event.title.ilike(f"%{search}%"))
    events = query.order_by(Event.date.asc()).all()

    events_list = []

    for event in events:
        count = Registration.query.filter_by(
            event_id=event.id,
            status='confirmed'
        ).count()

        seats_left = event.capacity - count
        events_list.append((event, seats_left))

    return render_template('student/events.html', events=events_list)


# ------------------------------REGISTER-----------------------------------
@student.route('/student/register/<int:event_id>', methods=["POST"])
@login_required
@role_required('student')
def register(event_id):
    event = Event.query.get_or_404(event_id)

    # # only approved events
    if event.status != 'approved':
        flash('This event is not available for registration.', 'danger')
        return redirect(url_for('student.events'))
    
    # check already registered: prevent duplicate
    existing = Registration.query.filter_by(
        user_id=current_user.id,
        event_id=event_id
    ).first()

    if existing:
        flash('Already registered!', 'warning')
        return redirect(url_for('student.my_events'))
    
    # count confirmed registrations
    count = Registration.query.filter_by(
        event_id=event_id,
        status='confirmed'
    ).count()

    if count < event.capacity:
        status = 'confirmed'
    else:
        status = 'waitlist'
    
    reg = Registration( #reg.id=None
        user_id=current_user.id,
        event_id=event_id,
        status=status
    )

    db.session.add(reg) # Added to session, still reg.id=None, because SQLAlchemy hasn’t sent query to DB yet
 
    # It sends pending changes to DB WITHOUT committing
    db.session.flush()  #get reg.id before commit(if i dont use flush then reg.id=None, thats crash the code)
    # if we dont use flush, data string for qr generation is: EVENZA-REG-None-5-3(useless, lost uniqueness)

    # flush = "talk to DB, but don’t finalize"
    # commit = "final save"

    #generate qr code only for confirmed registration
    # Waitlist users don’t have guaranteed seat
    if status == 'confirmed': 
        qr_filename = generate_qr(reg.id, current_user.id, event_id)
        reg.qr_code = qr_filename #stores filename in DB, link registration to qr image

    db.session.commit()

    if status == 'confirmed':
        send_confirmation_email(current_user, event, reg.id, current_user.id, event_id) # send mail
        flash('Registered successfully! Your QR code is ready.', 'success')
    else:
        flash('Event full — added to waitlist.', 'warning')

    return redirect(url_for('student.my_events'))

# -----------------------------------------------------------------------------
from flask import send_file
import io

@student.route('/student/qr/<int:reg_id>')
@login_required
@role_required('student')
def get_qr(reg_id):
    reg = Registration.query.get_or_404(reg_id)

    # security check
    if reg.user_id != current_user.id:
        return 'Unauthorized', 403

    from app.utils import generate_qr_image
    qr_bytes = generate_qr_image(reg.id, reg.user_id, reg.event_id)
    return send_file(
        io.BytesIO(qr_bytes),
        mimetype='image/png'
    )

# ------------------------------CERTIFICATES------------------------------
@student.route('/student/my-certificates')
@login_required
@role_required('student')
def my_certificates():
    '''Check registrations -> Check attendance -> Generate certificate (if needed) -> Show list'''

    # get all confirmed registrations
    regs = Registration.query.filter_by(
        user_id=current_user.id,
        status='confirmed'
    ).all()

    certs = [] #(event, certificate)
    for reg in regs:
        # check if student attended(Did user actually attend the event?)
        attendance = Attendance.query.filter_by(
            registration_id=reg.id,
            is_present=True
        ).first()

        # registered but absent
        if not attendance:
            continue  # skip if not attended

        # check if certificate already exists(“Did we already generate certificate?”)
        cert = Certificate.query.filter_by(registration_id=reg.id).first()

        if not cert:
            # generate certificate
            filename, pdf_bytes  = generate_certificate(
                student_name=current_user.name,
                event_name=reg.event.title,
                event_date=reg.event.date.strftime('%d %b %Y'),
                reg_id=reg.id
            )
            cert = Certificate(
                registration_id=reg.id,
                file_path=filename
            )
            db.session.add(cert)
            db.session.commit()
            # send certificate email — only on first generation
            send_certificate_email(current_user, reg.event, filename, pdf_bytes)

        certs.append((reg.event, cert)) #event name + certificate name

    # send data to frontend and shows the certificates list
    return render_template('student/my_certificates.html', certs=certs)


# -------------------------------Download Certificate------------------------
from flask import send_from_directory,current_app #Flask helper to send files from a folder
import os

@student.route('/student/download-certificate/<int:cert_id>')
@login_required
@role_required('student')
def download_certificate(cert_id):
    """Check ownership -> Find file -> Send file as download"""

    # fetch certificate if exists
    cert = Certificate.query.get_or_404(cert_id) 

    # security check — only owner can download
    if cert.registration.user_id != current_user.id:
        flash('You can only download your own certificates.', 'danger')
        return redirect(url_for('student.my_certificates'))

    # try disk first
    folder = os.path.join(current_app.root_path, 'static', 'certificates') # build path like "/home/project/app/static/certificates"
    filepath = os.path.join(folder, cert.file_path)

    if not os.path.exists(filepath):
        # regenerate if file missing (Render ephemeral filesystem)
        filename, _ = generate_certificate(
            student_name=cert.registration.user.name,
            event_name=cert.registration.event.title,
            event_date=cert.registration.event.date.strftime('%d %b %Y'),
            reg_id=cert.registration_id
        )

    return send_from_directory(folder, cert.file_path, as_attachment=True, download_name=f"{cert.registration.event.title}_certificate.pdf") #as_attachment=True: as_attachment=True
