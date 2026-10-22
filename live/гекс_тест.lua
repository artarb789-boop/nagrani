-- Тест гекса: выкладывает пробный шестиугольный тайл и сообщает его размеры (запуск 3)
local o = spawnObject({type = "Custom_Tile", position = {0, 3, -4}, rotation = {0, 180, 0}, scale = {3, 1, 3}})
o.setCustomObject({image = "file:///C:/NaGrani/images/hex_test.png", type = 1, thickness = 0.2, stretch = true})
o = o.reload()
o.setName("Тест гекса")
Wait.time(function()
  local t = getObjectFromGUID(o.getGUID()) or o
  local b = t.getBounds().size
  print("ГЕКС ширина x=" .. tostring(math.floor(b.x * 100 + 0.5) / 100) .. " глубина z=" .. tostring(math.floor(b.z * 100 + 0.5) / 100))
end, 2)
broadcastToAll("Тестовый гекс выложен рядом с Лагерем.", {0.78, 0.88, 0.29})
