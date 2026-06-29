; c2_abi.asm — FFmpeg-style cross-platform ABI macros for c2ImageD11 NASM kernels.
;
; Include this header at the top of every .asm kernel file.
; Use DECLARE_FUNC name to declare the public entry point.
; Use ARG1..ARG6, XMM_ARG1..XMM_ARG2 for register-passed arguments.
; Use STACK_ARG(N) for stack-passed arguments beyond register capacity.
;
; System V AMD64 (Linux): rdi/rsi/rdx/rcx/r8/r9, xmm0-xmm7, stack at [rsp+8]
; Microsoft x64 (Windows): rcx/rdx/r8/r9, xmm0-xmm3, stack at [rsp+40]

%ifndef C2_ABI_ASM
%define C2_ABI_ASM

DEFAULT REL

%macro DECLARE_FUNC 1
    global %1
    %1:
%endmacro

%ifidn __OUTPUT_FORMAT__, win64
    ; ── Windows x64 ABI ──
    %define ARG1 rcx
    %define ARG2 rdx
    %define ARG3 r8
    %define ARG4 r9
    %define XMM_ARG1 xmm0
    %define XMM_ARG2 xmm1
    %define XMM_ARG3 xmm2
    %define STACK_ARG1 qword [rsp + 40]
    %define STACK_ARG2 qword [rsp + 48]
    %define STACK_ARG3 qword [rsp + 56]
    %define STACK_ARG4 qword [rsp + 64]
    %define STACK_ARG5 qword [rsp + 72]
%else
    ; ── System V AMD64 ABI (Linux/macOS) ──
    %define ARG1 rdi
    %define ARG2 rsi
    %define ARG3 rdx
    %define ARG4 rcx
    %define ARG5 r8
    %define ARG6 r9
    %define XMM_ARG1 xmm0
    %define XMM_ARG2 xmm1
    %define XMM_ARG3 xmm2
    %define STACK_ARG1 qword [rsp + 8]
    %define STACK_ARG2 qword [rsp + 16]
    %define STACK_ARG3 qword [rsp + 24]
    %define STACK_ARG4 qword [rsp + 32]
    %define STACK_ARG5 qword [rsp + 40]
%endif

%endif  ; C2_ABI_ASM
