# samba-fpk — 飞牛 fnOS 原生 Samba 打包工程

上游源码：[samba-team/samba](https://github.com/samba-team/samba)（GPL-3.0-or-later）
维护者：ThalynnX · leo@jiuyuewl.cn
目标设备：飞牛 fnOS / ARM64（RK3566 等 aarch64 机型）

每次构建：`GitHub Actions` 在 **ARM64 原生 runner** 上编译 Samba，再由 fnpack 打成飞牛原生 `.fpk`，发布到 Release。**每周一 03:00 UTC（北京时间 11:00）自动跑一次**，也可手动触发。

---

## 这个仓库解决什么

你的 NAS 自带 Samba，但版本是飞牛定制的 Debian 包。本仓库让上游最新版 Samba 能在你的设备上以**独立应用**的形式跑起来：

| 项 | 系统自带 | 本包 |
|---|---|---|
| 版本 | 4.22.10（随系统更新） | 跟随上游（当前 4.25.1） |
| 端口 | 445 | **默认 1445**（不与系统冲突） |
| 配置 | fnOS 面板托管 | 本应用 `etc/smb.conf` 托管 |
| 卸载 | — | 不影响系统共享 |
| 更新节奏 | 随 fnOS 版本 | **每 7 天自动跟随上游重新构建** |

## 为什么不直接替换 445

445 端口同一时刻只能被一个进程监听。系统自带 smbd 由飞牛面板托管，如果本包抢占 445：

- 应用启动直接失败（端口占用）
- 面板里的共享管理、用户权限会失效

所以本包**默认跑 1445 端口并行工作**。确认新版本稳定后，如果你确实想接管 445：

1. fnOS 面板 → 文件共享 → 停用 SMB
2. 本应用控制台 → 运行参数 → 端口改 445 → 保存（自动重启）
3. Windows 侧直接 `\\NAS` 访问

> 注意：接管 445 后，面板里的共享设置不再生效，共享全部由本应用的 `smb.conf` 决定。

## 安装后三步

1. 应用中心打开「Samba 文件共享」控制台
2. **添加 SMB 账号**（用户名必须是系统已存在的用户，例如 `root` 或你的飞牛账号）
3. 改共享目录（默认 `/vol1`）→ 保存

Windows 访问：`\\NAS地址:1445\shared`

## 仓库结构

```
manifest                     # FPK 清单（包名 com.thalynnx.samba）
.github/workflows/build-fpk.yml   # 编译 + 打包流水线（ARM64 原生编译）
cmd/                         # 生命周期脚本：install / start / stop / config / upgrade / uninstall
wizard/                      # 安装向导文案
config/                      # 权限（run-as root）与数据授权
app/ui/index.cgi             # 控制台：状态、账号、端口、目录、日志
app/samba/prefix/            # 编译产物落地位置（CI 构建时生成，不入库）
build/                       # 本地复现构建脚本
```

## 本地复现构建（可选）

需要一台 aarch64 Linux（或 qemu binfmt）：

```bash
./build/build-samba.sh 4.25.1 /tmp/samba-build
```

产物在 `/tmp/samba-build/stage/usr/local/samba`，放到 `app/samba/prefix/` 后用 fnpack 打包。

## 手动触发构建

```bash
gh workflow run build-fpk.yml -R ThalynnX/samba-fpk
gh run watch -R ThalynnX/samba-fpk
```

## 许可

- `/cmd`、`/build`、`/app/ui` 等打包脚本：MIT
- 编译进 FPK 的 Samba 本体：GPL-3.0-or-later（随包提供源码链接与版本号）
