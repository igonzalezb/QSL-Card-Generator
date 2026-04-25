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
    
    scale = config.get("table_scale", 1.0)
    col_w = [int(w * scale) for w in [150, 120, 100, 120, 150, 100]]
    row_h = int(40 * scale)
    gap = int(5 * scale)
    
    show_comment = config.get("show_comments", True) and len(datos) > 7 and datos[7].strip() != ""
    
    tot_w = sum(col_w)
    tot_h = (row_h * 4) + (gap * 2) if show_comment else (row_h * 3) + gap
    
    font = get_font(int(24 * scale))
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

    w1 = int(150 * scale)
    w2 = int(220 * scale)
    w3 = int(150 * scale)
    w4 = tot_w - (w1 + w2 + w3) 

    _cell(base_x, base_y, w1, row_h, "OPERATOR:", c_h_bg, c_h_tx)
    _cell(base_x + w1, base_y, w2, row_h, config["callsign"], c_d_bg, c_d_tx)
    _cell(base_x + w1 + w2, base_y, w3, row_h, "QSO WITH:", c_h_bg, c_h_tx)
    _cell(base_x + w1 + w2 + w3, base_y, w4, row_h, datos[0], c_d_bg, c_d_tx)

    headers = ["DATE", "TIME", "BAND", "MODE", "FREQ", "RST"]
    cx, hy, dy = base_x, base_y + row_h + gap, base_y + (row_h * 2) + gap
    
    for i in range(6):
        _cell(cx, hy, col_w[i], row_h, headers[i], c_h_bg, c_h_tx)
        _cell(cx, dy, col_w[i], row_h, datos[i+1], c_d_bg, c_d_tx, outline=(200,200,200,op_alpha))
        cx += col_w[i]
        
    if show_comment:
        cy = base_y + (row_h * 3) + (gap * 2)
        _cell(base_x, cy, tot_w, row_h, datos[7], c_d_bg, c_d_tx, outline=(200,200,200,op_alpha))
        
    return Image.alpha_composite(base_img, overlay).convert("RGB"), datos[0]