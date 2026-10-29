# Native Go Reverse Engineering

Actionable reference for reverse engineering stripped Go executables (ELF, PE, Mach-O). Covers the Go 1.17+ register ABI, `pclntab` symbol recovery, runtime type descriptors, interfaces, and goroutines.

---

## 1. Go Calling Conventions & ABI Evolution

### Go 1.17+ Register ABI (ABIInternal)
Since Go 1.17, x86-64 and ARM64 use a register-based calling convention:
- **x86-64 Parameters**: Passed in 9 integer registers:
  1. `RAX`
  2. `RBX`
  3. `RCX`
  4. `RDI`
  5. `RSI`
  6. `R8`
  7. `R9`
  8. `R10`
  9. `RDX`
- **Floating Point Parameters**: `X0` through `X14`.
- **Return Values**: Multiple return values passed in the same registers (`RAX`, `RBX`, `RCX`, etc.).
- **Closure Context Pointer**: `RDX` (reserved when calling closures).

### Legacy Go ABI (ABI0, Go <= 1.16)
- Pure stack-based calling convention: all parameters pushed to stack in caller frame.
- Return values placed on stack above arguments.
- Stack frames do not use standard base pointer chaining by default.

### Stack Growth & `runtime.morestack`
Go functions use segmented/copying stacks. The function prologue checks whether the stack frame exceeds the available stack space:
```asm
; Go function prologue (x86-64)
mov rcx, qword ptr gs:[0x28]        ; load TLS (Thread Local Storage)
mov rcx, qword ptr [rcx - 8]         ; load current goroutine (g)
cmp rsp, qword ptr [rcx + 0x10]      ; compare RSP with g.stackguard0
jbe 0x48a1b0                         ; jump to stack split if insufficient
...
0x48a1b0:
call runtime.morestack_noctxt        ; allocate larger stack and copy frame
```
- In stripped binaries, xrefs to `runtime.morestack` identify almost every function entry point.

---

## 2. PC-Line Table (`pclntab`) Recovery

Even stripped Go binaries usually contain `.gopclntab`, a table mapping program counter addresses to line numbers, source files, and function names for stack traces and panic unwinding.

### Magic Signatures
Inspect `.gopclntab` or search binary bytes for magic headers:
- Go 1.2–1.15: `\xFB\xFF\xFF\xFF` (`0xFFFFFFFB`) with quantum=1 or 4, ptrsize=4 or 8.
- Go 1.16–1.17: `\xFA\xFF\xFF\xFF` (`0xFFFFFFFA`).
- Go 1.18–1.19: `\xF0\xFF\xFF\xFF` (`0xFFFFFFF0`).
- Go 1.20+: `\xF1\xFF\xFF\xFF` or updated header layout.

### Information Recoverable from `pclntab`:
1. **Function Names**: Full package-qualified names (e.g., `main.decryptPayload`, `crypto/aes.encryptBlockGo`).
2. **Function Bounds**: Entry address and end address.
3. **Source Files**: Complete path of the build directory and source files (e.g., `/Users/dev/project/cmd/server/main.go`).
4. **Source Line Numbers**: Maps instruction offsets directly to original Go source code lines.

### Recovery Tools:
- **GoReSym**: CLI Go symbol recovery utility.
- **IDA Pro / Ghidra Plugins**: `go_parser`, `Ghidra Go script`.
- **REA MCP**: `inspect_go_binary` extracts compiler version, module paths, and build settings without opening a disassembler.

---

## 3. Core Go Data Structures

### Go Strings (`string`)
Total size: 16 bytes (on 64-bit).
```c
struct GoString {
    const char* str_ptr;    // Pointer to UTF-8 bytes in .rodata
    int64_t     len;        // Length in bytes (NOT null-terminated)
};
```
- Passed as two registers in Go 1.17+ ABI (e.g., `RAX` = pointer, `RBX` = length).

### Go Slices (`[]T`)
Total size: 24 bytes (on 64-bit).
```c
struct GoSlice {
    void*   data_ptr;       // Pointer to backing array
    int64_t len;            // Current number of elements
    int64_t cap;            // Capacity of allocated backing array
};
```
- Passed as three registers (e.g., `RAX` = data, `RBX` = len, `RCX` = cap).

### Go Interfaces
Go has two interface layouts in `runtime`:

1. **Empty Interface (`any` / `interface{}`)**:
   ```c
   struct eface {
       struct _type* _type; // Pointer to concrete type descriptor
       void*         data;  // Pointer to data or value itself if fits
   };
   ```

2. **Non-Empty Interface (`iface`)**:
   ```c
   struct iface {
       struct itab* tab;    // Pointer to interface table
       void*        data;   // Pointer to concrete value
   };

   struct itab {
       struct InterType* inter;    // Interface type descriptor
       struct _type*     _type;    // Concrete type descriptor
       uint32_t          hash;     // Copy of _type.hash for fast type assertion
       uint32_t          _pad;
       void*             fun[1];   // Function pointers for interface methods
   };
   ```

---

## 4. Type Descriptors (`runtime._type`)

Go embeds rich runtime type information (RTTI) in `.rodata` for reflection (`reflect.Type`):
```c
struct _type {
    uintptr_t size;         // Size of type in bytes
    uintptr_t ptrdata;      // Bytes of type that may contain pointers (for GC)
    uint32_t  hash;         // Type hash for fast comparisons
    uint8_t   tflag;        // Extra type flags
    uint8_t   align;        // Alignment
    uint8_t   fieldAlign;
    uint8_t   kind;         // Type kind (Bool, Int, Struct, Pointer, etc.)
    void*     equal;        // Equality function pointer
    void*     gcdata;       // Garbage collection bitmap
    int32_t   str;          // Name offset in string table
    int32_t   ptrToThis;    // Offset to pointer type descriptor
};
```
- **Type Kind Enums**:
  `1` = Bool, `2` = Int, `6` = Uint, `14` = Float64, `22` = Array, `23` = Chan, `24` = Func, `25` = Interface, `26` = Map, `27` = Pointer, `28` = Slice, `29` = String, `30` = Struct.

---

## 5. Goroutines & Concurrency Primitives

- **Goroutine Creation**: Call to `runtime.newproc(fn, argsize)`.
- **Channels**:
  - `runtime.makechan(type, size)`: Channel allocation.
  - `runtime.chansend1(chan, elem_ptr)`: Sending on channel (`ch <- val`).
  - `runtime.chanrecv1(chan, elem_ptr)`: Receiving on channel (`val = <-ch`).
  - `runtime.selectgo(...)`: Non-blocking channel select.
- **Mutex**: `sync.Mutex.Lock()` calls `sync.(*Mutex).lockSlow` when contended.
