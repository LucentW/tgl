/* 
    This file is part of tgl-library

    This library is free software; you can redistribute it and/or
    modify it under the terms of the GNU Lesser General Public
    License as published by the Free Software Foundation; either
    version 2.1 of the License, or (at your option) any later version.

    This library is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
    Lesser General Public License for more details.

    You should have received a copy of the GNU Lesser General Public
    License along with this library; if not, write to the Free Software
    Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA

    Copyright Ben Wiederhake 2015
*/

#include "../config.h"

#ifndef TGL_AVOID_OPENSSL

#include <openssl/sha.h>
#include <openssl/evp.h>

#include "sha.h"

void TGLC_sha1 (const unsigned char *d, size_t n, unsigned char *md) {
  SHA1 (d, n, md);
}
void TGLC_sha256 (const unsigned char *d, size_t n, unsigned char *md) {
  SHA256 (d, n, md);
}
void TGLC_sha256_two (const unsigned char *d1, size_t n1,
                      const unsigned char *d2, size_t n2,
                      unsigned char *md) {
  EVP_MD_CTX *ctx = EVP_MD_CTX_new ();
  EVP_DigestInit_ex (ctx, EVP_sha256 (), NULL);
  EVP_DigestUpdate (ctx, d1, n1);
  EVP_DigestUpdate (ctx, d2, n2);
  unsigned int outlen = 32;
  EVP_DigestFinal_ex (ctx, md, &outlen);
  EVP_MD_CTX_free (ctx);
}

#endif
