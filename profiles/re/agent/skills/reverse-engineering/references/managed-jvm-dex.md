# Managed JVM & Android DEX Reverse Engineering

Actionable reference for reverse engineering Java bytecode (`.class`/`.jar`), Android Dalvik/ART executables (`.dex`/APK/AAB), Smali disassembly, ProGuard/R8 obfuscation, and JNI native bridges.

---

## 1. File Formats & Signatures

### Java Class File (`.class`)
- **Magic**: `0xCAFEBABE` (`\xCA\xFE\xBA\xBE`).
- Followed by `minor_version` (2 bytes), `major_version` (2 bytes) (e.g., 52 = Java 8, 61 = Java 17).
- Constant Pool holds all string literals, class references, field/method descriptors.

### Dalvik Executable (`.dex`)
- **Magic**: `dex\n035\0` (or `037`, `038`, `039`).
- **Header**: Contains checksum, SHA-1 signature, file size, and offset tables for:
  - `string_ids`: Offsets to UTF-8 strings.
  - `type_ids`: Indices into `string_ids` for type descriptors (`Lcom/example/MyClass;`).
  - `proto_ids`: Method prototypes (return type + parameter list).
  - `field_ids`: Fields (class + type + name).
  - `method_ids`: Methods (class + proto + name).
  - `class_defs`: Class definitions containing access flags, superclass, interfaces, and class data offset (fields and virtual/direct methods).
- **Multidex**: Applications exceeding 65,536 method references are split into `classes.dex`, `classes2.dex`, `classes3.dex`, etc. All must be analyzed together.

---

## 2. Decompilation & Disassembly Workflows

### JADX Decompiler
Convert DEX/APK/JAR directly into Java source:
```bash
# Decompile whole APK into directory
jadx -d /tmp/decompiled_src target.apk --no-imports --show-bad-code
# Decompile single class
jadx -d /tmp/decompiled_src -include-pkg com.example.crypto target.apk
```

### Apktool & Smali Bytecode
Decodes `AndroidManifest.xml`, resources (`res/values/strings.xml`), and disassembles DEX to Smali:
```bash
apktool d target.apk -o /tmp/apk_unpacked
```

### Smali Syntax Basics
Smali is a register-based assembly representation of Dalvik bytecode:
- **Registers**:
  - `v0`, `v1`, `v2`: Local registers.
  - `p0`: `this` pointer (for instance methods).
  - `p1`, `p2`: Incoming arguments.
- **Common Opcodes**:
  - `const-string v0, "secret"`: Load string literal.
  - `iget-object v1, p0, Lcom/example/Foo;->bar:Ljava/lang/String;`: Read instance field `bar`.
  - `sget-object v1, Lcom/example/Foo;->instance:Lcom/example/Foo;`: Read static field.
  - `invoke-virtual {p0, v0}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;`: Virtual call.
  - `invoke-direct {p0}, Ljava/lang/Object;-><init>()V`: Call constructor or private method.
  - `invoke-static {v0}, Lcom/example/Crypto;->decrypt([B)[B`: Static call.

---

## 3. Obfuscation Boundaries & Pitfalls

### ProGuard / R8
- **Renaming**: Classes, fields, and methods renamed to short arbitrary letters (`a.b.c.a`, `void a()`).
- **Class Merging & Inlining**: R8 aggressively inlines small helper methods and merges classes with single implementations.
- **String Encryption**: Sensitive strings replaced by decryptor calls (e.g., `a.a("3a5f9b")`).
- **Boundary Rule**: Do not infer behavior from short or recycled class names. Renamed identifiers are arbitrary labels. **Always anchor analysis on reachability and system API calls**:
  - Cryptography: `javax.crypto.Cipher`, `java.security.MessageDigest`.
  - Network: `java.net.HttpURLConnection`, `okhttp3.OkHttpClient`, `retrofit2.Retrofit`.
  - Android APIs: `android.telephony.TelephonyManager`, `android.provider.Settings.Secure`.

---

## 4. JNI (Java Native Interface) Bridge

Android apps frequently offload security, cryptography, or anti-tamper logic to native C/C++ shared libraries (`libnative-lib.so` in `lib/arm64-v8a/` or `lib/armeabi-v7a/`).

### 1. Dynamic Symbol Resolution
Java declaration:
```java
package com.example.app;
public class SecurityManager {
    public native boolean verifyLicense(String key);
}
```
Native exported C symbol in `libnative-lib.so`:
```c
JNIEXPORT jboolean JNICALL Java_com_example_app_SecurityManager_verifyLicense(
    JNIEnv* env, jobject thiz, jstring key) { ... }
```
- Identify these by inspecting dynamic symbol exports (`readelf -sW libnative-lib.so` or `inspect_native_exports`).

### 2. Static Registration via `RegisterNatives`
If native methods do not appear as exported symbols, the library uses `RegisterNatives` during `JNI_OnLoad`:
```c
static JNINativeMethod methods[] = {
    {"verifyLicense", "(Ljava/lang/String;)Z", (void*)native_verifyLicense}
};

JNIEXPORT jint JNI_OnLoad(JavaVM* vm, void* reserved) {
    JNIEnv* env;
    (*vm)->GetEnv(vm, (void**)&env, JNI_VERSION_1_6);
    jclass clazz = (*env)->FindClass(env, "com/example/app/SecurityManager");
    (*env)->RegisterNatives(env, clazz, methods, 1);
    return JNI_VERSION_1_6;
}
```
- **Triage**: In IDA or Ghidra, decompile `JNI_OnLoad`. Locate the call to `RegisterNatives` and inspect the 3rd parameter, which points to the array of `JNINativeMethod` structs (`name`, `signature`, `fnPtr`).
