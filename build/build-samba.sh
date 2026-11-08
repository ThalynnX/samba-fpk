#!/bin/bash
### 本地复现构建：./build/build-samba.sh <版本> <工作目录>
### 产物：<工作目录>/stage/usr/local/samba
set -euo pipefail
VER="${1:-4.25.1}"
WORK="${2:-/tmp/samba-build}"
PREFIX=/usr/local/samba

mkdir -p "${WORK}/src"
cd "${WORK}/src"
if [ ! -f "samba-${VER}.tar.gz" ]; then
  curl -fSL --connect-timeout 20 --max-time 600 \
    "https://download.samba.org/pub/samba/stable/samba-${VER}.tar.gz" -o "samba-${VER}.tar.gz"
fi
[ -d "samba-${VER}" ] || tar -xzf "samba-${VER}.tar.gz"

cd "samba-${VER}"
./configure --prefix=${PREFIX} \
  --localstatedir=${PREFIX}/var --with-configdir=${PREFIX}/etc \
  --with-lockdir=${PREFIX}/var/lock --with-piddir=${PREFIX}/var/run \
  --with-privatedir=${PREFIX}/private --with-logfilebase=${PREFIX}/var/log \
  --without-ad-dc --without-ads --without-gpgme --enable-selftest=no \
  --disable-cups --disable-avahi
make -j"$(nproc)"
rm -rf "${WORK}/stage"
make install DESTDIR="${WORK}/stage"
echo "完成：${WORK}/stage${PREFIX}"
