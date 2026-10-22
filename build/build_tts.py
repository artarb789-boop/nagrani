# -*- coding: utf-8 -*-
"""Собирает файл сохранения Tabletop Simulator для пробника «На грани» (v0.2)."""
import json, random, sys
from pathlib import Path
from PIL import Image
sys.path.insert(0, str(Path(__file__).parent))
from data import TILES, EVENTS, SRYV

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

tf_names = crop_sheet("tiles_front.png", 5, 512, 512, len(TILES), "tile_front")
tb_names = crop_sheet("tiles_back.png", 5, 512, 512, len(TILES), "tile_back")
kf_names = crop_sheet("tokens_front.png", 2, 256, 256, 4, "token_front")
kb_names = crop_sheet("tokens_back.png", 2, 256, 256, 4, "token_back")

# Скрипт тайла: счётчик запаса с кнопками − и + на обеих сторонах
TILE_LUA = r'''
local value = nil

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
  local z = h * 0.80
  local sc = {h * 0.22, 1, h * 0.22}
  local sides = {
    {y = 0.2,  rot = {0, 0, 0},   dir = -1},
    {y = -0.2, rot = {0, 0, 180}, dir = 1},
  }
  for _, sd in ipairs(sides) do
    local x0 = sd.dir * h * 0.52
    local step = sd.dir * h * 0.20
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

def custom_tile(front, back, transform, nick, desc="", thick=0.15, gm="", lua=""):
    return obj("Custom_Tile", transform, nick, desc, GMNotes=gm, LuaScript=lua,
               CustomImage={"ImageURL": url(front), "ImageSecondaryURL": url(back), "ImageScalar": 1.0,
                            "WidthScale": 0.0,
                            "CustomTile": {"Type": 0, "Thickness": thick, "Stackable": False, "Stretch": True}})

def infinite_bag(nick, inner, x, z, color=(0.25, 0.25, 0.25)):
    return obj("Infinite_Bag", tf(x, 1.5, z), nick, color=color, ContainedObjects=[inner])

def block(nick, color, s=0.45):
    return obj("BlockSquare", tf(0, 1, 0, s=s), nick, color=color)

objects = []
TILE_SCALE = 3.0

# Лагерь в центр
camp = custom_tile(tf_names[0], tb_names[0], tf(0, 1, 0, s=TILE_SCALE), "Лагерь",
                   "Старт. Сумерки: еда и вода из общего запаса.",
                   gm=json.dumps({"edges": "NESW", "zap": 0}))
objects.append(camp)

# Остальные тайлы в мешок
bag_tiles = []
for t in TILES[1:]:
    n, name, q, edges, srch, loot, zap, thr, nl, nle, dist, dname, *_ = t
    desc = f"{q} · Обыск {srch}+ · Угроза {thr} · Запас {zap} · {nl}: {nle}\nОборот: {dname} ({dist})"
    bag_tiles.append(custom_tile(tf_names[n], tb_names[n], tf(s=TILE_SCALE), name, desc,
                                 gm=json.dumps({"edges": edges, "zap": zap}), lua=TILE_LUA))
tile_bag = obj("Bag", tf(-13, 1.5, 7, s=1.3), "Тайлы города",
               "Тяни вслепую, клади обычной (светлой) стороной вверх.",
               color=(0.35, 0.3, 0.25), ContainedObjects=bag_tiles)
objects.append(tile_bag)

# ---------- колоды ----------
def card(deck_key, idx, cd, nick, desc=""):
    return obj("Card", tf(0, 1, 0, rz=180), nick, desc, CardID=deck_key * 100 + idx,
               HideWhenFaceDown=True, SidewaysCard=False, CustomDeck={str(deck_key): cd})

def deck(deck_key, cd, cards, transform, nick, desc=""):
    return obj("Deck", transform, nick, desc, HideWhenFaceDown=True, SidewaysCard=False,
               DeckIDs=[c["CardID"] for c in cards], CustomDeck={str(deck_key): cd}, ContainedObjects=cards)

ev_cd = {"FaceURL": url("events_front.png"), "BackURL": url("events_back.png"), "NumWidth": 7, "NumHeight": 4,
         "BackIsHidden": True, "UniqueBack": True, "Type": 0}
layers = ["Ранние", "Средние", "Поздние", "Последствия"]
layer_pos = [(21, 12), (24, 12), (27, 12), (24, 6.5)]
layer_guids = {}
for li, layer in enumerate(layers):
    cards = [card(2, i, ev_cd, ev[1], f"{layer} · Мир: {ev[4]} · Выживание: {ev[5]}")
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
objects.append(board("shared_board.png", tf(0, 1, 15, s=0.42), "Общее поле"))
table_surf = board("table_surface.png", tf(0, 0.5, 0, s=1.8), "Стол")
table_surf["Locked"] = True
table_surf["Tooltip"] = False
table_surf["Snap"] = False
objects.append(table_surf)

rules = (ROOT / "Правила_пробника.md").read_text(encoding="utf-8")
objects.append(obj("Notecard", tf(28, 1, 6.5), "Правила пробника", rules))

# Шаблон планшета игрока — его создаёт скрипт после выбора числа игроков
pb = board("player_board.png", tf(0, 1, 0, s=0.22), "Планшет игрока")
pb["GUID"] = ""  # TTS выдаст свой
BOARD_JSON = json.dumps(pb, ensure_ascii=False)

GLOBAL_LUA = r'''
-- На грани: подготовка партии
local TILE_BAG = "__TILE_BAG__"
local CAMP = "__CAMP__"
local TABLE = "__TABLE__"
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
local DICE_OFF = {{-4.5, 5.0}, {-3.5, 5.0}, {-2.5, 5.0}, {-1.5, 5.0}, {-0.5, 5.0}, {0.5, 5.0}}
-- Голод 0, Жажда 0, Здоровье 5, Фокус 5, Изменение 0
local MARK_OFF = {{-6.07, 0.75}, {-6.07, -0.03}, {-2.26, -0.82}, {-2.26, -1.6}, {-7.85, -2.84}}
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
  placeStartTiles()
  trimNightDecks()
  local boards = n
  if n == 1 then boards = 2 end
  spawnPlayers(boards)
  startSupply(boards)
  broadcastToAll("Выживших: " .. boards .. ". Вокруг Лагеря открыты 4 тайла, колоды ночей готовы, в общем запасе еда и вода.", {0.78, 0.88, 0.29})
end

-- Направления от Лагеря в мире: 0 = +z, 1 = +x, 2 = -z, 3 = -x.
-- Край тайла i (N=0, E=1, S=2, W=3) после k поворотов на 90° смотрит в сторону (i + k) % 4.
local EDGE = {N = 0, E = 1, S = 2, W = 3}
local OFFSETS = {{0, 1}, {1, 0}, {0, -1}, {-1, 0}}

function placeStartTiles()
  local bag = getObjectFromGUID(TILE_BAG)
  local camp = getObjectFromGUID(CAMP)
  if bag == nil or camp == nil then return end
  bag.shuffle()
  local cp = camp.getPosition()
  local step = camp.getBounds().size.x + 0.1
  for d = 0, 3 do
    local off = OFFSETS[d + 1]
    local pos = {cp.x + off[1] * step, cp.y + 0.6, cp.z + off[2] * step}
    bag.takeObject({
      position = pos, rotation = {0, 180, 0}, smooth = false,
      callback_function = function(o) orientToCamp(o, d) end,
    })
  end
end

function orientToCamp(o, d)
  local need = (d + 2) % 4
  local edges = "NESW"
  local ok, data = pcall(function() return JSON.decode(o.getGMNotes()) end)
  if ok and data ~= nil and data.edges ~= nil then edges = data.edges end
  local opts = {}
  for c in string.gmatch(edges, ".") do
    if EDGE[c] ~= nil then table.insert(opts, EDGE[c]) end
  end
  if #opts == 0 then return end
  -- предпочитаем поворот, при котором текст читается: 0, потом четверть оборота, потом вверх ногами
  local pref = {[0] = 0, [1] = 1, [3] = 1, [2] = 2}
  local bestK, bestScore = nil, 99
  for _, i in ipairs(opts) do
    local k = (need - i) % 4
    if pref[k] < bestScore then bestK, bestScore = k, pref[k] end
  end
  o.setRotation({0, 180 + 90 * bestK, 0})
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
      callback_function = function(o) o.setName("Планшет: " .. color) end,
    })
    for i = 1, 6 do
      spawnObject({
        type = "Die_6", position = {x + DICE_OFF[i][1], 2, BOARD_Z + DICE_OFF[i][2]}, rotation = {0, 180, 0},
        scale = {0.64, 0.64, 0.64},
        callback_function = function(o) o.setColorTint(stringColorToRGB(color)); o.setName("Кубик " .. color) end,
      })
    end
    for m, mk in ipairs(MARKERS) do
      spawnObject({
        type = "BlockSquare", position = {x + MARK_OFF[m][1], 2, BOARD_Z + MARK_OFF[m][2]}, rotation = {0, 180, 0},
        scale = {0.35, 0.35, 0.35},
        callback_function = function(o) o.setColorTint(mk.color); o.setName(mk.name .. " (" .. color .. ")") end,
      })
    end
  end
end
'''
for key, val in {"__TILE_BAG__": tile_bag["GUID"], "__CAMP__": camp["GUID"], "__TABLE__": table_surf["GUID"],
                 "__EARLY__": layer_guids["Ранние"], "__MID__": layer_guids["Средние"],
                 "__LATE__": layer_guids["Поздние"], "__BOARD__": BOARD_JSON}.items():
    GLOBAL_LUA = GLOBAL_LUA.replace(key, val)

btns = "".join(f'<Button id="p{i}" onClick="choosePlayers" fontSize="34" textColor="#EDE9DD" '
               f'colors="#3A3730|#5A5548|#2A2826|#3A3730">{i}</Button>' for i in range(1, 6))
XML_UI = f'''<Panel id="setup" width="560" height="250" rectAlignment="MiddleCenter" color="#1C1B19F0" outline="#C8E04A" outlineSize="2 2">
  <VerticalLayout padding="24 24 20 20" spacing="14" childForceExpandHeight="false">
    <Text fontSize="30" fontStyle="Bold" color="#EDE9DD" preferredHeight="44">На грани — сколько выживших?</Text>
    <HorizontalLayout spacing="12" preferredHeight="80">{btns}</HorizontalLayout>
    <Text fontSize="17" color="#A7A293" preferredHeight="50">Появятся планшеты, кубики и маркеры. Вокруг Лагеря откроются 4 случайных тайла. Соло: выбери 1 — получишь двух выживших.</Text>
  </VerticalLayout>
</Panel>'''

save = {
    "SaveName": "На грани — пробник 0.5", "GameMode": "На грани", "Gravity": 0.5, "PlayArea": 1.0,
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
