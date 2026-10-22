-- Раскладывает планшеты игроков в ряд без наложения (запуск 1)
local ORDER = {"White", "Red", "Blue", "Green", "Yellow"}
local boards, width = {}, 0
for _, o in ipairs(getAllObjects()) do
  local name = o.getName() or ""
  local color = string.match(name, "^Планшет: (%a+)$")
  if color then
    boards[color] = o
    width = math.max(width, o.getBounds().size.x)
  end
end
local list = {}
for _, c in ipairs(ORDER) do if boards[c] then table.insert(list, c) end end
local n = #list
if n == 0 then broadcastToAll("Планшетов на столе нет.", {1, 0.5, 0.4}) return end
local gap = width + 1
for p, color in ipairs(list) do
  local b = boards[color]
  local newX = (p - (n + 1) / 2) * gap
  local dx = newX - b.getPosition().x
  for _, o in ipairs(getAllObjects()) do
    local name = o.getName() or ""
    if name == "Планшет: " .. color or name == "Кубик " .. color
       or string.sub(name, -(#color + 3)) == "(" .. color .. ")" then
      local pos = o.getPosition()
      o.setPositionSmooth({pos.x + dx, pos.y + 0.3, pos.z}, false, true)
    end
  end
end
print(string.format("Ширина планшета %.1f, шаг %.1f, планшетов %d", width, gap, n))
broadcastToAll("Планшеты разложены.", {0.78, 0.88, 0.29})
