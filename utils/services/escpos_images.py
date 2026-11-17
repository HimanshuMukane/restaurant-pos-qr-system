import io
from PIL import Image


def _to_bw(img: Image.Image) -> Image.Image:
    if img.mode not in ("L", "1"):
        img = img.convert("L")
    img = img.point(lambda x: 0 if x < 160 else 255, "1")
    return img


def _resize_if_needed(img: Image.Image, max_width: int | None) -> Image.Image:
    if not max_width or img.width <= max_width:
        return img
    ratio = max_width / float(img.width)
    new_h = max(1, int(img.height * ratio))
    return img.resize((max_width, new_h), Image.NEAREST)


def image_to_raster_bytes(img: Image.Image, *, max_width: int | None = None) -> bytes:
    img = _resize_if_needed(img, max_width)
    img = _to_bw(img)

    width, height = img.size
    width_bytes = (width + 7) // 8
    padded_width = width_bytes * 8
    if padded_width != width:
        padded = Image.new("1", (padded_width, height), 1)
        padded.paste(img, (0, 0))
        img = padded
        width = padded_width

    width_bytes = width // 8
    xL = width_bytes & 0xFF
    xH = (width_bytes >> 8) & 0xFF
    yL = height & 0xFF
    yH = (height >> 8) & 0xFF

    header = bytes([0x1D, 0x76, 0x30, 0x00, xL, xH, yL, yH])
    data = bytearray()

    pix = img.load()
    for y in range(height):
        for xb in range(width_bytes):
            byte = 0
            for bit in range(8):
                x = xb * 8 + bit
                if pix[x, y] == 0:
                    byte |= 1 << (7 - bit)
            data.append(byte)

    return header + bytes(data)


def png_bytes_to_raster(png_bytes: bytes, *, max_width: int | None = None) -> bytes:
    img = Image.open(io.BytesIO(png_bytes))
    return image_to_raster_bytes(img, max_width=max_width)
