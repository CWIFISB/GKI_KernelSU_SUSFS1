#!/usr/bin/env python3
"""TracerPid 隐藏，采用 dev-dcs 已验证的自包含写法。

原型：dev-dcs/New-GKI-Dev_DcS-Way kernel-patches/hardening/0001-proc-hide-tracerpid.patch
  1) 文件内 static 标志，不引用任何外部符号，任何变体都能链接；
  2) task_state() 里 `if (hide_tracerpid) tpid = 0;` 就地清零。
本实现差异：默认值 1（开机即生效），且不注册 sysctl，避免多出原厂没有的
/proc/sys/kernel/hide_tracerpid 节点。
"""
import sys

p = sys.argv[1]
s = open(p, encoding='utf-8', errors='surrogateescape').read()

MARK = 'proc_hide_tracerpid'

if MARK in s:
    print('already patched ->', p)
    sys.exit(0)

decl_anchor = 'static inline void task_state(struct seq_file *m, struct pid_namespace *ns,\n'
if decl_anchor not in s:
    sys.exit('ERROR: task_state anchor missing in ' + p)

decl = (
    '/* ' + MARK + ': 1 = TracerPid 恒报 0（默认开启，不注册 sysctl 节点） */\n'
    'static int hide_tracerpid __read_mostly = 1;\n'
    '\n'
)
s = s.replace(decl_anchor, decl + decl_anchor, 1)

use_anchor = '\tseq_put_decimal_ull(m, "\\nTracerPid:\\t", tpid);\n'
if use_anchor not in s:
    sys.exit('ERROR: TracerPid anchor missing in ' + p)

use = (
    '\tif (hide_tracerpid)\n'
    '\t\ttpid = 0;\n'
)
s = s.replace(use_anchor, use + use_anchor, 1)

open(p, 'w', encoding='utf-8', errors='surrogateescape').write(s)
print('injected ' + MARK + ' ->', p)