
-- На грани: подготовка партии
local TILE_BAG = "724c60"
local CAMP = "a5cd68"
local NIGHT_DECKS = {
  {guid = "d69964", name = "Ночи 1–3"},
  {guid = "31e26b",   name = "Ночи 4–6"},
  {guid = "e807c8",  name = "Ночи 7–9"},
}
local OUT_POS = {33, 1.5, 0}
local BOARD_JSON = [==[{"GUID": "", "Name": "Custom_Board", "Transform": {"posX": 0, "posY": 1, "posZ": 0, "rotX": 0, "rotY": 180, "rotZ": 0, "scaleX": 0.22, "scaleY": 0.22, "scaleZ": 0.22}, "Nickname": "Планшет игрока", "Description": "", "GMNotes": "", "ColorDiffuse": {"r": 1, "g": 1, "b": 1}, "Locked": false, "Grid": false, "Snap": true, "Autoraise": true, "Sticky": true, "Tooltip": true, "GridProjection": false, "Hands": false, "LuaScript": "", "LuaScriptState": "", "CustomImage": {"ImageURL": "file:///C:/NaGrani/images/player_board.png", "ImageSecondaryURL": "", "ImageScalar": 1.0, "WidthScale": 0.0}}]==]
local BOARD_Z = -14
local BOARD_GAP = 10
local COLORS = {"White", "Red", "Blue", "Green", "Yellow"}
local MARKERS = {
  {name = "Голод",     color = {0.93, 0.55, 0.2}},
  {name = "Жажда",     color = {0.25, 0.55, 0.95}},
  {name = "Заражение", color = {0.55, 0.85, 0.2}},
  {name = "Изменение", color = {0.1, 0.1, 0.1}},
}
local started = false

function onLoad(state)
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
  broadcastToAll("Выживших: " .. boards .. ". Вокруг Лагеря открыты 4 тайла, колоды ночей готовы.", {0.78, 0.88, 0.29})
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
        type = "Die_6", position = {x - 3.6 + (i - 1) * 1.2, 2, BOARD_Z - 4}, rotation = {0, 180, 0},
        scale = {0.8, 0.8, 0.8},
        callback_function = function(o) o.setColorTint(stringColorToRGB(color)); o.setName("Кубик " .. color) end,
      })
    end
    for m, mk in ipairs(MARKERS) do
      spawnObject({
        type = "BlockSquare", position = {x + 4 + (m - 1) * 0.8, 2, BOARD_Z - 4}, rotation = {0, 180, 0},
        scale = {0.35, 0.35, 0.35},
        callback_function = function(o) o.setColorTint(mk.color); o.setName(mk.name .. " (" .. color .. ")") end,
      })
    end
  end
end
