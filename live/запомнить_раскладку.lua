-- Считывает, как разложены кубики и маркеры вокруг планшета (запуск 3)
local MARKERS = {"Голод", "Жажда", "Заражение", "Изменение"}
local best, bestD, bestColor = nil, 1e9, nil
for _, o in ipairs(getAllObjects()) do
  local nm = o.getName()
  if string.find(nm, "Планшет: ", 1, true) == 1 then
    local color = string.sub(nm, string.len("Планшет: ") + 1)
    for _, m in ipairs(getAllObjects()) do
      if m.getName() == "Голод (" .. color .. ")" then
        local a, b = o.getPosition(), m.getPosition()
        local d = (a.x - b.x) ^ 2 + (a.z - b.z) ^ 2
        if d < bestD then best, bestD, bestColor = o, d, color end
      end
    end
  end
end
if best == nil then broadcastToAll("Не нашёл планшет с маркерами.", {1, 0.5, 0.4}) return end
local function r(v) return tostring(math.floor(v * 100 + 0.5) / 100) end
local bp = best.getPosition()
local out = {}
local dice = 0
for _, o in ipairs(getAllObjects()) do
  local nm = o.getName()
  local label = nil
  if nm == "Кубик " .. bestColor then
    dice = dice + 1
    label = "D" .. dice
  else
    for _, mk in ipairs(MARKERS) do
      if nm == mk .. " (" .. bestColor .. ")" then label = mk end
    end
  end
  if label ~= nil then
    local p = o.getPosition()
    table.insert(out, label .. "=" .. r(p.x - bp.x) .. "," .. r(p.z - bp.z))
  end
end
local sz = best.getBounds().size
print("РАСКЛАДКА " .. bestColor .. " rot=" .. r(best.getRotation().y) .. " size=" .. r(sz.x) .. "x" .. r(sz.z) .. " " .. table.concat(out, " "))
broadcastToAll("Раскладка считана, смотри окно моста.", {0.78, 0.88, 0.29})
