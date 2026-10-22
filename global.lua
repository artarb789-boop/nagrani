
-- На грани: подготовка партии
local TERRAIN = {"4d3c1a", "ca264e", "18b8ff", "25165e", "3031d0", "bb3b93", "1db208", "6deceb", "1332a1", "2c0146", "de06ce", "d61aa9"}
local STACK_POS = {-14, 7}
local START_LEVEL1 = 2
local CAMP = "a5cd68"
local TABLE = "552df6"
local SHARED = "2941f3"
local SHARED_W = 33.3
local TABLE_SIZE = 140
local NIGHT_DECKS = {
  {guid = "1fac61", name = "Ночи 1–3"},
  {guid = "5c882b",   name = "Ночи 4–6"},
  {guid = "daed60",  name = "Ночи 7–9"},
}
local OUT_POS = {33, 1.5, 0}
local BOARD_JSON = [==[{"GUID": "", "Name": "Custom_Board", "Transform": {"posX": 0, "posY": 1, "posZ": 0, "rotX": 0, "rotY": 180, "rotZ": 0, "scaleX": 0.394, "scaleY": 0.394, "scaleZ": 0.394}, "Nickname": "Планшет игрока", "Description": "", "GMNotes": "", "ColorDiffuse": {"r": 1, "g": 1, "b": 1}, "Locked": false, "Grid": false, "Snap": true, "Autoraise": true, "Sticky": true, "Tooltip": true, "GridProjection": false, "Hands": false, "LuaScript": "", "LuaScriptState": "", "CustomImage": {"ImageURL": "file:///C:/NaGrani/images/player_board.png", "ImageSecondaryURL": "", "ImageScalar": 1.0, "WidthScale": 0.0}}]==]
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
