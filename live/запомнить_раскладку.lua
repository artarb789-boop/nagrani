-- Считывает, как разложены кубики и маркеры вокруг планшета (запуск 1)
local best, bestD, bestColor = nil, 1e9, nil
for _, o in ipairs(getAllObjects()) do
  local color = string.match(o.getName() or "", "^Планшет: (%a+)$")
  if color then
    for _, m in ipairs(getAllObjects()) do
      if m.getName() == "Голод (" .. color .. ")" then
        local a, b = o.getPosition(), m.getPosition()
        local d = (a.x - b.x) ^ 2 + (a.z - b.z) ^ 2
        if d < bestD then best, bestD, bestColor = o, d, color end
      end
    end
  end
end
if not best then broadcastToAll("Не нашёл планшет с маркерами.", {1, 0.5, 0.4}) return end
local out = {}
local dice = 0
for _, o in ipairs(getAllObjects()) do
  local name = o.getName() or ""
  local tag
  if name == "Кубик " .. bestColor then dice = dice + 1; tag = "D" .. dice
  elseif string.sub(name, -(#bestColor + 3)) == "(" .. bestColor .. ")" then tag = string.match(name, "^(%S+)") end
  if tag then
    local p = best.positionToLocal(o.getPosition())
    table.insert(out, string.format("%s=%.2f,%.2f", tag, p.x, p.z))
  end
end
local w = best.getBounds().size.x
print("РАСКЛАДКА " .. bestColor .. " w=" .. string.format("%.2f", w) .. " " .. table.concat(out, " "))
broadcastToAll("Раскладка считана, смотри окно моста.", {0.78, 0.88, 0.29})
