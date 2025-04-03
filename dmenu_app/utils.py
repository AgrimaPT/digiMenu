import qrcode
from io import BytesIO
from django.core.files.base import ContentFile

def generate_qr_code(table):
    table_url = f"http://localhost:8000/table/{table.number}"
    qr = qrcode.make(table_url)
    buffer = BytesIO()
    qr.save(buffer)
    buffer.seek(0)
    return ContentFile(buffer.getvalue(), f"table_{table.number}_qr.png")
