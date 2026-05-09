"""
Escpos-based printer utility for appointment tickets
"""
from escpos.printer import Serial, Network, File, Usb
from datetime import datetime
from app.helpers import get_local_now
import arabic_reshaper
from bidi.algorithm import get_display
from PIL import Image, ImageDraw, ImageFont
import io
import os


ARABIC_FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"  # change to your Arabic font path
PRINTER_WIDTH_PX = 560  # ~58mm printer = 384px, ~80mm printer = 560px


def render_arabic_image(text, font_path=ARABIC_FONT_PATH, font_size=26, width=PRINTER_WIDTH_PX, align='right'):
    """Render Arabic text into a PIL Image ready to send to the printer"""
    reshaped = arabic_reshaper.reshape(text)
    bidi_text = get_display(reshaped)

    font = ImageFont.truetype(font_path, font_size)

    # Measure text size
    dummy = Image.new('RGB', (1, 1))
    draw = ImageDraw.Draw(dummy)
    bbox = draw.textbbox((0, 0), bidi_text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1] + 8

    img = Image.new('RGB', (width, text_height), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)

    if align == 'right':
        x = width - text_width - 4
    elif align == 'center':
        x = (width - text_width) // 2
    else:
        x = 4

    draw.text((x, 4), bidi_text, font=font, fill=(0, 0, 0))
    return img


class TicketPrinter:
    """Handle thermal printer connections and ticket generation"""

    def __init__(
        self,
        printer_type='usb',
        usb_vendor_id=0x04b8,
        usb_product_id=0x0202,
    ):
        self.printer = None
        self.printer_type = printer_type
        self.connected = False

        try:
            if printer_type == 'usb':
                self.printer = Usb(usb_vendor_id, usb_product_id)
                self.connected = True
        except Exception as e:
            print(f"Printer connection failed: {str(e)}")
            self.connected = False

    def is_connected(self):
        return self.connected

    def print_appointment_ticket(self, appointment, ticket_number=None):
        if not self.connected or not self.printer:
            raise Exception("Printer not connected")

        try:
            patient_name = appointment.patient.name
            doctor_name = appointment.doctor.full_name
            appointment_time = appointment.time.strftime("%I:%M %p")
            appointment_id = appointment.id
            display_number = ticket_number or appointment_id
            clinic_name = appointment.clinic.name

            # Clinic name (Arabic image, centered)
            self.printer.image(render_arabic_image(clinic_name, font_size=28, align='center'))

            self.printer.set(align='center', font='a', height=1, width=1)
            self.printer.textln('─' * 32)

            # Ticket number (big, normal ESC/POS)
            self.printer.set(align='center', font='a', height=5, width=5)
            self.printer.textln(f"#{display_number}")

            self.printer.set(align='left', font='b', height=1, width=1)
            self.printer.textln('─' * 32)

            # Doctor name and time as Arabic images
            self.printer.image(render_arabic_image(f"الدكتور: {doctor_name}", font_size=24, align='right'))
            self.printer.image(render_arabic_image(f"الوقت: {appointment_time}", font_size=24, align='right'))

            self.printer.set(align='left', font='b', height=1, width=1)
            self.printer.textln('─' * 32)

            try:
                self.printer.cut()
            except:
                pass

            if self.printer_type in ['serial', 'network']:
                self.printer.close()

            return True

        except Exception as e:
            print(f"Error printing ticket: {str(e)}")
            return False

    def print_test_page(self):
        if not self.connected or not self.printer:
            raise Exception("Printer not connected")

        try:
            self.printer.image(render_arabic_image("اختبار الطباعة", font_size=28, align='center'))
            self.printer.set(align='left', font='b', height=1, width=1)
            self.printer.textln(f"Test time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

            try:
                self.printer.cut()
            except:
                pass

            if self.printer_type in ['serial', 'network']:
                self.printer.close()

            return True
        except Exception as e:
            print(f"Error printing test page: {str(e)}")
            return False