#!/usr/bin/env python3
"""TracerPid 只对同 uid 的 tracer 显示。

参照 rev1si0n/android_kernel_oneplus_msm8998 的 fs/proc/array.c：
  tracer = ptrace_parent(p);
  if (tracer && (get_task_uid(tracer) == get_task_uid(p)))
      tpid = task_pid_nr_ns(tracer, ns);
即 root/frida/gdb 等跨 uid 附加时 TracerPid 恒为 0，同 uid 调试仍可见。
不搬它的 State 三元改写（会把所有进程的 State 固定成 R (running)）。
幂等；锚点缺失即报错退出。
"""
import sys

p = sys.argv[1]
s = open(p, encoding='utf-8', errors='surrogateescape').read()

MARK = 'susfs_get_task_uid'

if MARK in s:
    print('already patched ->', p)
    sys.exit(0)

# 1) 辅助函数：紧跟 #include "internal.h"
inc_anchor = '#include "internal.h"\n'
if inc_anchor not in s:
    sys.exit('ERROR: internal.h anchor missing in ' + p)

helper = (
    '\n'
    '/* ' + MARK + ': 取 task 的真实 uid，用于 TracerPid 同源判定 */\n'
    'static inline uid_t ' + MARK + '(struct task_struct *task)\n'
    '{\n'
    '\tuid_t uid = 0;\n'
    '\tconst struct cred *cred;\n'
    '\n'
    '\tcred = get_task_cred(task);\n'
    '\tuid = cred->uid.val;\n'
    '\n'
    '\tput_cred(cred);\n'
    '\treturn uid;\n'
    '}\n'
)
s = s.replace(inc_anchor, inc_anchor + helper, 1)

# 2) TracerPid 判定：只对同 uid 的 tracer 报告
use_anchor = '\ttracer = ptrace_parent(p);\n\tif (tracer)\n'
if use_anchor not in s:
    sys.exit('ERROR: ptrace_parent anchor missing in ' + p)

use_new = (
    '\ttracer = ptrace_parent(p);\n'
    '\t/* ' + MARK + ': 跨 uid 的 tracer（root/frida/gdb）不报告 */\n'
    '\tif (tracer && (' + MARK + '(tracer) == ' + MARK + '(p)))\n'
)
s = s.replace(use_anchor, use_new, 1)

open(p, 'w', encoding='utf-8', errors='surrogateescape').write(s)
print('injected ' + MARK + ' ->', p)