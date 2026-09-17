import random
import io
from PIL import Image, ImageDraw, ImageFont


def generate_captcha():
    chars = ''.join(random.choices('ABCDEFGHJKLMNPQRSTUVWXYZ23456789', k=4))
    width, height = 120, 40
    img = Image.new('RGB', (width, height), (255, 255, 255))
    draw = ImageDraw.Draw(img)

    for x in range(width):
        for y in range(height):
            if random.random() < 0.08:
                draw.point((x, y), fill=(
                    random.randint(200, 240),
                    random.randint(200, 240),
                    random.randint(200, 240)
                ))

    x = 10
    for c in chars:
        draw.text((x, random.randint(5, 15)), c, fill=(
            random.randint(30, 120),
            random.randint(30, 120),
            random.randint(30, 120)
        ))
        x += 26

    buf = io.BytesIO()
    img.save(buf, 'PNG')
    buf.seek(0)
    return chars, buf
