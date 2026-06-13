import base64
import os
from io import BytesIO
from decimal import Decimal

import qrcode
from dotenv import load_dotenv


load_dotenv(override=True)


def get_promptpay_id() -> str:
    promptpay_id = os.getenv("PROMPTPAY_ID", "").strip()

    if promptpay_id == "":
        raise RuntimeError("PROMPTPAY_ID is not configured")

    return promptpay_id


def crc16_ccitt(data: str) -> str:
    crc = 0xFFFF

    for char in data.encode("ascii"):
        crc ^= char << 8
        for _ in range(8):
            if crc & 0x8000:
                crc = (crc << 1) ^ 0x1021
            else:
                crc <<= 1
            crc &= 0xFFFF

    return format(crc, "04X")


def format_tlv(tag: str, value: str) -> str:
    return f"{tag}{len(value):02d}{value}"


def format_promptpay_id(promptpay_id: str) -> str:
    value = promptpay_id.replace("-", "").replace(" ", "")

    if len(value) == 10 and value.startswith("0"):
        return "0066" + value[1:]

    return value


def generate_promptpay_payload(amount: Decimal) -> str:
    promptpay_value = format_promptpay_id(get_promptpay_id())

    merchant_account = (
        format_tlv("00", "A000000677010111")
        + format_tlv("01", promptpay_value)
    )

    payload = ""
    payload += format_tlv("00", "01")
    payload += format_tlv("01", "12")
    payload += format_tlv("29", merchant_account)
    payload += format_tlv("53", "764")
    payload += format_tlv("54", f"{Decimal(amount):.2f}")
    payload += format_tlv("58", "TH")
    payload += "6304"

    crc = crc16_ccitt(payload)

    return payload + crc


def generate_qr_base64(payload: str) -> str:
    img = qrcode.make(payload)

    buffer = BytesIO()
    img.save(buffer, format="PNG")

    base64_img = base64.b64encode(buffer.getvalue()).decode("utf-8")

    return f"data:image/png;base64,{base64_img}"
