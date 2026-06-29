SECTION .note.GNU-stack noalloc noexec nowrite progbits
%include "c2_abi.asm"
SECTION .text

%ifidn __OUTPUT_FORMAT__, win64
global sa_inner_f64_sov_avx512
call_sa_inner_f64_sov_avx512:  ; @call_sa_inner_f64_sov_avx512:
jmp	sa_inner_f64_sov_avx512
align 4
sa_inner_f64_sov_avx512:  ; @sa_inner_f64_sov_avx512:
push	r15
push	r14
push	r13
push	r12
push	rsi
push	rdi
push	rbp
push	rbx
sub	rsp, 200
vmovapd	oword [rsp + 176], xmm12  ; 16-byte Spill
vmovapd	oword [rsp + 160], xmm11  ; 16-byte Spill
vmovapd	oword [rsp + 144], xmm10  ; 16-byte Spill
vmovapd	oword [rsp + 128], xmm9  ; 16-byte Spill
vmovapd	oword [rsp + 112], xmm8  ; 16-byte Spill
vmovapd	oword [rsp + 96], xmm7  ; 16-byte Spill
vmovdqa	oword [rsp + 80], xmm6  ; 16-byte Spill
mov	r10, qword [rsp + 336]
mov	ebp, dword [rsp + 328]
mov	rdi, qword [rsp + 320]
mov	rsi, qword [rsp + 312]
vmovsd	xmm0, qword [rsp + 304]  ; xmm0 = mem[0],zero
vmulsd	xmm0, xmm0, xmm0
vbroadcastsd	zmm1, xmm0
vpbroadcastd	ymm2, ebp
cmp	r10, 8
jge	BB1_11
xor	r15d, r15d
xor	eax, eax
BB1_2:
mov	r11, r10
sub	r11, r15
jle	BB1_27
cmp	r11, 16
jb	BB1_4
mov	qword [rsp + 56], r11  ; 8-byte Spill
lea	r11, [rdi + 4*r15]
lea	rbx, [rdi + 4*r10]
lea	r14, [rsi + 8*r15]
lea	r12, [rsi + 8*r10]
mov	qword [rsp + 72], r12  ; 8-byte Spill
lea	r13, [rcx + 72]
mov	qword [rsp + 40], r13  ; 8-byte Spill
lea	r13, [rdx + 8*r15]
mov	qword [rsp + 24], r13  ; 8-byte Spill
lea	r13, [rdx + 8*r10]
mov	qword [rsp + 48], r13  ; 8-byte Spill
lea	rbp, [r8 + 8*r15]
mov	qword [rsp + 32], rbp  ; 8-byte Spill
lea	rbp, [r8 + 8*r10]
mov	qword [rsp + 64], rbp  ; 8-byte Spill
cmp	r11, r12
setb	byte [rsp + 23]  ; 1-byte Folded Spill
cmp	r14, rbx
setb	byte [rsp + 22]  ; 1-byte Folded Spill
mov	rbp, qword [rsp + 40]  ; 8-byte Reload
cmp	r11, rbp
setb	byte [rsp + 21]  ; 1-byte Folded Spill
cmp	rbx, rcx
seta	byte [rsp + 20]  ; 1-byte Folded Spill
lea	r12, [r9 + 8*r10]
cmp	r11, r13
setb	byte [rsp + 19]  ; 1-byte Folded Spill
cmp	qword [rsp + 24], rbx  ; 8-byte Folded Reload
setb	byte [rsp + 18]  ; 1-byte Folded Spill
mov	r13, qword [rsp + 64]  ; 8-byte Reload
cmp	r11, r13
setb	byte [rsp + 17]  ; 1-byte Folded Spill
cmp	qword [rsp + 32], rbx  ; 8-byte Folded Reload
setb	byte [rsp + 16]  ; 1-byte Folded Spill
cmp	r11, r12
lea	r11, [r9 + 8*r15]
setb	byte [rsp + 15]  ; 1-byte Folded Spill
cmp	r11, rbx
setb	byte [rsp + 14]  ; 1-byte Folded Spill
cmp	r14, rbp
setb	byte [rsp + 40]  ; 1-byte Folded Spill
mov	rbx, qword [rsp + 72]  ; 8-byte Reload
cmp	rbx, rcx
seta	byte [rsp + 13]  ; 1-byte Folded Spill
cmp	r14, qword [rsp + 48]  ; 8-byte Folded Reload
setb	byte [rsp + 48]  ; 1-byte Folded Spill
cmp	qword [rsp + 24], rbx  ; 8-byte Folded Reload
mov	rbp, rbx
setb	bl
cmp	r14, r13
setb	byte [rsp + 24]  ; 1-byte Folded Spill
cmp	qword [rsp + 32], rbp  ; 8-byte Folded Reload
setb	r13b
cmp	r14, r12
setb	r14b
cmp	r11, rbp
setb	r11b
movzx	ebp, byte [rsp + 22]  ; 1-byte Folded Reload
test	byte [rsp + 23], bpl  ; 1-byte Folded Reload
jne	BB1_35
movzx	ebp, byte [rsp + 20]  ; 1-byte Folded Reload
and	byte [rsp + 21], bpl  ; 1-byte Folded Spill
jne	BB1_35
movzx	ebp, byte [rsp + 18]  ; 1-byte Folded Reload
and	byte [rsp + 19], bpl  ; 1-byte Folded Spill
jne	BB1_35
movzx	ebp, byte [rsp + 16]  ; 1-byte Folded Reload
and	byte [rsp + 17], bpl  ; 1-byte Folded Spill
jne	BB1_35
movzx	ebp, byte [rsp + 14]  ; 1-byte Folded Reload
and	byte [rsp + 15], bpl  ; 1-byte Folded Spill
jne	BB1_35
movzx	ebp, byte [rsp + 13]  ; 1-byte Folded Reload
and	byte [rsp + 40], bpl  ; 1-byte Folded Spill
jne	BB1_35
and	byte [rsp + 48], bl  ; 1-byte Folded Spill
jne	BB1_35
and	byte [rsp + 24], r13b  ; 1-byte Folded Spill
jne	BB1_35
and	r14b, r11b
jne	BB1_35
mov	r11, qword [rsp + 56]  ; 8-byte Reload
mov	r12, r11
and	r12, -16
lea	rbx, [r15 + r12]
mov	qword [rsp + 32], rbx  ; 8-byte Spill
vmovd	xmm3, eax
vbroadcastsd	zmm4, qword [rcx]
vbroadcastsd	zmm5, qword [rcx + 8]
vbroadcastsd	zmm16, qword [rcx + 16]
vbroadcastsd	zmm17, qword [rcx + 24]
vbroadcastsd	zmm18, qword [rcx + 32]
vbroadcastsd	zmm19, qword [rcx + 40]
vbroadcastsd	zmm20, qword [rcx + 48]
vbroadcastsd	zmm21, qword [rcx + 56]
vbroadcastsd	zmm22, qword [rcx + 64]
lea	rax, [rdx + 8*r15 + 64]
lea	r13, [r8 + 8*r15 + 64]
lea	rbp, [r9 + 8*r15 + 64]
lea	rbx, [rsi + 8*r15]
add	rbx, 64
lea	r15, [rdi + 4*r15]
add	r15, 32
vxorpd	xmm23, xmm23, xmm23
xor	r14d, r14d
vpcmpeqd	ymm6, ymm6, ymm6
align 4
BB1_25:  ; =>This Inner Loop Header: Depth=1:
vmovupd	zmm24, zword [rax + 8*r14 - 64]
vmovupd	zmm25, zword [rax + 8*r14]
vmulpd	zmm26, zmm24, zmm4
vmulpd	zmm27, zmm25, zmm4
vmovupd	zmm28, zword [r13 + 8*r14 - 64]
vmovupd	zmm29, zword [r13 + 8*r14]
vfmadd231pd	zmm26, zmm28, zmm5  ; zmm26 = (zmm28 * zmm5) + zmm26
vfmadd231pd	zmm27, zmm29, zmm5  ; zmm27 = (zmm29 * zmm5) + zmm27
vmovupd	zmm30, zword [rbp + 8*r14 - 64]
vmovupd	zmm31, zword [rbp + 8*r14]
vfmadd231pd	zmm26, zmm30, zmm16  ; zmm26 = (zmm30 * zmm16) + zmm26
vfmadd231pd	zmm27, zmm31, zmm16  ; zmm27 = (zmm31 * zmm16) + zmm27
vrndscalepd	zmm7, zmm26, 12
vrndscalepd	zmm8, zmm27, 12
vmulpd	zmm9, zmm17, zmm24
vmulpd	zmm10, zmm17, zmm25
vfmadd231pd	zmm9, zmm18, zmm28  ; zmm9 = (zmm18 * zmm28) + zmm9
vfmadd231pd	zmm10, zmm18, zmm29  ; zmm10 = (zmm18 * zmm29) + zmm10
vfmadd231pd	zmm9, zmm19, zmm30  ; zmm9 = (zmm19 * zmm30) + zmm9
vfmadd231pd	zmm10, zmm19, zmm31  ; zmm10 = (zmm19 * zmm31) + zmm10
vrndscalepd	zmm11, zmm9, 12
vrndscalepd	zmm12, zmm10, 12
vmulpd	zmm24, zmm20, zmm24
vmulpd	zmm25, zmm20, zmm25
vfmadd231pd	zmm24, zmm21, zmm28  ; zmm24 = (zmm21 * zmm28) + zmm24
vfmadd231pd	zmm25, zmm21, zmm29  ; zmm25 = (zmm21 * zmm29) + zmm25
vfmadd231pd	zmm24, zmm22, zmm30  ; zmm24 = (zmm22 * zmm30) + zmm24
vfmadd231pd	zmm25, zmm22, zmm31  ; zmm25 = (zmm22 * zmm31) + zmm25
vrndscalepd	zmm28, zmm24, 12
vrndscalepd	zmm29, zmm25, 12
vsubpd	zmm26, zmm26, zmm7
vsubpd	zmm27, zmm27, zmm8
vmulpd	zmm26, zmm26, zmm26
vmulpd	zmm27, zmm27, zmm27
vsubpd	zmm30, zmm9, zmm11
vsubpd	zmm31, zmm10, zmm12
vfmadd213pd	zmm30, zmm30, zmm26  ; zmm30 = (zmm30 * zmm30) + zmm26
vfmadd213pd	zmm31, zmm31, zmm27  ; zmm31 = (zmm31 * zmm31) + zmm27
vsubpd	zmm24, zmm24, zmm28
vsubpd	zmm25, zmm25, zmm29
vfmadd213pd	zmm24, zmm24, zmm30  ; zmm24 = (zmm24 * zmm24) + zmm30
vfmadd213pd	zmm25, zmm25, zmm31  ; zmm25 = (zmm25 * zmm25) + zmm31
vcmplepd	k0, zmm1, zmm24
vcmpltpd	k2, zmm24, zmm1
vcmplepd	k1, zmm1, zmm25
vcmpltpd	k3, zmm25, zmm1
vmovupd	zmm26 {k2} {z}, zword [rbx + 8*r14 - 64]
vmovupd	zmm27 {k3} {z}, zword [rbx + 8*r14]
vcmplepd	k4 {k2}, zmm26, zmm24
vcmplepd	k5 {k3}, zmm27, zmm25
korb	k4, k4, k0
korb	k1, k5, k1
vmovdqu32	ymm28 {k4} {z}, yword [r15 + 4*r14 - 32]
vmovdqu32	ymm29 {k1} {z}, yword [r15 + 4*r14]
vpcmpeqd	k6, ymm28, ymm2
vpcmpeqd	k0, ymm29, ymm2
kandb	k7, k4, k6
kandb	k5, k1, k0
vmovdqu32	yword [r15 + 4*r14 - 32] {k7}, ymm6
vmovdqu32	yword [r15 + 4*r14] {k5}, ymm6
vcmpltpd	k2 {k2}, zmm24, zmm26
vcmpltpd	k3 {k3}, zmm25, zmm27
vmovdqu32	yword [r15 + 4*r14 - 32] {k2}, ymm2
vmovdqu32	yword [r15 + 4*r14] {k3}, ymm2
vmovupd	zword [rbx + 8*r14 - 64] {k2}, zmm24
vmovupd	zword [rbx + 8*r14] {k3}, zmm25
knotb	k2, k4
korb	k2, k2, k6
kandnb	k2, k7, k2
vpmovm2d	ymm24, k2
vpsubd	ymm3, ymm3, ymm24
knotb	k1, k1
korb	k0, k1, k0
kandnb	k0, k5, k0
vpmovm2d	ymm24, k0
vpsubd	ymm23, ymm23, ymm24
add	r14, 16
cmp	r12, r14
jne	BB1_25
vpaddd	ymm1, ymm23, ymm3
vextracti128	xmm2, ymm1, 1
vpaddd	xmm1, xmm1, xmm2
vpshufd	xmm2, xmm1, 238  ; xmm2 = xmm1[2,3,2,3]
vpaddd	xmm1, xmm1, xmm2
vpshufd	xmm2, xmm1, 85  ; xmm2 = xmm1[1,1,1,1]
vpaddd	xmm1, xmm1, xmm2
vmovd	eax, xmm1
cmp	r11, r12
mov	ebp, dword [rsp + 328]
mov	r15, qword [rsp + 32]  ; 8-byte Reload
jne	BB1_4
BB1_27:
vmovaps	xmm6, oword [rsp + 80]  ; 16-byte Reload
vmovaps	xmm7, oword [rsp + 96]  ; 16-byte Reload
vmovaps	xmm8, oword [rsp + 112]  ; 16-byte Reload
vmovaps	xmm9, oword [rsp + 128]  ; 16-byte Reload
vmovaps	xmm10, oword [rsp + 144]  ; 16-byte Reload
vmovaps	xmm11, oword [rsp + 160]  ; 16-byte Reload
vmovaps	xmm12, oword [rsp + 176]  ; 16-byte Reload
add	rsp, 200
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
BB1_11:
vbroadcastsd	zmm3, qword [rcx]
vbroadcastsd	zmm4, qword [rcx + 8]
vbroadcastsd	zmm5, qword [rcx + 16]
vbroadcastsd	zmm16, qword [rcx + 24]
vbroadcastsd	zmm17, qword [rcx + 32]
vbroadcastsd	zmm18, qword [rcx + 40]
vbroadcastsd	zmm19, qword [rcx + 48]
vbroadcastsd	zmm20, qword [rcx + 56]
vbroadcastsd	zmm21, qword [rcx + 64]
xor	ebx, ebx
vpcmpeqd	ymm6, ymm6, ymm6
xor	eax, eax
jmp	BB1_13
align 4
BB1_12:  ; in Loop: Header=BB1_13 Depth=1:
lea	r15, [rbx + 8]
add	rbx, 16
cmp	rbx, r10
mov	rbx, r15
jg	BB1_2
BB1_13:  ; =>This Inner Loop Header: Depth=1:
vmovupd	zmm22, zword [rdx + 8*rbx]
vmovupd	zmm23, zword [r8 + 8*rbx]
vmovupd	zmm24, zword [r9 + 8*rbx]
vmulpd	zmm25, zmm24, zmm5
vfmadd231pd	zmm25, zmm4, zmm23  ; zmm25 = (zmm4 * zmm23) + zmm25
vfmadd231pd	zmm25, zmm3, zmm22  ; zmm25 = (zmm3 * zmm22) + zmm25
vmulpd	zmm26, zmm24, zmm18
vfmadd231pd	zmm26, zmm17, zmm23  ; zmm26 = (zmm17 * zmm23) + zmm26
vfmadd231pd	zmm26, zmm16, zmm22  ; zmm26 = (zmm16 * zmm22) + zmm26
vmulpd	zmm24, zmm24, zmm21
vfmadd231pd	zmm24, zmm20, zmm23  ; zmm24 = (zmm20 * zmm23) + zmm24
vfmadd231pd	zmm24, zmm19, zmm22  ; zmm24 = (zmm19 * zmm22) + zmm24
vrndscalepd	zmm22, zmm25, 8
vsubpd	zmm23, zmm25, zmm22
vrndscalepd	zmm22, zmm26, 8
vsubpd	zmm25, zmm26, zmm22
vrndscalepd	zmm22, zmm24, 8
vsubpd	zmm22, zmm24, zmm22
vmulpd	zmm22, zmm22, zmm22
vfmadd231pd	zmm22, zmm25, zmm25  ; zmm22 = (zmm25 * zmm25) + zmm22
vfmadd231pd	zmm22, zmm23, zmm23  ; zmm22 = (zmm23 * zmm23) + zmm22
vmovupd	zmm23, zword [rsi + 8*rbx]
vcmpltpd	k1, zmm22, zmm1
vcmpltpd	k1 {k1}, zmm22, zmm23
vmovdqu64	ymm24, yword [rdi + 4*rbx]
vpcmpeqd	k2, ymm24, ymm2
vmovdqa32	ymm24 {k2}, ymm6
vmovdqa32	ymm24 {k1}, ymm2
vmovdqu64	yword [rdi + 4*rbx], ymm24
kortestb	k1, k1
je	BB1_12
;  ; in Loop: Header=BB1_13 Depth=1:
kmovd	r11d, k1
movzx	r11d, r11b
popcnt	r11d, r11d
add	eax, r11d
vmovapd	zmm23 {k1}, zmm22
vmovupd	zword [rsi + 8*rbx], zmm23
jmp	BB1_12
BB1_35:
mov	ebp, dword [rsp + 328]
BB1_4:
sub	r10, r15
lea	rdi, [rdi + 4*r15]
lea	rsi, [rsi + 8*r15]
lea	r9, [r9 + 8*r15]
lea	r8, [r8 + 8*r15]
lea	rdx, [rdx + 8*r15]
xor	ebx, ebx
jmp	BB1_7
align 4
BB1_5:  ; in Loop: Header=BB1_7 Depth=1:
mov	dword [rdi + 4*rbx], ebp
vmovsd	qword [rsi + 8*rbx], xmm1
inc	eax
BB1_6:  ; in Loop: Header=BB1_7 Depth=1:
inc	rbx
cmp	r10, rbx
je	BB1_27
BB1_7:  ; =>This Inner Loop Header: Depth=1:
vmovddup	xmm1, qword [rdx + 8*rbx]  ; xmm1 = mem[0,0]
vmulsd	xmm2, xmm1, qword [rcx]
vmovddup	xmm3, qword [r8 + 8*rbx]  ; xmm3 = mem[0,0]
vmovsd	xmm4, qword [rcx + 24]  ; xmm4 = mem[0],zero
vmovsd	xmm5, qword [rcx + 32]  ; xmm5 = mem[0],zero
vmovhpd	xmm4, xmm4, qword [rcx + 48]  ; xmm4 = xmm4[0],mem[0]
vmulpd	xmm1, xmm4, xmm1
vmovhpd	xmm4, xmm5, qword [rcx + 56]  ; xmm4 = xmm5[0],mem[0]
vfmadd213pd	xmm4, xmm3, xmm1  ; xmm4 = (xmm3 * xmm4) + xmm1
vfmadd132sd	xmm3, xmm2, qword [rcx + 8]  ; xmm3 = (xmm3 * mem) + xmm2
vmovddup	xmm1, qword [r9 + 8*rbx]  ; xmm1 = mem[0,0]
vmovsd	xmm2, qword [rcx + 40]  ; xmm2 = mem[0],zero
vmovhpd	xmm2, xmm2, qword [rcx + 64]  ; xmm2 = xmm2[0],mem[0]
vfmadd213pd	xmm2, xmm1, xmm4  ; xmm2 = (xmm1 * xmm2) + xmm4
vfmadd132sd	xmm1, xmm3, qword [rcx + 16]  ; xmm1 = (xmm1 * mem) + xmm3
vroundsd	xmm3, xmm1, xmm1, 12
vsubsd	xmm1, xmm1, xmm3
vroundpd	xmm3, xmm2, 12
vsubpd	xmm2, xmm2, xmm3
vmulpd	xmm2, xmm2, xmm2
vfmadd213sd	xmm1, xmm1, xmm2  ; xmm1 = (xmm1 * xmm1) + xmm2
vshufpd	xmm2, xmm2, xmm2, 1  ; xmm2 = xmm2[1,0]
vaddsd	xmm1, xmm1, xmm2
vucomisd	xmm1, xmm0
jae	BB1_9
;  ; in Loop: Header=BB1_7 Depth=1:
vucomisd	xmm1, qword [rsi + 8*rbx]
jb	BB1_5
BB1_9:  ; in Loop: Header=BB1_7 Depth=1:
cmp	dword [rdi + 4*rbx], ebp
jne	BB1_6
;  ; in Loop: Header=BB1_7 Depth=1:
mov	dword [rdi + 4*rbx], -1
jmp	BB1_6

%else
global sa_inner_f64_sov_avx512
call_sa_inner_f64_sov_avx512:  ; @call_sa_inner_f64_sov_avx512:
jmp	sa_inner_f64_sov_avx512
func_end0:
align 4
sa_inner_f64_sov_avx512:  ; @sa_inner_f64_sov_avx512:
push	rbp
push	r15
push	r14
push	r13
push	r12
push	rbx
mov	r10, qword [rsp + 64]
mov	ebp, dword [rsp + 56]
vmulsd	xmm0, xmm0, xmm0
vbroadcastsd	zmm1, xmm0
vpbroadcastd	ymm2, ebp
cmp	r10, 8
jge	BB1_11
xor	r15d, r15d
xor	eax, eax
BB1_2:
mov	r11, r10
sub	r11, r15
jle	BB1_27
cmp	r11, 16
jb	BB1_4
mov	qword [rsp - 24], r11  ; 8-byte Spill
lea	r11, [r9 + 4*r15]
lea	rbx, [r9 + 4*r10]
lea	r14, [r8 + 8*r15]
lea	r12, [r8 + 8*r10]
mov	qword [rsp - 8], r12  ; 8-byte Spill
lea	r13, [rdi + 72]
mov	qword [rsp - 40], r13  ; 8-byte Spill
lea	r13, [rsi + 8*r15]
mov	qword [rsp - 56], r13  ; 8-byte Spill
lea	r13, [rsi + 8*r10]
mov	qword [rsp - 32], r13  ; 8-byte Spill
lea	rbp, [rdx + 8*r15]
mov	qword [rsp - 48], rbp  ; 8-byte Spill
lea	rbp, [rdx + 8*r10]
mov	qword [rsp - 16], rbp  ; 8-byte Spill
cmp	r11, r12
setb	byte [rsp - 57]  ; 1-byte Folded Spill
cmp	r14, rbx
setb	byte [rsp - 58]  ; 1-byte Folded Spill
mov	rbp, qword [rsp - 40]  ; 8-byte Reload
cmp	r11, rbp
setb	byte [rsp - 59]  ; 1-byte Folded Spill
cmp	rbx, rdi
seta	byte [rsp - 60]  ; 1-byte Folded Spill
lea	r12, [rcx + 8*r10]
cmp	r11, r13
setb	byte [rsp - 61]  ; 1-byte Folded Spill
cmp	qword [rsp - 56], rbx  ; 8-byte Folded Reload
setb	byte [rsp - 62]  ; 1-byte Folded Spill
mov	r13, qword [rsp - 16]  ; 8-byte Reload
cmp	r11, r13
setb	byte [rsp - 63]  ; 1-byte Folded Spill
cmp	qword [rsp - 48], rbx  ; 8-byte Folded Reload
setb	byte [rsp - 64]  ; 1-byte Folded Spill
cmp	r11, r12
lea	r11, [rcx + 8*r15]
setb	byte [rsp - 65]  ; 1-byte Folded Spill
cmp	r11, rbx
setb	byte [rsp - 66]  ; 1-byte Folded Spill
cmp	r14, rbp
setb	byte [rsp - 40]  ; 1-byte Folded Spill
mov	rbx, qword [rsp - 8]  ; 8-byte Reload
cmp	rbx, rdi
seta	byte [rsp - 67]  ; 1-byte Folded Spill
cmp	r14, qword [rsp - 32]  ; 8-byte Folded Reload
setb	byte [rsp - 32]  ; 1-byte Folded Spill
cmp	qword [rsp - 56], rbx  ; 8-byte Folded Reload
mov	rbp, rbx
setb	bl
cmp	r14, r13
setb	byte [rsp - 56]  ; 1-byte Folded Spill
cmp	qword [rsp - 48], rbp  ; 8-byte Folded Reload
setb	r13b
cmp	r14, r12
setb	r14b
cmp	r11, rbp
setb	r11b
movzx	ebp, byte [rsp - 58]  ; 1-byte Folded Reload
test	byte [rsp - 57], bpl  ; 1-byte Folded Reload
jne	BB1_35
movzx	ebp, byte [rsp - 60]  ; 1-byte Folded Reload
and	byte [rsp - 59], bpl  ; 1-byte Folded Spill
jne	BB1_35
movzx	ebp, byte [rsp - 62]  ; 1-byte Folded Reload
and	byte [rsp - 61], bpl  ; 1-byte Folded Spill
jne	BB1_35
movzx	ebp, byte [rsp - 64]  ; 1-byte Folded Reload
and	byte [rsp - 63], bpl  ; 1-byte Folded Spill
jne	BB1_35
movzx	ebp, byte [rsp - 66]  ; 1-byte Folded Reload
and	byte [rsp - 65], bpl  ; 1-byte Folded Spill
jne	BB1_35
movzx	ebp, byte [rsp - 67]  ; 1-byte Folded Reload
and	byte [rsp - 40], bpl  ; 1-byte Folded Spill
jne	BB1_35
and	byte [rsp - 32], bl  ; 1-byte Folded Spill
jne	BB1_35
and	byte [rsp - 56], r13b  ; 1-byte Folded Spill
jne	BB1_35
and	r14b, r11b
jne	BB1_35
mov	r11, qword [rsp - 24]  ; 8-byte Reload
mov	r12, r11
and	r12, -16
lea	rbx, [r15 + r12]
mov	qword [rsp - 48], rbx  ; 8-byte Spill
vmovd	xmm3, eax
vbroadcastsd	zmm4, qword [rdi]
vbroadcastsd	zmm5, qword [rdi + 8]
vbroadcastsd	zmm6, qword [rdi + 16]
vbroadcastsd	zmm7, qword [rdi + 24]
vbroadcastsd	zmm8, qword [rdi + 32]
vbroadcastsd	zmm9, qword [rdi + 40]
vbroadcastsd	zmm10, qword [rdi + 48]
vbroadcastsd	zmm11, qword [rdi + 56]
vbroadcastsd	zmm12, qword [rdi + 64]
lea	rax, [rsi + 8*r15 + 64]
lea	r13, [rdx + 8*r15 + 64]
lea	rbp, [rcx + 8*r15 + 64]
lea	rbx, [r8 + 8*r15]
add	rbx, 64
lea	r15, [r9 + 4*r15]
add	r15, 32
vxorpd	xmm13, xmm13, xmm13
xor	r14d, r14d
vpcmpeqd	ymm14, ymm14, ymm14
align 4
BB1_25:  ; =>This Inner Loop Header: Depth=1:
vmovupd	zmm15, zword [rax + 8*r14 - 64]
vmovupd	zmm16, zword [rax + 8*r14]
vmulpd	zmm17, zmm15, zmm4
vmulpd	zmm18, zmm16, zmm4
vmovupd	zmm19, zword [r13 + 8*r14 - 64]
vmovupd	zmm20, zword [r13 + 8*r14]
vfmadd231pd	zmm17, zmm19, zmm5  ; zmm17 = (zmm19 * zmm5) + zmm17
vfmadd231pd	zmm18, zmm20, zmm5  ; zmm18 = (zmm20 * zmm5) + zmm18
vmovupd	zmm21, zword [rbp + 8*r14 - 64]
vmovupd	zmm22, zword [rbp + 8*r14]
vfmadd231pd	zmm17, zmm21, zmm6  ; zmm17 = (zmm21 * zmm6) + zmm17
vfmadd231pd	zmm18, zmm22, zmm6  ; zmm18 = (zmm22 * zmm6) + zmm18
vrndscalepd	zmm23, zmm17, 12
vrndscalepd	zmm24, zmm18, 12
vmulpd	zmm25, zmm7, zmm15
vmulpd	zmm26, zmm7, zmm16
vfmadd231pd	zmm25, zmm8, zmm19  ; zmm25 = (zmm8 * zmm19) + zmm25
vfmadd231pd	zmm26, zmm8, zmm20  ; zmm26 = (zmm8 * zmm20) + zmm26
vfmadd231pd	zmm25, zmm9, zmm21  ; zmm25 = (zmm9 * zmm21) + zmm25
vfmadd231pd	zmm26, zmm9, zmm22  ; zmm26 = (zmm9 * zmm22) + zmm26
vrndscalepd	zmm27, zmm25, 12
vrndscalepd	zmm28, zmm26, 12
vmulpd	zmm15, zmm10, zmm15
vmulpd	zmm16, zmm10, zmm16
vfmadd231pd	zmm15, zmm11, zmm19  ; zmm15 = (zmm11 * zmm19) + zmm15
vfmadd231pd	zmm16, zmm11, zmm20  ; zmm16 = (zmm11 * zmm20) + zmm16
vfmadd231pd	zmm15, zmm12, zmm21  ; zmm15 = (zmm12 * zmm21) + zmm15
vfmadd231pd	zmm16, zmm12, zmm22  ; zmm16 = (zmm12 * zmm22) + zmm16
vrndscalepd	zmm19, zmm15, 12
vrndscalepd	zmm20, zmm16, 12
vsubpd	zmm17, zmm17, zmm23
vsubpd	zmm18, zmm18, zmm24
vmulpd	zmm17, zmm17, zmm17
vmulpd	zmm18, zmm18, zmm18
vsubpd	zmm21, zmm25, zmm27
vsubpd	zmm22, zmm26, zmm28
vfmadd213pd	zmm21, zmm21, zmm17  ; zmm21 = (zmm21 * zmm21) + zmm17
vfmadd213pd	zmm22, zmm22, zmm18  ; zmm22 = (zmm22 * zmm22) + zmm18
vsubpd	zmm15, zmm15, zmm19
vsubpd	zmm16, zmm16, zmm20
vfmadd213pd	zmm15, zmm15, zmm21  ; zmm15 = (zmm15 * zmm15) + zmm21
vfmadd213pd	zmm16, zmm16, zmm22  ; zmm16 = (zmm16 * zmm16) + zmm22
vcmplepd	k0, zmm1, zmm15
vcmpltpd	k2, zmm15, zmm1
vcmplepd	k1, zmm1, zmm16
vcmpltpd	k3, zmm16, zmm1
vmovupd	zmm17 {k2} {z}, zword [rbx + 8*r14 - 64]
vmovupd	zmm18 {k3} {z}, zword [rbx + 8*r14]
vcmplepd	k4 {k2}, zmm17, zmm15
vcmplepd	k5 {k3}, zmm18, zmm16
korb	k4, k4, k0
korb	k1, k5, k1
vmovdqu32	ymm19 {k4} {z}, yword [r15 + 4*r14 - 32]
vmovdqu32	ymm20 {k1} {z}, yword [r15 + 4*r14]
vpcmpeqd	k6, ymm19, ymm2
vpcmpeqd	k0, ymm20, ymm2
kandb	k7, k4, k6
kandb	k5, k1, k0
vmovdqu32	yword [r15 + 4*r14 - 32] {k7}, ymm14
vmovdqu32	yword [r15 + 4*r14] {k5}, ymm14
vcmpltpd	k2 {k2}, zmm15, zmm17
vcmpltpd	k3 {k3}, zmm16, zmm18
vmovdqu32	yword [r15 + 4*r14 - 32] {k2}, ymm2
vmovdqu32	yword [r15 + 4*r14] {k3}, ymm2
vmovupd	zword [rbx + 8*r14 - 64] {k2}, zmm15
vmovupd	zword [rbx + 8*r14] {k3}, zmm16
knotb	k2, k4
korb	k2, k2, k6
kandnb	k2, k7, k2
vpmovm2d	ymm15, k2
vpsubd	ymm3, ymm3, ymm15
knotb	k1, k1
korb	k0, k1, k0
kandnb	k0, k5, k0
vpmovm2d	ymm15, k0
vpsubd	ymm13, ymm13, ymm15
add	r14, 16
cmp	r12, r14
jne	BB1_25
vpaddd	ymm1, ymm13, ymm3
vextracti128	xmm2, ymm1, 1
vpaddd	xmm1, xmm1, xmm2
vpshufd	xmm2, xmm1, 238  ; xmm2 = xmm1[2,3,2,3]
vpaddd	xmm1, xmm1, xmm2
vpshufd	xmm2, xmm1, 85  ; xmm2 = xmm1[1,1,1,1]
vpaddd	xmm1, xmm1, xmm2
vmovd	eax, xmm1
cmp	r11, r12
mov	ebp, dword [rsp + 56]
mov	r15, qword [rsp - 48]  ; 8-byte Reload
jne	BB1_4
BB1_27:
pop	rbx
pop	r12
pop	r13
pop	r14
pop	r15
pop	rbp
vzeroupper
ret
BB1_11:
vbroadcastsd	zmm3, qword [rdi]
vbroadcastsd	zmm4, qword [rdi + 8]
vbroadcastsd	zmm5, qword [rdi + 16]
vbroadcastsd	zmm6, qword [rdi + 24]
vbroadcastsd	zmm7, qword [rdi + 32]
vbroadcastsd	zmm8, qword [rdi + 40]
vbroadcastsd	zmm9, qword [rdi + 48]
vbroadcastsd	zmm10, qword [rdi + 56]
vbroadcastsd	zmm11, qword [rdi + 64]
xor	ebx, ebx
vpcmpeqd	ymm12, ymm12, ymm12
xor	eax, eax
jmp	BB1_13
align 4
BB1_12:  ; in Loop: Header=BB1_13 Depth=1:
lea	r15, [rbx + 8]
add	rbx, 16
cmp	rbx, r10
mov	rbx, r15
jg	BB1_2
BB1_13:  ; =>This Inner Loop Header: Depth=1:
vmovupd	zmm13, zword [rsi + 8*rbx]
vmovupd	zmm14, zword [rdx + 8*rbx]
vmovupd	zmm15, zword [rcx + 8*rbx]
vmulpd	zmm16, zmm15, zmm5
vfmadd231pd	zmm16, zmm4, zmm14  ; zmm16 = (zmm4 * zmm14) + zmm16
vfmadd231pd	zmm16, zmm3, zmm13  ; zmm16 = (zmm3 * zmm13) + zmm16
vmulpd	zmm17, zmm15, zmm8
vfmadd231pd	zmm17, zmm7, zmm14  ; zmm17 = (zmm7 * zmm14) + zmm17
vfmadd231pd	zmm17, zmm6, zmm13  ; zmm17 = (zmm6 * zmm13) + zmm17
vmulpd	zmm15, zmm15, zmm11
vfmadd231pd	zmm15, zmm10, zmm14  ; zmm15 = (zmm10 * zmm14) + zmm15
vfmadd231pd	zmm15, zmm9, zmm13  ; zmm15 = (zmm9 * zmm13) + zmm15
vrndscalepd	zmm13, zmm16, 8
vsubpd	zmm14, zmm16, zmm13
vrndscalepd	zmm13, zmm17, 8
vsubpd	zmm16, zmm17, zmm13
vrndscalepd	zmm13, zmm15, 8
vsubpd	zmm13, zmm15, zmm13
vmulpd	zmm13, zmm13, zmm13
vfmadd231pd	zmm13, zmm16, zmm16  ; zmm13 = (zmm16 * zmm16) + zmm13
vfmadd231pd	zmm13, zmm14, zmm14  ; zmm13 = (zmm14 * zmm14) + zmm13
vmovupd	zmm14, zword [r8 + 8*rbx]
vcmpltpd	k1, zmm13, zmm1
vcmpltpd	k1 {k1}, zmm13, zmm14
vmovdqu	ymm15, yword [r9 + 4*rbx]
vpcmpeqd	k2, ymm15, ymm2
vmovdqa32	ymm15 {k2}, ymm12
vmovdqa32	ymm15 {k1}, ymm2
vmovdqu	yword [r9 + 4*rbx], ymm15
kortestb	k1, k1
je	BB1_12
;  ; in Loop: Header=BB1_13 Depth=1:
kmovd	r11d, k1
movzx	r11d, r11b
popcnt	r11d, r11d
add	eax, r11d
vmovapd	zmm14 {k1}, zmm13
vmovupd	zword [r8 + 8*rbx], zmm14
jmp	BB1_12
BB1_35:
mov	ebp, dword [rsp + 56]
BB1_4:
sub	r10, r15
lea	r9, [r9 + 4*r15]
lea	r8, [r8 + 8*r15]
lea	rcx, [rcx + 8*r15]
lea	rdx, [rdx + 8*r15]
lea	rsi, [rsi + 8*r15]
xor	ebx, ebx
jmp	BB1_7
align 4
BB1_5:  ; in Loop: Header=BB1_7 Depth=1:
mov	dword [r9 + 4*rbx], ebp
vmovsd	qword [r8 + 8*rbx], xmm1
inc	eax
BB1_6:  ; in Loop: Header=BB1_7 Depth=1:
inc	rbx
cmp	r10, rbx
je	BB1_27
BB1_7:  ; =>This Inner Loop Header: Depth=1:
vmovddup	xmm1, qword [rsi + 8*rbx]  ; xmm1 = mem[0,0]
vmulsd	xmm2, xmm1, qword [rdi]
vmovddup	xmm3, qword [rdx + 8*rbx]  ; xmm3 = mem[0,0]
vmovsd	xmm4, qword [rdi + 24]  ; xmm4 = mem[0],zero
vmovsd	xmm5, qword [rdi + 32]  ; xmm5 = mem[0],zero
vmovhpd	xmm4, xmm4, qword [rdi + 48]  ; xmm4 = xmm4[0],mem[0]
vmulpd	xmm1, xmm4, xmm1
vmovhpd	xmm4, xmm5, qword [rdi + 56]  ; xmm4 = xmm5[0],mem[0]
vfmadd213pd	xmm4, xmm3, xmm1  ; xmm4 = (xmm3 * xmm4) + xmm1
vfmadd132sd	xmm3, xmm2, qword [rdi + 8]  ; xmm3 = (xmm3 * mem) + xmm2
vmovddup	xmm1, qword [rcx + 8*rbx]  ; xmm1 = mem[0,0]
vmovsd	xmm2, qword [rdi + 40]  ; xmm2 = mem[0],zero
vmovhpd	xmm2, xmm2, qword [rdi + 64]  ; xmm2 = xmm2[0],mem[0]
vfmadd213pd	xmm2, xmm1, xmm4  ; xmm2 = (xmm1 * xmm2) + xmm4
vfmadd132sd	xmm1, xmm3, qword [rdi + 16]  ; xmm1 = (xmm1 * mem) + xmm3
vroundsd	xmm3, xmm1, xmm1, 12
vsubsd	xmm1, xmm1, xmm3
vroundpd	xmm3, xmm2, 12
vsubpd	xmm2, xmm2, xmm3
vmulpd	xmm2, xmm2, xmm2
vfmadd213sd	xmm1, xmm1, xmm2  ; xmm1 = (xmm1 * xmm1) + xmm2
vshufpd	xmm2, xmm2, xmm2, 1  ; xmm2 = xmm2[1,0]
vaddsd	xmm1, xmm1, xmm2
vucomisd	xmm1, xmm0
jae	BB1_9
;  ; in Loop: Header=BB1_7 Depth=1:
vucomisd	xmm1, qword [r8 + 8*rbx]
jb	BB1_5
BB1_9:  ; in Loop: Header=BB1_7 Depth=1:
cmp	dword [r9 + 4*rbx], ebp
jne	BB1_6
;  ; in Loop: Header=BB1_7 Depth=1:
mov	dword [r9 + 4*rbx], -1
jmp	BB1_6
func_end1:

%endif
