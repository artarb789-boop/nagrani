# -*- coding: utf-8 -*-
"""Собирает файл сохранения Tabletop Simulator для пробника «На грани» (v0.6, гексы)."""
import json, random, sys
from pathlib import Path
from PIL import Image
sys.path.insert(0, str(Path(__file__).parent))
from data import TILES, EVENTS, SRYV, HEX_TILES, RIFT_MEMO, CHARACTERS

ROOT = Path(__file__).parent.parent
IMG = ROOT / "images"
TILE_DIR = IMG / "tiles"
TILE_DIR.mkdir(exist_ok=True)
BASE = sys.argv[1] if len(sys.argv) > 1 else "file:///C:/NaGrani/images/"

random.seed(7)
_used = set()
def guid():
    while True:
        g = "%06x" % random.randrange(16**6)
        if g not in _used:
            _used.add(g); return g

def url(name): return BASE + name

def tf(x=0, y=1, z=0, rx=0, ry=180, rz=0, s=1.0, sy=None):
    return {"posX": x, "posY": y, "posZ": z, "rotX": rx, "rotY": ry, "rotZ": rz,
            "scaleX": s, "scaleY": sy if sy is not None else s, "scaleZ": s}

def obj(name, transform, nick="", desc="", color=(1, 1, 1), **extra):
    o = {"GUID": guid(), "Name": name, "Transform": transform, "Nickname": nick, "Description": desc,
         "GMNotes": "", "ColorDiffuse": {"r": color[0], "g": color[1], "b": color[2]},
         "Locked": False, "Grid": False, "Snap": True, "Autoraise": True, "Sticky": True,
         "Tooltip": True, "GridProjection": False, "Hands": False, "LuaScript": "", "LuaScriptState": ""}
    o.update(extra)
    return o

# ---------- нарезка тайлов и жетонов ----------
def crop_sheet(sheet, cols, cw, ch, count, prefix):
    im = Image.open(IMG / sheet)
    names = []
    for i in range(count):
        c, r = i % cols, i // cols
        part = im.crop((c * cw, r * ch, (c + 1) * cw, (r + 1) * ch))
        n = f"{prefix}_{i:02d}.png"
        part.save(TILE_DIR / n)
        names.append("tiles/" + n)
    return names

kf_names = crop_sheet("tokens_front.png", 2, 256, 256, 4, "token_front")
kb_names = crop_sheet("tokens_back.png", 2, 256, 256, 4, "token_back")

# Скрипт тайла: счётчик запаса с кнопками − и + на лицевой стороне
TILE_LUA = r'''
local value = nil

function onLoad(state)
  if state ~= nil and state ~= "" then value = tonumber(state) end
  if value == nil then
    local ok, d = pcall(function() return JSON.decode(self.getGMNotes()) end)
    if ok and d ~= nil and d.zap ~= nil then value = d.zap else value = 0 end
  end
  Wait.frames(draw, 2)
end

function onSave() return tostring(value) end

function noop() end
function plus() value = value + 1; draw() end
function minus() if value > 0 then value = value - 1 end; draw() end

function draw()
  self.clearButtons()
  local b = self.getBounds()
  local s = self.getScale()
  local h = (b.size.x / s.x) / 2
  if h <= 0 then h = 1 end
  local z = h * 0.58
  local sc = {h * 0.2, 1, h * 0.2}
  local sd = {y = 0.2, rot = {0, 0, 0}}
  do
    local x0 = h * 0.2
    local step = -h * 0.2
    self.createButton({click_function = "minus", function_owner = self, label = "−",
      position = {x0, sd.y, z}, rotation = sd.rot, width = 380, height = 380, font_size = 320,
      scale = sc, color = {0.12, 0.12, 0.1}, font_color = {0.93, 0.91, 0.86}, tooltip = "Запас −1"})
    self.createButton({click_function = "noop", function_owner = self, label = tostring(value),
      position = {x0 + step, sd.y, z}, rotation = sd.rot, width = 420, height = 380, font_size = 320,
      scale = sc, color = {0.81, 0.9, 0.63}, font_color = {0.1, 0.12, 0.05}, tooltip = "Запас тайла"})
    self.createButton({click_function = "plus", function_owner = self, label = "+",
      position = {x0 + step * 2, sd.y, z}, rotation = sd.rot, width = 380, height = 380, font_size = 320,
      scale = sc, color = {0.12, 0.12, 0.1}, font_color = {0.93, 0.91, 0.86}, tooltip = "Запас +1"})
  end
end
'''

def custom_tile(front, back, transform, nick, desc="", thick=0.15, gm="", lua="", shape=0):
    return obj("Custom_Tile", transform, nick, desc, GMNotes=gm, LuaScript=lua,
               CustomImage={"ImageURL": url(front), "ImageSecondaryURL": url(back), "ImageScalar": 1.0,
                            "WidthScale": 0.0,
                            "CustomTile": {"Type": shape, "Thickness": thick, "Stackable": False, "Stretch": True}})

def infinite_bag(nick, inner, x, z, color=(0.25, 0.25, 0.25)):
    return obj("Infinite_Bag", tf(x, 1.5, z), nick, color=color, ContainedObjects=[inner])

def block(nick, color, s=0.45):
    return obj("BlockSquare", tf(0, 1, 0, s=s), nick, color=color)

objects = []
TILE_SCALE = 3.0

# Лагерь в центр (гекс)
def hexf(n): return f"hex/hex_front_{n:02d}.png"
def hexb(l): return f"hex/hex_back_{l}.png"
camp = custom_tile(hexf(0), hexb(0), tf(0, 1, 0, s=TILE_SCALE), "Лагерь",
                   "Старт. Сумерки: еда и вода из общего запаса.", thick=0.2, shape=1,
                   gm=json.dumps({"edges": "111111", "zap": 0}))
objects.append(camp)

# Стопка местности: рубашкой (уровнем) вверх, скрипт перемешивает при выборе игроков
STACK = (-14, 7)
terrain = []
for i, t in enumerate(HEX_TILES[1:]):
    n, name, lvl, q, edges, srch, loot, zap, nl, nle, rift, dist, own = t
    desc = f"Уровень {lvl} · {q} · Обыск {srch}+ · Лут: {loot} · {nl}: {nle}\nРазлом: {rift}" + (f" (с начала игры) — {own}" if dist else "")
    o = custom_tile(hexf(n), hexb(lvl), tf(STACK[0], 1.2 + i * 0.3, STACK[1], rz=180, s=TILE_SCALE), name, desc,
                    thick=0.2, shape=1, gm=json.dumps({"edges": edges, "zap": zap, "level": lvl}), lua=TILE_LUA)
    terrain.append(o)
    objects.append(o)


# ---------- колоды ----------
def card(deck_key, idx, cd, nick, desc=""):
    return obj("Card", tf(0, 1, 0, rz=180), nick, desc, CardID=deck_key * 100 + idx,
               HideWhenFaceDown=True, SidewaysCard=False, CustomDeck={str(deck_key): cd})

def deck(deck_key, cd, cards, transform, nick, desc=""):
    return obj("Deck", transform, nick, desc, HideWhenFaceDown=True, SidewaysCard=False,
               DeckIDs=[c["CardID"] for c in cards], CustomDeck={str(deck_key): cd}, ContainedObjects=cards)

ev_cd = {"FaceURL": url("events_front.png"), "BackURL": url("events_back.png"), "NumWidth": 7, "NumHeight": 5,
         "BackIsHidden": True, "UniqueBack": True, "Type": 0}
layers = ["Ранние", "Средние", "Поздние", "Последствия"]
layer_pos = [(21, 12), (24, 12), (27, 12), (24, 6.5)]
layer_guids = {}
for li, layer in enumerate(layers):
    cards = [card(2, i, ev_cd, ev[1], (f"{layer} · УГРОЗА · Отвести: {ev[4]} · Не отвели: {ev[5]}" if ev[6] == "УГРОЗА" else f"{layer} · Мир: {ev[4]} · Выживание: {ev[5]}"))
             for i, ev in enumerate(EVENTS) if ev[2] == layer]
    x, z = layer_pos[li]
    d = deck(2, ev_cd, cards, tf(x, 1.2, z, rz=180, s=1.0), f"События: {layer}",
             "Тяни по одной карте каждую ночь: сначала Ночи 1–3, потом 4–6, потом 7–9.")
    layer_guids[layer] = d["GUID"]
    objects.append(d)

sr_cd = {"FaceURL": url("sryv_front.png"), "BackURL": url("sryv_back.png"), "NumWidth": 5, "NumHeight": 2,
         "BackIsHidden": True, "UniqueBack": False, "Type": 0}
sr_cards = [card(3, i, sr_cd, c[0], f"{c[1]}: {c[2]}") for i, c in enumerate(SRYV)]
objects.append(deck(3, sr_cd, sr_cards, tf(21, 1.2, 6.5, rz=180, s=1.0), "Срыв",
                    "Переполнил Изменение — тайно возьми карту себе в руку."))

# ---------- памятки разломов и жетон разлома ----------
mm_cd = {"FaceURL": url("memo_front.png"), "BackURL": url("memo_back.png"), "NumWidth": 5, "NumHeight": 1,
         "BackIsHidden": True, "UniqueBack": False, "Type": 0}
mm_cards = []
for i, r in enumerate(RIFT_MEMO):
    c = card(4, i, mm_cd, f"Разлом: {r}", " / ".join(f"{x}: {t}" for x, t in zip(["I", "II", "III"], RIFT_MEMO[r])))
    c["Transform"]["rotZ"] = 0
    mm_cards.append(c)
objects.append(deck(4, mm_cd, mm_cards, tf(30.5, 1.2, 12, s=1.0), "Памятки разломов",
                    "Разложи все пять рядом с общим полем."))
rift_tok = custom_tile("rift_token.png", "rift_token.png", tf(s=0.55), "Разлом",
                       "Кладётся на чистый тайл. Ступень отмечай маркером.", thick=0.15, shape=2)
objects.append(infinite_bag("Жетоны разлома", rift_tok, -14, 13, color=(0.45, 0.3, 0.65)))

# ---------- персонажи ----------
ch_cd = {"FaceURL": url("chars_front.png"), "BackURL": url("chars_back.png"), "NumWidth": 6, "NumHeight": 1,
         "BackIsHidden": True, "UniqueBack": False, "Type": 0}
ch_cards = []
for i, c in enumerate(CHARACTERS):
    cc = card(5, i, ch_cd, c[0], f"Кубики {c[2]}/{c[3]} · Здоровье {c[4]} · Фокус {c[5]} · Переход {c[6]}+ · Открыть {c[7]}+ и 1 Фокус\n{c[8]}\nСлабость: {c[9]}")
    cc["Transform"]["rotZ"] = 0
    ch_cards.append(cc)
objects.append(deck(5, ch_cd, ch_cards, tf(-24, 1.2, -4, s=1.0), "Персонажи",
                    "Каждый выбирает или тянет одного персонажа."))

# ---------- жетоны, ресурсы, маркеры: сетка слева ----------
def grid_pos(k):
    return -31 + (k % 3) * 2.6, 13 - (k // 3) * 2.8

TOK = [("Ходячий (оборот: Труп)", 0), ("Бегун (оборот: Труп)", 1), ("Бронированный (оборот: Труп)", 2), ("Восставший (оборот: Труп)", 3)]
k = 0
for nick, i in TOK:
    inner = custom_tile(kf_names[i], kb_names[i], tf(s=0.8), nick.split(" (")[0], nick, thick=0.2)
    x, z = grid_pos(k); k += 1
    objects.append(infinite_bag(nick, inner, x, z, color=(0.4, 0.2, 0.15)))

RES = [("Еда", (0.93, 0.55, 0.2)), ("Вода", (0.25, 0.55, 0.95)), ("Медикамент", (0.95, 0.95, 0.95)),
       ("Материал", (0.5, 0.33, 0.2)), ("Техника", (0.95, 0.85, 0.2)), ("Мутаген", (0.6, 0.9, 0.2)),
       ("Маркер ступени / Сдвига / Ночи", (0.08, 0.08, 0.08))]
for nick, col in RES:
    x, z = grid_pos(k); k += 1
    objects.append(infinite_bag(nick, block(nick, col), x, z, color=col))
x, z = grid_pos(k)
objects.append(infinite_bag("Кубики d6", obj("Die_6", tf(s=0.64), "Кубик"), x, z, color=(0.9, 0.9, 0.9)))

# ---------- общее поле и правила ----------
def board(img, transform, nick):
    return obj("Custom_Board", transform, nick, CustomImage={"ImageURL": url(img), "ImageSecondaryURL": "",
                                                            "ImageScalar": 1.0, "WidthScale": 0.0})
shared = board("shared_board.png", tf(0, 1, 15, s=0.42), "Общее поле")
objects.append(shared)
table_surf = board("table_surface.png", tf(0, 0.5, 0, s=1.8), "Стол")
table_surf["Locked"] = True
table_surf["Tooltip"] = False
table_surf["Snap"] = False
objects.append(table_surf)

rules = (ROOT / "Правила_пробника.md").read_text(encoding="utf-8")
objects.append(obj("Custom_PDF", tf(30, 1, 4, s=1.6), "Правила пробника",
                   "Листай стрелками внизу. Правила также в Блокноте (Notebook).",
                   CustomPDF={"PDFUrl": url("rules.pdf"), "PDFPassword": "", "PDFPage": 0, "PDFPageOffset": 0}))

# Шаблон планшета игрока — его создаёт скрипт после выбора числа игроков
pb = board("player_board.png", tf(0, 1, 0, s=0.394), "Планшет игрока")
pb["GUID"] = ""  # TTS выдаст свой
BOARD_JSON = json.dumps(pb, ensure_ascii=False)

GLOBAL_LUA = r'''
-- На грани: подготовка партии
local TERRAIN = {__TERRAIN__}
local STACK_POS = {__STACK_X__, __STACK_Z__}
local START_LEVEL1 = 2
local CAMP = "__CAMP__"
local TABLE = "__TABLE__"
local SHARED = "__SHARED__"
local SHARED_W = 33.3
local TABLE_SIZE = 140
local NIGHT_DECKS = {
  {guid = "__EARLY__", name = "Ночи 1–3"},
  {guid = "__MID__",   name = "Ночи 4–6"},
  {guid = "__LATE__",  name = "Ночи 7–9"},
}
local OUT_POS = {33, 1.5, 0}
local BOARD_JSON = [==[__BOARD__]==]
local BOARD_Z = -14
local BOARD_GAP = 19
-- Смещения от центра планшета (планшет 17.45 x 6.43, повёрнут на 180): +x вправо, +z к верху планшета
-- Планшет при масштабе 0.394: 17.45 x 7.2 (замерено в TTS)
local BOARD_W = 17.45
local BOARD_H = 7.2
-- Кубики: смещение по x от центра планшета, над верхним краем
local DICE_X = {-4.5, -3.5, -2.5}
-- Маркеры: смещения от центра планшета, замерены по раскладке в TTS
-- Голод 0, Жажда 0, Здоровье 5, Фокус 5, Изменение 0
local MARK_OFF = {{-5.57, 0.70}, {-5.56, -0.02}, {-2.05, -0.77}, {-2.05, -1.49}, {-7.19, -2.58}}
local COLORS = {"White", "Red", "Blue", "Green", "Yellow"}
local MARKERS = {
  {name = "Голод",     color = {0.93, 0.55, 0.2}},
  {name = "Жажда",     color = {0.25, 0.55, 0.95}},
  {name = "Здоровье",  color = {0.85, 0.2, 0.2}},
  {name = "Фокус",     color = {0.7, 0.55, 0.95}},
  {name = "Изменение", color = {0.1, 0.1, 0.1}},
}
local started = false

-- Стол: большая заблокированная поверхность, подгоняется под TABLE_SIZE x TABLE_SIZE, верх на высоте 0.95
function fitTable()
  local t = getObjectFromGUID(TABLE)
  if t == nil then return end
  t.interactable = false
  local size = t.getBounds().size
  if size.x > 0 and math.abs(size.x - TABLE_SIZE) > 0.5 then
    local sc = t.getScale()
    local k = TABLE_SIZE / size.x
    t.setScale({sc.x * k, sc.y, sc.z * k})
  end
  local b = t.getBounds()
  local pos = t.getPosition()
  t.setPosition({pos.x, pos.y + (0.95 - (b.center.y + b.size.y / 2)), pos.z})
end

function onLoad(state)
  fitTable()
  if state ~= nil and state ~= "" then
    local ok, d = pcall(function() return JSON.decode(state) end)
    if ok and d ~= nil and d.started then started = true end
  end
  if started then UI.hide("setup") end
end

function onSave() return JSON.encode({started = started}) end

function choosePlayers(player, value, id)
  if started then return end
  local n = tonumber(string.sub(id, 2))
  if n == nil then return end
  started = true
  UI.hide("setup")
  pcall(function() math.randomseed(os.time()) end)
  stackTerrain()
  trimNightDecks()
  local boards = n
  if n == 1 then boards = 2 end
  spawnPlayers(boards)
  startSupply(boards)
  broadcastToAll("Выживших: " .. boards .. ". Стопка местности перемешана, колоды ночей готовы, в общем запасе еда и вода.", {0.78, 0.88, 0.29})
end

-- Стопка местности: перемешать и сложить рубашкой (уровнем) вверх
function stackTerrain()
  local list = {}
  for _, g in ipairs(TERRAIN) do
    local o = getObjectFromGUID(g)
    if o ~= nil then table.insert(list, o) end
  end
  for i = #list, 2, -1 do
    local j = math.random(i)
    list[i], list[j] = list[j], list[i]
  end
  -- Первые START_LEVEL1 тайлов сверху стопки — всегда уровня I
  local top, rest = {}, {}
  for _, o in ipairs(list) do
    local ok, d = pcall(function() return JSON.decode(o.getGMNotes()) end)
    if #top < START_LEVEL1 and ok and d ~= nil and d.level == 1 then table.insert(top, o) else table.insert(rest, o) end
  end
  list = rest
  for _, o in ipairs(top) do table.insert(list, o) end
  for i, o in ipairs(list) do
    o.setRotation({0, 180, 180})
    o.setPosition({STACK_POS[1], 1.2 + i * 0.3, STACK_POS[2]})
  end
end

function trimNightDecks()
  for idx, info in ipairs(NIGHT_DECKS) do
    local deck = getObjectFromGUID(info.guid)
    if deck ~= nil then
      deck.shuffle()
      local extra = deck.getQuantity() - 3
      for j = 1, extra do
        deck.takeObject({position = {OUT_POS[1], OUT_POS[2] + idx * 0.6 + j * 0.15, OUT_POS[3] - idx * 3.5},
                         rotation = {0, 180, 180}, smooth = false})
      end
      deck.setName(info.name)
    end
  end
end

-- Общий запас: по 2 еды и 2 воды на выжившего
function startSupply(n)
  local function put(name, color, x0, count)
    for i = 1, count do
      spawnObject({
        type = "BlockSquare",
        position = {x0 + ((i - 1) % 4) * 0.7, 2 + math.floor((i - 1) / 4) * 0.6, 13.5},
        scale = {0.45, 0.45, 0.45},
        callback_function = function(o) o.setColorTint(color); o.setName(name) end,
      })
    end
  end
  put("Вода", {0.25, 0.55, 0.95}, -4.5, 2 * n)
  put("Еда", {0.93, 0.55, 0.2}, 1.5, 2 * n)
end

function piecePositions(o)
  local p = o.getPosition()
  local size = {x = BOARD_W, z = BOARD_H}
  local dice, marks = {}, {}
  for i, dx in ipairs(DICE_X) do dice[i] = {p.x + dx, 2, p.z + size.z / 2 + 1.4} end
  for m, f in ipairs(MARK_OFF) do marks[m] = {p.x + f[1], 2, p.z + f[2]} end
  return dice, marks
end

function spawnPieces(o, color)
  local dice, marks = piecePositions(o)
  for i = 1, #DICE_X do
    spawnObject({
      type = "Die_6", position = dice[i], rotation = {0, 180, 0}, scale = {0.64, 0.64, 0.64},
      callback_function = function(d) d.setColorTint(stringColorToRGB(color)); d.setName("Кубик " .. color) end,
    })
  end
  for m, mk in ipairs(MARKERS) do
    spawnObject({
      type = "BlockSquare", position = marks[m], rotation = {0, 180, 0}, scale = {0.28, 0.28, 0.28},
      callback_function = function(b) b.setColorTint(mk.color); b.setName(mk.name .. " (" .. color .. ")") end,
    })
  end
end

function spawnPlayers(n)
  local camp = getObjectFromGUID(CAMP)
  local cp = {x = 0, y = 1, z = 0}
  if camp ~= nil then cp = camp.getPosition() end
  for p = 1, n do
    local pcolor = COLORS[p]
    spawnObject({
      type = "PlayerPawn", position = {cp.x - 1.6 + (p - 1) * 0.8, cp.y + 1.5, cp.z - 1}, rotation = {0, 180, 0},
      scale = {0.6, 0.6, 0.6},
      callback_function = function(o) o.setColorTint(stringColorToRGB(pcolor)); o.setName("Выживший " .. pcolor) end,
    })
  end
  for p = 1, n do
    local x = (p - (n + 1) / 2) * BOARD_GAP
    local color = COLORS[p]
    spawnObjectJSON({
      json = BOARD_JSON, position = {x, 1.3, BOARD_Z}, rotation = {0, 180, 0},
      callback_function = function(o)
        o.setName("Планшет: " .. color)
        spawnPieces(o, color)
      end,
    })
  end
end
'''
for key, val in {"__TERRAIN__": ", ".join('"%s"' % o["GUID"] for o in terrain), "__STACK_X__": str(STACK[0]), "__STACK_Z__": str(STACK[1]), "__CAMP__": camp["GUID"], "__TABLE__": table_surf["GUID"], "__SHARED__": shared["GUID"],
                 "__EARLY__": layer_guids["Ранние"], "__MID__": layer_guids["Средние"],
                 "__LATE__": layer_guids["Поздние"], "__BOARD__": BOARD_JSON}.items():
    GLOBAL_LUA = GLOBAL_LUA.replace(key, val)

btns = "".join(f'<Button id="p{i}" onClick="choosePlayers" fontSize="34" textColor="#EDE9DD" '
               f'colors="#3A3730|#5A5548|#2A2826|#3A3730">{i}</Button>' for i in range(1, 6))
XML_UI = f'''<Panel id="setup" width="560" height="250" rectAlignment="MiddleCenter" color="#1C1B19F0" outline="#C8E04A" outlineSize="2 2">
  <VerticalLayout padding="24 24 20 20" spacing="14" childForceExpandHeight="false">
    <Text fontSize="30" fontStyle="Bold" color="#EDE9DD" preferredHeight="44">На грани — сколько выживших?</Text>
    <HorizontalLayout spacing="12" preferredHeight="80">{btns}</HorizontalLayout>
    <Text fontSize="17" color="#A7A293" preferredHeight="50">Появятся планшеты, 3 кубика и маркеры. Стопка местности перемешается. Потом выберите персонажей. Соло: выбери 1 — получишь двух выживших.</Text>
  </VerticalLayout>
</Panel>'''

save = {
    "SaveName": "На грани — пробник 0.8", "GameMode": "На грани", "Gravity": 0.5, "PlayArea": 1.0,
    "Date": "", "Table": "Table_None", "TableURL": "", "Sky": "",
    "Note": rules, "Rules": "", "XmlUI": XML_UI,
    "LuaScript": GLOBAL_LUA, "LuaScriptState": "",
    "Grid": {"Type": 0, "Lines": False, "Color": {"r": 0, "g": 0, "b": 0}, "Opacity": 0.75,
             "ThickLines": False, "Snapping": False, "Offset": False, "BothSnapping": False,
             "xSize": 2.0, "ySize": 2.0, "PosOffset": {"x": 0.0, "y": 1.0, "z": 0.0}},
    "TabStates": {}, "VersionNumber": "v13.2.2", "ObjectStates": objects,
}
out = ROOT / "NaGrani.json"
out.write_text(json.dumps(save, ensure_ascii=False, indent=1), encoding="utf-8")
(ROOT / "global.lua").write_text(GLOBAL_LUA, encoding="utf-8")
(ROOT / "tile.lua").write_text(TILE_LUA, encoding="utf-8")
Image.open(IMG / "shared_board.png").resize((256, 144)).save(ROOT / "NaGrani.png")
print("objects:", len(objects), "->", out)
