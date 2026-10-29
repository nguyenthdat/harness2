#!/usr/bin/env python3
"""
auto_triage.py - Fast signature scanner and runtime detection for binary artifacts.
Scans file headers, magic bytes, section names, and strings to identify compiler/runtime
signatures and recommend appropriate progressive disclosure references.
"""

import json
import os
import struct
import sys


def is_plain_text(data):
    """Checks if a byte buffer looks like UTF-8 or ASCII plain text."""
    try:
        data.decode("utf-8")
        return True
    except UnicodeDecodeError:
        return False


def triage_file(filepath):
    if not os.path.exists(filepath):
        return {"error": f"File not found: {filepath}"}

    file_size = os.path.getsize(filepath)
    result = {
        "file": os.path.abspath(filepath),
        "size_bytes": file_size,
        "format": "Unknown",
        "runtime": "Unknown",
        "indicators": [],
        "recommended_reference": "references/01-static-architectures/native-cpp-abi.md",
        "category": "01-static-architectures",
    }

    try:
        with open(filepath, "rb") as f:
            header = f.read(4096)
            f.seek(0)
            head_sample = f.read(min(file_size, 1024 * 1024))
            tail_sample = b""
            if file_size > 1024 * 1024:
                f.seek(max(0, file_size - 512 * 1024))
                tail_sample = f.read(512 * 1024)
            sample_data = head_sample + tail_sample
    except Exception as e:
        result["error"] = f"Failed to read file: {e}"
        return result

    # 1. Container / Format Detection
    if header.startswith(b"\x7fELF"):
        result["format"] = "ELF"
    elif header.startswith(b"MZ"):
        result["format"] = "PE"
    elif header.startswith(b"\xca\xfe\xba\xbe"):
        # Disambiguate between Java .class and Fat Mach-O
        # Java .class: bytes 4-8 are minor_version (2 bytes), major_version (2 bytes e.g. 0x0034 = Java 8, 0x003D = Java 17)
        # Fat Mach-O: bytes 4-8 are nfat_arch (big-endian 32-bit int, typically 1-5 architectures)
        if len(header) >= 8:
            major_ver = struct.unpack(">H", header[6:8])[0]
            if 45 <= major_ver <= 70:
                result["format"] = "Java Class"
            else:
                result["format"] = "Mach-O (Fat)"
        else:
            result["format"] = "Java Class"
    elif (
        header.startswith(b"\xcf\xfa\xed\xfe")
        or header.startswith(b"\xce\xfa\xed\xfe")
        or header.startswith(b"\xfe\xed\xfa\xcf")
        or header.startswith(b"\xfe\xed\xfa\xce")
    ):
        result["format"] = "Mach-O"
    elif header.startswith(b"dex\n"):
        result["format"] = "DEX"
    elif header.startswith(b"PK\x03\x04"):
        result["format"] = "ZIP/Package"
    elif header.startswith(b"\x1f\x8b"):
        result["format"] = "GZIP"
    elif header.startswith(b"\x00asm"):
        result["format"] = "WASM"
    elif header.startswith(b"\xc6\x1f\xbc\x03"):
        result["format"] = "Hermes Bytecode"
    elif header[:4] in [b"hsqs", b"sqsh", b"qshs", b"shsq"]:
        result["format"] = "SquashFS"
    elif header.startswith(b"\x27\x05\x19\x56"):
        result["format"] = "U-Boot Image"
    elif (
        header.startswith(b"\xd4\xc3\xb2\xa1")
        or header.startswith(b"\xa1\xb2\xc3\xd4")
        or header.startswith(b"\x0a\x0d\x0d\x0a")
    ):
        result["format"] = "PCAP"
    elif is_plain_text(head_sample):
        result["format"] = "Text/Script"

    # Avoid matching internal binary signatures inside plain text / source scripts
    if result["format"] == "Text/Script":
        if filepath.endswith((".js", ".mjs", ".ts")):
            result["runtime"] = "Browser JS / Script"
            result["recommended_reference"] = "references/01-static-architectures/browser-js-wasm.md"
        else:
            result["runtime"] = "Plain Text / Script"
            result["recommended_reference"] = "references/01-static-architectures/native-cpp-abi.md"
        return result

    # 2. Runtime / Compiler Signatures Scan

    # Hermes Bytecode (React Native)
    if result["format"] == "Hermes Bytecode":
        result["runtime"] = "React Native (Hermes Bytecode)"
        result["indicators"].append("Found Hermes bytecode magic header")
        result["recommended_reference"] = "references/01-static-architectures/browser-js-wasm.md"
        result["category"] = "01-static-architectures"
        return result

    # Binary container targets (ELF, PE, Mach-O)
    is_native_binary = result["format"] in ["ELF", "PE", "Mach-O", "Mach-O (Fat)"]

    # Go check (restricted to native binaries or explicit Go build IDs)
    if is_native_binary and (
        b".gopclntab" in sample_data
        or b"runtime.morestack" in sample_data
        or b"Go build ID:" in sample_data
    ):
        result["runtime"] = "Go"
        result["indicators"].append("Found .gopclntab / runtime.morestack")
        result["recommended_reference"] = (
            "references/01-static-architectures/native-golang.md"
        )
        result["category"] = "01-static-architectures"
        return result

    # Rust check (restricted to native binaries)
    if is_native_binary and (
        b"rust_eh_personality" in sample_data
        or b"core::panicking" in sample_data
        or b"library/std/src" in sample_data
        or b".dep-v0" in sample_data
    ):
        result["runtime"] = "Rust"
        result["indicators"].append(
            "Found rust_eh_personality / core::panicking"
        )
        result["recommended_reference"] = (
            "references/01-static-architectures/native-rust.md"
        )
        result["category"] = "01-static-architectures"
        return result

    # .NET CLR check (PE binaries with CLI metadata)
    if result["format"] == "PE" and (
        b"_CorExeMain" in sample_data
        or b"_CorDllMain" in sample_data
        or b"BSJB" in sample_data
    ):
        result["runtime"] = ".NET / CLR"
        result["indicators"].append(
            "Found .NET metadata marker BSJB / _CorExeMain"
        )
        result["recommended_reference"] = (
            "references/01-static-architectures/managed-dotnet-jvm.md"
        )
        result["category"] = "01-static-architectures"
        return result

    # Dalvik DEX / Android / Java Class
    if (
        result["format"] in ["DEX", "Java Class"]
        or b"classes.dex" in sample_data
        or b"META-INF/MANIFEST.MF" in sample_data
    ):
        result["runtime"] = "JVM / Dalvik / Android"
        result["indicators"].append(
            "Found DEX magic, Java .class, or Android package markers"
        )
        result["recommended_reference"] = (
            "references/01-static-architectures/managed-dotnet-jvm.md"
        )
        result["category"] = "01-static-architectures"
        return result

    # Unity IL2CPP check
    if (
        b"Il2Cpp" in sample_data
        or b"libil2cpp.so" in sample_data
        or b"global-metadata.dat" in sample_data
        or header.startswith(b"\xaf\x1b\xb1\xfa")
    ):
        result["runtime"] = "Unity IL2CPP"
        result["indicators"].append(
            "Found Unity IL2CPP strings or global-metadata signature"
        )
        result["recommended_reference"] = (
            "references/01-static-architectures/unity-il2cpp.md"
        )
        result["category"] = "01-static-architectures"
        return result

    # WebAssembly / Browser JS
    if (
        result["format"] == "WASM"
        or b"webpackJsonp" in sample_data
        or b"sourceMappingURL=" in sample_data
        or filepath.endswith(".js")
    ):
        result["runtime"] = "Browser JS / WASM"
        result["indicators"].append(
            "Found WASM binary or JavaScript bundle structure"
        )
        result["recommended_reference"] = (
            "references/01-static-architectures/browser-js-wasm.md"
        )
        result["category"] = "01-static-architectures"
        return result

    # Firmware / IoT
    if (
        result["format"] in ["SquashFS", "U-Boot Image"]
        or b"u-boot" in sample_data.lower()
        or b"busybox" in sample_data.lower()
    ):
        result["runtime"] = "Firmware / Embedded Linux"
        result["indicators"].append(
            "Found embedded bootloader or SquashFS markers"
        )
        result["recommended_reference"] = (
            "references/01-static-architectures/firmware-iot.md"
        )
        result["category"] = "01-static-architectures"
        return result

    # Apple iOS / Mach-O with ObjC/Swift (strictly require Apple runtime markers or .ipa)
    if (
        b"__objc_classlist" in sample_data
        or b"_swift_release" in sample_data
        or filepath.endswith(".ipa")
        or b"/System/Library/Frameworks" in sample_data
    ):
        result["runtime"] = "Apple ObjC / Swift"
        result["indicators"].append(
            "Found Objective-C / Swift runtime markers"
        )
        result["recommended_reference"] = (
            "references/01-static-architectures/mobile-ios.md"
        )
        result["category"] = "01-static-architectures"
        return result

    # Network PCAP
    if (
        result["format"] == "PCAP"
        or filepath.endswith(".pcap")
        or filepath.endswith(".pcapng")
    ):
        result["runtime"] = "Network Capture"
        result["indicators"].append("Found PCAP network packet capture header")
        result["recommended_reference"] = (
            "references/03-objectives/protocol-recovery.md"
        )
        result["category"] = "03-objectives"
        return result

    # Standard C / C++ Default (ELF, PE, Mach-O)
    if is_native_binary:
        result["runtime"] = "Native C/C++"
        result["indicators"].append("Native compiled binary (x86/ARM/MIPS)")
        result["recommended_reference"] = (
            "references/01-static-architectures/native-cpp-abi.md"
        )
        result["category"] = "01-static-architectures"

    return result


def main():
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <binary-or-artifact-file> [--json]")
        sys.exit(1)

    filepath = sys.argv[1]
    res = triage_file(filepath)
    print(json.dumps(res, indent=2))


if __name__ == "__main__":
    main()
