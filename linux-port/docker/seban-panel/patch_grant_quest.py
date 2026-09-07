from pathlib import Path

p = Path(__file__).with_name('web_admin.quest')
text = p.read_text(encoding='utf-8')
anchor = '\t' * 8 + 'if cmd == "ITEM" then'
replacement = '''if cmd == "RIDER_CHECK" then
    result = "done"
elseif cmd == "RIDER_ITEM" then
    local vnum = tonumber(arg1)
    if vnum == nil or vnum < 1 or vnum > 2147483647 or vnum ~= math.floor(vnum) then
        result = "bad_args"
    elseif pc.get_skill_level(130) < 1 then
        result = "no_skill"
    elseif pc.count_item(vnum) > 0 then
        result = "has_item"
    elseif not pc.enough_inventory(vnum) then
        result = "full"
    else
        local item_id = pc.give_item2(vnum, 1)
        if item_id == nil or item_id == 0 or pc.count_item(vnum) < 1 then
            result = "failed"
        end
    end
elseif cmd == "ITEM" then'''
assert text.count(anchor) == 1
text = text.replace(anchor, '\n'.join('\t' * 8 + line for line in replacement.splitlines()))
old = '''if result ~= "done" then
									if result ~= "bad_args" then
										result = "unknown_cmd"
									end
								end'''
new = '''if result ~= "done" and result ~= "bad_args" and result ~= "no_skill" and result ~= "has_item" and result ~= "full" and result ~= "failed" then
									result = "unknown_cmd"
								end'''
assert old in text
p.write_text(text.replace(old, new), encoding='utf-8', newline='\n')
