import os
import PyPDF2

from base64 import b64decode
from io import BytesIO

from django.conf import settings
from django.utils import timezone

from PIL import Image, ImageFont, ImageDraw
from cryptography.hazmat import backends
from cryptography.hazmat.primitives.serialization import Encoding, pkcs12


SIGNATURE_TITLE = "Digital Signature"
FONT = os.path.join(os.path.dirname(settings.BASE_DIR), "assets", "fonts", "light.ttf")
BACKGROUND_IMAGE = os.path.join(os.path.dirname(settings.BASE_DIR), "assets", "images", "dit_emblem.png")
TITLE_FONT_SIZE = 80
FONT_SIZE = 50
SIGNATURE_POSITIONING = (50, 675, 450, 775)
TITLE_POSITIONING = (500, 10)
TEXT_POSITIONING = (500, 150)


def get_certificate_data():
    _, cert, _ = _load_certificate_and_key()
    return cert.public_bytes(Encoding.PEM)


def _load_certificate_and_key():
    """
    Extracts the key & certificate from the p12 file specified with CERTIFICATE_PATH & CERTIFICATE_PASSWORD
    """
    return pkcs12.load_key_and_certificates(
        b64decode(settings.P12_CERTIFICATE),
        str.encode(settings.CERTIFICATE_PASSWORD),
        backends.default_backend(),
    )


def _get_signature_text(date):
    return "\n\n".join(
        [
            f"Date: {date.strftime('%Y.%m.%d %H:%M:%S GMT')}",
            f"Reason: {settings.SIGNING_REASON}",
            f"Location: {settings.SIGNING_LOCATION}",
        ]
    )


def _add_blank_page(pdf_bytes: bytes):
    # Write a blank page
    pdf = PyPDF2.PdfFileReader(BytesIO(pdf_bytes))
    out_pdf = PyPDF2.PdfFileWriter()
    out_pdf.appendPagesFromReader(pdf)
    out_pdf.addBlankPage()
    num_pages = out_pdf.getNumPages()

    # Convert back into bytes
    output_buffer = BytesIO()
    out_pdf.write(output_buffer)
    output_buffer.seek(0)
    return output_buffer.read(), num_pages


def _get_signature_image(text):
    # Load image and fonts
    image = Image.open(BACKGROUND_IMAGE)
    title_font = ImageFont.truetype(FONT, TITLE_FONT_SIZE)
    text_font = ImageFont.truetype(FONT, FONT_SIZE)
    drawing = ImageDraw.Draw(image)

    # Add text
    drawing.text(TITLE_POSITIONING, SIGNATURE_TITLE, font=title_font, fill=(0, 0, 0))
    drawing.text(TEXT_POSITIONING, text, font=text_font, fill=(0, 0, 0))

    return image


def sign_pdf(original_pdf: bytes):
    """
    Takes raw bytes of a PDF file and adds a new page with a digital signature.
    Relies on a p12 file specified in CERTIFICATE_PATH & CERTIFICATE_PASSWORD.
    Also uses SIGNING_EMAIL, SIGNING_LOCATION & SIGNING_REASON as key data in the signing process.
    """
    if settings.DOCUMENT_SIGNING_ENABLED:
        from endesive.pdf.cms import sign  # noqa

        date = timezone.localtime()
        # Specify signing metadata
        signing_metadata = {
            "sigandcertify": True,
            "signaturebox": SIGNATURE_POSITIONING,
            "signature_img": _get_signature_image(_get_signature_text(date)),
            "contact": settings.SIGNING_EMAIL,
            "location": settings.SIGNING_LOCATION,
            "signingdate": date.strftime("D:%Y%m%d%H%M%S+00'00'"),
            "reason": settings.SIGNING_REASON,
        }

        # Load key & certificate
        key, cert, othercerts = _load_certificate_and_key()

        # Add a blank page to the end
        pdf, num_pages = _add_blank_page(original_pdf)

        # Add the signature to the last page
        signing_metadata["sigpage"] = num_pages - 1
        signature = sign(pdf, signing_metadata, key, cert, othercerts, "sha256")

        return pdf + signature

    return original_pdf
