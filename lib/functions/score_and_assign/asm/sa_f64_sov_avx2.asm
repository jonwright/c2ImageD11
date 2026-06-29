SECTION .note.GNU-stack noalloc noexec nowrite progbits
%include "c2_abi.asm"
SECTION .text

%ifidn __OUTPUT_FORMAT__, win64
global sa_inner_f64_sov_avx2
call_sa_inner_f64_sov_avx2:  ; @call_sa_inner_f64_sov_avx2:
jmp	sa_inner_f64_sov_avx2
SECTION .text
align 4
CPI1_0:
dd	1  ; 0x1
times 12 db 0
CPI1_1:
times 16 db 255
SECTION .text
align 4
sa_inner_f64_sov_avx2:  ; @sa_inner_f64_sov_avx2:
push	r15
push	r14
push	r13
push	r12
push	rsi
push	rdi
push	rbp
push	rbx
sub	rsp, 552
vmovapd	oword [rsp + 528], xmm15  ; 16-byte Spill
vmovapd	oword [rsp + 512], xmm14  ; 16-byte Spill
vmovdqa	oword [rsp + 496], xmm13  ; 16-byte Spill
vmovdqa	oword [rsp + 480], xmm12  ; 16-byte Spill
vmovdqa	oword [rsp + 464], xmm11  ; 16-byte Spill
vmovapd	oword [rsp + 448], xmm10  ; 16-byte Spill
vmovapd	oword [rsp + 432], xmm9  ; 16-byte Spill
vmovapd	oword [rsp + 416], xmm8  ; 16-byte Spill
vmovapd	oword [rsp + 400], xmm7  ; 16-byte Spill
vmovapd	oword [rsp + 384], xmm6  ; 16-byte Spill
mov	r10, qword [rsp + 688]
mov	r13d, dword [rsp + 680]
mov	rdi, qword [rsp + 672]
mov	rsi, qword [rsp + 664]
vmovsd	xmm0, qword [rsp + 656]  ; xmm0 = mem[0],zero
vmulsd	xmm0, xmm0, xmm0
vmovapd	oword [rsp + 48], xmm0  ; 16-byte Spill
vbroadcastsd	ymm1, xmm0
cmp	r10, 4
jge	BB1_23
xor	r12d, r12d
xor	eax, eax
BB1_2:
mov	r11, r10
sub	r11, r12
jle	BB1_30
cmp	r11, 12
jae	BB1_5
mov	r14, r12
vmovapd	xmm5, oword [rsp + 48]  ; 16-byte Reload
BB1_19:
sub	r10, r14
lea	r11, [rdi + 4*r14]
lea	rsi, [rsi + 8*r14]
lea	r9, [r9 + 8*r14]
lea	r8, [r8 + 8*r14]
lea	rdx, [rdx + 8*r14]
xor	edi, edi
jmp	BB1_20
align 4
BB1_22:  ; in Loop: Header=BB1_20 Depth=1:
mov	dword [r11 + 4*rdi], r13d
vmovsd	qword [rsi + 8*rdi], xmm0
inc	eax
BB1_29:  ; in Loop: Header=BB1_20 Depth=1:
inc	rdi
cmp	r10, rdi
je	BB1_30
BB1_20:  ; =>This Inner Loop Header: Depth=1:
vmovddup	xmm0, qword [rdx + 8*rdi]  ; xmm0 = mem[0,0]
vmulsd	xmm1, xmm0, qword [rcx]
vmovddup	xmm2, qword [r8 + 8*rdi]  ; xmm2 = mem[0,0]
vmovsd	xmm3, qword [rcx + 24]  ; xmm3 = mem[0],zero
vmovsd	xmm4, qword [rcx + 32]  ; xmm4 = mem[0],zero
vmovhpd	xmm3, xmm3, qword [rcx + 48]  ; xmm3 = xmm3[0],mem[0]
vmulpd	xmm0, xmm3, xmm0
vmovhpd	xmm3, xmm4, qword [rcx + 56]  ; xmm3 = xmm4[0],mem[0]
vfmadd213pd	xmm3, xmm2, xmm0  ; xmm3 = (xmm2 * xmm3) + xmm0
vfmadd132sd	xmm2, xmm1, qword [rcx + 8]  ; xmm2 = (xmm2 * mem) + xmm1
vmovddup	xmm0, qword [r9 + 8*rdi]  ; xmm0 = mem[0,0]
vmovsd	xmm1, qword [rcx + 40]  ; xmm1 = mem[0],zero
vmovhpd	xmm1, xmm1, qword [rcx + 64]  ; xmm1 = xmm1[0],mem[0]
vfmadd213pd	xmm1, xmm0, xmm3  ; xmm1 = (xmm0 * xmm1) + xmm3
vfmadd132sd	xmm0, xmm2, qword [rcx + 16]  ; xmm0 = (xmm0 * mem) + xmm2
vroundsd	xmm2, xmm0, xmm0, 12
vsubsd	xmm0, xmm0, xmm2
vroundpd	xmm2, xmm1, 12
vsubpd	xmm1, xmm1, xmm2
vmulpd	xmm1, xmm1, xmm1
vfmadd213sd	xmm0, xmm0, xmm1  ; xmm0 = (xmm0 * xmm0) + xmm1
vshufpd	xmm1, xmm1, xmm1, 1  ; xmm1 = xmm1[1,0]
vaddsd	xmm0, xmm0, xmm1
vucomisd	xmm0, xmm5
jae	BB1_27
;  ; in Loop: Header=BB1_20 Depth=1:
vucomisd	xmm0, qword [rsi + 8*rdi]
jb	BB1_22
BB1_27:  ; in Loop: Header=BB1_20 Depth=1:
cmp	dword [r11 + 4*rdi], r13d
jne	BB1_29
;  ; in Loop: Header=BB1_20 Depth=1:
mov	dword [r11 + 4*rdi], -1
jmp	BB1_29
BB1_23:
vbroadcastsd	ymm2, qword [rcx]
vbroadcastsd	ymm3, qword [rcx + 8]
vbroadcastsd	ymm4, qword [rcx + 16]
vbroadcastsd	ymm5, qword [rcx + 24]
vbroadcastsd	ymm6, qword [rcx + 32]
vbroadcastsd	ymm7, qword [rcx + 40]
vbroadcastsd	ymm8, qword [rcx + 48]
vbroadcastsd	ymm9, qword [rcx + 56]
vbroadcastsd	ymm10, qword [rcx + 64]
vmovd	xmm0, r13d
vpbroadcastd	xmm11, xmm0
xor	r11d, r11d
xor	eax, eax
jmp	BB1_24
align 4
BB1_26:  ; in Loop: Header=BB1_24 Depth=1:
vmovdqu	xmm0, oword [rdi + 4*r11]
vpcmpeqd	xmm12, xmm11, xmm0
mov	ebp, ebx
shl	ebp, 28
sar	ebp, 31
mov	r14d, ebx
shl	r14d, 29
sar	r14d, 31
mov	r15d, ebx
shl	r15d, 30
sar	r15d, 31
and	ebx, 1
neg	ebx
vmovd	xmm13, ebx
vpinsrd	xmm13, xmm13, r15d, 1
vpinsrd	xmm13, xmm13, r14d, 2
vpinsrd	xmm13, xmm13, ebp, 3
vpblendvb	xmm0, xmm0, xmm11, xmm13
vpandn	xmm12, xmm13, xmm12
vpblendvb	xmm0, xmm0, oword [rel CPI1_1], xmm12
vmovdqu	oword [rdi + 4*r11], xmm0
lea	r12, [r11 + 4]
add	r11, 8
cmp	r11, r10
mov	r11, r12
jg	BB1_2
BB1_24:  ; =>This Inner Loop Header: Depth=1:
vmovupd	ymm0, yword [rdx + 8*r11]
vmovupd	ymm13, yword [r8 + 8*r11]
vmovupd	ymm14, yword [r9 + 8*r11]
vmulpd	ymm15, ymm14, ymm4
vfmadd231pd	ymm15, ymm3, ymm13  ; ymm15 = (ymm3 * ymm13) + ymm15
vfmadd231pd	ymm15, ymm2, ymm0  ; ymm15 = (ymm2 * ymm0) + ymm15
vmulpd	ymm12, ymm14, ymm7
vfmadd231pd	ymm12, ymm6, ymm13  ; ymm12 = (ymm6 * ymm13) + ymm12
vfmadd231pd	ymm12, ymm5, ymm0  ; ymm12 = (ymm5 * ymm0) + ymm12
vmulpd	ymm14, ymm14, ymm10
vfmadd231pd	ymm14, ymm9, ymm13  ; ymm14 = (ymm9 * ymm13) + ymm14
vfmadd231pd	ymm14, ymm8, ymm0  ; ymm14 = (ymm8 * ymm0) + ymm14
vroundpd	ymm0, ymm15, 8
vsubpd	ymm13, ymm15, ymm0
vroundpd	ymm0, ymm12, 8
vsubpd	ymm12, ymm12, ymm0
vroundpd	ymm0, ymm14, 8
vsubpd	ymm0, ymm14, ymm0
vmulpd	ymm0, ymm0, ymm0
vfmadd231pd	ymm0, ymm12, ymm12  ; ymm0 = (ymm12 * ymm12) + ymm0
vfmadd231pd	ymm0, ymm13, ymm13  ; ymm0 = (ymm13 * ymm13) + ymm0
vmovupd	ymm13, yword [rsi + 8*r11]
vcmpltpd	ymm12, ymm0, ymm13
vcmpltpd	ymm14, ymm0, ymm1
vandpd	ymm14, ymm14, ymm12
vmovmskpd	ebx, ymm14
test	ebx, ebx
je	BB1_26
;  ; in Loop: Header=BB1_24 Depth=1:
vextractf128	xmm12, ymm14, 1
vpackssdw	xmm12, xmm14, xmm12
popcnt	ebp, ebx
add	eax, ebp
vpslld	xmm12, xmm12, 31
vpmovsxdq	ymm12, xmm12
vblendvpd	ymm0, ymm13, ymm0, ymm12
vmovupd	yword [rsi + 8*r11], ymm0
jmp	BB1_26
BB1_5:
mov	qword [rsp + 40], r11  ; 8-byte Spill
lea	rbp, [rdi + 4*r12]
lea	r11, [rdi + 4*r10]
lea	rbx, [rsi + 8*r12]
lea	r14, [rsi + 8*r10]
mov	qword [rsp + 288], r14  ; 8-byte Spill
lea	r15, [rcx + 72]
mov	qword [rsp + 128], r15  ; 8-byte Spill
lea	r15, [rdx + 8*r12]
mov	qword [rsp + 96], r15  ; 8-byte Spill
lea	r15, [rdx + 8*r10]
mov	qword [rsp + 160], r15  ; 8-byte Spill
lea	r13, [r8 + 8*r12]
mov	qword [rsp + 16], r13  ; 8-byte Spill
lea	r13, [r8 + 8*r10]
mov	qword [rsp + 256], r13  ; 8-byte Spill
cmp	rbp, r14
setb	byte [rsp + 352]  ; 1-byte Folded Spill
cmp	rbx, r11
setb	byte [rsp + 320]  ; 1-byte Folded Spill
mov	r13, qword [rsp + 128]  ; 8-byte Reload
cmp	rbp, r13
setb	byte [rsp + 224]  ; 1-byte Folded Spill
cmp	r11, rcx
seta	byte [rsp + 192]  ; 1-byte Folded Spill
lea	r14, [r9 + 8*r10]
cmp	rbp, r15
setb	byte [rsp + 80]  ; 1-byte Folded Spill
cmp	qword [rsp + 96], r11  ; 8-byte Folded Reload
setb	byte [rsp + 64]  ; 1-byte Folded Spill
mov	r15, qword [rsp + 256]  ; 8-byte Reload
cmp	rbp, r15
setb	byte [rsp + 15]  ; 1-byte Folded Spill
cmp	qword [rsp + 16], r11  ; 8-byte Folded Reload
setb	byte [rsp + 14]  ; 1-byte Folded Spill
cmp	rbp, r14
lea	rbp, [r9 + 8*r12]
setb	byte [rsp + 13]  ; 1-byte Folded Spill
cmp	rbp, r11
setb	byte [rsp + 12]  ; 1-byte Folded Spill
cmp	rbx, r13
setb	byte [rsp + 128]  ; 1-byte Folded Spill
mov	r11, qword [rsp + 288]  ; 8-byte Reload
cmp	r11, rcx
seta	byte [rsp + 11]  ; 1-byte Folded Spill
cmp	rbx, qword [rsp + 160]  ; 8-byte Folded Reload
setb	byte [rsp + 160]  ; 1-byte Folded Spill
cmp	qword [rsp + 96], r11  ; 8-byte Folded Reload
mov	r13, r11
setb	r11b
cmp	rbx, r15
setb	byte [rsp + 96]  ; 1-byte Folded Spill
cmp	qword [rsp + 16], r13  ; 8-byte Folded Reload
setb	r15b
cmp	rbx, r14
setb	bl
cmp	rbp, r13
setb	r14b
movzx	ebp, byte [rsp + 320]  ; 1-byte Folded Reload
test	byte [rsp + 352], bpl  ; 1-byte Folded Reload
vmovapd	xmm5, oword [rsp + 48]  ; 16-byte Reload
jne	BB1_6
movzx	ebp, byte [rsp + 192]  ; 1-byte Folded Reload
and	byte [rsp + 224], bpl  ; 1-byte Folded Spill
jne	BB1_6
movzx	ebp, byte [rsp + 64]  ; 1-byte Folded Reload
and	byte [rsp + 80], bpl  ; 1-byte Folded Spill
jne	BB1_6
movzx	ebp, byte [rsp + 14]  ; 1-byte Folded Reload
and	byte [rsp + 15], bpl  ; 1-byte Folded Spill
jne	BB1_6
movzx	ebp, byte [rsp + 12]  ; 1-byte Folded Reload
and	byte [rsp + 13], bpl  ; 1-byte Folded Spill
jne	BB1_6
movzx	ebp, byte [rsp + 11]  ; 1-byte Folded Reload
and	byte [rsp + 128], bpl  ; 1-byte Folded Spill
jne	BB1_6
and	byte [rsp + 160], r11b  ; 1-byte Folded Spill
jne	BB1_6
and	byte [rsp + 96], r15b  ; 1-byte Folded Spill
jne	BB1_6
and	bl, r14b
mov	r13d, dword [rsp + 680]
jne	BB1_15
mov	r15, qword [rsp + 40]  ; 8-byte Reload
and	r15, -8
lea	r14, [r12 + r15]
vmovd	xmm13, eax
vmovd	xmm0, r13d
vpbroadcastd	xmm0, xmm0
vmovdqa	oword [rsp + 80], xmm0  ; 16-byte Spill
vbroadcastsd	ymm0, qword [rcx]
vmovups	yword [rsp + 96], ymm0  ; 32-byte Spill
vbroadcastsd	ymm0, qword [rcx + 8]
vmovups	yword [rsp + 352], ymm0  ; 32-byte Spill
vbroadcastsd	ymm0, qword [rcx + 16]
vmovups	yword [rsp + 320], ymm0  ; 32-byte Spill
vbroadcastsd	ymm0, qword [rcx + 24]
vmovups	yword [rsp + 288], ymm0  ; 32-byte Spill
vbroadcastsd	ymm0, qword [rcx + 32]
vmovups	yword [rsp + 160], ymm0  ; 32-byte Spill
vbroadcastsd	ymm0, qword [rcx + 40]
vmovups	yword [rsp + 256], ymm0  ; 32-byte Spill
vbroadcastsd	ymm0, qword [rcx + 48]
vmovups	yword [rsp + 128], ymm0  ; 32-byte Spill
vbroadcastsd	ymm0, qword [rcx + 56]
vmovups	yword [rsp + 224], ymm0  ; 32-byte Spill
vpbroadcastq	ymm0, qword [rcx + 64]
vmovdqu	yword [rsp + 192], ymm0  ; 32-byte Spill
lea	rax, [rdx + 8*r12 + 32]
lea	r13, [r8 + 8*r12 + 32]
lea	rbp, [r9 + 8*r12 + 32]
lea	rbx, [rsi + 8*r12]
add	rbx, 32
lea	r12, [rdi + 4*r12]
add	r12, 16
vpxor	xmm0, xmm0, xmm0
xor	r11d, r11d
vpbroadcastd	xmm3, dword [rel CPI1_0]  ; xmm3 = [1,1,1,1]
vmovdqa	oword [rsp + 64], xmm3  ; 16-byte Spill
vmovdqa	xmm2, oword [rsp + 80]  ; 16-byte Reload
align 4
BB1_17:  ; =>This Inner Loop Header: Depth=1:
vmovdqa	oword [rsp + 16], xmm0  ; 16-byte Spill
vmovupd	ymm0, yword [rax + 8*r11 - 32]
vmovupd	ymm4, yword [rax + 8*r11]
vmovupd	ymm5, yword [rsp + 96]  ; 32-byte Reload
vmulpd	ymm7, ymm0, ymm5
vmulpd	ymm8, ymm4, ymm5
vmovupd	ymm6, yword [r13 + 8*r11 - 32]
vmovupd	ymm5, yword [r13 + 8*r11]
vmovupd	ymm9, yword [rsp + 352]  ; 32-byte Reload
vfmadd231pd	ymm7, ymm6, ymm9  ; ymm7 = (ymm6 * ymm9) + ymm7
vfmadd231pd	ymm8, ymm5, ymm9  ; ymm8 = (ymm5 * ymm9) + ymm8
vmovupd	ymm9, yword [rbp + 8*r11 - 32]
vmovupd	ymm10, yword [rbp + 8*r11]
vmovupd	ymm11, yword [rsp + 320]  ; 32-byte Reload
vfmadd231pd	ymm7, ymm9, ymm11  ; ymm7 = (ymm9 * ymm11) + ymm7
vfmadd231pd	ymm8, ymm10, ymm11  ; ymm8 = (ymm10 * ymm11) + ymm8
vroundpd	ymm11, ymm7, 12
vroundpd	ymm12, ymm8, 12
vsubpd	ymm7, ymm7, ymm11
vsubpd	ymm8, ymm8, ymm12
vmovupd	ymm12, yword [rsp + 288]  ; 32-byte Reload
vmulpd	ymm11, ymm12, ymm0
vmulpd	ymm12, ymm12, ymm4
vmovupd	ymm14, yword [rsp + 160]  ; 32-byte Reload
vfmadd231pd	ymm11, ymm14, ymm6  ; ymm11 = (ymm14 * ymm6) + ymm11
vfmadd231pd	ymm12, ymm14, ymm5  ; ymm12 = (ymm14 * ymm5) + ymm12
vmovupd	ymm14, yword [rsp + 256]  ; 32-byte Reload
vfmadd231pd	ymm11, ymm14, ymm9  ; ymm11 = (ymm14 * ymm9) + ymm11
vfmadd231pd	ymm12, ymm14, ymm10  ; ymm12 = (ymm14 * ymm10) + ymm12
vroundpd	ymm14, ymm11, 12
vroundpd	ymm15, ymm12, 12
vsubpd	ymm11, ymm11, ymm14
vsubpd	ymm12, ymm12, ymm15
vmovupd	ymm14, yword [rsp + 128]  ; 32-byte Reload
vmulpd	ymm0, ymm14, ymm0
vmulpd	ymm4, ymm14, ymm4
vmovupd	ymm14, yword [rsp + 224]  ; 32-byte Reload
vfmadd231pd	ymm0, ymm14, ymm6  ; ymm0 = (ymm14 * ymm6) + ymm0
vfmadd231pd	ymm4, ymm14, ymm5  ; ymm4 = (ymm14 * ymm5) + ymm4
vmovupd	ymm5, yword [rsp + 192]  ; 32-byte Reload
vfmadd231pd	ymm0, ymm5, ymm9  ; ymm0 = (ymm5 * ymm9) + ymm0
vfmadd231pd	ymm4, ymm5, ymm10  ; ymm4 = (ymm5 * ymm10) + ymm4
vroundpd	ymm5, ymm0, 12
vroundpd	ymm6, ymm4, 12
vsubpd	ymm5, ymm0, ymm5
vsubpd	ymm6, ymm4, ymm6
vmulpd	ymm0, ymm7, ymm7
vmulpd	ymm4, ymm8, ymm8
vfmadd231pd	ymm0, ymm11, ymm11  ; ymm0 = (ymm11 * ymm11) + ymm0
vfmadd231pd	ymm4, ymm12, ymm12  ; ymm4 = (ymm12 * ymm12) + ymm4
vfmadd231pd	ymm0, ymm5, ymm5  ; ymm0 = (ymm5 * ymm5) + ymm0
vfmadd231pd	ymm4, ymm6, ymm6  ; ymm4 = (ymm6 * ymm6) + ymm4
vcmplepd	ymm7, ymm1, ymm0
vcmpltpd	ymm8, ymm0, ymm1
vcmplepd	ymm9, ymm1, ymm4
vmaskmovpd	ymm10, ymm8, yword [rbx + 8*r11 - 32]
vcmpltpd	ymm5, ymm4, ymm1
vmaskmovpd	ymm6, ymm5, yword [rbx + 8*r11]
vcmplepd	ymm11, ymm10, ymm0
vcmplepd	ymm12, ymm6, ymm4
vandpd	ymm11, ymm8, ymm11
vorpd	ymm7, ymm11, ymm7
vandpd	ymm11, ymm12, ymm5
vorpd	ymm9, ymm11, ymm9
vextractf128	xmm11, ymm7, 1
vpackssdw	xmm7, xmm7, xmm11
vextractf128	xmm11, ymm9, 1
vpmaskmovd	xmm12, xmm7, oword [r12 + 4*r11 - 16]
vpackssdw	xmm9, xmm9, xmm11
vpmaskmovd	xmm11, xmm9, oword [r12 + 4*r11]
vpcmpeqd	xmm12, xmm12, xmm2
vpcmpeqd	xmm11, xmm11, xmm2
vpand	xmm14, xmm12, xmm7
vpand	xmm15, xmm9, xmm11
vmovapd	ymm3, ymm1
vpcmpeqd	xmm1, xmm1, xmm1
vpmaskmovd	oword [r12 + 4*r11 - 16], xmm14, xmm1
vpmaskmovd	oword [r12 + 4*r11], xmm15, xmm1
vcmpltpd	ymm10, ymm0, ymm10
vandpd	ymm8, ymm8, ymm10
vextractf128	xmm10, ymm8, 1
vpackssdw	xmm10, xmm8, xmm10
vpmaskmovd	oword [r12 + 4*r11 - 16], xmm10, xmm2
vcmpltpd	ymm6, ymm4, ymm6
vandpd	ymm5, ymm5, ymm6
vextractf128	xmm6, ymm5, 1
vpackssdw	xmm6, xmm5, xmm6
vpmaskmovd	oword [r12 + 4*r11], xmm6, xmm2
vmaskmovpd	yword [rbx + 8*r11 - 32], ymm8, ymm0
vmaskmovpd	yword [rbx + 8*r11], ymm5, ymm4
vpxor	xmm0, xmm7, xmm1
vpor	xmm0, xmm12, xmm0
vpandn	xmm0, xmm14, xmm0
vmovdqa	xmm4, oword [rsp + 64]  ; 16-byte Reload
vpand	xmm0, xmm0, xmm4
vpaddd	xmm13, xmm13, xmm0
vpxor	xmm0, xmm9, xmm1
vmovapd	ymm1, ymm3
vpor	xmm0, xmm11, xmm0
vpandn	xmm0, xmm15, xmm0
vpand	xmm0, xmm0, xmm4
vmovdqa	xmm3, oword [rsp + 16]  ; 16-byte Reload
vpaddd	xmm3, xmm3, xmm0
vmovdqa	oword [rsp + 16], xmm3  ; 16-byte Spill
vmovdqa	xmm0, oword [rsp + 16]  ; 16-byte Reload
add	r11, 8
cmp	r15, r11
jne	BB1_17
vpaddd	xmm0, xmm13, xmm0
vpshufd	xmm1, xmm0, 238  ; xmm1 = xmm0[2,3,2,3]
vpaddd	xmm0, xmm0, xmm1
vpshufd	xmm1, xmm0, 85  ; xmm1 = xmm0[1,1,1,1]
vpaddd	xmm0, xmm0, xmm1
vmovd	eax, xmm0
cmp	qword [rsp + 40], r15  ; 8-byte Folded Reload
mov	r13d, dword [rsp + 680]
vmovapd	xmm5, oword [rsp + 48]  ; 16-byte Reload
jne	BB1_19
BB1_30:
vmovaps	xmm6, oword [rsp + 384]  ; 16-byte Reload
vmovaps	xmm7, oword [rsp + 400]  ; 16-byte Reload
vmovaps	xmm8, oword [rsp + 416]  ; 16-byte Reload
vmovaps	xmm9, oword [rsp + 432]  ; 16-byte Reload
vmovaps	xmm10, oword [rsp + 448]  ; 16-byte Reload
vmovaps	xmm11, oword [rsp + 464]  ; 16-byte Reload
vmovaps	xmm12, oword [rsp + 480]  ; 16-byte Reload
vmovaps	xmm13, oword [rsp + 496]  ; 16-byte Reload
vmovaps	xmm14, oword [rsp + 512]  ; 16-byte Reload
vmovaps	xmm15, oword [rsp + 528]  ; 16-byte Reload
add	rsp, 552
pop	rbx
pop	rbp
pop	rdi
pop	rsi
pop	r12
pop	r13
pop	r14
pop	r15
vzeroupper
ret
BB1_6:
mov	r14, r12
mov	r13d, dword [rsp + 680]
jmp	BB1_19
BB1_15:
mov	r14, r12
jmp	BB1_19

%else
global sa_inner_f64_sov_avx2
call_sa_inner_f64_sov_avx2:  ; @call_sa_inner_f64_sov_avx2:
jmp	sa_inner_f64_sov_avx2
func_end0:
SECTION .rodata
align 4
CPI1_0:
dd	1  ; 0x1
SECTION .rodata
align 4
CPI1_1:
times 16 db 255
SECTION .text
align 4
sa_inner_f64_sov_avx2:  ; @sa_inner_f64_sov_avx2:
push	rbp
push	r15
push	r14
push	r13
push	r12
push	rbx
sub	rsp, 264
mov	r10, qword [rsp + 328]
mov	r13d, dword [rsp + 320]
vmulsd	xmm0, xmm0, xmm0
vmovapd	oword [rsp - 96], xmm0  ; 16-byte Spill
vbroadcastsd	ymm1, xmm0
cmp	r10, 4
jge	BB1_22
xor	r12d, r12d
xor	eax, eax
BB1_2:
mov	r11, r10
sub	r11, r12
jle	BB1_29
cmp	r11, 12
jae	BB1_5
vmovapd	xmm5, oword [rsp - 96]  ; 16-byte Reload
BB1_18:
sub	r10, r12
lea	r9, [r9 + 4*r12]
lea	r8, [r8 + 8*r12]
lea	rcx, [rcx + 8*r12]
lea	rdx, [rdx + 8*r12]
lea	rsi, [rsi + 8*r12]
xor	ebx, ebx
jmp	BB1_19
align 4
BB1_21:  ; in Loop: Header=BB1_19 Depth=1:
mov	dword [r9 + 4*rbx], r13d
vmovsd	qword [r8 + 8*rbx], xmm0
inc	eax
BB1_28:  ; in Loop: Header=BB1_19 Depth=1:
inc	rbx
cmp	r10, rbx
je	BB1_29
BB1_19:  ; =>This Inner Loop Header: Depth=1:
vmovddup	xmm0, qword [rsi + 8*rbx]  ; xmm0 = mem[0,0]
vmulsd	xmm1, xmm0, qword [rdi]
vmovddup	xmm2, qword [rdx + 8*rbx]  ; xmm2 = mem[0,0]
vmovsd	xmm3, qword [rdi + 24]  ; xmm3 = mem[0],zero
vmovsd	xmm4, qword [rdi + 32]  ; xmm4 = mem[0],zero
vmovhpd	xmm3, xmm3, qword [rdi + 48]  ; xmm3 = xmm3[0],mem[0]
vmulpd	xmm0, xmm3, xmm0
vmovhpd	xmm3, xmm4, qword [rdi + 56]  ; xmm3 = xmm4[0],mem[0]
vfmadd213pd	xmm3, xmm2, xmm0  ; xmm3 = (xmm2 * xmm3) + xmm0
vfmadd132sd	xmm2, xmm1, qword [rdi + 8]  ; xmm2 = (xmm2 * mem) + xmm1
vmovddup	xmm0, qword [rcx + 8*rbx]  ; xmm0 = mem[0,0]
vmovsd	xmm1, qword [rdi + 40]  ; xmm1 = mem[0],zero
vmovhpd	xmm1, xmm1, qword [rdi + 64]  ; xmm1 = xmm1[0],mem[0]
vfmadd213pd	xmm1, xmm0, xmm3  ; xmm1 = (xmm0 * xmm1) + xmm3
vfmadd132sd	xmm0, xmm2, qword [rdi + 16]  ; xmm0 = (xmm0 * mem) + xmm2
vroundsd	xmm2, xmm0, xmm0, 12
vsubsd	xmm0, xmm0, xmm2
vroundpd	xmm2, xmm1, 12
vsubpd	xmm1, xmm1, xmm2
vmulpd	xmm1, xmm1, xmm1
vfmadd213sd	xmm0, xmm0, xmm1  ; xmm0 = (xmm0 * xmm0) + xmm1
vshufpd	xmm1, xmm1, xmm1, 1  ; xmm1 = xmm1[1,0]
vaddsd	xmm0, xmm0, xmm1
vucomisd	xmm0, xmm5
jae	BB1_26
;  ; in Loop: Header=BB1_19 Depth=1:
vucomisd	xmm0, qword [r8 + 8*rbx]
jb	BB1_21
BB1_26:  ; in Loop: Header=BB1_19 Depth=1:
cmp	dword [r9 + 4*rbx], r13d
jne	BB1_28
;  ; in Loop: Header=BB1_19 Depth=1:
mov	dword [r9 + 4*rbx], -1
jmp	BB1_28
BB1_22:
vbroadcastsd	ymm2, qword [rdi]
vbroadcastsd	ymm3, qword [rdi + 8]
vbroadcastsd	ymm4, qword [rdi + 16]
vbroadcastsd	ymm5, qword [rdi + 24]
vbroadcastsd	ymm6, qword [rdi + 32]
vbroadcastsd	ymm7, qword [rdi + 40]
vbroadcastsd	ymm8, qword [rdi + 48]
vbroadcastsd	ymm9, qword [rdi + 56]
vbroadcastsd	ymm10, qword [rdi + 64]
vmovd	xmm0, r13d
vpbroadcastd	xmm11, xmm0
xor	ebx, ebx
xor	eax, eax
jmp	BB1_23
align 4
BB1_25:  ; in Loop: Header=BB1_23 Depth=1:
vmovdqu	xmm0, oword [r9 + 4*rbx]
vpcmpeqd	xmm12, xmm11, xmm0
mov	r11d, ebp
shl	r11d, 28
sar	r11d, 31
mov	r14d, ebp
shl	r14d, 29
sar	r14d, 31
mov	r15d, ebp
shl	r15d, 30
sar	r15d, 31
and	ebp, 1
neg	ebp
vmovd	xmm13, ebp
vpinsrd	xmm13, xmm13, r15d, 1
vpinsrd	xmm13, xmm13, r14d, 2
vpinsrd	xmm13, xmm13, r11d, 3
vpblendvb	xmm0, xmm0, xmm11, xmm13
vpandn	xmm12, xmm13, xmm12
vpblendvb	xmm0, xmm0, oword [rel CPI1_1], xmm12
vmovdqu	oword [r9 + 4*rbx], xmm0
lea	r12, [rbx + 4]
add	rbx, 8
cmp	rbx, r10
mov	rbx, r12
jg	BB1_2
BB1_23:  ; =>This Inner Loop Header: Depth=1:
vmovupd	ymm0, yword [rsi + 8*rbx]
vmovupd	ymm13, yword [rdx + 8*rbx]
vmovupd	ymm14, yword [rcx + 8*rbx]
vmulpd	ymm15, ymm14, ymm4
vfmadd231pd	ymm15, ymm3, ymm13  ; ymm15 = (ymm3 * ymm13) + ymm15
vfmadd231pd	ymm15, ymm2, ymm0  ; ymm15 = (ymm2 * ymm0) + ymm15
vmulpd	ymm12, ymm14, ymm7
vfmadd231pd	ymm12, ymm6, ymm13  ; ymm12 = (ymm6 * ymm13) + ymm12
vfmadd231pd	ymm12, ymm5, ymm0  ; ymm12 = (ymm5 * ymm0) + ymm12
vmulpd	ymm14, ymm14, ymm10
vfmadd231pd	ymm14, ymm9, ymm13  ; ymm14 = (ymm9 * ymm13) + ymm14
vfmadd231pd	ymm14, ymm8, ymm0  ; ymm14 = (ymm8 * ymm0) + ymm14
vroundpd	ymm0, ymm15, 8
vsubpd	ymm13, ymm15, ymm0
vroundpd	ymm0, ymm12, 8
vsubpd	ymm12, ymm12, ymm0
vroundpd	ymm0, ymm14, 8
vsubpd	ymm0, ymm14, ymm0
vmulpd	ymm0, ymm0, ymm0
vfmadd231pd	ymm0, ymm12, ymm12  ; ymm0 = (ymm12 * ymm12) + ymm0
vfmadd231pd	ymm0, ymm13, ymm13  ; ymm0 = (ymm13 * ymm13) + ymm0
vmovupd	ymm13, yword [r8 + 8*rbx]
vcmpltpd	ymm12, ymm0, ymm13
vcmpltpd	ymm14, ymm0, ymm1
vandpd	ymm14, ymm14, ymm12
vmovmskpd	ebp, ymm14
test	ebp, ebp
je	BB1_25
;  ; in Loop: Header=BB1_23 Depth=1:
vextractf128	xmm12, ymm14, 1
vpackssdw	xmm12, xmm14, xmm12
popcnt	r11d, ebp
add	eax, r11d
vpslld	xmm12, xmm12, 31
vpmovsxdq	ymm12, xmm12
vblendvpd	ymm0, ymm13, ymm0, ymm12
vmovupd	yword [r8 + 8*rbx], ymm0
jmp	BB1_25
BB1_5:
mov	qword [rsp - 40], r11  ; 8-byte Spill
lea	r11, [r9 + 4*r12]
lea	rbx, [r9 + 4*r10]
lea	r14, [r8 + 8*r12]
lea	r15, [r8 + 8*r10]
mov	qword [rsp + 160], r15  ; 8-byte Spill
lea	r13, [rdi + 72]
mov	qword [rsp], r13  ; 8-byte Spill
lea	r13, [rsi + 8*r12]
mov	qword [rsp - 32], r13  ; 8-byte Spill
lea	r13, [rsi + 8*r10]
mov	qword [rsp + 32], r13  ; 8-byte Spill
lea	rbp, [rdx + 8*r12]
mov	qword [rsp - 112], rbp  ; 8-byte Spill
lea	rbp, [rdx + 8*r10]
mov	qword [rsp + 128], rbp  ; 8-byte Spill
cmp	r11, r15
setb	byte [rsp + 224]  ; 1-byte Folded Spill
cmp	r14, rbx
setb	byte [rsp + 192]  ; 1-byte Folded Spill
mov	rbp, qword [rsp]  ; 8-byte Reload
cmp	r11, rbp
setb	byte [rsp + 96]  ; 1-byte Folded Spill
cmp	rbx, rdi
seta	byte [rsp + 64]  ; 1-byte Folded Spill
lea	r15, [rcx + 8*r10]
cmp	r11, r13
setb	byte [rsp - 64]  ; 1-byte Folded Spill
cmp	qword [rsp - 32], rbx  ; 8-byte Folded Reload
setb	byte [rsp - 80]  ; 1-byte Folded Spill
mov	r13, qword [rsp + 128]  ; 8-byte Reload
cmp	r11, r13
setb	byte [rsp - 120]  ; 1-byte Folded Spill
cmp	qword [rsp - 112], rbx  ; 8-byte Folded Reload
setb	byte [rsp - 121]  ; 1-byte Folded Spill
cmp	r11, r15
lea	r11, [rcx + 8*r12]
setb	byte [rsp - 122]  ; 1-byte Folded Spill
cmp	r11, rbx
setb	byte [rsp - 123]  ; 1-byte Folded Spill
cmp	r14, rbp
setb	byte [rsp]  ; 1-byte Folded Spill
mov	rbx, qword [rsp + 160]  ; 8-byte Reload
cmp	rbx, rdi
seta	byte [rsp - 124]  ; 1-byte Folded Spill
cmp	r14, qword [rsp + 32]  ; 8-byte Folded Reload
setb	byte [rsp + 32]  ; 1-byte Folded Spill
cmp	qword [rsp - 32], rbx  ; 8-byte Folded Reload
mov	rbp, rbx
setb	bl
cmp	r14, r13
setb	byte [rsp - 32]  ; 1-byte Folded Spill
cmp	qword [rsp - 112], rbp  ; 8-byte Folded Reload
setb	r13b
cmp	r14, r15
setb	r14b
cmp	r11, rbp
setb	r11b
movzx	ebp, byte [rsp + 192]  ; 1-byte Folded Reload
test	byte [rsp + 224], bpl  ; 1-byte Folded Reload
vmovapd	xmm5, oword [rsp - 96]  ; 16-byte Reload
jne	BB1_6
mov	r15d, r13d
movzx	ebp, byte [rsp + 64]  ; 1-byte Folded Reload
and	byte [rsp + 96], bpl  ; 1-byte Folded Spill
mov	r13d, dword [rsp + 320]
jne	BB1_18
movzx	ebp, byte [rsp - 80]  ; 1-byte Folded Reload
and	byte [rsp - 64], bpl  ; 1-byte Folded Spill
jne	BB1_18
movzx	ebp, byte [rsp - 121]  ; 1-byte Folded Reload
and	byte [rsp - 120], bpl  ; 1-byte Folded Spill
jne	BB1_18
movzx	ebp, byte [rsp - 123]  ; 1-byte Folded Reload
and	byte [rsp - 122], bpl  ; 1-byte Folded Spill
jne	BB1_18
movzx	ebp, byte [rsp - 124]  ; 1-byte Folded Reload
and	byte [rsp], bpl  ; 1-byte Folded Spill
jne	BB1_18
and	byte [rsp + 32], bl  ; 1-byte Folded Spill
jne	BB1_18
and	byte [rsp - 32], r15b  ; 1-byte Folded Spill
jne	BB1_18
and	r14b, r11b
jne	BB1_18
mov	r11, qword [rsp - 40]  ; 8-byte Reload
mov	r15, r11
and	r15, -8
lea	rbx, [r12 + r15]
mov	qword [rsp - 120], rbx  ; 8-byte Spill
vmovd	xmm13, eax
vmovd	xmm0, r13d
vpbroadcastd	xmm0, xmm0
vmovdqa	oword [rsp - 64], xmm0  ; 16-byte Spill
vbroadcastsd	ymm0, qword [rdi]
vmovups	yword [rsp - 32], ymm0  ; 32-byte Spill
vbroadcastsd	ymm0, qword [rdi + 8]
vmovups	yword [rsp + 224], ymm0  ; 32-byte Spill
vbroadcastsd	ymm0, qword [rdi + 16]
vmovups	yword [rsp + 192], ymm0  ; 32-byte Spill
vbroadcastsd	ymm0, qword [rdi + 24]
vmovups	yword [rsp + 160], ymm0  ; 32-byte Spill
vbroadcastsd	ymm0, qword [rdi + 32]
vmovups	yword [rsp + 32], ymm0  ; 32-byte Spill
vbroadcastsd	ymm0, qword [rdi + 40]
vmovups	yword [rsp + 128], ymm0  ; 32-byte Spill
vbroadcastsd	ymm0, qword [rdi + 48]
vmovups	yword [rsp], ymm0  ; 32-byte Spill
vbroadcastsd	ymm0, qword [rdi + 56]
vmovups	yword [rsp + 96], ymm0  ; 32-byte Spill
vpbroadcastq	ymm0, qword [rdi + 64]
vmovdqu	yword [rsp + 64], ymm0  ; 32-byte Spill
lea	rax, [rsi + 8*r12 + 32]
lea	r13, [rdx + 8*r12 + 32]
lea	rbp, [rcx + 8*r12 + 32]
lea	rbx, [r8 + 8*r12]
add	rbx, 32
lea	r12, [r9 + 4*r12]
add	r12, 16
vpxor	xmm0, xmm0, xmm0
xor	r14d, r14d
vpbroadcastd	xmm3, dword [rel CPI1_0]  ; xmm3 = [1,1,1,1]
vmovdqa	oword [rsp - 80], xmm3  ; 16-byte Spill
vmovdqa	xmm2, oword [rsp - 64]  ; 16-byte Reload
align 4
BB1_16:  ; =>This Inner Loop Header: Depth=1:
vmovdqa	oword [rsp - 112], xmm0  ; 16-byte Spill
vmovupd	ymm0, yword [rax + 8*r14 - 32]
vmovupd	ymm4, yword [rax + 8*r14]
vmovupd	ymm5, yword [rsp - 32]  ; 32-byte Reload
vmulpd	ymm7, ymm0, ymm5
vmulpd	ymm8, ymm4, ymm5
vmovupd	ymm6, yword [r13 + 8*r14 - 32]
vmovupd	ymm5, yword [r13 + 8*r14]
vmovupd	ymm9, yword [rsp + 224]  ; 32-byte Reload
vfmadd231pd	ymm7, ymm6, ymm9  ; ymm7 = (ymm6 * ymm9) + ymm7
vfmadd231pd	ymm8, ymm5, ymm9  ; ymm8 = (ymm5 * ymm9) + ymm8
vmovupd	ymm9, yword [rbp + 8*r14 - 32]
vmovupd	ymm10, yword [rbp + 8*r14]
vmovupd	ymm11, yword [rsp + 192]  ; 32-byte Reload
vfmadd231pd	ymm7, ymm9, ymm11  ; ymm7 = (ymm9 * ymm11) + ymm7
vfmadd231pd	ymm8, ymm10, ymm11  ; ymm8 = (ymm10 * ymm11) + ymm8
vroundpd	ymm11, ymm7, 12
vroundpd	ymm12, ymm8, 12
vsubpd	ymm7, ymm7, ymm11
vsubpd	ymm8, ymm8, ymm12
vmovupd	ymm12, yword [rsp + 160]  ; 32-byte Reload
vmulpd	ymm11, ymm12, ymm0
vmulpd	ymm12, ymm12, ymm4
vmovupd	ymm14, yword [rsp + 32]  ; 32-byte Reload
vfmadd231pd	ymm11, ymm14, ymm6  ; ymm11 = (ymm14 * ymm6) + ymm11
vfmadd231pd	ymm12, ymm14, ymm5  ; ymm12 = (ymm14 * ymm5) + ymm12
vmovupd	ymm14, yword [rsp + 128]  ; 32-byte Reload
vfmadd231pd	ymm11, ymm14, ymm9  ; ymm11 = (ymm14 * ymm9) + ymm11
vfmadd231pd	ymm12, ymm14, ymm10  ; ymm12 = (ymm14 * ymm10) + ymm12
vroundpd	ymm14, ymm11, 12
vroundpd	ymm15, ymm12, 12
vsubpd	ymm11, ymm11, ymm14
vsubpd	ymm12, ymm12, ymm15
vmovupd	ymm14, yword [rsp]  ; 32-byte Reload
vmulpd	ymm0, ymm14, ymm0
vmulpd	ymm4, ymm14, ymm4
vmovupd	ymm14, yword [rsp + 96]  ; 32-byte Reload
vfmadd231pd	ymm0, ymm14, ymm6  ; ymm0 = (ymm14 * ymm6) + ymm0
vfmadd231pd	ymm4, ymm14, ymm5  ; ymm4 = (ymm14 * ymm5) + ymm4
vmovupd	ymm5, yword [rsp + 64]  ; 32-byte Reload
vfmadd231pd	ymm0, ymm5, ymm9  ; ymm0 = (ymm5 * ymm9) + ymm0
vfmadd231pd	ymm4, ymm5, ymm10  ; ymm4 = (ymm5 * ymm10) + ymm4
vroundpd	ymm5, ymm0, 12
vroundpd	ymm6, ymm4, 12
vsubpd	ymm5, ymm0, ymm5
vsubpd	ymm6, ymm4, ymm6
vmulpd	ymm0, ymm7, ymm7
vmulpd	ymm4, ymm8, ymm8
vfmadd231pd	ymm0, ymm11, ymm11  ; ymm0 = (ymm11 * ymm11) + ymm0
vfmadd231pd	ymm4, ymm12, ymm12  ; ymm4 = (ymm12 * ymm12) + ymm4
vfmadd231pd	ymm0, ymm5, ymm5  ; ymm0 = (ymm5 * ymm5) + ymm0
vfmadd231pd	ymm4, ymm6, ymm6  ; ymm4 = (ymm6 * ymm6) + ymm4
vcmplepd	ymm7, ymm1, ymm0
vcmpltpd	ymm8, ymm0, ymm1
vcmplepd	ymm9, ymm1, ymm4
vmaskmovpd	ymm10, ymm8, yword [rbx + 8*r14 - 32]
vcmpltpd	ymm5, ymm4, ymm1
vmaskmovpd	ymm6, ymm5, yword [rbx + 8*r14]
vcmplepd	ymm11, ymm10, ymm0
vcmplepd	ymm12, ymm6, ymm4
vandpd	ymm11, ymm8, ymm11
vorpd	ymm7, ymm11, ymm7
vandpd	ymm11, ymm12, ymm5
vorpd	ymm9, ymm11, ymm9
vextractf128	xmm11, ymm7, 1
vpackssdw	xmm7, xmm7, xmm11
vextractf128	xmm11, ymm9, 1
vpmaskmovd	xmm12, xmm7, oword [r12 + 4*r14 - 16]
vpackssdw	xmm9, xmm9, xmm11
vpmaskmovd	xmm11, xmm9, oword [r12 + 4*r14]
vpcmpeqd	xmm12, xmm12, xmm2
vpcmpeqd	xmm11, xmm11, xmm2
vpand	xmm14, xmm12, xmm7
vpand	xmm15, xmm9, xmm11
vmovapd	ymm3, ymm1
vpcmpeqd	xmm1, xmm1, xmm1
vpmaskmovd	oword [r12 + 4*r14 - 16], xmm14, xmm1
vpmaskmovd	oword [r12 + 4*r14], xmm15, xmm1
vcmpltpd	ymm10, ymm0, ymm10
vandpd	ymm8, ymm8, ymm10
vextractf128	xmm10, ymm8, 1
vpackssdw	xmm10, xmm8, xmm10
vpmaskmovd	oword [r12 + 4*r14 - 16], xmm10, xmm2
vcmpltpd	ymm6, ymm4, ymm6
vandpd	ymm5, ymm5, ymm6
vextractf128	xmm6, ymm5, 1
vpackssdw	xmm6, xmm5, xmm6
vpmaskmovd	oword [r12 + 4*r14], xmm6, xmm2
vmaskmovpd	yword [rbx + 8*r14 - 32], ymm8, ymm0
vmaskmovpd	yword [rbx + 8*r14], ymm5, ymm4
vpxor	xmm0, xmm7, xmm1
vpor	xmm0, xmm12, xmm0
vpandn	xmm0, xmm14, xmm0
vmovdqa	xmm4, oword [rsp - 80]  ; 16-byte Reload
vpand	xmm0, xmm0, xmm4
vpaddd	xmm13, xmm13, xmm0
vpxor	xmm0, xmm9, xmm1
vmovapd	ymm1, ymm3
vpor	xmm0, xmm11, xmm0
vpandn	xmm0, xmm15, xmm0
vpand	xmm0, xmm0, xmm4
vmovdqa	xmm3, oword [rsp - 112]  ; 16-byte Reload
vpaddd	xmm3, xmm3, xmm0
vmovdqa	oword [rsp - 112], xmm3  ; 16-byte Spill
vmovdqa	xmm0, oword [rsp - 112]  ; 16-byte Reload
add	r14, 8
cmp	r15, r14
jne	BB1_16
vpaddd	xmm0, xmm13, xmm0
vpshufd	xmm1, xmm0, 238  ; xmm1 = xmm0[2,3,2,3]
vpaddd	xmm0, xmm0, xmm1
vpshufd	xmm1, xmm0, 85  ; xmm1 = xmm0[1,1,1,1]
vpaddd	xmm0, xmm0, xmm1
vmovd	eax, xmm0
cmp	r11, r15
mov	r13d, dword [rsp + 320]
vmovapd	xmm5, oword [rsp - 96]  ; 16-byte Reload
mov	r12, qword [rsp - 120]  ; 8-byte Reload
jne	BB1_18
BB1_29:
add	rsp, 264
pop	rbx
pop	r12
pop	r13
pop	r14
pop	r15
pop	rbp
vzeroupper
ret
BB1_6:
mov	r13d, dword [rsp + 320]
jmp	BB1_18
func_end1:

%endif
