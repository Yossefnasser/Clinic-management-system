import logging
from datetime import datetime

logger = logging.getLogger(__name__)

try:
    from escpos.printer import Usb
    ESC_POS_AVAILABLE = True
except Exception:
    ESC_POS_AVAILABLE = False


class TicketPrinter:
    def __init__(self, printer_type='usb', usb_vendor_id=None, usb_product_id=None):
        self.printer_type = printer_type
        self.usb_vendor_id = usb_vendor_id
        self.usb_product_id = usb_product_id
        self._printer = None

    def is_connected(self):
        # best-effort: try to instantiate the escpos printer if available
        if ESC_POS_AVAILABLE and self.printer_type == 'usb' and self.usb_vendor_id and self.usb_product_id:
            try:
                self._printer = Usb(int(self.usb_vendor_id, 0) if isinstance(self.usb_vendor_id, str) and self.usb_vendor_id.startswith('0x') else int(self.usb_vendor_id),
                                     int(self.usb_product_id, 0) if isinstance(self.usb_product_id, str) and self.usb_product_id.startswith('0x') else int(self.usb_product_id))
                return True
            except Exception as e:
                logger.warning('ESC/POS USB printer not available: %s', e)
                return False
        # if escpos not available, we still "connected" in fallback mode
        return True

    def print_appointment_ticket(self, appointment, ticket_number=None):
        # Compose ticket text
        ticket_no = ticket_number or getattr(appointment, 'ticket_number', None) or appointment.id
        patient_name = appointment.patient.name if appointment.patient else ''
        patient_phone = appointment.patient.phone_number if appointment.patient else ''
        doctor_name = appointment.doctor.full_name if appointment.doctor else ''
        clinic_name = appointment.clinic.name if appointment.clinic else ''
        appt_date = appointment.date.strftime('%Y-%m-%d') if appointment.date else ''
        appt_time = appointment.time.strftime('%H:%M') if appointment.time else ''

        # Simple text representation — prioritize large ticket number
        lines = []
        lines.append('----- تذكرة الحضور -----')
        lines.append('الطبيب: %s' % doctor_name)
        lines.append('العيادة: %s' % clinic_name)
        lines.append('التاريخ: %s' % appt_date)
        lines.append('الوقت: %s' % appt_time)
        lines.append('المريض: %s' % patient_name)
        lines.append('الهاتف: %s' % patient_phone)
        lines.append('')
        lines.append('----- الرقم -----')
        lines.append(str(ticket_no))
        lines.append('')
        lines.append(datetime.now().strftime('%Y-%m-%d %H:%M'))
        lines.append('---------------------')

        if ESC_POS_AVAILABLE and self.printer_type == 'usb' and self.usb_vendor_id and self.usb_product_id:
            try:
                p = self._printer or Usb(int(self.usb_vendor_id), int(self.usb_product_id))
                p.set(align='center', text_type='B', width=3, height=3)
                p.text(str(ticket_no) + '\n')
                p.set(align='left')
                p.text('\n'.join(lines[1:]) + '\n\n')
                p.cut()
                return True
            except Exception as e:
                logger.warning('Failed to print via escpos: %s', e)

        # Fallback: log the ticket (useful for local agent or debugging)
        logger.info('\n'.join(lines))
        return True
