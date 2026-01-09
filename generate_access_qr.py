
import socket
import qrcode
import os
import sys
import threading
import time
import webbrowser
from PIL import Image

def get_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # doesn't even have to be reachable
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP

def generate_qr_and_show():
    ip = get_ip()
    port = '8000'
    url = f"http://{ip}:{port}"
    
    print(f"\n{'='*50}")
    print(f"   RABIT AL-WOSOOL (ACCESS LINK)")
    print(f"{'='*50}")
    print(f"\nURL: {url}")
    print(f"\n[INFO] Generating QR Code for easy access...")
    
    # Generate QR
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(url)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    
    # Save temp image
    img_path = "access_qr_temp.png"
    img.save(img_path)
    
    # Open image
    try:
        # os.startfile is Windows only
        os.startfile(img_path)
    except:
        print(f"[WARN] Could not open image automatically. Open '{img_path}' manually.")
        
    print(f"[SUCCESS] QR Code should be visible on your screen.")
    print(f"SCAN THIS QR CODE WITH YOUR PHONE TO CONNECT.")
    print(f"{'='*50}\n")

if __name__ == '__main__':
    generate_qr_and_show()
