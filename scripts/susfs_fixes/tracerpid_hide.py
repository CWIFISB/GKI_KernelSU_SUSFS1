#!/usr/bin/env python3
"""向 fs/proc/array.c 注入 TracerPid 隐藏（SUSFS 域）。幂等，失败即报错退出。"""
import sys

p = sys.argv[1]
s = open(p, encoding='utf-8', errors='surrogateescape').read()

if 'susfs_tracerpid_hide' in s:
    print('already patched ->', p)
    sys.exit(0)

inc_anchor = '#include "internal.h"\n'
if inc_anchor not in s:
    sys.exit('ERROR: include anchor missing in ' + p)

inc_patch = (
    inc_anchor
    + '#ifdef CONFIG_KSU_SUSFS\n'
    + '/* susfs_tracerpid_hide */\n'
    + 'extern bool susfs_is_current_ksu_domain(void);\n'
    + '#endif\n'
)
s = s.replace(inc_anchor, inc_patch, 1)

fn_anchor = '\ttracer = ptrace_parent(p);\n'
if fn_anchor not in s:
    sys.exit('ERROR: ptrace_parent anchor missing in ' + p)

fn_patch = (
    fn_anchor
    + '#ifdef CONFIG_KSU_SUSFS\n'
    + '\t/* susfs_tracerpid_hide: 非 su 域读者看到的 TracerPid 恒为 0 */\n'
    + '\tif (tracer && !susfs_is_current_ksu_domain())\n'
    + '\t\ttracer = NULL;\n'
    + '#endif\n'
)
s = s.replace(fn_anchor, fn_patch, 1)

open(p, 'w', encoding='utf-8', errors='surrogateescape').write(s)
print('injected TracerPid hide ->', p)
