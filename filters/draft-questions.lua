-- draft-questions.lua
-- Authors list the questions a section must answer in an HTML comment:
--
--   <!-- Q
--   - First question?
--   - Second question?
--   -->
--
-- Pandoc reads that comment as a raw HTML block. In a normal render it
-- stays an invisible comment. When the metadata flag draft-questions is
-- true (set by the draft profile), each block becomes a collapsed tip
-- callout with a numbered list.

local show = false

local function read_meta(meta)
  local flag = meta["draft-questions"]
  if flag == true then
    show = true
  elseif type(flag) == "table" and pandoc.utils.stringify(flag) == "true" then
    show = true
  end
end

local function questions_from(text)
  if not text:match("^%s*<!%-%-%s*Q%s*\n") then
    return nil
  end
  local items = {}
  for line in text:gmatch("[^\n]+") do
    local q = line:match("^%s*%-%s+(.+)$")
    if q then
      table.insert(items, { pandoc.Plain(pandoc.Inlines(pandoc.read(q, "markdown").blocks[1].content)) })
    end
  end
  return items
end

local function replace_block(el)
  if not show then return nil end
  if el.format ~= "html" then return nil end
  local items = questions_from(el.text)
  if items == nil or #items == 0 then return nil end
  return quarto.Callout({
    type = "tip",
    title = "Questions this section must answer (draft)",
    collapse = true,
    content = { pandoc.OrderedList(items) },
  })
end

return {
  { Meta = read_meta },
  { RawBlock = replace_block },
}
