# Dependency Inventory and Redistribution Notices: FreeRDP Build 2101

This document provides the complete dependency inventory, licensing terms, and
redistribution notices for the pinned Windows executable `sdl-freerdp.exe`
(FreeRDP Nightly build 2101) and its companion WinPR runtime distribution.

This inventory fulfills the licensing and provenance prerequisite documented in
[Durable FreeRDP downloads](freerdp-release-hosting.md) and tracked in
[freerdp-2101-candidate.json](freerdp-2101-candidate.json) for release tag
`deps-freerdp-5c8aac73c-win64-r1`.

---

## 1. Primary Artifact Identification

* **Filename**: `sdl-freerdp.exe`
* **Upstream Project**: FreeRDP ([github.com/FreeRDP/FreeRDP](https://github.com/FreeRDP/FreeRDP))
* **Version**: `3.32.3-dev0 (5c8aac73c)`
* **Source Commit**: `5c8aac73cd293d44022c5ccfe36fd6f266b17098`
* **File Size**: `16,056,320` bytes
* **SHA-256**: `0976457fbbb27b970de1aaf92a48474e1168efc3230ae271c7d0dc56e2bda2fd`
* **Upstream CI Origin**: FreeRDP Jenkins CI `freerdp-nightly-windows/arch=win64,label=vs2017/2101`
* **Compiler Toolchain**: MSVC `19.16.27045.0` (Visual Studio 2017), Target Architecture `x64`
* **Build Configuration Flags** (extracted from binary):
  ```text
  Build type:          Release
  CFLAGS:              /DWIN32 /D_WINDOWS /W3 /O2 /Ob2 /DNDEBUG
  Compiler:            MSVC, 19.16.27045.0
  Target architecture: x64
  Key features:        WITH_CLIENT=ON WITH_CLIENT_SDL=ON WITH_CLIENT_SDL3=ON
                       WITH_SDL_LINK_SHARED=OFF WITH_SDL_IMAGE_DIALOGS=ON
                       WITH_OPENSSL=ON WITH_OPUS=ON WITH_URIPARSER=ON
                       WITH_WINPR_JSON=ON WITH_SMARTCARD_PCSC=ON
                       WITH_NATIVE_SSPI=ON WITH_AVX2=ON WITH_SIMD=ON
  ```

---

## 2. Inventory of Components

The official upstream build `sdl-freerdp.exe` statically links FreeRDP, SDL3,
and their supporting audio, graphic, and cryptographic dependencies into a
single standalone binary. Dynamic imports are restricted exclusively to standard
Microsoft Windows system libraries (`KERNEL32.dll`, `USER32.dll`, `GDI32.dll`,
`IMM32.dll`, `WINMM.dll`, `ADVAPI32.dll`, `SHELL32.dll`, `ole32.dll`, etc.).

The separate WinPR build (`libwinpr3.dll`) and SSPI shim load external DLLs
from the MSYS2 MinGW-w64 distribution.

### 2.1 Statically Linked in `sdl-freerdp.exe`

| Component | Upstream Project / Origin | Version / Build Context | SPDX License ID | Linkage |
|:---|:---|:---|:---|:---|
| **FreeRDP Core & SDL Client** | [FreeRDP/FreeRDP](https://github.com/FreeRDP/FreeRDP) | `3.32.3-dev0 (5c8aac73c)` | Apache-2.0 | Static |
| **WinPR Core** | [FreeRDP/FreeRDP (winpr)](https://github.com/FreeRDP/FreeRDP/tree/master/winpr) | `5c8aac73c` | Apache-2.0 | Static |
| **SDL3** | [libsdl-org/SDL](https://github.com/libsdl-org/SDL) | 3.x (from `C:\frdp\deps\SDL`) | Zlib | Static |
| **SDL3_ttf** | [libsdl-org/SDL_ttf](https://github.com/libsdl-org/SDL_ttf) | 3.x | Zlib | Static |
| **SDL3_image** | [libsdl-org/SDL_image](https://github.com/libsdl-org/SDL_image) | 3.x (from `C:\frdp\deps\SDL_image`) | Zlib | Static |
| **OpenSSL** (embedded client crypto) | [openssl/openssl](https://github.com/openssl/openssl) | `3.6.2` (7 Apr 2026, built 2025-03-10, `VC-WIN64A`) | Apache-2.0 | Static |
| **Opus** | [xiph/opus](https://gitlab.xiph.org/xiph/opus) | CELT + SILK (from `C:\frdp\deps\opus`) | BSD-3-Clause | Static |
| **FreeType 2** | [freetype/freetype](https://gitlab.freedesktop.org/freetype/freetype) | Bundled via SDL_ttf | FTL / GPL-2.0-only | Static |
| **HarfBuzz** | [harfbuzz/harfbuzz](https://github.com/harfbuzz/harfbuzz) | Bundled via SDL_ttf | MIT | Static |
| **libtiff** | [libtiff/libtiff](https://gitlab.com/libtiff/libtiff) | >= 4.5.1 (from `SDL_image\external\libtiff`) | libtiff (BSD-like) | Static |
| **libpng** | [pnggroup/libpng](https://github.com/pnggroup/libpng) | Bundled via SDL_image | Libpng | Static |
| **zlib** | [madler/zlib](https://github.com/madler/zlib) | `1.3.1` (deflate 1.3.1) | Zlib | Static |
| **cJSON** | [DaveGamble/cJSON](https://github.com/DaveGamble/cJSON) | 1.x (FreeRDP WinPR json) | MIT | Static |
| **uriparser** | [uriparser/uriparser](https://github.com/uriparser/uriparser) | 1.x (FreeRDP URI parser) | BSD-3-Clause | Static |
| **Android cpufeatures** | Android Open Source Project | In `winpr/libwinpr/sysinfo/cpufeatures` | Apache-2.0 | Static |

### 2.2 Dynamically Loaded WinPR Runtime Companions

The bridge runtime environment includes dynamically loaded libraries produced
via `scripts/build-winpr.sh` using MSYS2 MinGW-w64 packages:

| File | Upstream Component | Version / Package | SPDX License ID | Linkage |
|:---|:---|:---|:---|:---|
| `libwinpr3.dll` | FreeRDP WinPR | Commit `5c8aac73cd293d44022c5ccfe36fd6f266b17098` | Apache-2.0 | Dynamic |
| `libcrypto-3-x64.dll` | OpenSSL Crypto | `mingw-w64-x86_64-openssl-3.6.3-1` | Apache-2.0 | Dynamic |
| `libssl-3-x64.dll` | OpenSSL SSL | `mingw-w64-x86_64-openssl-3.6.3-1` | Apache-2.0 | Dynamic |
| `ossl-modules/legacy.dll` | OpenSSL Legacy Provider | `mingw-w64-x86_64-openssl-3.6.3-1` | Apache-2.0 | Dynamic |
| `libcjson-1.dll` | cJSON | `mingw-w64-x86_64-cjson-1.7.19-1` | MIT | Dynamic |
| `liburiparser-1.dll` | uriparser | `mingw-w64-x86_64-uriparser-1.0.2-1` | BSD-3-Clause | Dynamic |
| `winpr-sspi-shim.dll` | UU Remote Bridge SSPI Shim | Local source compilation | MIT / Apache-2.0 | Dynamic |

> **Note on OpenSSL versions:** The executable `sdl-freerdp.exe` contains
> statically linked OpenSSL 3.6.2 (compiled by the upstream FreeRDP CI with
> MSVC). The accompanying WinPR runtime uses OpenSSL 3.6.3 DLLs from MSYS2.
> Both belong to the OpenSSL 3.x series and are distributed under the Apache
> License 2.0.

---

## 3. Verbatim Copyright and License Notices

### 3.1 Apache License 2.0
*Applies to: FreeRDP, WinPR, OpenSSL 3.6.2 / 3.6.3, Android cpufeatures*

```text
                                 Apache License
                           Version 2.0, January 2004
                        http://www.apache.org/licenses/

   TERMS AND CONDITIONS FOR USE, REPRODUCTION, AND DISTRIBUTION

   1. Definitions.

      "License" shall mean the terms and conditions for use, reproduction,
      and distribution as defined by Sections 1 through 9 of this document.

      "Licensor" shall mean the copyright owner or entity authorized by
      the copyright owner that is granting the License.

      "Legal Entity" shall mean the union of the acting entity and all
      other entities that control, are controlled by, or are under common
      control with that entity. For the purposes of this definition,
      "control" means (i) the power, direct or indirect, to cause the
      direction or management of such entity, whether by contract or
      otherwise, or (ii) ownership of fifty percent (50%) or more of the
      outstanding shares, or (iii) beneficial ownership of such entity.

      "You" (or "Your") shall mean an individual or Legal Entity
      exercising permissions granted by this License.

      "Source" form shall mean the preferred form for making modifications,
      including but not limited to software source code, documentation
      source, and configuration files.

      "Object" form shall mean any form resulting from mechanical
      transformation or translation of a Source form, including but
      not limited to compiled object code, generated documentation,
      and conversions to other media types.

      "Work" shall mean the work of authorship, whether in Source or
      Object form, made available under the License, as indicated by a
      copyright notice that is included in or attached to the work.

      "Derivative Works" shall mean any work, whether in Source or Object
      form, that is based on (or derived from) the Work and for which the
      editorial revisions, annotations, elaborations, or other modifications
      represent, as a whole, an original work of authorship. For the purposes
      of this License, Derivative Works shall not include works that remain
      separable from, or merely link (or bind by name) to the interfaces of,
      the Work and Derivative Works thereof.

      "Contribution" shall mean any work of authorship, including
      the original version of the Work and any modifications or additions
      to that Work or Derivative Works thereof, that is intentionally
      submitted to Licensor for inclusion in the Work by the copyright owner
      or by an individual or Legal Entity authorized to submit on behalf of
      the copyright owner. For the purposes of this definition, "submitted"
      means any form of electronic, verbal, or written communication sent
      to the Licensor or its representatives, including but not limited to
      communication on electronic mailing lists, source code control systems,
      and issue tracking systems that are managed by, or on behalf of, the
      Licensor for the purpose of discussing and improving the Work, but
      excluding communication that is conspicuously marked or otherwise
      designated in writing by the copyright owner as "Not a Contribution."

      "Contributor" shall mean Licensor and any individual or Legal Entity
      on behalf of whom a Contribution has been received by Licensor and
      subsequently incorporated within the Work.

   2. Grant of Copyright License. Subject to the terms and conditions of
      this License, each Contributor hereby grants to You a perpetual,
      worldwide, non-exclusive, no-charge, royalty-free, irrevocable
      copyright license to reproduce, prepare Derivative Works of,
      publicly display, publicly perform, sublicense, and distribute the
      Work and such Derivative Works in Source or Object form.

   3. Grant of Patent License. Subject to the terms and conditions of
      this License, each Contributor hereby grants to You a perpetual,
      worldwide, non-exclusive, no-charge, royalty-free, irrevocable
      (except as stated in this section) patent license to make, have made,
      use, offer to sell, sell, import, and otherwise transfer the Work,
      where such license applies only to those patent claims licensable
      by such Contributor that are necessarily infringed by their
      Contribution(s) alone or by combination of their Contribution(s)
      with the Work to which such Contribution(s) was submitted. If You
      institute patent litigation against any entity (including a
      cross-claim or counterclaim in a lawsuit) alleging that the Work
      or a Contribution incorporated within the Work constitutes direct
      or contributory patent infringement, then any patent licenses
      granted to You under this License for that Work shall terminate
      as of the date such litigation is filed.

   4. Redistribution. You may reproduce and distribute copies of the
      Work or Derivative Works thereof in any medium, with or without
      modifications, and in Source or Object form, provided that You
      meet the following conditions:

      (a) You must give any other recipients of the Work or
          Derivative Works a copy of this License; and

      (b) You must cause any modified files to carry prominent notices
          stating that You changed the files; and

      (c) You must retain, in the Source form of any Derivative Works
          that You distribute, all copyright, patent, trademark, and
          attribution notices from the Source form of the Work,
          excluding those notices that do not pertain to any part of
          the Derivative Works; and

      (d) If the Work includes a "NOTICE" text file as part of its
          distribution, then any Derivative Works that You distribute must
          include a readable copy of the attribution notices contained
          within such NOTICE file, excluding those notices that do not
          pertain to any part of the Derivative Works, in at least one
          of the following places: within a NOTICE text file distributed
          as part of the Derivative Works; within the Source form or
          documentation, if provided along with the Derivative Works; or,
          within a display generated by the Derivative Works, if and
          wherever such third-party notices normally appear. The contents
          of the NOTICE file are for informational purposes only and
          do not modify the License. You may add Your own attribution
          notices within Derivative Works that You distribute, alongside
          or as an addendum to the NOTICE text from the Work, provided
          that such additional attribution notices cannot be construed
          as modifying the License.

      You may add Your own copyright statement to Your modifications and
      may provide additional or different license terms and conditions
      for use, reproduction, or distribution of Your modifications, or
      for any such Derivative Works as a whole, provided Your use,
      reproduction, and distribution of the Work otherwise complies with
      the conditions stated in this License.

   5. Submission of Contributions. Unless You explicitly state otherwise,
      any Contribution intentionally submitted for inclusion in the Work
      by You to the Licensor shall be under the terms and conditions of
      this License, without any additional terms or conditions.
      Notwithstanding the above, nothing herein shall supersede or modify
      the terms of any separate license agreement you may have executed
      with Licensor regarding such Contributions.

   6. Trademarks. This License does not grant permission to use the trade
      names, trademarks, service marks, or product names of the Licensor,
      except as required for reasonable and customary use in describing the
      origin of the Work and reproducing the content of the NOTICE file.

   7. Disclaimer of Warranty. Unless required by applicable law or
      agreed to in writing, Licensor provides the Work (and each
      Contributor provides its Contributions) on an "AS IS" BASIS,
      WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
      implied, including, without limitation, any warranties or conditions
      of TITLE, NON-INFRINGEMENT, MERCHANTABILITY, or FITNESS FOR A
      PARTICULAR PURPOSE. You are solely responsible for determining the
      appropriateness of using or redistributing the Work and assume any
      risks associated with Your exercise of permissions under this License.

   8. Limitation of Liability. In no event and under no legal theory,
      whether in tort (including negligence), contract, or otherwise,
      unless required by applicable law (such as deliberate and grossly
      negligent acts) or agreed to in writing, shall any Contributor be
      liable to You for damages, including any direct, indirect, special,
      incidental, or consequential damages of any character arising as a
      result of this License or out of the use or inability to use the
      Work (including but not limited to damages for loss of goodwill,
      work stoppage, computer failure or malfunction, or any and all
      other commercial damages or losses), even if such Contributor
      has been advised of the possibility of such damages.

   9. Accepting Warranty or Additional Liability. While redistributing
      the Work or Derivative Works thereof, You may choose to offer,
      and charge a fee for, acceptance of support, warranty, indemnity,
      or other liability obligations and/or rights consistent with this
      License. However, in accepting such obligations, You may act only
      on Your own behalf and on Your sole responsibility, not on behalf
      of any other Contributor, and only if You agree to indemnify,
      defend, and hold each Contributor harmless for any liability
      incurred by, or claims asserted against, such Contributor by reason
      of your accepting any such warranty or additional liability.

   END OF TERMS AND CONDITIONS
```

#### OpenSSL Attribution Notice
```text
OpenSSL License Notice:
Copyright (c) 1998-2024 The OpenSSL Project Authors. All rights reserved.
This product includes software developed by the OpenSSL Project
for use in the OpenSSL Toolkit (http://www.openssl.org/).
```

#### Android cpufeatures Notice
```text
Copyright (C) 2016 The Android Open Source Project
Licensed under the Apache License, Version 2.0.
```

---

### 3.2 zlib License
*Applies to: SDL3, SDL3_ttf, SDL3_image, zlib (1.3.1)*

```text
This software is provided 'as-is', without any express or implied
warranty. In no event will the authors be held liable for any damages
arising from the use of this software.

Permission is granted to anyone to use this software for any purpose,
including commercial applications, and to alter it and redistribute it
freely, subject to the following restrictions:

1. The origin of this software must not be misrepresented; you must not
   claim that you wrote the original software. If you use this software
   in a product, an acknowledgment in the product documentation would be
   appreciated but is not required.
2. Altered source versions must be plainly marked as such, and must not be
   misrepresented as being the original software.
3. This notice may not be removed or altered from any source distribution.
```

#### Copyright Statements:
* **SDL3 / SDL3_ttf / SDL3_image**:
  ```text
  Copyright (C) 1997-2024 Sam Lantinga <slouken@libsdl.org>
  ```
* **zlib**:
  ```text
  Copyright (C) 1995-2024 Jean-loup Gailly and Mark Adler
  ```

---

### 3.3 BSD 3-Clause License
*Applies to: Opus, uriparser*

#### Opus Audio Codec Notice
```text
Copyright 2001-2011 Xiph.Org Foundation, Skype Limited, Octasic,
                    Jean-Marc Valin, Timothy B. Terriberry,
                    CSIRO, Gregory Maxwell, Mark Borgerding,
                    Erik de Castro Lopo

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions
are met:

- Redistributions of source code must retain the above copyright
notice, this list of conditions and the following disclaimer.

- Redistributions in binary form must reproduce the above copyright
notice, this list of conditions and the following disclaimer in the
documentation and/or other materials provided with the distribution.

- Neither the name of Internet Society, IETF or IETF Trust, nor the
names of specific contributors, may be used to endorse or promote
products derived from this software without specific prior written
permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
``AS IS'' AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER
OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
```

#### uriparser Notice
```text
uriparser - RFC 3986 URI parsing library
Copyright (C) 2007, Weijia Song <songweijia@gmail.com>
Copyright (C) 2007, Sebastian Pipping <sebastian@pipping.org>
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions
are met:

    1. Redistributions of source code must retain the above
       copyright notice, this list of conditions and the following
       disclaimer.

    2. Redistributions in binary form must reproduce the above
       copyright notice, this list of conditions and the following
       disclaimer in the documentation and/or other materials
       provided with the distribution.

    3. Neither the name of the copyright holder nor the names of
       its contributors may be used to endorse or promote products
       derived from this software without specific prior written
       permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
"AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
POSSIBILITY OF SUCH DAMAGE.
```

---

### 3.4 MIT License
*Applies to: cJSON, HarfBuzz*

#### cJSON Notice
```text
Copyright (c) 2009-2017 Dave Gamble and cJSON contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
```

#### HarfBuzz Notice
```text
HarfBuzz is licensed under the so-called "Old MIT" license.  Details follow.

For parts of HarfBuzz that are licensed under different licenses see individual
files names.

Copyright © 2010,2011,2012  Google, Inc.
Copyright © 2012  Mozilla Foundation
Copyright © 2011  Codethink Limited
Copyright © 2008,2010  Nokia Corporation and/or its subsidiary(-ies)
Copyright © 2009  Keith Stribley
Copyright © 2009  Martin Hosken and SIL International
Copyright © 2007  Chris Wilson
Copyright © 2006  Behdad Esfahbod
Copyright © 2005  David Turner
Copyright © 2004,2007,2009  Red Hat, Inc.

Permission is hereby granted, without written agreement and without
license or royalty fees, to use, copy, modify, and distribute this
software and its documentation for any purpose, provided that the
above copyright notice and the following two paragraphs appear in
all copies of this software.

IN NO EVENT SHALL THE COPYRIGHT HOLDER BE LIABLE TO ANY PARTY FOR
DIRECT, INDIRECT, SPECIAL, INCIDENTAL, OR CONSEQUENTIAL DAMAGES
ARISING OUT OF THE USE OF THIS SOFTWARE AND ITS DOCUMENTATION, EVEN
IF THE COPYRIGHT HOLDER HAS BEEN ADVISED OF THE POSSIBILITY OF SUCH
DAMAGE.

THE COPYRIGHT HOLDER SPECIFICALLY DISCLAIMS ANY WARRANTIES, INCLUDING,
BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND
FITNESS FOR A PARTICULAR PURPOSE.  THE SOFTWARE PROVIDED HEREUNDER IS
ON AN "AS IS" BASIS, AND THE COPYRIGHT HOLDER HAS NO OBLIGATION TO
PROVIDE MAINTENANCE, SUPPORT, UPDATES, ENHANCEMENTS, OR MODIFICATIONS.
```

---

### 3.5 The FreeType Project LICENSE (FTL)
*Applies to: FreeType 2 (bundled via SDL3_ttf)*

```text
The FreeType Project LICENSE
2006-Jan-27
Copyright 1996-2002, 2006 by David Turner, Robert Wilhelm, and Werner Lemberg

Introduction
============

  The FreeType  Project is distributed  in several  archive packages;
  some of  them may contain, in  addition to the FreeType  font engine,
  various tools and  contributions which rely on, or  relate to, the
  FreeType Project.

  This  license applies  to all  files found  in such  packages, and
  which do not  fall under their own explicit  license.  The license
  affects thus  the FreeType font engine,  the test programs,
  documentation and makefiles -- at the very least.

  This  license   was  inspired  by  the  BSD,   Artistic,  and  IJG
  (Independent JPEG  Group) licenses, which  all encourage inclusion
  and  use of  free  software in  commercial  and freeware  products
  alike.  As a consequence, its main points are that:

    o We don't promise that this software works.  However, we'll be
      interested in any kind of bug reports. (`as is' distribution)

    o You can  use this software for whatever you  want, in parts or
      full form, without having to pay us. (`royalty-free' usage)

    o You may not pretend that  you wrote this software.  If you use
      it, or  only parts of it,  in a program,  you must acknowledge
      somewhere  in  your  documentation that  you  have  used  the
      FreeType code. (`credits')

  We  specifically  permit  and  encourage  the  inclusion  of  this
  software, with  or without modifications,  in commercial products.
  We  disclaim  all warranties  covering  The  FreeType Project  and
  assume no liability related to The FreeType Project.

Legal Terms
===========

0. Definitions
--------------

  Throughout this license,  the terms `package', `FreeType Project',
  and  `FreeType  archive' refer  to  the  set  of files  originally
  distributed by the  authors (David Turner, Robert Wilhelm, and
  Werner Lemberg) as the `FreeType Project', be they source or binary.

  `You' refers to the licensee, or person using the project, where
  `using' is a generic term including compiling the project's source
  code as well as running it, without regards to the discretion or
  purpose of that use.

  `Control'  is  used in  its  generic  sense to  include  editorial
  control that is, who has the power to decide whether a given file
  is to be included in the project or not.  A modified version of the
  FreeType Project does not refer to the original FreeType Project,
  all copyright holders and contributors of the original FreeType
  Project must not be mentioned in that modified version.

  `Contribution' refers to a contribution to the FreeType Project,
  be it source code, documentation, or something else.

1. No Warranty
--------------

  THE FREETYPE PROJECT  IS PROVIDED `AS IS' WITHOUT  WARRANTY OF ANY
  KIND, EITHER  EXPRESS OR IMPLIED,  INCLUDING, BUT NOT  LIMITED TO,
  WARRANTIES  OF  MERCHANTABILITY   AND  FITNESS  FOR  A  PARTICULAR
  PURPOSE.  IN NO EVENT WILL ANY OF THE AUTHORS OR COPYRIGHT HOLDERS
  BE LIABLE  FOR ANY DAMAGES CAUSED  BY THE USE OR  THE INABILITY TO
  USE, OF THE FREETYPE PROJECT.

2. Redistribution
-----------------

  This  license  grants  a  worldwide, royalty-free,  perpetual  and
  irrevocable right  to use, execute, perform,  compile, display,
  copy,   create  derivative   works   of,  distribute   and  sublicense
  the  FreeType  Project (in   both  source  and  binary  forms)  and
  derivative works thereof for any  purpose; and to authorize others
  to exercise some or all of the rights granted herein, subject to
  the following conditions:

    o Redistribution of  source code  must  retain this  license file
      (`FTL.TXT') unaltered; any  additions, deletions or changes to
      the original  files must be clearly  indicated in accompanying
      documentation.   The  copyright   notices  of  the  unaltered,
      original  files must  be  preserved in  all  copies of  source
      files.

    o Redistribution in binary form must provide a disclaimer that
      states  that  the software  is  based  in  part on  the  work of
      the FreeType Team, in  the distribution documentation.  We also
      encourage you to put an URL to the FreeType web page in your
      documentation, though this isn't mandatory.

  These conditions  apply to any  software that contains part  of the
  FreeType Project, in  any form, that is to say  as binary or source
  code.

3. Advertising
--------------

  Neither the  FreeType authors and  contributors nor you  shall use
  the name of the  FreeType authors or contributors for advertising
  or publicity purposes without specific prior written permission.

  We suggest,  but do not require, that  you use one or  more of the
  following phrases to refer  to this software in your documentation
  or advertising materials: `FreeType Project', `FreeType Engine',
  `FreeType library', or `FreeType Distribution'.

  As you have not signed this license, you are not required to accept
  it.  However,  as the FreeType Project is  copyrighted material, only
  this license, or another one contracted with the authors, grants
  you the right to use, distribute, and modify it.  Therefore, by
  using, distributing, or modifying the FreeType Project, you indicate
  that you understand and accept all the terms of this license.
```

---

### 3.6 libtiff License
*Applies to: libtiff (>= 4.5.1, bundled via SDL3_image)*

```text
Copyright (c) 1988-1997 Sam Leffler
Copyright (c) 1991-1997 Silicon Graphics, Inc.

Permission to use, copy, modify, distribute, and sell this software and
its documentation for any purpose is hereby granted without fee, provided
that (i) the above copyright notices and this permission notice appear in
all copies of the software and related documentation, and (ii) the names of
Sam Leffler and Silicon Graphics may not be used in any advertising or
publicity relating to the software without the specific, prior written
permission of Sam Leffler and Silicon Graphics.

THE SOFTWARE IS PROVIDED "AS-IS" AND WITHOUT WARRANTY OF ANY KIND,
EXPRESS, IMPLIED OR OTHERWISE, INCLUDING WITHOUT LIMITATION, ANY
WARRANTY OF MERCHANTABILITY OR FITNESS FOR A PARTICULAR PURPOSE.

IN NO EVENT SHALL SAM LEFFLER OR SILICON GRAPHICS BE LIABLE FOR
ANY SPECIAL, INCIDENTAL, INDIRECT OR CONSEQUENTIAL DAMAGES OF ANY KIND,
OR ANY DAMAGES WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS,
WHETHER OR NOT ADVISED OF THE POSSIBILITY OF DAMAGE, AND ON ANY THEORY OF
LIABILITY, ARISING OUT OF OR IN CONNECTION WITH THE USE OR PERFORMANCE
OF THIS SOFTWARE.
```

---

### 3.7 libpng License
*Applies to: libpng (bundled via SDL3_image)*

```text
This copy of the libpng notices is provided for your convenience.  In case of
any discrepancy between this copy and the notices in the file png.h that is
included in the libpng distribution, the latter shall prevail.

COPYRIGHT NOTICE, DISCLAIMER, and LICENSE:

If you modify libpng you may insert additional notices immediately following
this sentence.

This code is released under the libpng license.

libpng versions 1.0.7, July 1, 2000 through 1.6.43, February 23, 2024 are
Copyright (c) 2000-2002, 2004, 2006-2024 Glenn Randers-Pehrson, are
derived from libpng-1.0.6, and are distributed according to the same
disclaimer and license as libpng-1.0.6 with the following individuals
added to the list of Contributing Authors:

   Simon-Pierre Cadieux
   Eric S. Raymond
   Mans Rullgard
   Cosmin Truta
   Gilles Vollant
   James Yu
   Mandar Sahastrabuddhe
   Google Inc.
   Vadim Barkov

and with the following additions to the disclaimer:

   There is no warranty against interference with your enjoyment of the
   library or against infringement.  There is no warranty that our
   efforts or the library will fulfill any of your particular purposes
   or needs.  This library is provided with all faults, and the entire
   risk of satisfactory quality, performance, accuracy, and effort is with
   the user.

Some files in the "contrib" directory and some code-generating scripts that
are not used in creating the libpng distribution are released under other
licenses.

libpng versions 0.97, January 1998, through 1.0.6, March 20, 2000, are
Copyright (c) 1998-2000 Glenn Randers-Pehrson, are derived from
libpng-0.96, and are distributed according to the same disclaimer and
license as libpng-0.96, with the following individuals added to the list of
Contributing Authors:

   Tom Lane
   Glenn Randers-Pehrson
   Willem van Schaik

libpng versions 0.89, June 1996, through 0.96, May 1997, are
Copyright (c) 1996-1997 Andreas Dilger, are derived from libpng-0.88,
and are distributed according to the same disclaimer and license as
libpng-0.88, with the following individuals added to the list of
Contributing Authors:

   John Bowler
   Kevin Bracey
   Sam Bushell
   Magnus Holmgren
   Greg Roelofs
   Tom Tanner

libpng versions 0.5, May 1995, through 0.88, January 1996, are
Copyright (c) 1995-1996 Guy Eric Schalnat, Group 42, Inc.

For the purposes of this copyright and license, "Contributing Authors"
is defined as the following set of individuals:

   Andreas Dilger
   Dave Martindale
   Guy Eric Schalnat
   Paul Schmidt
   Tim Wegner

The PNG Reference Library is supplied "AS IS".  The Contributing Authors
and Group 42, Inc. disclaim all warranties, expressed or implied,
including, without limitation, the warranties of merchantability and of
fitness for any purpose.  The Contributing Authors and Group 42, Inc.
assume no liability for direct, indirect, incidental, special, exemplary,
or consequential damages, which may result from the use of the PNG
Reference Library, even if advised of the possibility of such damage.

Permission is hereby granted to use, copy, modify, and distribute this
source code, or portions hereof, for any purpose, without fee, subject
to the following restrictions:

1. The origin of this source code must not be misrepresented.

2. Altered versions must be plainly marked as such and must not
   be misrepresented as being the original source.

3. This Copyright notice may not be removed or altered from any
   source or altered source distribution.

The Contributing Authors and Group 42, Inc. specifically permit, without
fee, and charge no royalties for, use of this source code as a component
to supporting the PNG file format in commercial products.  Changes to
this code are suitable for inclusion in the PNG Reference Library.
```
