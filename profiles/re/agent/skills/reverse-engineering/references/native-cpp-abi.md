# Native C++ ABI, RTTI & Data Structures

Actionable reference for reverse engineering compiled C++ binaries across major compilers (MSVC, GCC, Clang) and architectures (x86-64, ARM64).

---

## 1. Calling Conventions

### x86-64 System V AMD64 ABI (Linux, macOS, BSD)
- **Integer/Pointer Arguments**: Passed in registers in order:
  1. `RDI`
  2. `RSI`
  3. `RDX`
  4. `RCX`
  5. `R8`
  6. `R9`
- **Floating-Point Arguments**: Passed in `XMM0` through `XMM7`.
- **Return Value**: `RAX` (integer/pointer), `RDX:RAX` (128-bit), `XMM0` (floating-point).
- **Callee-Saved Registers**: `RBX`, `RSP`, `RBP`, `R12`, `R13`, `R14`, `R15`.
- **Stack Alignment**: 16-byte alignment before `call` instruction.
- **`this` pointer**: Passed as the first hidden parameter in `RDI`.

### x86-64 Microsoft x64 ABI (Windows)
- **Integer/Pointer Arguments**: Passed in 4 registers:
  1. `RCX` (or `XMM0` for float)
  2. `RDX` (or `XMM1` for float)
  3. `R8` (or `XMM2` for float)
  4. `R9` (or `XMM3` for float)
- **Shadow Space (Home Space)**: Caller **must** allocate 32 bytes (4 quadwords) on the stack directly above return address before `call`, even for 0-argument functions. Callee can use this area to spill `RCX`, `RDX`, `R8`, `R9`.
- **Return Value**: `RAX` (integer/pointer) or `XMM0` (floating-point). Aggregates > 8 bytes return via caller-allocated pointer passed in `RCX` (shifting user parameters by one register).
- **Callee-Saved Registers**: `RBX`, `RBP`, `RDI`, `RSI`, `RSP`, `R12`, `R13`, `R14`, `R15`, `XMM6`-`XMM15`.
- **`this` pointer**: Passed in `RCX`.

### ARM64 (AArch64)
- **General Purpose Arguments**: `X0` through `X7`.
- **SIMD/Float Arguments**: `V0` through `V7`.
- **Return Value**: `X0` (or `X0-X1` for 128-bit results), `V0` (floats).
- **Indirect Result Location**: `X8` (for returning structs too large for registers).
- **Caller-Saved Registers**: `X9` through `X15`.
- **Callee-Saved Registers**: `X19` through `X28`, `X29` (Frame Pointer FP), `X30` (Link Register LR).
- **`this` pointer**: Passed in `X0`.

---

## 2. Virtual Method Tables (Vtables) & Polymorphism

### Single Inheritance
- **Object Layout**:
  ```text
  Offset +0x00: [ vptr (pointer to vtable) ]
  Offset +0x08: [ BaseClass field 1         ]
  Offset +0x10: [ DerivedClass field 1      ]
  ```
- **Vtable Memory Layout**:
  - `vtable[0]`: Address of first virtual function.
  - `vtable[1]`: Address of second virtual function, etc.
- In disassembly, a virtual call appears as:
  ```asm
  mov rax, [rdi]        ; load vptr from object (+0)
  call [rax + 0x18]     ; call 4th virtual method in vtable
  ```

### Multiple Inheritance & Thunk Functions
- When a class inherits from multiple base classes, an instance contains multiple `vptr`s:
  ```text
  Offset +0x00: [ vptr for Base1 ]
  Offset +0x08: [ Base1 fields   ]
  Offset +0x18: [ vptr for Base2 ]
  Offset +0x20: [ Base2 fields   ]
  ```
- **Thunk adjustments**: Calling a virtual function implemented by `Derived` via a pointer to `Base2` requires adjusting the `this` pointer back to `Derived`:
  ```asm
  sub rcx, 0x18         ; adjust this pointer (Base2* -> Derived*)
  jmp Derived::Method   ; jump to actual implementation
  ```

---

## 3. Run-Time Type Information (RTTI) Recovery

### MSVC RTTI Layout (PE Binaries)
MSVC places RTTI structures in `.rdata`. At `vtable[-1]` (pointer 8 bytes before the first virtual function pointer), there is a pointer to `_RTTICompleteObjectLocator`:

```c
struct _RTTICompleteObjectLocator {
    uint32_t signature;         // 0 on x86, 1 on x64 (relative RVAs)
    uint32_t offset;            // Offset of vptr within the complete class
    uint32_t cdOffset;          // Constructor displacement offset
    int32_t  pTypeDescriptor;   // ImageBase-relative RVA to TypeDescriptor
    int32_t  pClassHierarchy;   // ImageBase-relative RVA to ClassHierarchyDescriptor
};

struct TypeDescriptor {
    void*   pVFTable;           // type_info vtable pointer
    void*   spare;              // Internal runtime state
    char    name[];             // Mangled class name, e.g., ".?AVMyClass@@"
};
```
- **Recovery Workflow**:
  1. Locate vtable candidate in `.rdata`.
  2. Read pointer directly preceding vtable entry `0`: `qword ptr [vtable - 8]`.
  3. Verify `signature == 1` (on x64).
  4. Follow `pTypeDescriptor` RVA to read ASCII string: `.?AV<ClassName>@@`.

### Itanium C++ ABI RTTI (GCC / Clang on Linux & macOS)
In GCC/Clang binaries, `vtable[-1]` points directly to an instance of `std::type_info` (or derived classes like `abi::__si_class_type_info` for single inheritance, `abi::__vmi_class_type_info` for multiple inheritance):
```c
struct __class_type_info {
    void*       vptr;           // Pointer to vtable of type_info
    const char* type_name;      // Pointer to mangled name string (e.g., "7MyClass")
};

struct __si_class_type_info {
    void*       vptr;
    const char* type_name;
    const __class_type_info* base_type; // Pointer to parent class type_info
};
```
- **Recovery Workflow**:
  1. Read pointer at `[vtable - 8]`.
  2. Offset `+0x08` of that structure points to the mangled symbol name.
  3. Base class hierarchy can be recursively reconstructed by following `base_type`.

---

## 4. Standard Template Library (STL) Memory Layouts

### `std::string`
- **GCC `libstdc++` (post-C++11 SSO - Small String Optimization)**:
  - Total size: 32 bytes (64-bit).
  - Structure:
    ```c
    struct std_string {
        char* data_ptr;         // Points to buffer if heap, or &sso_buffer if SSO
        size_t size;            // Length of string
        union {
            char sso_buffer[16];
            size_t capacity;    // Allocated capacity if heap allocated
        };
    };
    ```
- **MSVC STL `std::basic_string`**:
  - Total size: 32 bytes (64-bit).
  - Structure:
    ```c
    struct msvc_string {
        union {
            char sso_buffer[16]; // Used if capacity < 16
            char* heap_ptr;      // Pointer to buffer if capacity >= 16
        } buffer;
        size_t size;             // String length
        size_t capacity;         // Buffer capacity (default 15 for SSO)
    };
    ```

### `std::vector<T>`
- Standard 3-pointer layout across GCC, Clang, and MSVC (24 bytes on 64-bit):
  ```c
  struct std_vector {
      T* start;                 // Pointer to first element
      T* finish;                // Pointer to past-the-end element (size = (finish - start) / sizeof(T))
      T* end_of_storage;        // Pointer to end of allocated buffer (cap = (end_of_storage - start) / sizeof(T))
  };
  ```

### Smart Pointers
- **`std::unique_ptr<T>`**:
  - Size: 8 bytes (single pointer to heap object). Zero runtime memory overhead over raw pointer unless custom non-empty deleter is used.
- **`std::shared_ptr<T>`**:
  - Size: 16 bytes (two 64-bit pointers):
    1. Pointer to managed object `T*`.
    2. Pointer to control block containing: virtual deleter, strong reference count (atomic), weak reference count (atomic).

---

## 5. Mangled Symbols & Demangling

### Itanium ABI Mangling (GCC / Clang)
- Prefixed with `_Z`.
- Namespaces/nested classes preceded by `N`, followed by length-prefixed identifiers, terminated with `E`.
  - Example: `_ZN7MyClass6MethodEi` -> `MyClass::Method(int)`
  - `vtable` for class: `_ZTV7MyClass`
  - RTTI `type_info` for class: `_ZTI7MyClass`
  - RTTI type name string: `_ZTS7MyClass`
- CLI demangler: `c++filt _ZN7MyClass6MethodEi` or `llvm-cxxfilt`.

### MSVC Mangling
- Prefixed with `?`.
- Namespaces follow class name in reverse order, terminated with `@@`.
- Access and calling convention encoded in letters (`Q` = public, `E` = `__cdecl`, `A` = non-const).
  - Example: `?Method@MyClass@@QEAAXH@Z` -> `public: void __cdecl MyClass::Method(int)`
  - Vtable symbol: `??_7MyClass@@6B@`
- Demangler: `undname` (Windows SDK) or built-in IDA/Ghidra demangler.
