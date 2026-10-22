# -*- coding: utf-8 -*-
"""Рисует листы компонентов пробника в PNG через Chromium."""
import html, sys
from pathlib import Path
from playwright.sync_api import sync_playwright
sys.path.insert(0, str(Path(__file__).parent))
from data import TILES, EVENTS, SRYV, DISTORTION_COLOR, LAYER_COLOR

OUT = Path(__file__).parent.parent / "images"
OUT.mkdir(parents=True, exist_ok=True)
e = html.escape

BASE_CSS = """
*{box-sizing:border-box;margin:0;padding:0}
body{background:#000;font-family:'Inter',sans-serif;color:#EDE9DD}
.sheet{display:grid}
.cell{position:relative;overflow:hidden}
.h{font-family:'DejaVu Sans Condensed','Inter',sans-serif;font-weight:700;letter-spacing:.01em}
.muted{color:#A7A293}
"""

def page(body, w, h, extra=""):
    return f"<!doctype html><html><head><meta charset='utf-8'><style>{BASE_CSS}{extra}</style></head><body style='width:{w}px;height:{h}px'>{body}</body></html>"

def shoot(pw, name, markup, w, h):
    b = pw.chromium.launch()
    p = b.new_page(viewport={"width": w, "height": h})
    p.set_content(markup)
    p.wait_for_timeout(150)
    p.screenshot(path=str(OUT / name), clip={"x": 0, "y": 0, "width": w, "height": h})
    b.close()
    print("saved", name)

def grid(cells, cols, rows, cw, ch, filler=""):
    cells = list(cells) + [filler] * (cols * rows - len(cells))
    inner = "".join(f"<div class='cell' style='width:{cw}px;height:{ch}px'>{c}</div>" for c in cells)
    return f"<div class='sheet' style='grid-template-columns:repeat({cols},{cw}px)'>{inner}</div>"

# ---------- тайлы ----------
T = 512
def edges_svg(open_edges, bg, road, closed):
    # стороны: N,E,S,W. Открытая — дорога по центру края, закрытая — штрих вдоль края
    parts = []
    m = 26
    if "N" in open_edges: parts.append(f"<rect x='{T/2-60}' y='0' width='120' height='{m}' fill='{road}'/>")
    else: parts.append(f"<rect x='0' y='0' width='{T}' height='14' fill='url(#hatch)'/>")
    if "S" in open_edges: parts.append(f"<rect x='{T/2-60}' y='{T-m}' width='120' height='{m}' fill='{road}'/>")
    else: parts.append(f"<rect x='0' y='{T-14}' width='{T}' height='14' fill='url(#hatch)'/>")
    if "W" in open_edges: parts.append(f"<rect x='0' y='{T/2-60}' width='{m}' height='120' fill='{road}'/>")
    else: parts.append(f"<rect x='0' y='0' width='14' height='{T}' fill='url(#hatch)'/>")
    if "E" in open_edges: parts.append(f"<rect x='{T-m}' y='{T/2-60}' width='{m}' height='120' fill='{road}'/>")
    else: parts.append(f"<rect x='{T-14}' y='0' width='14' height='{T}' fill='url(#hatch)'/>")
    return (f"<svg width='{T}' height='{T}' style='position:absolute;inset:0'>"
            f"<defs><pattern id='hatch' width='14' height='14' patternUnits='userSpaceOnUse' patternTransform='rotate(45)'>"
            f"<rect width='7' height='14' fill='{closed}'/><rect x='7' width='7' height='14' fill='#2a1a14'/></pattern></defs>"
            + "".join(parts) + "</svg>")

def mirror(edges):
    return "".join({"E": "W", "W": "E"}.get(c, c) for c in edges)

def pips(n, color):
    return "".join(f"<span style='display:inline-block;width:18px;height:18px;border-radius:50%;background:{color};margin-right:6px'></span>" for _ in range(n))

def tile_front(t):
    n, name, q, edges, srch, loot, zap, thr, nl, nle, dist, *_ = t
    bg = "#3A3730" if q != "Старт" else "#2C3A44"
    qcol = {"Окраина": "#9FCB7A", "Промзона": "#E0A35A", "Старт": "#8CC4E8"}[q]
    if n == 0:
        body = (f"<div class='h' style='font-size:56px;text-align:center;margin-top:150px'>ЛАГЕРЬ</div>"
                f"<div style='text-align:center;font-size:22px;margin-top:14px' class='muted'>спортзал школы</div>"
                f"<div style='text-align:center;font-size:20px;margin-top:60px;padding:0 70px;line-height:1.35'>Сумерки: еда и вода<br>из общего запаса.<br>После 9-й ночи —<br>эвакуация отсюда.</div>")
    else:
        dcol = DISTORTION_COLOR[dist]
        body = f"""
        <div style='display:flex;justify-content:space-between;font-size:17px;text-transform:uppercase;letter-spacing:.08em'>
          <span style='color:{qcol}'>{e(q)}</span><span class='muted'>№{n}</span></div>
        <div class='h' style='font-size:{40 if len(name) < 15 else 33}px;line-height:1.05;margin-top:8px;height:84px'>{e(name)}</div>
        <div style='display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-top:6px'>
          <div style='background:#24221E;border-radius:8px;padding:10px 14px'><div class='muted' style='font-size:15px'>Обыск</div><div class='h' style='font-size:40px'>{srch}+</div></div>
          <div style='background:#24221E;border-radius:8px;padding:10px 14px'><div class='muted' style='font-size:15px'>Угроза</div><div class='h' style='font-size:40px;color:#E8875A'>{thr}</div></div>
        </div>
        <div style='margin-top:12px;font-size:21px'><span class='muted'>Лут:</span> {e(loot)}</div>
        <div style='margin-top:8px;font-size:21px'><span class='muted'>Запас:</span> {pips(zap, '#CFE6A0')}</div>
        <div style='margin-top:12px;font-size:20px;line-height:1.3'><span style='color:#9FCB7A;font-weight:700'>{e(nl)}:</span> {e(nle)}</div>
        <div style='position:absolute;left:44px;right:44px;bottom:42px;display:flex;align-items:center;gap:10px;font-size:17px'>
          <span style='width:16px;height:16px;transform:rotate(45deg);background:{dcol};display:inline-block'></span>
          <span class='muted'>искажается:</span><span style='color:{dcol};font-weight:700'>{e(dist)}</span></div>"""
    return (f"<div style='position:absolute;inset:0;background:{bg}'></div>"
            + edges_svg(edges, bg, "#C9C2AC", "#D0643A")
            + f"<div style='position:absolute;inset:40px 44px'>{body}</div>")

def tile_back(t):
    n, name, q, edges, srch, loot, zap, thr, nl, nle, dist, dname, s1, s2, s3 = t
    medges = mirror(edges)
    if n == 0:
        bg = "#2C3A44"
        body = (f"<div class='h' style='font-size:56px;text-align:center;margin-top:150px'>ЛАГЕРЬ</div>"
                f"<div style='text-align:center;font-size:22px;margin-top:14px' class='muted'>не искажается</div>")
        return f"<div style='position:absolute;inset:0;background:{bg}'></div>" + edges_svg(medges, bg, "#C9C2AC", "#D0643A") + f"<div style='position:absolute;inset:40px 44px'>{body}</div>"
    bg = "#1E2216"
    dcol = DISTORTION_COLOR[dist]
    srch2 = min(6, srch + 2)
    zap2 = max(1, zap - 1)
    steps = ""
    for roman, txt in (("I", s1), ("II", s2), ("III", s3)):
        steps += (f"<div style='display:flex;gap:10px;align-items:flex-start;margin-top:7px'>"
                  f"<span style='flex:none;width:34px;height:34px;border-radius:50%;border:2px solid {dcol};display:flex;align-items:center;justify-content:center;font-size:14px;font-weight:700;color:{dcol}'>{roman}</span>"
                  f"<span style='font-size:17px;line-height:1.22'>{e(txt)}</span></div>")
    body = f"""
      <div style='display:flex;justify-content:space-between;font-size:17px;text-transform:uppercase;letter-spacing:.08em'>
        <span style='color:{dcol}'>◆ {e(dist)}</span><span class='muted'>№{n} · {e(name)}</span></div>
      <div class='h' style='font-size:{36 if len(dname) < 16 else 30}px;line-height:1.05;margin-top:8px'>{e(dname)}</div>
      <div style='display:flex;gap:18px;margin-top:10px;font-size:19px'>
        <span><span class='muted'>Обыск</span> <b>{srch2}+</b></span>
        <span><span class='muted'>Запас</span> {pips(zap2, dcol)}</span></div>
      <div style='font-size:17px;margin-top:6px'><span class='muted'>Лут:</span> {e(loot)} + мутаген</div>
      <div style='font-size:17px;margin-top:4px'><span style='color:#E8875A;font-weight:700'>Опасное:</span> +1 Голод, +1 Жажда</div>
      <div style='margin-top:6px;border-top:1px solid #3C4230;padding-top:2px'>{steps}</div>"""
    return (f"<div style='position:absolute;inset:0;background:{bg}'></div>"
            + edges_svg(medges, bg, "#7E8A55", "#D0643A")
            + f"<div style='position:absolute;inset:38px 42px'>{body}</div>")

# ---------- события ----------
CW, CH = 400, 560
def event_front(ev):
    n, name, layer, rifts, world, surv, choice = ev
    lc = LAYER_COLOR[layer]
    rift = ""
    if rifts:
        rift = "<div style='margin-top:14px;font-size:20px'>" + " ".join(
            f"<span style='display:inline-block;padding:4px 12px;border-radius:999px;border:2px solid {DISTORTION_COLOR[r]};color:{DISTORTION_COLOR[r]};margin:0 6px 6px 0'>Разлом: {e(r)}</span>" for r in rifts) + "</div>"
    ch = f"<div style='position:absolute;right:26px;top:26px;background:#E0B84A;color:#2A2000;font-weight:700;font-size:15px;padding:4px 10px;border-radius:6px'>ВЫБОР</div>" if choice else ""
    def block(title, txt):
        if txt in ("—", ""): return ""
        return (f"<div style='margin-top:16px'><div style='font-size:14px;text-transform:uppercase;letter-spacing:.1em' class='muted'>{title}</div>"
                f"<div style='font-size:21px;line-height:1.3;margin-top:4px'>{e(txt)}</div></div>")
    return f"""<div style='position:absolute;inset:0;background:#2E2B25'></div>
      <div style='position:absolute;left:0;right:0;top:0;height:12px;background:{lc}'></div>
      {ch}
      <div style='position:absolute;inset:34px 28px'>
        <div style='font-size:15px;text-transform:uppercase;letter-spacing:.12em;color:{lc}'>Ночь · {e(layer)}</div>
        <div class='h' style='font-size:34px;line-height:1.08;margin-top:10px;padding-right:{80 if choice else 0}px'>{e(name)}</div>
        {rift}{block('Мир', world)}{block('Выживание', surv)}
      </div>
      <div style='position:absolute;bottom:20px;left:28px' class='muted'>#{n}</div>"""

def event_back(ev):
    layer = ev[2]
    lc = LAYER_COLOR[layer]
    return f"""<div style='position:absolute;inset:0;background:#1C1A17'></div>
      <div style='position:absolute;inset:18px;border:3px solid {lc};border-radius:14px;display:flex;flex-direction:column;align-items:center;justify-content:center'>
        <div class='h' style='font-size:58px;letter-spacing:.06em'>НОЧЬ</div>
        <div style='font-size:28px;color:{lc};margin-top:12px'>{e(layer)}</div></div>"""

def sryv_front(c):
    name, kind, goal = c
    col = "#C8E04A" if kind == "мутант" else "#E8C38A"
    return f"""<div style='position:absolute;inset:0;background:#2A1E1C'></div>
      <div style='position:absolute;inset:34px 30px'>
        <div style='font-size:15px;text-transform:uppercase;letter-spacing:.12em;color:{col}'>Срыв · {e(kind)}</div>
        <div class='h' style='font-size:38px;margin-top:12px'>{e(name)}</div>
        <div style='font-size:23px;line-height:1.35;margin-top:22px'>{e(goal)}</div>
        <div style='position:absolute;bottom:0;left:0;right:0;font-size:16px;line-height:1.35' class='muted'>Держи карту в секрете. Это твоя новая цель победы.</div>
      </div>"""

def sryv_back():
    return """<div style='position:absolute;inset:0;background:#1C1214'></div>
      <div style='position:absolute;inset:18px;border:3px solid #8E3A2E;border-radius:14px;display:flex;align-items:center;justify-content:center'>
      <div class='h' style='font-size:60px;letter-spacing:.06em;color:#E8A88E'>СРЫВ</div></div>"""

# ---------- жетоны ----------
K = 256
def token(label, sub, bg, fg="#EDE9DD", ring="#000"):
    return f"""<div style='position:absolute;inset:0;background:{bg};border-radius:28px;border:8px solid {ring}'></div>
      <div style='position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;color:{fg}'>
      <div class='h' style='font-size:{34 if len(label) < 10 else 26}px;text-align:center'>{e(label)}</div>
      <div style='font-size:24px;margin-top:8px;opacity:.9;white-space:pre-line;text-align:center;line-height:1.3'>{e(sub)}</div></div>"""
TOK_FRONT = [token("Ходячий", "Защ 2 · Жив 1\nУрон 1 · Скор 1", "#5A6B4A"),
             token("Бегун", "Защ 4 · Жив 1\nУрон 1 · Скор 2", "#8A6A2E"),
             token("Бронированный", "Защ 6 · Жив 3\nУрон 2 · Скор 1", "#7A2E24"),
             token("Восставший", "Защ 2 · Жив 1\nУрон 1 · Скор 1", "#3C2A44", ring="#A88BE0")]
TOK_BACK = [token("Труп", "ночью встанет", "#4A4640", ring="#2a2826") for _ in range(4)]

# ---------- планшеты ----------
def player_board():
    W, H = 1600, 660
    scales = ["Голод", "Жажда", "Здоровье", "Фокус"]
    over = {"Голод": "6-е: в след. День на 2 кубика меньше", "Жажда": "6-е: пропускаешь след. День",
            "Здоровье": "0: шрам — закрой ячейку кубика, Здоровье = 3",
            "Фокус": "0: Бой и Крафт с −1 к кубику"}
    start = {"Голод": 0, "Жажда": 0, "Здоровье": 5, "Фокус": 5}
    rows = ""
    for s in scales:
        cells = "".join(f"<div style='width:62px;height:62px;border:2px solid {'#C8E04A' if i == start[s] else '#5C584D'};border-radius:8px;display:flex;align-items:center;justify-content:center;color:#6C6759;font-size:22px'>{i}</div>" for i in range(6))
        rows += (f"<div style='display:flex;align-items:center;gap:8px;margin-bottom:10px'>"
                 f"<div class='h' style='width:170px;font-size:26px'>{s}</div>{cells}"
                 f"<div style='margin-left:12px;font-size:17px;line-height:1.2;width:240px' class='muted'>{over[s]}</div></div>")
    change = "".join(f"<div style='flex:1;height:58px;border-radius:6px;background:{'#33302A' if i<4 else ('#4A3426' if i<8 else '#6B2E22')};display:flex;align-items:center;justify-content:center;font-size:20px;color:#CFC8B6'>{i}</div>" for i in range(11))
    dice = "".join(f"<div style='width:96px;height:96px;border:3px solid #5C584D;border-radius:12px;display:flex;align-items:center;justify-content:center;font-size:26px;color:#6C6759'>{i}</div>" for i in range(1, 7))
    acts = [("Переход: шаг или новый тайл", "любой"), ("Рывок, 2 тайла (+1 Жажда)", "5+"), ("Обыск", "≥ порога"),
            ("Бой: 1 попадание, −1 Фокус", "≥ Защиты"), ("Добить труп", "любой"),
            ("Лечение + медикамент:", "4+"), ("   +2 Здоровье или −1 Изменение", ""),
            ("Отдых: весь День, Фокус = 5", "все"), ("Помочь на своём тайле", "любой"),
            ("Усилие: сложить 2 кубика", "+1 Голод"), ("Еда: −2 Голод, +1 Фокус", "—"), ("Вода: −2 Жажда", "—")]
    acts_html = "".join(f"<div style='display:flex;justify-content:space-between;font-size:18px;padding:3px 0;border-bottom:1px solid #3A372F'><span>{a}</span><span class='muted'>{c}</span></div>" for a, c in acts)
    body = f"""<div style='width:{W}px;height:{H}px;background:#26241F;padding:34px;display:grid;grid-template-columns:1fr 430px;gap:34px'>
      <div>
        <div class='h' style='font-size:22px;letter-spacing:.1em' class='muted'>КУБИКИ ДЕЙСТВИЙ <span style='font-weight:400;font-size:17px;color:#A7A293'>· шрам закрывает ячейку навсегда</span></div>
        <div style='display:flex;gap:14px;margin:12px 0 26px'>{dice}</div>
        <div class='h' style='font-size:22px;letter-spacing:.1em;margin-bottom:12px'>ШКАЛЫ <span style='font-weight:400;font-size:17px;color:#A7A293'>· Голод и Жажда растут от 0, Здоровье и Фокус тратятся с 5</span></div>
        {rows}
        <div class='h' style='font-size:22px;letter-spacing:.1em;margin:18px 0 10px'>ИЗМЕНЕНИЕ <span style='font-weight:400;font-size:17px;color:#A7A293'>· переполнение → тайно тяни карту Срыва</span></div>
        <div style='display:flex;gap:6px'>{change}</div>
      </div>
      <div style='display:flex;flex-direction:column;gap:18px'>
        <div style='background:#1C1B19;border-radius:12px;padding:18px 22px'><div class='h' style='font-size:22px;margin-bottom:8px'>Действия</div>{acts_html}
          <div style='font-size:17px;margin-top:10px;line-height:1.3;color:#E8A88E'>Непотраченная единица в конце Дня приводит ходячего на твой тайл.</div></div>
      </div></div>"""
    return page(body, W, H), W, H

def shared_board():
    W, H = 1600, 900
    nights = "".join(f"<div style='flex:1;height:90px;border-radius:8px;background:{'#3B4A2E' if i<=3 else ('#5A4A22' if i<=6 else '#5A2620')};display:flex;align-items:center;justify-content:center;font-size:34px' class='h'>{i}</div>" for i in range(1, 10))
    shift = "".join(f"<div style='flex:1;height:64px;border-radius:6px;background:#33302A;display:flex;align-items:center;justify-content:center;font-size:22px;color:#CFC8B6'>{i}</div>" for i in range(16))
    steps = ["Событие (разлом по типу → ближайший тайл)", "Сдвиг +1", "Искажённые тайлы +1 ступень, гнёзда выпускают врагов",
             "Трупы встают: труп → Восставший", "Враги идут к ближайшему: шагов = Скорость",
             "Нападение: каждый враг −Урон Здоровья", "Ночь +1"]
    st = "".join(f"<div style='font-size:21px;padding:5px 0'><b style='color:#C8E04A'>{i}.</b> {s}</div>" for i, s in enumerate(steps, 1))
    body = f"""<div style='width:{W}px;height:{H}px;background:#211F1B;padding:34px;display:grid;grid-template-columns:1fr 560px;gap:34px'>
      <div>
        <div class='h' style='font-size:52px'>НА ГРАНИ</div><div class='muted' style='font-size:20px'>пробник 0.5</div>
        <div class='h' style='font-size:22px;letter-spacing:.1em;margin:28px 0 10px'>НОЧЬ · эвакуация после 9-й</div>
        <div style='display:flex;gap:8px'>{nights}</div>
        <div class='h' style='font-size:22px;letter-spacing:.1em;margin:28px 0 10px'>СДВИГ</div>
        <div style='display:flex;gap:5px'>{shift}</div>
        <div style='display:grid;grid-template-columns:1fr 1fr;gap:18px;margin-top:30px'>
          <div style='height:200px;border:2px dashed #5A8EC8;border-radius:12px;display:flex;align-items:center;justify-content:center;font-size:26px;color:#8CB4E8'>Общая вода</div>
          <div style='height:200px;border:2px dashed #C88A5A;border-radius:12px;display:flex;align-items:center;justify-content:center;font-size:26px;color:#E8B48C'>Общая еда</div>
        </div>
      </div>
      <div style='background:#1A1916;border-radius:12px;padding:22px 26px'>
        <div class='h' style='font-size:26px;margin-bottom:6px'>Раунд</div>
        <div style='font-size:21px;line-height:1.35'><b>День:</b> бросок, действия.<br><b>Сумерки:</b> в Лагере 1 еда + 1 вода каждому (нет → +1 Голод/+1 Жажда); вне Лагеря — Ночлег тайла.</div>
        <div class='h' style='font-size:26px;margin:16px 0 6px'>Ночь</div>{st}
      </div></div>"""
    return page(body, W, H), W, H

def main():
    with sync_playwright() as pw:
        # тайлы 5x4
        shoot(pw, "tiles_front.png", page(grid([tile_front(t) for t in TILES], 5, 4, T, T), 5*T, 4*T), 5*T, 4*T)
        shoot(pw, "tiles_back.png", page(grid([tile_back(t) for t in TILES], 5, 4, T, T), 5*T, 4*T), 5*T, 4*T)
        # события 7x4
        shoot(pw, "events_front.png", page(grid([event_front(x) for x in EVENTS], 7, 4, CW, CH), 7*CW, 4*CH), 7*CW, 4*CH)
        shoot(pw, "events_back.png", page(grid([event_back(x) for x in EVENTS], 7, 4, CW, CH), 7*CW, 4*CH), 7*CW, 4*CH)
        # срыв 5x2
        shoot(pw, "sryv_front.png", page(grid([sryv_front(c) for c in SRYV], 5, 2, CW, CH), 5*CW, 2*CH), 5*CW, 2*CH)
        shoot(pw, "sryv_back.png", page(sryv_back().join(["<div class='cell' style='width:400px;height:560px'>", "</div>"]), CW, CH), CW, CH)
        # жетоны 2x2
        shoot(pw, "tokens_front.png", page(grid(TOK_FRONT, 2, 2, K, K), 2*K, 2*K), 2*K, 2*K)
        shoot(pw, "tokens_back.png", page(grid(TOK_BACK, 2, 2, K, K), 2*K, 2*K), 2*K, 2*K)
        m, w, h = player_board(); shoot(pw, "player_board.png", m, w, h)
        m, w, h = shared_board(); shoot(pw, "shared_board.png", m, w, h)
        felt = ("<div style='width:2048px;height:2048px;background:#2A2622;"
                "background-image:radial-gradient(circle at 50% 45%, #34302A 0%, #2A2622 55%, #1E1B18 100%)'></div>")
        shoot(pw, "table_surface.png", page(felt, 2048, 2048), 2048, 2048)

if __name__ == "__main__":
    main()
