-- Подгоняет планшеты под ширину 17.45 и ставит кубики и маркеры на места (запуск 1)
local BOARD_W = 17.45
local DICE_X = {-4.5, -3.5, -2.5, -1.5, -0.5, 0.5}
local MARKS = {{"Голод", -0.348, 0.104}, {"Жажда", -0.348, -0.004}, {"Здоровье", -0.1295, -0.114},
               {"Фокус", -0.1295, -0.222}, {"Изменение", -0.45, -0.3945}}
local boards = {}
for _, o in ipairs(getAllObjects()) do
  if string.find(o.getName(), "Планшет: ", 1, true) == 1 then
    local size = o.getBounds().size
    local sc = o.getScale()
    o.setScale({sc.x * BOARD_W / size.x, sc.y, sc.z * BOARD_W / size.x})
    table.insert(boards, o)
  end
end
Wait.frames(function()
  for _, b in ipairs(boards) do
    local color = string.sub(b.getName(), string.len("Планшет: ") + 1)
    local p, size = b.getPosition(), b.getBounds().size
    local i = 0
    for _, o in ipairs(getAllObjects()) do
      local nm = o.getName()
      if nm == "Кубик " .. color then
        i = i + 1
        if DICE_X[i] then o.setPositionSmooth({p.x + DICE_X[i], 2, p.z + size.z / 2 + 1.4}, false, true) end
      end
      for _, mk in ipairs(MARKS) do
        if nm == mk[1] .. " (" .. color .. ")" then
          local s = o.getScale()
          if s.x > 0.3 then o.setScale({s.x * 0.8, s.y * 0.8, s.z * 0.8}) end
          o.setPositionSmooth({p.x + mk[2] * size.x, 2, p.z + mk[3] * size.z}, false, true)
        end
      end
    end
  end
  broadcastToAll("Планшеты подогнаны, маркеры на нулях.", {0.78, 0.88, 0.29})
end, 5)
