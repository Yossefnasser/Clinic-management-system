"""
Django management command to test printer connection
"""
from django.core.management.base import BaseCommand
from django.conf import settings
from app.printer import TicketPrinter


class Command(BaseCommand):
    help = 'Test thermal printer connection and print a test page'

    def handle(self, *args, **options):
        printer_config = getattr(settings, 'PRINTER_CONFIG', {})
        
        if not printer_config.get('enabled', False):
            self.stdout.write(self.style.ERROR('Printer is disabled in settings'))
            return

        self.stdout.write(self.style.SUCCESS('Attempting to connect to printer...'))
        
        try:
            printer = TicketPrinter(
                printer_type=printer_config.get('type', 'usb'),
                usb_vendor_id=printer_config.get('usb_vendor_id'),
                usb_product_id=printer_config.get('usb_product_id'),
            )
            
            if printer.is_connected():
                self.stdout.write(self.style.SUCCESS('✓ Printer connected successfully!'))
                self.stdout.write('Printing test page...')
                
                if printer.print_test_page():
                    self.stdout.write(self.style.SUCCESS('✓ Test page printed successfully!'))
                else:
                    self.stdout.write(self.style.ERROR('✗ Failed to print test page'))
            else:
                self.stdout.write(self.style.ERROR('✗ Printer connection failed'))
                self.stdout.write('Check printer configuration:')
                self.stdout.write(f"  Type: {printer_config.get('type', 'serial')}")
                self.stdout.write(f"  Port: {printer_config.get('port', 'COM1')}")
                self.stdout.write(f"  Host: {printer_config.get('host', '192.168.1.100')}")
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Error: {str(e)}'))
