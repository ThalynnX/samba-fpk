#!/bin/bash

### Samba 控制台（CGI）
### GET  : 状态页
### POST : adduser / setport / setpath / restart / start / stop

APP_ID="com.thalynnx.samba"
PREFIX="/var/apps/${APP_ID}/target/samba/prefix"
VAR="/var/apps/${APP_ID}/var"
ETC="/var/apps/${APP_ID}/etc"
CONF="${ETC}/smb.conf"
PIDF="${VAR}/pids/smbd.pid"
LOGDIR="${VAR}/log"

get_pid() { [ -f "$PIDF" ] && head -n 1 "$PIDF" | tr -d '[:space:]'; }
is_running() { local p; p="$(get_pid)"; [ -n "$p" ] && kill -0 "$p" 2>/dev/null; }
cport() { grep -E '^[[:space:]]*smb ports[[:space:]]*=' "$CONF" 2>/dev/null | tail -1 | sed -E 's/.*=[[:space:]]*([0-9]+).*/\1/'; }
cpath() { awk '/^\[shared\]/{f=1;next}/^\[/{f=0}f&&/^[[:space:]]*path[[:space:]]*=/{print $0;exit}' "$CONF" 2>/dev/null | sed -E 's/.*=[[:space:]]*//'; }

urldecode() { printf '%b' "${1//%/\\x}"; }

msg=""
if [ "$REQUEST_METHOD" = "POST" ]; then
    LEN="${CONTENT_LENGTH:-0}"
    BODY="$(head -c "${LEN}" 2>/dev/null)"
    ACTION="$(echo "$BODY" | tr '&' '\n' | grep '^action=' | head -1 | cut -d= -f2-)"
    USER_="$(echo "$BODY" | tr '&' '\n' | grep '^user=' | head -1 | cut -d= -f2- | sed 's/+/ /g')"
    PASS_="$(echo "$BODY" | tr '&' '\n' | grep '^pass=' | head -1 | cut -d= -f2- | sed 's/+/ /g')"
    PORT_="$(echo "$BODY" | tr '&' '\n' | grep '^port=' | head -1 | cut -d= -f2-)"
    PATH_="$(echo "$BODY" | tr '&' '\n' | grep '^path=' | head -1 | cut -d= -f2- | sed 's/+/ /g')"

    case "$ACTION" in
        restart) bash /var/apps/${APP_ID}/target/cmd/main restart >/dev/null 2>&1; msg="已重启" ;;
        start)   bash /var/apps/${APP_ID}/target/cmd/main start   >/dev/null 2>&1; msg="已启动" ;;
        stop)    bash /var/apps/${APP_ID}/target/cmd/main stop    >/dev/null 2>&1; msg="已停止" ;;
        adduser)
            if [ -n "$USER_" ] && [ -n "$PASS_" ]; then
                out=$(printf '%s\n%s\n' "$PASS_" "$PASS_" | "${PREFIX}/bin/smbpasswd" -s -a "$USER_" 2>&1)
                msg="账号 ${USER_} 已添加（需重启生效）：${out:-ok}"
            else
                msg="用户名或密码为空"
            fi ;;
        setport)
            if echo "$PORT_" | grep -qE '^[0-9]+$'; then
                sed -i -E "s#^(\s*smb ports\s*=\s*)[0-9]+#\1${PORT_}#" "$CONF"
                bash /var/apps/${APP_ID}/target/cmd/main restart >/dev/null 2>&1
                msg="端口已改为 ${PORT_} 并重启"
            else
                msg="端口非法"
            fi ;;
        setpath)
            if [ -n "$PATH_" ]; then
                awk -v p="$PATH_" '/^\[shared\]/{s=1} /^\s*path\s*=/{if(s){sub(/path\s*=.*/,"path = " p)}} {print}' "$CONF" > "$CONF.tmp" && mv "$CONF.tmp" "$CONF"
                bash /var/apps/${APP_ID}/target/cmd/main restart >/dev/null 2>&1
                msg="共享目录已改为 ${PATH_} 并重启"
            else
                msg="目录为空"
            fi ;;
        *) msg="未知操作" ;;
    esac
fi

status="已停止"; cls="stopped"; badge="Inactive"
if is_running; then status="运行中"; cls="running"; badge="Active"; fi
pid="$(get_pid)"; [ -z "$pid" ] && pid="--"
port="$(cport)"; [ -z "$port" ] && port="1445"
sharepath="$(cpath)"; [ -z "$sharepath" ] && sharepath="/vol1"
ver="$("${PREFIX}/sbin/smbd" --version 2>/dev/null | sed -E 's/Version //')"
[ -z "$ver" ] && ver="unknown"

echo "Content-Type: text/html; charset=utf-8"
echo ""
cat <<HTMLEOF
<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Samba 控制台</title>
<style>
:root{--bg:#f5f7fa;--card:#fff;--bd:#e8ecf0;--tx:#1f2937;--t2:#6b7280;--pri:#3b82f6;--ok:#10b981;--warn:#f59e0b}
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:-apple-system,"PingFang SC","Microsoft YaHei",sans-serif;background:var(--bg);color:var(--tx);padding:20px;line-height:1.6}
.wrap{max-width:820px;margin:0 auto}
.title{font-size:22px;font-weight:700}.sub{color:var(--t2);font-size:13px;margin-bottom:18px}
.card{background:var(--card);border:1px solid var(--bd);border-radius:12px;padding:18px;margin-bottom:14px}
.st{display:flex;justify-content:space-between;align-items:center;background:linear-gradient(135deg,#f0fdf4,#ecfdf5);border-color:#bbf7d0}
.st.stopped{background:linear-gradient(135deg,#fef2f2,#fee2e2);border-color:#fecaca}
.st h2{font-size:18px;display:flex;gap:8px;align-items:center}
.badge{font-size:12px;padding:2px 8px;border-radius:99px;background:#dcfce7;color:#166534}
.st.stopped .badge{background:#fecaca;color:#991b1b}
.grid{display:grid;grid-template-columns:repeat(3,1fr);gap:12px}
.i{background:var(--card);border:1px solid var(--bd);border-radius:12px;padding:14px}
.l{font-size:12px;color:var(--t2)}.v{font-size:17px;font-weight:600;font-family:monospace}
.btn{display:inline-block;padding:7px 14px;border-radius:8px;font-size:13px;border:0;cursor:pointer;text-decoration:none;color:#fff}
.bp{background:var(--pri)}.bw{background:var(--warn)}.bg2{background:#6b7280}
input{width:100%;padding:7px 10px;border:1px solid var(--bd);border-radius:8px;font-size:13px;margin:4px 0 10px}
label{font-size:12px;color:var(--t2)}
.row{display:flex;gap:10px}.row>div{flex:1}
.alert{background:#dcfce7;color:#166534;padding:10px 14px;border-radius:8px;margin-bottom:14px;font-size:13px}
pre{background:#0f172a;color:#e2e8f0;padding:12px;border-radius:8px;font-size:12px;overflow:auto;max-height:220px}
h3{font-size:15px;margin-bottom:12px}
@media(max-width:760px){.grid{grid-template-columns:1fr}}
</style></head><body><div class="wrap">
<div class="title">Samba 文件共享</div>
<div class="sub">ThalynnX 自编译 · 上游 samba-team/samba ${ver}</div>
HTMLEOF

[ -n "$msg" ] && echo "<div class=\"alert\">${msg}</div>"

cat <<HTMLEOF
<div class="card st ${cls}">
  <div><h2>服务 ${status} <span class="badge">${badge}</span></h2>
  <div class="sub">PID ${pid} · 端口 ${port}</div></div>
  <div style="display:flex;gap:8px">
    <form method="post"><input type="hidden" name="action" value="restart"><button class="btn bp">重启</button></form>
    <form method="post"><input type="hidden" name="action" value="stop"><button class="btn bg2">停止</button></form>
    <form method="post"><input type="hidden" name="action" value="start"><button class="btn bp">启动</button></form>
  </div>
</div>

<div class="grid">
  <div class="i"><div class="l">访问地址</div><div class="v">\\\\NAS:${port}\\shared</div></div>
  <div class="i"><div class="l">共享目录</div><div class="v" style="font-size:13px">${sharepath}</div></div>
  <div class="i"><div class="l">配置文件</div><div class="v" style="font-size:13px">etc/smb.conf</div></div>
</div>

<div class="card">
  <h3>添加 SMB 账号</h3>
  <form method="post">
    <input type="hidden" name="action" value="adduser">
    <div class="row">
      <div><label>用户名（须为系统已有用户，如 root 或 fnOS 用户）</label><input name="user" placeholder="leo" required></div>
      <div><label>密码</label><input name="pass" type="password" placeholder="设置 SMB 密码" required></div>
    </div>
    <button class="btn bp">添加账号</button>
  </form>
</div>

<div class="card">
  <h3>运行参数</h3>
  <form method="post">
    <input type="hidden" name="action" value="setport">
    <div class="row">
      <div><label>监听端口（默认 1445，接管系统共享请填 445 并先停用面板 SMB）</label><input name="port" value="${port}"></div>
      <div style="display:flex;align-items:flex-end"><button class="btn bw">保存端口</button></div>
    </div>
  </form>
  <form method="post">
    <input type="hidden" name="action" value="setpath">
    <div class="row">
      <div><label>共享目录</label><input name="path" value="${sharepath}"></div>
      <div style="display:flex;align-items:flex-end"><button class="btn bw">保存目录</button></div>
    </div>
  </form>
</div>

<div class="card">
  <h3>最近日志（${LOGDIR}）</h3>
  <pre>$(tail -n 20 "${LOGDIR}"/log.* "${VAR}/samba.log" 2>/dev/null | tail -n 20 | sed 's/&/\&amp;/g;s/</\&lt;/g')</pre>
</div>
</div></body></html>
HTMLEOF
exit 0
