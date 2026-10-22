
local value = nil

function onLoad(state)
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
  local z = h * 0.58
  local sc = {h * 0.2, 1, h * 0.2}
  local sd = {y = 0.2, rot = {0, 0, 0}}
  do
    local x0 = h * 0.2
    local step = -h * 0.2
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
