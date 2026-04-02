# QR gen, PDF cert, email helpers
import qrcode
import os

def generate_qr(registration_id, user_id, event_id):
    # unique data string for this registration
    data = f"EVENZA-REG-{registration_id}-{user_id}-{event_id}"

    # create QR code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4
    )
    qr.add_data(data=data)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")

    # save to static/qrcodes/
    filename = f"qr_{registration_id}_{user_id}_{event_id}.png"
    folder = os.path.join('app','static','qrcodes')
    os.makedirs(folder, exist_ok=True)

    filepath = os.path.join(folder,filename)
    img.save(filepath)

    return filename