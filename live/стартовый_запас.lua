-- Кладёт в общий запас по 2 еды и 2 воды на каждого выжившего (запуск 1)
local n = 0
for _, o in ipairs(getAllObjects()) do
  local name = o.getName() or ""
  if string.find(name, "Планшет:", 1, true) then n = n + 1 end
end
if n == 0 then
  broadcastToAll("Сначала выбери число игроков: планшетов на столе нет.", {1, 0.5, 0.4})
  return
end
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
broadcastToAll("В общий запас: " .. (2 * n) .. " еды и " .. (2 * n) .. " воды на " .. n .. " выживших.", {0.78, 0.88, 0.29})
