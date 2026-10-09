-- lazy-images.lua
-- Adds lazy loading and async decoding to every image, drops fixed
-- width and height attributes, and makes the image fluid.

function Image(img)
  local attrs = img.attributes
  if attrs["loading"] == nil then
    attrs["loading"] = "lazy"
  end
  if attrs["decoding"] == nil then
    attrs["decoding"] = "async"
  end
  attrs["width"] = nil
  attrs["height"] = nil
  local has_fluid = false
  for _, c in ipairs(img.classes) do
    if c == "img-fluid" then has_fluid = true end
  end
  if not has_fluid then
    img.classes:insert("img-fluid")
  end
  if attrs["style"] == nil then
    attrs["style"] = "max-width: 100%;"
  end
  return img
end
