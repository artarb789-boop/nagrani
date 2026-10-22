-- Замер планшета и маркеров (запуск 1)
local function r(v) return tostring(math.floor(v * 100 + 0.5) / 100) end
for _, o in ipairs(getAllObjects()) do
  local nm = o.getName()
  if string.find(nm, "Планшет: ", 1, true) == 1 then
    local color = string.sub(nm, string.len("Планшет: ") + 1)
    local bp, sz = o.getPosition(), o.getBounds().size
    local out = {}
    for _, m in ipairs(getAllObjects()) do
      local mn = m.getName()
      if mn ~= nm and string.find(mn, color, 1, true) and m.tag ~= "Dice" and string.find(mn, "Выживший", 1, true) == nil then
        local p = m.getPosition()
        table.insert(out, mn .. "=" .. r(p.x - bp.x) .. "," .. r(p.z - bp.z))
      end
    end
    print("ЗАМЕР " .. color .. " pos=" .. r(bp.x) .. "," .. r(bp.z) .. " size=" .. r(sz.x) .. "x" .. r(sz.z) .. " scale=" .. r(o.getScale().x) .. " | " .. table.concat(out, " "))
  end
end
broadcastToAll("Замер готов, смотри окно моста.", {0.78, 0.88, 0.29})
