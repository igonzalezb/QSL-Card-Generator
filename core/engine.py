import logging
from PIL import Image, ImageDraw, ImageFont, ImageColor

logger = logging.getLogger(__name__)

def get_font(size: int):
    try: 
        return ImageFont.truetype("arial.ttf", size)
    except IOError:
        logger.warning("Font not found, using default.")
        return ImageFont.load_default()

def draw_qsl_core(base_img: Image.Image, config: dict, datos: list) -> tuple[Image.Image, str]:
    if not datos or not datos[0].strip(): 
        logger.warning("Attempt to draw row without callsign.")
        raise ValueError("Missing callsign")
        
    overlay = Image.new('RGBA', base_img.size, (255, 255, 255, 0))
    draw = ImageDraw.Draw(overlay)
    op_alpha = int((config["opacity"] / 100.0) * 255)
    
    def get_rgba(hex_c: str, a: int = 255) -> tuple:
        rgb = ImageColor.getrgb(hex_c)
        return (rgb[0], rgb[1], rgb[2], a)

    c_h_bg, c_d_bg = get_rgba(config["color_h_bg"], op_alpha), get_rgba(config["color_d_bg"], op_alpha)
    c_h_tx, c_d_tx = get_rgba(config["color_h_txt"], 255), get_rgba(config["color_d_txt"], 255)
    col_w, row_h = [150, 120, 100, 120, 150, 100], 40
    tot_w, tot_h = sum(col_w), (row_h * 2) + 5 
    font = get_font(24)
    pos = config["pos"]
    
    base_x = 50 if "left" in pos else (base_img.width - tot_w - 50 if "right" in pos else (base_img.width - tot_w) // 2)
    base_y = 50 if "top" in pos else (base_img.height - tot_h - 50 if "bottom" in pos else (base_img.height - tot_h) // 2)

    def _cell(x, y, w, h, text, bg_c, txt_c, outline=None):
        draw.rectangle([x, y, x + w, y + h], fill=bg_c, outline=outline)
        if text:
            bbox = draw.textbbox((0, 0), text, font=font)
            text_x = x + (w - (bbox[2] - bbox[0])) // 2
            text_y = y + (h - (bbox[3] - bbox[1])) // 2 - bbox[1] 
            draw.text((text_x, text_y), text, fill=txt_c, font=font)

    _cell(base_x, base_y, 150, row_h, "OPERATOR:", c_h_bg, c_h_tx)
    _cell(base_x + 150, base_y, 220, row_h, config["indicativo"], c_d_bg, c_d_tx)
    _cell(base_x + 370, base_y, 150, row_h, "QSO WITH:", c_h_bg, c_h_tx)
    _cell(base_x + 520, base_y, tot_w - 520, row_h, datos[0], c_d_bg, c_d_tx)

    headers = ["DATE", "TIME", "BAND", "MODE", "FREQ", "RST"]
    cx, hy, dy = base_x, base_y + row_h + 5, base_y + (row_h * 2) + 5
    for i in range(6):
        _cell(cx, hy, col_w[i], row_h, headers[i], c_h_bg, c_h_tx)
        _cell(cx, dy, col_w[i], row_h, datos[i+1], c_d_bg, c_d_tx, outline=(200,200,200,op_alpha))
        cx += col_w[i]
        
    return Image.alpha_composite(base_img, overlay).convert("RGB"), datos[0]