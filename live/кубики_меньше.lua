-- Уменьшает все кубики на столе на 20% (запуск 1)
local n = 0
for _, o in ipairs(getAllObjects()) do
  if o.tag == "Dice" then
    local s = o.getScale()
    o.setScale({s.x * 0.8, s.y * 0.8, s.z * 0.8})
    n = n + 1
  end
end
broadcastToAll("Кубики уменьшены: " .. n, {0.78, 0.88, 0.29})
