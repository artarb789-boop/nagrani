-- Замер раскладки всех планшетов (запуск 3)
local function r(v) return tostring(math.floor(v * 100 + 0.5) / 100) end
local NAMES = {"Голод", "Жажда", "Здоровье", "Фокус", "Изменение"}
for _, b in ipairs(getAllObjects()) do
  local bn = b.getName()
  if string.find(bn, "Планшет: ", 1, true) == 1 then
    local color = string.sub(bn, string.len("Планшет: ") + 1)
    local p = b.getPosition()
    local out, dice = {}, {}
    for _, o in ipairs(getAllObjects()) do
      local nm = o.getName()
      local q = o.getPosition()
      if nm == "Кубик " .. color then table.insert(dice, r(q.x - p.x) .. "," .. r(q.z - p.z)) end
      for _, mk in ipairs(NAMES) do
        if nm == mk .. " (" .. color .. ")" then table.insert(out, mk .. "=" .. r(q.x - p.x) .. "," .. r(q.z - p.z)) end
      end
    end
    print("ЗАМЕР " .. color .. " scale=" .. r(b.getScale().x) .. " size=" .. r(b.getBounds().size.x) .. "x" .. r(b.getBounds().size.z)
      .. " | " .. table.concat(out, " ") .. " | кубики " .. table.concat(dice, " "))
  end
end
broadcastToAll("Замер готов, смотри окно моста.", {0.78, 0.88, 0.29})
