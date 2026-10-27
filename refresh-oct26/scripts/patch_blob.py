#!/usr/bin/env python3
"""Utilities to replace a `const NAME = {...}` / `[...]` blob inside template.html,
matching braces outside strings. Importable; also runnable:
  patch_blob.py <template> <NAME> <json-file>   -- replace NAME's blob with the JSON file's content
"""
import json, sys

def find_blob(tpl, name):
    for anchor in (f'const {name} = ', f'const {name} =', f'const {name}      = '):
        i = tpl.find(anchor)
        if i >= 0: break
    else:
        raise KeyError(name)
    j = i + len(anchor)
    while tpl[j] in ' \t': j += 1
    open_c = tpl[j]; close_c = {'{':'}','[':']'}[open_c]
    depth = 0; instr = False; escp = False
    k = j
    while True:
        ch = tpl[k]
        if instr:
            if escp: escp = False
            elif ch == '\\': escp = True
            elif ch == '"': instr = False
        else:
            if ch == '"': instr = True
            elif ch == open_c: depth += 1
            elif ch == close_c:
                depth -= 1
                if depth == 0: return j, k + 1
        k += 1

def replace_blob(tpl, name, obj):
    a, b = find_blob(tpl, name)
    return tpl[:a] + json.dumps(obj, ensure_ascii=False, separators=(',', ':')) + tpl[b:]

def get_blob(tpl, name):
    a, b = find_blob(tpl, name)
    return json.loads(tpl[a:b])

if __name__ == '__main__':
    t, name, jf = sys.argv[1:4]
    tpl = open(t, encoding='utf-8').read()
    obj = json.load(open(jf))
    out = replace_blob(tpl, name, obj)
    open(t, 'w', encoding='utf-8').write(out)
    print(f'replaced {name} ({len(json.dumps(obj))} bytes)')
