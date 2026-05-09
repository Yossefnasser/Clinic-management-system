"""
Escpos-based printer utility for appointment tickets
"""
from escpos.printer import Serial, Network, File, Usb
from datetime import datetime
from app.helpers import get_local_now

class TicketPrinter:
    """Handle thermal printer connections and ticket generation"""

    def __init__(
        self,
        printer_type='usb',
        usb_vendor_id=0x04b8,
        usb_product_id=0x0202,
    ):
        """
        Initialize printer connection
        printer_type: 'usb', 'serial', 'network', or 'file' (for testing)
        """
        self.printer = None
        self.printer_type = printer_type
        self.connected = False

        try:
            if printer_type == 'usb':
                self.printer = Usb(
                    usb_vendor_id,
                    usb_product_id,
                )
                self.connected = True
        except Exception as e:
            print(f"Printer connection failed: {str(e)}")
            self.connected = False

    def is_connected(self):
        """Check if printer is connected"""
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

            self.printer.set(align='center', font='a', height=1, width=1)
            self.printer.textln(clinic_name)

            self.printer.set(align='center', font='a', height=3, width=3)
            self.printer.textln(f"#{display_number}")

            self.printer.set(align='left', font='b', height=1, width=1)
            self.printer.textln('─' * 32)
            self.printer.textln(f"Doctor: {doctor_name}")
            self.printer.textln(f"Time:   {appointment_time}")
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
        """Print a test page to verify printer is working"""
        if not self.connected or not self.printer:
            raise Exception("Printer not connected")

        try:
            self.printer.set(align='center')
            self.printer.text("PRINTER TEST")
            self.printer.text('─' * 32)
            self.printer.set(align='left')
            self.printer.textln("Printer is working correctly!")
            self.printer.textln(f"Test time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            self.printer.text('─' * 32)
            
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
