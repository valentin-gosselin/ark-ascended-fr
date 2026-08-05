#!/usr/bin/env bash
# Compile ooz, decompresseur Oodle libre (github.com/powzix/ooz), en libooz.so.
#
# Oodle est propriétaire et non redistribuable : le depot n'en contient pas.
# ooz en est une reimplementation independante ; sur le pak d'ARK elle produit
# un resultat identique au bit pres a la bibliotheque officielle (verifie).
#
# Le code amont ne compile que sous MSVC : on lui fournit un stdafx portable et
# on ecarte son outil en ligne de commande, qui charge la DLL Windows d'Oodle.
set -euo pipefail
DEST="${1:-$(cd "$(dirname "$0")" && pwd)/libooz.so}"
TRAVAIL="$(mktemp -d)"
trap 'rm -rf "$TRAVAIL"' EXIT

git clone -q --depth 1 https://github.com/powzix/ooz.git "$TRAVAIL/ooz"
cd "$TRAVAIL/ooz"

cat > stdafx.h <<'EOF'
#pragma once
#define _CRT_SECURE_NO_WARNINGS 1
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <assert.h>
#include <stdint.h>
#include <x86intrin.h>
typedef uint8_t  byte;
typedef uint8_t  uint8;
typedef uint16_t uint16;
typedef uint32_t uint32;
typedef uint64_t uint64;
typedef int8_t   int8;
typedef int16_t  int16;
typedef int32_t  int32;
typedef int64_t  int64;
#define _rotl(x, n)   (((x) << (n)) | ((x) >> (32 - (n))))
#define _rotr(x, n)   (((x) >> (n)) | ((x) << (32 - (n))))
#define _byteswap_ushort(x) __builtin_bswap16(x)
#define _byteswap_ulong(x)  __builtin_bswap32(x)
#define _byteswap_uint64(x) __builtin_bswap64(x)
#define _BitScanReverse(i, m)  (*(i) = 31 - __builtin_clz(m), (m) != 0)
#define _BitScanForward(i, m)  (*(i) = __builtin_ctz(m), (m) != 0)
#define __forceinline inline __attribute__((always_inline))
EOF

# la partie CLI (chargement de la DLL Windows) commence a la declaration
# OodLZ_CompressFunc : on ne garde que ce qui precede
COUPE=$(grep -n "typedef int WINAPI OodLZ_CompressFunc" kraken.cpp | cut -d: -f1)
head -n "$((COUPE - 1))" kraken.cpp > kraken_lib.cpp
cat >> kraken_lib.cpp <<'EOF'
extern "C" int Ooz_Decompress(const byte *src, size_t src_len, byte *dst, size_t dst_len) {
  return Kraken_Decompress(src, src_len, dst, dst_len);
}
EOF

g++ -std=c++17 -O2 -fPIC -shared -msse4.1 -o "$DEST" kraken_lib.cpp lzna.cpp bitknit.cpp
echo "libooz.so construit : $DEST"
