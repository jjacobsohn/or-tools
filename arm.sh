#!/usr/bin/env bash
# Copyright 2010-2025 Google LLC
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

set -euo pipefail

#./tools/cross_compile.sh --help

export PROJECT=or-tools
#export PROJECT=glop

#export TARGET=x86_64
export TARGET=aarch64
#export TARGET=mips64
#export TARGET=ppc64

./tools/cross_compile.sh toolchain
./tools/cross_compile.sh build
./tools/cross_compile.sh qemu
./tools/cross_compile.sh test
