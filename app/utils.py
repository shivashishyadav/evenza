# QR gen, PDF cert, email helpers
import qrcode #generate QR codes from text/data
import os

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