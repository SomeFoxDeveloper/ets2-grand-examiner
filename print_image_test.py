import win32print
import win32ui
from PIL import Image, ImageWin
import os
from win32con import HORZRES, VERTRES, PHYSICALWIDTH, PHYSICALHEIGHT

def print_image_with_pillow(image_path, printer_name=None):
    """
    Prints an image using Pillow to prepare the data and pywin32 to send it to the printer.
    This method offers more control and is more reliable than ShellExecute.
    """
    if not os.path.exists(image_path):
        print(f"ERROR: Image file not found at '{image_path}'")
        return

    if printer_name is None:
        printer_name = win32print.GetDefaultPrinter()
        if not printer_name:
            print("ERROR: No default printer found.")
            return

    print(f"Printing '{image_path}' to printer: '{printer_name}'")

    try:
        image = Image.open(image_path)
        hDC = win32ui.CreateDC()
        hDC.CreatePrinterDC(printer_name)
        print("Printer DC created.")

        printable_area = hDC.GetDeviceCaps(HORZRES), hDC.GetDeviceCaps(VERTRES)
        printer_size = hDC.GetDeviceCaps(PHYSICALWIDTH), hDC.GetDeviceCaps(PHYSICALHEIGHT)
        img_size = image.size

        ratios = [float(printable_area[i]) / float(img_size[i]) for i in range(2)]
        scale = min(ratios)

        new_width = int(img_size[0] * scale)
        new_height = int(img_size[1] * scale)
        x_offset = (printable_area[0] - new_width) // 2
        y_offset = (printable_area[1] - new_height) // 2
        print(f"Image will be printed at {new_width}x{new_height} with offset ({x_offset}, {y_offset})")

        hDC.StartDoc(image_path)
        hDC.StartPage()

        dib = ImageWin.Dib(image)

        # --- THIS IS THE CORRECTED LINE ---
        # Use GetSafeHdc() to get the handle for the device context
        dib.draw(hDC.GetSafeHdc(), (x_offset, y_offset, x_offset + new_width, y_offset + new_height))

        hDC.EndPage()
        hDC.EndDoc()
        hDC.DeleteDC()
        print("Print job sent successfully.")

    except Exception as e:
        print(f"ERROR: An error occurred during printing: {e}")
        if 'hDC' in locals() and hDC:
            hDC.DeleteDC()

if __name__ == "__main__":
    image_file = "image.png"
    print_image_with_pillow(image_file)