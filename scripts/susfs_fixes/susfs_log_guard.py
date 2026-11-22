#!/usr/bin/env python3
"""补全 susfs.c 的 #else 空宏分支。

关闭 CONFIG_KSU_SUSFS_ENABLE_LOG 后，上游 susfs.c 的 #else 只定义了
SUSFS_LOGI / SUSFS_LOGE，漏掉 SUSFS_LOGI_RL / SUSFS_LOGE_RL，
导致 -Werror=implicit-function-declaration 编译失败。此处补齐为无副作用空宏。
幂等；锚点缺失即报错退出。
"""
import sys

p = sys.argv[1]
s = open(p, encoding='utf-8', errors='surrogateescape').read()

MARK = 'susfs_log_guard'

if MARK in s:
    print('already patched ->', p)
    sys.exit(0)

anchor = '#else\n#define SUSFS_LOGI(fmt, ...) \n#define SUSFS_LOGE(fmt, ...) \n'
if anchor not in s:
    # 兼容行尾空格差异
    alt = '#else\n#define SUSFS_LOGI(fmt, ...)\n#define SUSFS_LOGE(fmt, ...)\n'
    if alt in s:
        anchor = alt
    else:
        sys.exit('ERROR: susfs.c log macro #else anchor missing in ' + p)

if anchor.endswith('\n') and 'SUSFS_LOGI_RL' in anchor:
    sys.exit('ERROR: unexpected anchor content in ' + p)

insert = (
    anchor
    + '/* ' + MARK + ': 补齐空宏分支，避免关闭 ENABLE_LOG 后隐式声明报错 */\n'
    + '#define SUSFS_LOGI_RL(fmt, ...)\n'
    + '#define SUSFS_LOGE_RL(fmt, ...)\n'
)
s = s.replace(anchor, insert, 1)

open(p, 'w', encoding='utf-8', errors='surrogateescape').write(s)
print('injected ' + MARK + ' ->', p)