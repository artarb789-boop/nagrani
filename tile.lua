
local value = nil

-- Стол: большая заблокированная поверхность, подгоняется под TABLE_SIZE x TABLE_SIZE, верх на высоте 0.95
function fitTable()
  local t = getObjectFromGUID(TABLE)
  if t == nil then return end
  t.interactable = false
  local size = t.getBounds().size
  if size.x > 0 and math.abs(size.x - TABLE_SIZE) > 0.5 then
    local sc = t.getScale()
    local k = TABLE_SIZE / size.x
    t.setScale({sc.x * k, sc.y, sc.z * k})
  end
  local b = t.getBounds()
  local pos = t.getPosition()
  t.setPosition({pos.x, pos.y + (0.95 - (b.center.y + b.size.y / 2)), pos.z})
end

function onLoad(state)
  fitTable()
  if state ~= nil and state ~= "" then value = tonumber(state) end
  if value == nil then
    local ok, d = pcall(function() return JSON.decode(self.getGMNotes()) end)
    if ok and d ~= nil and d.zap ~= nil then value = d.zap else value = 0 end
  end
  Wait.frames(draw, 2)
end

function onSave() return tostring(value) end

function noop() end
function plus() value = value + 1; draw() end
function minus() if value > 0 then value = value - 1 end; draw() end

function draw()
  self.clearButtons()
  local b = self.getBounds()
  local s = self.getScale()
  local h = (b.size.x / s.x) / 2
  if h <= 0 then h = 1 end
  local z = h * 0.80
  local sc = {h * 0.22, 1, h * 0.22}
  local sides = {
    {y = 0.2,  rot = {0, 0, 0},   dir = -1},
    {y = -0.2, rot = {0, 0, 180}, dir = 1},
  }
  for _, sd in ipairs(sides) do
    local x0 = sd.dir * h * 0.52
    local step = sd.dir * h * 0.20
    self.createButton({click_function = "minus", function_owner = self, label = "−",
      position = {x0, sd.y, z}, rotation = sd.rot, width = 380, height = 380, font_size = 320,
      scale = sc, color = {0.12, 0.12, 0.1}, font_color = {0.93, 0.91, 0.86}, tooltip = "Запас −1"})
    self.createButton({click_function = "noop", function_owner = self, label = tostring(value),
      position = {x0 + step, sd.y, z}, rotation = sd.rot, width = 420, height = 380, font_size = 320,
      scale = sc, color = {0.81, 0.9, 0.63}, font_color = {0.1, 0.12, 0.05}, tooltip = "Запас тайла"})
    self.createButton({click_function = "plus", function_owner = self, label = "+",
      position = {x0 + step * 2, sd.y, z}, rotation = sd.rot, width = 380, height = 380, font_size = 320,
      scale = sc, color = {0.12, 0.12, 0.1}, font_color = {0.93, 0.91, 0.86}, tooltip = "Запас +1"})
  end
end
