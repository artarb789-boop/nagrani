-- Ставит планшеты в масштаб 0.394 и раскладывает кубики и маркеры (запуск 2)
local W, H = 17.45, 7.2
local DICE_X = {-4.5, -3.5, -2.5, -1.5, -0.5, 0.5}
local MARKS = {{"Голод", -0.348, 0.104}, {"Жажда", -0.348, -0.004}, {"Здоровье", -0.1295, -0.114},
               {"Фокус", -0.1295, -0.222}, {"Изменение", -0.45, -0.3945}}
for _, b in ipairs(getAllObjects()) do
  local bn = b.getName()
  if string.find(bn, "Планшет: ", 1, true) == 1 then
    b.setScale({0.394, 0.394, 0.394})
    local color = string.sub(bn, string.len("Планшет: ") + 1)
    local p = b.getPosition()
    local i = 0
    for _, o in ipairs(getAllObjects()) do
      local nm = o.getName()
      if nm == "Кубик " .. color then
        i = i + 1
        if DICE_X[i] ~= nil then o.setPosition({p.x + DICE_X[i], 2, p.z + H / 2 + 1.4}) end
      end
      for _, mk in ipairs(MARKS) do
        if nm == mk[1] .. " (" .. color .. ")" then
          o.setPosition({p.x + mk[2] * W, 2, p.z + mk[3] * H})
        end
      end
    end
  end
end
broadcastToAll("Планшеты и маркеры на местах.", {0.78, 0.88, 0.29})
