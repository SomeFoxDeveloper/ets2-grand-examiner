import win32api
import win32print
import win32ui
from PIL import Image, ImageWin
import os
from win32con import HORZRES, VERTRES, PHYSICALWIDTH, PHYSICALHEIGHT
from modules.utils import print_event

def send_to_printer(image_path, printer_name=None):
    """
    Prints an image using Pillow to prepare the data and pywin32 to send it to the printer.
    This method offers more control and is more reliable than ShellExecute.
    """
    if not os.path.exists(image_path):
        print_event(f"[Printer] ERROR: Image file not found at '{image_path}'")
        return

    if printer_name is None:
        printer_name = win32print.GetDefaultPrinter()
        if not printer_name:
            print_event("[Printer] ERROR: No default printer found.")
            return

    print_event(f"[Printer] Printing '{image_path}' to printer: '{printer_name}'")

    hDC = None # Initialize hDC to None
    try:
        image = Image.open(image_path)
        hDC = win32ui.CreateDC()
        hDC.CreatePrinterDC(printer_name)
        print_event("Printer DC created.")

        printable_area = hDC.GetDeviceCaps(HORZRES), hDC.GetDeviceCaps(VERTRES)
        # printer_size = hDC.GetDeviceCaps(PHYSICALWIDTH), hDC.GetDeviceCaps(PHYSICALHEIGHT) # Not directly used for scaling
        img_size = image.size

        # Calculate scale to fill width of the printable area
        scale = float(printable_area[0]) / float(img_size[0])
        
        # Apply a multiplier to make it 2x bigger
        scale_multiplier = 2.0
        scale *= scale_multiplier

        new_width = int(img_size[0] * scale)
        new_height = int(img_size[1] * scale)
        
        # Position at top-left
        x_offset = 0
        y_offset = 0
        print_event(f"Image will be printed at {new_width}x{new_height} with offset ({x_offset}, {y_offset})")

        hDC.StartDoc(os.path.basename(image_path)) # Use basename for doc name
        hDC.StartPage()

        dib = ImageWin.Dib(image)

        dib.draw(hDC.GetSafeHdc(), (x_offset, y_offset, x_offset + new_width, y_offset + new_height))

        hDC.EndPage()
        hDC.EndDoc()
        print_event("Print job sent successfully.")

    except Exception as e:
        print_event(f"[Printer] ERROR: An error occurred during printing: {e}")
    finally:
        if hDC:
            hDC.DeleteDC()
        # Clean up the temporary image file
        if os.path.exists(image_path):
            try:
                os.remove(image_path)
                print_event(f"[Printer] Cleaned up temporary image: {os.path.basename(image_path)}")
            except Exception as e:
                print_event(f"[Printer] ERROR: Failed to clean up temporary image {os.path.basename(image_path)}: {e}")
