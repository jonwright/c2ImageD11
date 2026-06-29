SECTION .note.GNU-stack noalloc noexec nowrite progbits
%include "c2_abi.asm"
SECTION .text

%ifidn __OUTPUT_FORMAT__, win64
global sa_inner_f32_sov_avx512
call_sa_inner_f32_sov_avx512:  ; @call_sa_inner_f32_sov_avx512:
jmp	sa_inner_f32_sov_avx512
align 4
sa_inner_f32_sov_avx512:  ; @sa_inner_f32_sov_avx512:
push	r15
push	r14
push	r13
push	r12
push	rsi
push	rdi
push	rbp
push	rbx
sub	rsp, 312
vmovaps	oword [rsp + 288], xmm15  ; 16-byte Spill
vmovaps	oword [rsp + 272], xmm14  ; 16-byte Spill
vmovaps	oword [rsp + 256], xmm13  ; 16-byte Spill
vmovaps	oword [rsp + 240], xmm12  ; 16-byte Spill
vmovaps	oword [rsp + 224], xmm11  ; 16-byte Spill
vmovaps	oword [rsp + 208], xmm10  ; 16-byte Spill
vmovaps	oword [rsp + 192], xmm9  ; 16-byte Spill
vmovaps	oword [rsp + 176], xmm8  ; 16-byte Spill
vmovdqa	oword [rsp + 160], xmm7  ; 16-byte Spill
vmovdqa	oword [rsp + 144], xmm6  ; 16-byte Spill
mov	r10, qword [rsp + 448]
mov	ebp, dword [rsp + 440]
mov	rsi, qword [rsp + 432]
vmovsd	xmm0, qword [rsp + 416]  ; xmm0 = mem[0],zero
vmulsd	xmm0, xmm0, xmm0
vcvtsd2ss	xmm9, xmm0, xmm0
mov	rdi, qword [rsp + 424]
vbroadcastss	zmm16, xmm9
vpbroadcastd	zmm17, ebp
cmp	r10, 16
jge	BB1_29
xor	ebx, ebx
xor	eax, eax
BB1_2:
mov	r11, r10
sub	r11, rbx
jle	BB1_36
vmovsd	xmm1, qword [rcx]  ; xmm1 = mem[0],zero
vcvtsd2ss	xmm1, xmm1, xmm1
vcvtpd2ps	xmm2, oword [rcx + 8]
vmovsd	xmm3, qword [rcx + 24]  ; xmm3 = mem[0],zero
vmovhps	xmm3, xmm3, qword [rcx + 48]  ; xmm3 = xmm3[0,1],mem[0,1]
vcvtpd2ps	xmm3, xmm3
vmovsd	xmm4, qword [rcx + 32]  ; xmm4 = mem[0],zero
vmovhps	xmm4, xmm4, qword [rcx + 56]  ; xmm4 = xmm4[0,1],mem[0,1]
vcvtpd2ps	xmm4, xmm4
vmovsd	xmm5, qword [rcx + 40]  ; xmm5 = mem[0],zero
vmovhps	xmm5, xmm5, qword [rcx + 64]  ; xmm5 = xmm5[0,1],mem[0,1]
vcvtpd2ps	xmm5, xmm5
cmp	r11, 8
jb	BB1_26
mov	qword [rsp + 72], r11  ; 8-byte Spill
lea	rcx, [rsi + 4*rbx]
lea	r12, [rsi + 4*r10]
lea	rbp, [rdi + 4*rbx]
lea	r11, [rdi + 4*r10]
lea	r15, [rdx + 4*rbx]
lea	r14, [rdx + 4*r10]
mov	qword [rsp + 32], r14  ; 8-byte Spill
lea	r14, [r8 + 4*rbx]
mov	qword [rsp + 88], r14  ; 8-byte Spill
lea	r14, [r8 + 4*r10]
mov	qword [rsp + 48], r14  ; 8-byte Spill
lea	r13, [r9 + 4*rbx]
mov	qword [rsp + 80], r13  ; 8-byte Spill
lea	r13, [r9 + 4*r10]
mov	qword [rsp + 16], r13  ; 8-byte Spill
cmp	rcx, r11
setb	byte [rsp + 112]  ; 1-byte Folded Spill
cmp	rbp, r12
setb	byte [rsp + 96]  ; 1-byte Folded Spill
cmp	rcx, qword [rsp + 32]  ; 8-byte Folded Reload
setb	byte [rsp + 15]  ; 1-byte Folded Spill
cmp	r15, r12
setb	byte [rsp + 14]  ; 1-byte Folded Spill
cmp	rcx, r14
setb	byte [rsp + 13]  ; 1-byte Folded Spill
mov	r14, qword [rsp + 88]  ; 8-byte Reload
cmp	r14, r12
setb	byte [rsp + 12]  ; 1-byte Folded Spill
cmp	rcx, qword [rsp + 16]  ; 8-byte Folded Reload
setb	byte [rsp + 11]  ; 1-byte Folded Spill
mov	r13, qword [rsp + 80]  ; 8-byte Reload
cmp	r13, r12
setb	byte [rsp + 10]  ; 1-byte Folded Spill
cmp	rbp, qword [rsp + 32]  ; 8-byte Folded Reload
setb	r12b
mov	qword [rsp + 128], r15  ; 8-byte Spill
cmp	r15, r11
setb	byte [rsp + 32]  ; 1-byte Folded Spill
cmp	rbp, qword [rsp + 48]  ; 8-byte Folded Reload
setb	byte [rsp + 9]  ; 1-byte Folded Spill
cmp	r14, r11
setb	byte [rsp + 48]  ; 1-byte Folded Spill
mov	qword [rsp + 136], rbp  ; 8-byte Spill
cmp	rbp, qword [rsp + 16]  ; 8-byte Folded Reload
setb	r15b
cmp	r13, r11
setb	r11b
movzx	ebp, byte [rsp + 96]  ; 1-byte Folded Reload
test	byte [rsp + 112], bpl  ; 1-byte Folded Reload
jne	BB1_5
movzx	ebp, byte [rsp + 14]  ; 1-byte Folded Reload
and	byte [rsp + 15], bpl  ; 1-byte Folded Spill
jne	BB1_7
movzx	ebp, byte [rsp + 12]  ; 1-byte Folded Reload
and	byte [rsp + 13], bpl  ; 1-byte Folded Spill
jne	BB1_9
movzx	ebp, byte [rsp + 10]  ; 1-byte Folded Reload
and	byte [rsp + 11], bpl  ; 1-byte Folded Spill
jne	BB1_11
and	r12b, byte [rsp + 32]  ; 1-byte Folded Reload
jne	BB1_13
movzx	ebp, byte [rsp + 9]  ; 1-byte Folded Reload
and	bpl, byte [rsp + 48]  ; 1-byte Folded Reload
mov	ebp, dword [rsp + 440]
jne	BB1_26
and	r15b, r11b
jne	BB1_26
vmovshdup	xmm18, xmm2  ; xmm18 = xmm2[1,1,3,3]
vmovshdup	xmm0, xmm3  ; xmm0 = xmm3[1,1,3,3]
vmovshdup	xmm19, xmm4  ; xmm19 = xmm4[1,1,3,3]
vmovshdup	xmm20, xmm5  ; xmm20 = xmm5[1,1,3,3]
mov	r15, qword [rsp + 72]  ; 8-byte Reload
cmp	r15, 32
jae	BB1_18
xor	r14d, r14d
jmp	BB1_23
BB1_29:
vmovsd	xmm1, qword [rcx]  ; xmm1 = mem[0],zero
vcvtsd2ss	xmm1, xmm1, xmm1
vmovsd	xmm2, qword [rcx + 8]  ; xmm2 = mem[0],zero
vbroadcastss	zmm1, xmm1
vcvtsd2ss	xmm2, xmm2, xmm2
vbroadcastss	zmm2, xmm2
vmovsd	xmm3, qword [rcx + 16]  ; xmm3 = mem[0],zero
vcvtsd2ss	xmm3, xmm3, xmm3
vbroadcastss	zmm3, xmm3
vmovsd	xmm4, qword [rcx + 24]  ; xmm4 = mem[0],zero
vcvtsd2ss	xmm4, xmm4, xmm4
vbroadcastss	zmm4, xmm4
vmovsd	xmm5, qword [rcx + 32]  ; xmm5 = mem[0],zero
vcvtsd2ss	xmm5, xmm5, xmm5
vbroadcastss	zmm5, xmm5
vmovsd	xmm18, qword [rcx + 40]  ; xmm18 = mem[0],zero
vcvtsd2ss	xmm18, xmm18, xmm18
vbroadcastss	zmm18, xmm18
vmovsd	xmm19, qword [rcx + 48]  ; xmm19 = mem[0],zero
vcvtsd2ss	xmm19, xmm19, xmm19
vbroadcastss	zmm19, xmm19
vmovsd	xmm20, qword [rcx + 56]  ; xmm20 = mem[0],zero
vcvtsd2ss	xmm20, xmm20, xmm20
vbroadcastss	zmm20, xmm20
vmovsd	xmm21, qword [rcx + 64]  ; xmm21 = mem[0],zero
vcvtsd2ss	xmm21, xmm21, xmm21
vbroadcastss	zmm21, xmm21
xor	r11d, r11d
vpternlogd	zmm22, zmm22, zmm22, 255
xor	eax, eax
jmp	BB1_30
align 4
BB1_32:  ; in Loop: Header=BB1_30 Depth=1:
lea	rbx, [r11 + 16]
add	r11, 32
cmp	r11, r10
mov	r11, rbx
jg	BB1_2
BB1_30:  ; =>This Inner Loop Header: Depth=1:
vmovups	zmm0, zword [rdx + 4*r11]
vmovups	zmm23, zword [r8 + 4*r11]
vmovups	zmm24, zword [r9 + 4*r11]
vmulps	zmm25, zmm24, zmm3
vfmadd231ps	zmm25, zmm2, zmm23  ; zmm25 = (zmm2 * zmm23) + zmm25
vfmadd231ps	zmm25, zmm1, zmm0  ; zmm25 = (zmm1 * zmm0) + zmm25
vmulps	zmm26, zmm24, zmm18
vfmadd231ps	zmm26, zmm5, zmm23  ; zmm26 = (zmm5 * zmm23) + zmm26
vfmadd231ps	zmm26, zmm4, zmm0  ; zmm26 = (zmm4 * zmm0) + zmm26
vmulps	zmm24, zmm24, zmm21
vfmadd231ps	zmm24, zmm20, zmm23  ; zmm24 = (zmm20 * zmm23) + zmm24
vfmadd231ps	zmm24, zmm19, zmm0  ; zmm24 = (zmm19 * zmm0) + zmm24
vrndscaleps	zmm0, zmm25, 8
vsubps	zmm0, zmm25, zmm0
vrndscaleps	zmm23, zmm26, 8
vsubps	zmm25, zmm26, zmm23
vrndscaleps	zmm23, zmm24, 8
vsubps	zmm23, zmm24, zmm23
vmulps	zmm23, zmm23, zmm23
vfmadd231ps	zmm23, zmm25, zmm25  ; zmm23 = (zmm25 * zmm25) + zmm23
vfmadd231ps	zmm23, zmm0, zmm0  ; zmm23 = (zmm0 * zmm0) + zmm23
vmovups	zmm24, zword [rdi + 4*r11]
vcmpltps	k1, zmm23, zmm16
vcmpltps	k1 {k1}, zmm23, zmm24
vmovdqu64	zmm0, zword [rsi + 4*r11]
vpcmpeqd	k2, zmm0, zmm17
vmovdqa32	zmm0 {k2}, zmm22
vmovdqa32	zmm0 {k1}, zmm17
vmovdqu64	zword [rsi + 4*r11], zmm0
kortestw	k1, k1
je	BB1_32
;  ; in Loop: Header=BB1_30 Depth=1:
kmovd	ebx, k1
movzx	ebx, bx
popcnt	ebx, ebx
add	eax, ebx
vmovaps	zmm24 {k1}, zmm23
vmovups	zword [rdi + 4*r11], zmm24
jmp	BB1_32
BB1_18:
vmovaps	oword [rsp + 16], xmm9  ; 16-byte Spill
mov	r14, r15
and	r14, -32
vmovd	xmm22, eax
vbroadcastss	zmm23, xmm1
vbroadcastss	zmm24, xmm2
vmovaps	oword [rsp + 48], xmm18  ; 16-byte Spill
vbroadcastsd	zmm25, xmm18
vbroadcastss	zmm26, xmm3
vbroadcastss	zmm27, xmm4
vbroadcastss	zmm28, xmm5
vmovaps	oword [rsp + 32], xmm0  ; 16-byte Spill
vbroadcastsd	zmm29, xmm0
vmovaps	oword [rsp + 112], xmm19  ; 16-byte Spill
vbroadcastsd	zmm30, xmm19
vmovaps	oword [rsp + 96], xmm20  ; 16-byte Spill
vbroadcastsd	zmm31, xmm20
lea	rax, [rdx + 4*rbx + 64]
lea	r13, [r8 + 4*rbx + 64]
lea	rbp, [r9 + 4*rbx + 64]
lea	r11, [rdi + 4*rbx]
add	r11, 64
lea	r12, [rsi + 4*rbx]
add	r12, 64
vpxor	xmm6, xmm6, xmm6
xor	r15d, r15d
align 4
BB1_19:  ; =>This Inner Loop Header: Depth=1:
vmovups	zmm8, zword [rax + 4*r15 - 64]
vmovups	zmm9, zword [rax + 4*r15]
vmulps	zmm10, zmm8, zmm23
vmulps	zmm11, zmm9, zmm23
vmovups	zmm12, zword [r13 + 4*r15 - 64]
vmovups	zmm13, zword [r13 + 4*r15]
vfmadd231ps	zmm10, zmm12, zmm24  ; zmm10 = (zmm12 * zmm24) + zmm10
vfmadd231ps	zmm11, zmm13, zmm24  ; zmm11 = (zmm13 * zmm24) + zmm11
vmovups	zmm14, zword [rbp + 4*r15 - 64]
vmovups	zmm15, zword [rbp + 4*r15]
vfmadd231ps	zmm10, zmm14, zmm25  ; zmm10 = (zmm14 * zmm25) + zmm10
vfmadd231ps	zmm11, zmm15, zmm25  ; zmm11 = (zmm15 * zmm25) + zmm11
vrndscaleps	zmm18, zmm10, 12
vrndscaleps	zmm19, zmm11, 12
vmulps	zmm20, zmm8, zmm26
vmulps	zmm21, zmm9, zmm26
vfmadd231ps	zmm20, zmm12, zmm27  ; zmm20 = (zmm12 * zmm27) + zmm20
vfmadd231ps	zmm21, zmm13, zmm27  ; zmm21 = (zmm13 * zmm27) + zmm21
vfmadd231ps	zmm20, zmm14, zmm28  ; zmm20 = (zmm14 * zmm28) + zmm20
vfmadd231ps	zmm21, zmm15, zmm28  ; zmm21 = (zmm15 * zmm28) + zmm21
vrndscaleps	zmm7, zmm20, 12
vrndscaleps	zmm0, zmm21, 12
vmulps	zmm8, zmm8, zmm29
vmulps	zmm9, zmm9, zmm29
vfmadd231ps	zmm8, zmm30, zmm12  ; zmm8 = (zmm30 * zmm12) + zmm8
vfmadd231ps	zmm9, zmm30, zmm13  ; zmm9 = (zmm30 * zmm13) + zmm9
vfmadd231ps	zmm8, zmm31, zmm14  ; zmm8 = (zmm31 * zmm14) + zmm8
vfmadd231ps	zmm9, zmm31, zmm15  ; zmm9 = (zmm31 * zmm15) + zmm9
vrndscaleps	zmm12, zmm8, 12
vrndscaleps	zmm13, zmm9, 12
vsubps	zmm18, zmm10, zmm18
vsubps	zmm19, zmm11, zmm19
vmulps	zmm18, zmm18, zmm18
vmulps	zmm19, zmm19, zmm19
vsubps	zmm20, zmm20, zmm7
vsubps	zmm0, zmm21, zmm0
vfmadd213ps	zmm20, zmm20, zmm18  ; zmm20 = (zmm20 * zmm20) + zmm18
vfmadd213ps	zmm0, zmm0, zmm19  ; zmm0 = (zmm0 * zmm0) + zmm19
vsubps	zmm18, zmm8, zmm12
vsubps	zmm19, zmm9, zmm13
vfmadd213ps	zmm18, zmm18, zmm20  ; zmm18 = (zmm18 * zmm18) + zmm20
vfmadd213ps	zmm19, zmm19, zmm0  ; zmm19 = (zmm19 * zmm19) + zmm0
vcmpleps	k0, zmm16, zmm18
vcmpltps	k2, zmm18, zmm16
vcmpleps	k1, zmm16, zmm19
vcmpltps	k3, zmm19, zmm16
vmovups	zmm0 {k2} {z}, zword [r11 + 4*r15 - 64]
vmovups	zmm20 {k3} {z}, zword [r11 + 4*r15]
vcmpleps	k4 {k2}, zmm0, zmm18
vcmpleps	k5 {k3}, zmm20, zmm19
korw	k4, k4, k0
korw	k1, k5, k1
vmovdqu32	zmm21 {k4} {z}, zword [r12 + 4*r15 - 64]
vmovdqu32	zmm7 {k1} {z}, zword [r12 + 4*r15]
vpcmpeqd	k6, zmm21, zmm17
vpcmpeqd	k0, zmm7, zmm17
kandw	k7, k4, k6
kandw	k5, k1, k0
vpternlogd	zmm21, zmm21, zmm21, 255
vmovdqu32	zword [r12 + 4*r15 - 64] {k7}, zmm21
vmovdqu32	zword [r12 + 4*r15] {k5}, zmm21
vcmpltps	k2 {k2}, zmm18, zmm0
vcmpltps	k3 {k3}, zmm19, zmm20
vmovdqu32	zword [r12 + 4*r15 - 64] {k2}, zmm17
vmovdqu32	zword [r12 + 4*r15] {k3}, zmm17
vmovups	zword [r11 + 4*r15 - 64] {k2}, zmm18
vmovups	zword [r11 + 4*r15] {k3}, zmm19
knotw	k2, k4
korw	k2, k2, k6
kandnw	k2, k7, k2
vpmovm2d	zmm0, k2
vpsubd	zmm22, zmm22, zmm0
knotw	k1, k1
korw	k0, k1, k0
kandnw	k0, k5, k0
vpmovm2d	zmm0, k0
vpsubd	zmm6, zmm6, zmm0
add	r15, 32
cmp	r14, r15
jne	BB1_19
vpaddd	zmm0, zmm6, zmm22
vextracti64x4	ymm16, zmm0, 1
vpaddd	zmm0, zmm0, zmm16
vextracti32x4	xmm16, ymm0, 1
vpaddd	xmm0, xmm0, xmm16
vpshufd	xmm16, xmm0, 238  ; xmm16 = xmm0[2,3,2,3]
vpaddd	xmm0, xmm0, xmm16
vpshufd	xmm16, xmm0, 85  ; xmm16 = xmm0[1,1,1,1]
vpaddd	xmm0, xmm0, xmm16
vmovd	eax, xmm0
mov	r15, qword [rsp + 72]  ; 8-byte Reload
cmp	r15, r14
je	BB1_36
test	r15b, 24
je	BB1_37
mov	ebp, dword [rsp + 440]
vmovaps	xmm9, oword [rsp + 16]  ; 16-byte Reload
vmovaps	xmm0, oword [rsp + 32]  ; 16-byte Reload
vmovaps	xmm19, oword [rsp + 112]  ; 16-byte Reload
vmovaps	xmm20, oword [rsp + 96]  ; 16-byte Reload
vmovaps	xmm18, oword [rsp + 48]  ; 16-byte Reload
BB1_23:
mov	r11d, r10d
and	r11d, 7
mov	qword [rsp + 16], r11  ; 8-byte Spill
sub	r15, r11
add	rbx, r15
vmovd	xmm16, eax
vbroadcastss	ymm17, xmm1
vbroadcastss	ymm22, xmm2
vbroadcastsd	ymm21, xmm18
vbroadcastss	ymm23, xmm3
vbroadcastss	ymm24, xmm4
vbroadcastss	ymm25, xmm5
vbroadcastsd	ymm18, xmm0
vbroadcastsd	ymm19, xmm19
vbroadcastsd	ymm20, xmm20
vbroadcastss	ymm26, xmm9
vpbroadcastd	ymm27, ebp
vpcmpeqd	ymm6, ymm6, ymm6
mov	rax, qword [rsp + 136]  ; 8-byte Reload
mov	r12, qword [rsp + 128]  ; 8-byte Reload
mov	r13, qword [rsp + 88]  ; 8-byte Reload
mov	r11, qword [rsp + 80]  ; 8-byte Reload
align 4
BB1_24:  ; =>This Inner Loop Header: Depth=1:
vmovups	ymm0, yword [r12 + 4*r14]
vmulps	ymm28, ymm0, ymm17
vmovups	ymm29, yword [r13 + 4*r14]
vfmadd231ps	ymm28, ymm29, ymm22  ; ymm28 = (ymm29 * ymm22) + ymm28
vmovups	ymm30, yword [r11 + 4*r14]
vfmadd231ps	ymm28, ymm30, ymm21  ; ymm28 = (ymm30 * ymm21) + ymm28
vrndscaleps	ymm31, ymm28, 12
vmulps	ymm7, ymm0, ymm23
vfmadd231ps	ymm7, ymm29, ymm24  ; ymm7 = (ymm29 * ymm24) + ymm7
vfmadd231ps	ymm7, ymm30, ymm25  ; ymm7 = (ymm30 * ymm25) + ymm7
vroundps	ymm8, ymm7, 12
vmulps	ymm0, ymm0, ymm18
vfmadd231ps	ymm0, ymm19, ymm29  ; ymm0 = (ymm19 * ymm29) + ymm0
vfmadd231ps	ymm0, ymm20, ymm30  ; ymm0 = (ymm20 * ymm30) + ymm0
vrndscaleps	ymm29, ymm0, 12
vsubps	ymm28, ymm28, ymm31
vmulps	ymm28, ymm28, ymm28
vsubps	ymm30, ymm7, ymm8
vfmadd213ps	ymm30, ymm30, ymm28  ; ymm30 = (ymm30 * ymm30) + ymm28
vsubps	ymm0, ymm0, ymm29
vfmadd213ps	ymm0, ymm0, ymm30  ; ymm0 = (ymm0 * ymm0) + ymm30
vcmpleps	k0, ymm26, ymm0
vcmpltps	k1, ymm0, ymm26
vmovups	ymm28 {k1} {z}, yword [rax + 4*r14]
vcmpleps	k2 {k1}, ymm28, ymm0
korb	k2, k2, k0
vmovdqu32	ymm29 {k2} {z}, yword [rcx + 4*r14]
vpcmpeqd	k0, ymm29, ymm27
kandb	k3, k2, k0
vmovdqu32	yword [rcx + 4*r14] {k3}, ymm6
vcmpltps	k1 {k1}, ymm0, ymm28
vmovdqu32	yword [rcx + 4*r14] {k1}, ymm27
vmovups	yword [rax + 4*r14] {k1}, ymm0
knotb	k1, k2
korb	k0, k1, k0
kandnb	k0, k3, k0
vpmovm2d	ymm0, k0
vpsubd	ymm16, ymm16, ymm0
add	r14, 8
cmp	r15, r14
jne	BB1_24
vextracti32x4	xmm0, ymm16, 1
vpaddd	xmm0, xmm16, xmm0
vpshufd	xmm16, xmm0, 238  ; xmm16 = xmm0[2,3,2,3]
vpaddd	xmm0, xmm0, xmm16
vpshufd	xmm16, xmm0, 85  ; xmm16 = xmm0[1,1,1,1]
vpaddd	xmm0, xmm0, xmm16
vmovd	eax, xmm0
cmp	qword [rsp + 16], 0  ; 8-byte Folded Reload
jne	BB1_26
BB1_36:
vmovaps	xmm6, oword [rsp + 144]  ; 16-byte Reload
vmovaps	xmm7, oword [rsp + 160]  ; 16-byte Reload
vmovaps	xmm8, oword [rsp + 176]  ; 16-byte Reload
vmovaps	xmm9, oword [rsp + 192]  ; 16-byte Reload
vmovaps	xmm10, oword [rsp + 208]  ; 16-byte Reload
vmovaps	xmm11, oword [rsp + 224]  ; 16-byte Reload
vmovaps	xmm12, oword [rsp + 240]  ; 16-byte Reload
vmovaps	xmm13, oword [rsp + 256]  ; 16-byte Reload
vmovaps	xmm14, oword [rsp + 272]  ; 16-byte Reload
vmovaps	xmm15, oword [rsp + 288]  ; 16-byte Reload
add	rsp, 312
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
BB1_13:
mov	ebp, dword [rsp + 440]
jmp	BB1_26
BB1_37:
add	rbx, r14
mov	ebp, dword [rsp + 440]
vmovaps	xmm9, oword [rsp + 16]  ; 16-byte Reload
jmp	BB1_26
BB1_11:
mov	ebp, dword [rsp + 440]
jmp	BB1_26
BB1_9:
mov	ebp, dword [rsp + 440]
jmp	BB1_26
BB1_5:
mov	ebp, dword [rsp + 440]
jmp	BB1_26
BB1_7:
mov	ebp, dword [rsp + 440]
jmp	BB1_26
align 4
BB1_28:  ; in Loop: Header=BB1_26 Depth=1:
mov	dword [rsi + 4*rbx], ebp
vmovss	dword [rdi + 4*rbx], xmm16
inc	eax
BB1_35:  ; in Loop: Header=BB1_26 Depth=1:
inc	rbx
cmp	r10, rbx
je	BB1_36
BB1_26:  ; =>This Inner Loop Header: Depth=1:
vbroadcastss	xmm0, dword [r8 + 4*rbx]
vbroadcastss	xmm16, dword [r9 + 4*rbx]
vinsertps	xmm17, xmm0, xmm16, 28  ; xmm17 = xmm0[0],xmm16[0],zero,zero
vmulps	xmm17, xmm17, xmm2
vbroadcastss	xmm18, dword [rdx + 4*rbx]
vmovaps	xmm19, xmm1
vfmadd213ss	xmm19, xmm18, xmm17  ; xmm19 = (xmm18 * xmm19) + xmm17
vmovshdup	xmm17, xmm17  ; xmm17 = xmm17[1,1,3,3]
vaddss	xmm17, xmm19, xmm17
vrndscaless	xmm19, xmm17, xmm17, 12
vsubss	xmm17, xmm17, xmm19
vmulps	xmm18, xmm18, xmm3
vfmadd231ps	xmm18, xmm4, xmm0  ; xmm18 = (xmm4 * xmm0) + xmm18
vfmadd231ps	xmm18, xmm5, xmm16  ; xmm18 = (xmm5 * xmm16) + xmm18
vrndscaleps	xmm0, xmm18, 12
vsubps	xmm0, xmm18, xmm0
vmulps	xmm0, xmm0, xmm0
vfmadd213ss	xmm17, xmm17, xmm0  ; xmm17 = (xmm17 * xmm17) + xmm0
vmovshdup	xmm0, xmm0  ; xmm0 = xmm0[1,1,3,3]
vaddss	xmm16, xmm17, xmm0
vucomiss	xmm16, xmm9
jae	BB1_33
;  ; in Loop: Header=BB1_26 Depth=1:
vucomiss	xmm16, dword [rdi + 4*rbx]
jb	BB1_28
BB1_33:  ; in Loop: Header=BB1_26 Depth=1:
cmp	dword [rsi + 4*rbx], ebp
jne	BB1_35
;  ; in Loop: Header=BB1_26 Depth=1:
mov	dword [rsi + 4*rbx], -1
jmp	BB1_35

%else
global sa_inner_f32_sov_avx512
call_sa_inner_f32_sov_avx512:  ; @call_sa_inner_f32_sov_avx512:
jmp	sa_inner_f32_sov_avx512
func_end0:
align 4
sa_inner_f32_sov_avx512:  ; @sa_inner_f32_sov_avx512:
push	rbp
push	r15
push	r14
push	r13
push	r12
push	rbx
sub	rsp, 24
mov	r10, qword [rsp + 88]
vmulsd	xmm0, xmm0, xmm0
vcvtsd2ss	xmm24, xmm0, xmm0
mov	ebp, dword [rsp + 80]
vbroadcastss	zmm6, xmm24
vpbroadcastd	zmm7, ebp
cmp	r10, 16
jge	BB1_29
xor	ebx, ebx
xor	eax, eax
BB1_2:
mov	r11, r10
sub	r11, rbx
jle	BB1_36
vmovsd	xmm1, qword [rdi]  ; xmm1 = mem[0],zero
vcvtsd2ss	xmm1, xmm1, xmm1
vcvtpd2ps	xmm2, oword [rdi + 8]
vmovsd	xmm3, qword [rdi + 24]  ; xmm3 = mem[0],zero
vmovhps	xmm3, xmm3, qword [rdi + 48]  ; xmm3 = xmm3[0,1],mem[0,1]
vcvtpd2ps	xmm3, xmm3
vmovsd	xmm4, qword [rdi + 32]  ; xmm4 = mem[0],zero
vmovhps	xmm4, xmm4, qword [rdi + 56]  ; xmm4 = xmm4[0,1],mem[0,1]
vcvtpd2ps	xmm4, xmm4
vmovsd	xmm5, qword [rdi + 40]  ; xmm5 = mem[0],zero
vmovhps	xmm5, xmm5, qword [rdi + 64]  ; xmm5 = xmm5[0,1],mem[0,1]
vcvtpd2ps	xmm5, xmm5
cmp	r11, 8
jb	BB1_26
mov	qword [rsp - 56], r11  ; 8-byte Spill
lea	rdi, [r9 + 4*rbx]
lea	r12, [r9 + 4*r10]
lea	rbp, [r8 + 4*rbx]
lea	r11, [r8 + 4*r10]
lea	r15, [rsi + 4*rbx]
lea	r14, [rsi + 4*r10]
mov	qword [rsp - 96], r14  ; 8-byte Spill
lea	r14, [rdx + 4*rbx]
mov	qword [rsp - 40], r14  ; 8-byte Spill
lea	r14, [rdx + 4*r10]
mov	qword [rsp - 80], r14  ; 8-byte Spill
lea	r13, [rcx + 4*rbx]
mov	qword [rsp - 48], r13  ; 8-byte Spill
lea	r13, [rcx + 4*r10]
mov	qword [rsp - 112], r13  ; 8-byte Spill
cmp	rdi, r11
setb	byte [rsp - 16]  ; 1-byte Folded Spill
cmp	rbp, r12
setb	byte [rsp - 32]  ; 1-byte Folded Spill
cmp	rdi, qword [rsp - 96]  ; 8-byte Folded Reload
setb	byte [rsp - 113]  ; 1-byte Folded Spill
cmp	r15, r12
setb	byte [rsp - 114]  ; 1-byte Folded Spill
cmp	rdi, r14
setb	byte [rsp - 115]  ; 1-byte Folded Spill
mov	r14, qword [rsp - 40]  ; 8-byte Reload
cmp	r14, r12
setb	byte [rsp - 116]  ; 1-byte Folded Spill
cmp	rdi, qword [rsp - 112]  ; 8-byte Folded Reload
setb	byte [rsp - 117]  ; 1-byte Folded Spill
mov	r13, qword [rsp - 48]  ; 8-byte Reload
cmp	r13, r12
setb	byte [rsp - 118]  ; 1-byte Folded Spill
cmp	rbp, qword [rsp - 96]  ; 8-byte Folded Reload
setb	r12b
mov	qword [rsp + 8], r15  ; 8-byte Spill
cmp	r15, r11
setb	byte [rsp - 96]  ; 1-byte Folded Spill
cmp	rbp, qword [rsp - 80]  ; 8-byte Folded Reload
setb	byte [rsp - 119]  ; 1-byte Folded Spill
cmp	r14, r11
setb	byte [rsp - 80]  ; 1-byte Folded Spill
mov	qword [rsp + 16], rbp  ; 8-byte Spill
cmp	rbp, qword [rsp - 112]  ; 8-byte Folded Reload
setb	r15b
cmp	r13, r11
setb	r11b
movzx	ebp, byte [rsp - 32]  ; 1-byte Folded Reload
test	byte [rsp - 16], bpl  ; 1-byte Folded Reload
jne	BB1_5
movzx	ebp, byte [rsp - 114]  ; 1-byte Folded Reload
and	byte [rsp - 113], bpl  ; 1-byte Folded Spill
jne	BB1_7
movzx	ebp, byte [rsp - 116]  ; 1-byte Folded Reload
and	byte [rsp - 115], bpl  ; 1-byte Folded Spill
jne	BB1_9
movzx	ebp, byte [rsp - 118]  ; 1-byte Folded Reload
and	byte [rsp - 117], bpl  ; 1-byte Folded Spill
jne	BB1_11
and	r12b, byte [rsp - 96]  ; 1-byte Folded Reload
jne	BB1_13
movzx	ebp, byte [rsp - 119]  ; 1-byte Folded Reload
and	bpl, byte [rsp - 80]  ; 1-byte Folded Reload
mov	ebp, dword [rsp + 80]
jne	BB1_26
and	r15b, r11b
jne	BB1_26
vmovshdup	xmm8, xmm2  ; xmm8 = xmm2[1,1,3,3]
vmovshdup	xmm0, xmm3  ; xmm0 = xmm3[1,1,3,3]
vmovshdup	xmm9, xmm4  ; xmm9 = xmm4[1,1,3,3]
vmovshdup	xmm10, xmm5  ; xmm10 = xmm5[1,1,3,3]
mov	r15, qword [rsp - 56]  ; 8-byte Reload
cmp	r15, 32
jae	BB1_18
xor	r14d, r14d
jmp	BB1_23
BB1_29:
vmovsd	xmm1, qword [rdi]  ; xmm1 = mem[0],zero
vcvtsd2ss	xmm1, xmm1, xmm1
vmovsd	xmm2, qword [rdi + 8]  ; xmm2 = mem[0],zero
vbroadcastss	zmm1, xmm1
vcvtsd2ss	xmm2, xmm2, xmm2
vbroadcastss	zmm2, xmm2
vmovsd	xmm3, qword [rdi + 16]  ; xmm3 = mem[0],zero
vcvtsd2ss	xmm3, xmm3, xmm3
vbroadcastss	zmm3, xmm3
vmovsd	xmm4, qword [rdi + 24]  ; xmm4 = mem[0],zero
vcvtsd2ss	xmm4, xmm4, xmm4
vbroadcastss	zmm4, xmm4
vmovsd	xmm5, qword [rdi + 32]  ; xmm5 = mem[0],zero
vcvtsd2ss	xmm5, xmm5, xmm5
vbroadcastss	zmm5, xmm5
vmovsd	xmm8, qword [rdi + 40]  ; xmm8 = mem[0],zero
vcvtsd2ss	xmm8, xmm8, xmm8
vbroadcastss	zmm8, xmm8
vmovsd	xmm9, qword [rdi + 48]  ; xmm9 = mem[0],zero
vcvtsd2ss	xmm9, xmm9, xmm9
vbroadcastss	zmm9, xmm9
vmovsd	xmm10, qword [rdi + 56]  ; xmm10 = mem[0],zero
vcvtsd2ss	xmm10, xmm10, xmm10
vbroadcastss	zmm10, xmm10
vmovsd	xmm11, qword [rdi + 64]  ; xmm11 = mem[0],zero
vcvtsd2ss	xmm11, xmm11, xmm11
vbroadcastss	zmm11, xmm11
xor	r11d, r11d
vpternlogd	zmm12, zmm12, zmm12, 255
xor	eax, eax
jmp	BB1_30
align 4
BB1_32:  ; in Loop: Header=BB1_30 Depth=1:
lea	rbx, [r11 + 16]
add	r11, 32
cmp	r11, r10
mov	r11, rbx
jg	BB1_2
BB1_30:  ; =>This Inner Loop Header: Depth=1:
vmovups	zmm0, zword [rsi + 4*r11]
vmovups	zmm13, zword [rdx + 4*r11]
vmovups	zmm14, zword [rcx + 4*r11]
vmulps	zmm15, zmm14, zmm3
vfmadd231ps	zmm15, zmm2, zmm13  ; zmm15 = (zmm2 * zmm13) + zmm15
vfmadd231ps	zmm15, zmm1, zmm0  ; zmm15 = (zmm1 * zmm0) + zmm15
vmulps	zmm16, zmm14, zmm8
vfmadd231ps	zmm16, zmm5, zmm13  ; zmm16 = (zmm5 * zmm13) + zmm16
vfmadd231ps	zmm16, zmm4, zmm0  ; zmm16 = (zmm4 * zmm0) + zmm16
vmulps	zmm14, zmm14, zmm11
vfmadd231ps	zmm14, zmm10, zmm13  ; zmm14 = (zmm10 * zmm13) + zmm14
vfmadd231ps	zmm14, zmm9, zmm0  ; zmm14 = (zmm9 * zmm0) + zmm14
vrndscaleps	zmm0, zmm15, 8
vsubps	zmm0, zmm15, zmm0
vrndscaleps	zmm13, zmm16, 8
vsubps	zmm15, zmm16, zmm13
vrndscaleps	zmm13, zmm14, 8
vsubps	zmm13, zmm14, zmm13
vmulps	zmm13, zmm13, zmm13
vfmadd231ps	zmm13, zmm15, zmm15  ; zmm13 = (zmm15 * zmm15) + zmm13
vfmadd231ps	zmm13, zmm0, zmm0  ; zmm13 = (zmm0 * zmm0) + zmm13
vmovups	zmm14, zword [r8 + 4*r11]
vcmpltps	k1, zmm13, zmm6
vcmpltps	k1 {k1}, zmm13, zmm14
vmovdqu64	zmm0, zword [r9 + 4*r11]
vpcmpeqd	k2, zmm0, zmm7
vmovdqa32	zmm0 {k2}, zmm12
vmovdqa32	zmm0 {k1}, zmm7
vmovdqu64	zword [r9 + 4*r11], zmm0
kortestw	k1, k1
je	BB1_32
;  ; in Loop: Header=BB1_30 Depth=1:
kmovd	ebx, k1
movzx	ebx, bx
popcnt	ebx, ebx
add	eax, ebx
vmovaps	zmm14 {k1}, zmm13
vmovups	zword [r8 + 4*r11], zmm14
jmp	BB1_32
BB1_18:
vmovaps	oword [rsp - 112], xmm24  ; 16-byte Spill
mov	r14, r15
and	r14, -32
vmovd	xmm12, eax
vbroadcastss	zmm13, xmm1
vbroadcastss	zmm14, xmm2
vmovaps	oword [rsp - 80], xmm8  ; 16-byte Spill
vbroadcastsd	zmm15, xmm8
vbroadcastss	zmm16, xmm3
vbroadcastss	zmm17, xmm4
vbroadcastss	zmm18, xmm5
vmovaps	oword [rsp - 96], xmm0  ; 16-byte Spill
vbroadcastsd	zmm19, xmm0
vmovaps	oword [rsp - 16], xmm9  ; 16-byte Spill
vbroadcastsd	zmm20, xmm9
vmovaps	oword [rsp - 32], xmm10  ; 16-byte Spill
vbroadcastsd	zmm21, xmm10
lea	rax, [rsi + 4*rbx + 64]
lea	r13, [rdx + 4*rbx + 64]
lea	rbp, [rcx + 4*rbx + 64]
lea	r11, [r8 + 4*rbx]
add	r11, 64
lea	r12, [r9 + 4*rbx]
add	r12, 64
vpxord	xmm22, xmm22, xmm22
xor	r15d, r15d
align 4
BB1_19:  ; =>This Inner Loop Header: Depth=1:
vmovups	zmm24, zword [rax + 4*r15 - 64]
vmovups	zmm25, zword [rax + 4*r15]
vmulps	zmm26, zmm24, zmm13
vmulps	zmm27, zmm25, zmm13
vmovups	zmm28, zword [r13 + 4*r15 - 64]
vmovups	zmm29, zword [r13 + 4*r15]
vfmadd231ps	zmm26, zmm28, zmm14  ; zmm26 = (zmm28 * zmm14) + zmm26
vfmadd231ps	zmm27, zmm29, zmm14  ; zmm27 = (zmm29 * zmm14) + zmm27
vmovups	zmm30, zword [rbp + 4*r15 - 64]
vmovups	zmm31, zword [rbp + 4*r15]
vfmadd231ps	zmm26, zmm30, zmm15  ; zmm26 = (zmm30 * zmm15) + zmm26
vfmadd231ps	zmm27, zmm31, zmm15  ; zmm27 = (zmm31 * zmm15) + zmm27
vrndscaleps	zmm8, zmm26, 12
vrndscaleps	zmm9, zmm27, 12
vmulps	zmm10, zmm24, zmm16
vmulps	zmm11, zmm25, zmm16
vfmadd231ps	zmm10, zmm28, zmm17  ; zmm10 = (zmm28 * zmm17) + zmm10
vfmadd231ps	zmm11, zmm29, zmm17  ; zmm11 = (zmm29 * zmm17) + zmm11
vfmadd231ps	zmm10, zmm30, zmm18  ; zmm10 = (zmm30 * zmm18) + zmm10
vfmadd231ps	zmm11, zmm31, zmm18  ; zmm11 = (zmm31 * zmm18) + zmm11
vrndscaleps	zmm23, zmm10, 12
vrndscaleps	zmm0, zmm11, 12
vmulps	zmm24, zmm24, zmm19
vmulps	zmm25, zmm25, zmm19
vfmadd231ps	zmm24, zmm20, zmm28  ; zmm24 = (zmm20 * zmm28) + zmm24
vfmadd231ps	zmm25, zmm20, zmm29  ; zmm25 = (zmm20 * zmm29) + zmm25
vfmadd231ps	zmm24, zmm21, zmm30  ; zmm24 = (zmm21 * zmm30) + zmm24
vfmadd231ps	zmm25, zmm21, zmm31  ; zmm25 = (zmm21 * zmm31) + zmm25
vrndscaleps	zmm28, zmm24, 12
vrndscaleps	zmm29, zmm25, 12
vsubps	zmm8, zmm26, zmm8
vsubps	zmm9, zmm27, zmm9
vmulps	zmm8, zmm8, zmm8
vmulps	zmm9, zmm9, zmm9
vsubps	zmm10, zmm10, zmm23
vsubps	zmm0, zmm11, zmm0
vfmadd213ps	zmm10, zmm10, zmm8  ; zmm10 = (zmm10 * zmm10) + zmm8
vfmadd213ps	zmm0, zmm0, zmm9  ; zmm0 = (zmm0 * zmm0) + zmm9
vsubps	zmm8, zmm24, zmm28
vsubps	zmm9, zmm25, zmm29
vfmadd213ps	zmm8, zmm8, zmm10  ; zmm8 = (zmm8 * zmm8) + zmm10
vfmadd213ps	zmm9, zmm9, zmm0  ; zmm9 = (zmm9 * zmm9) + zmm0
vcmpleps	k0, zmm6, zmm8
vcmpltps	k2, zmm8, zmm6
vcmpleps	k1, zmm6, zmm9
vcmpltps	k3, zmm9, zmm6
vmovups	zmm0 {k2} {z}, zword [r11 + 4*r15 - 64]
vmovups	zmm10 {k3} {z}, zword [r11 + 4*r15]
vcmpleps	k4 {k2}, zmm0, zmm8
vcmpleps	k5 {k3}, zmm10, zmm9
korw	k4, k4, k0
korw	k1, k5, k1
vmovdqu32	zmm11 {k4} {z}, zword [r12 + 4*r15 - 64]
vmovdqu32	zmm23 {k1} {z}, zword [r12 + 4*r15]
vpcmpeqd	k6, zmm11, zmm7
vpcmpeqd	k0, zmm23, zmm7
kandw	k7, k4, k6
kandw	k5, k1, k0
vpternlogd	zmm11, zmm11, zmm11, 255
vmovdqu32	zword [r12 + 4*r15 - 64] {k7}, zmm11
vmovdqu32	zword [r12 + 4*r15] {k5}, zmm11
vcmpltps	k2 {k2}, zmm8, zmm0
vcmpltps	k3 {k3}, zmm9, zmm10
vmovdqu32	zword [r12 + 4*r15 - 64] {k2}, zmm7
vmovdqu32	zword [r12 + 4*r15] {k3}, zmm7
vmovups	zword [r11 + 4*r15 - 64] {k2}, zmm8
vmovups	zword [r11 + 4*r15] {k3}, zmm9
knotw	k2, k4
korw	k2, k2, k6
kandnw	k2, k7, k2
vpmovm2d	zmm0, k2
vpsubd	zmm12, zmm12, zmm0
knotw	k1, k1
korw	k0, k1, k0
kandnw	k0, k5, k0
vpmovm2d	zmm0, k0
vpsubd	zmm22, zmm22, zmm0
add	r15, 32
cmp	r14, r15
jne	BB1_19
vpaddd	zmm0, zmm22, zmm12
vextracti64x4	ymm6, zmm0, 1
vpaddd	zmm0, zmm0, zmm6
vextracti128	xmm6, ymm0, 1
vpaddd	xmm0, xmm0, xmm6
vpshufd	xmm6, xmm0, 238  ; xmm6 = xmm0[2,3,2,3]
vpaddd	xmm0, xmm0, xmm6
vpshufd	xmm6, xmm0, 85  ; xmm6 = xmm0[1,1,1,1]
vpaddd	xmm0, xmm0, xmm6
vmovd	eax, xmm0
mov	r15, qword [rsp - 56]  ; 8-byte Reload
cmp	r15, r14
je	BB1_36
test	r15b, 24
je	BB1_37
vmovaps	xmm24, oword [rsp - 112]  ; 16-byte Reload
mov	ebp, dword [rsp + 80]
vmovaps	xmm0, oword [rsp - 96]  ; 16-byte Reload
vmovaps	xmm9, oword [rsp - 16]  ; 16-byte Reload
vmovaps	xmm10, oword [rsp - 32]  ; 16-byte Reload
vmovaps	xmm8, oword [rsp - 80]  ; 16-byte Reload
BB1_23:
mov	r11d, r10d
and	r11d, 7
mov	qword [rsp - 112], r11  ; 8-byte Spill
sub	r15, r11
add	rbx, r15
vmovd	xmm6, eax
vbroadcastss	ymm25, xmm1
vbroadcastss	ymm12, xmm2
vbroadcastsd	ymm11, xmm8
vbroadcastss	ymm13, xmm3
vbroadcastss	ymm14, xmm4
vbroadcastss	ymm15, xmm5
vbroadcastsd	ymm8, xmm0
vbroadcastsd	ymm9, xmm9
vbroadcastsd	ymm10, xmm10
vbroadcastss	ymm16, xmm24
vpbroadcastd	ymm17, ebp
mov	rax, qword [rsp + 16]  ; 8-byte Reload
mov	r12, qword [rsp + 8]  ; 8-byte Reload
mov	r13, qword [rsp - 40]  ; 8-byte Reload
mov	r11, qword [rsp - 48]  ; 8-byte Reload
vpcmpeqd	ymm7, ymm7, ymm7
align 4
BB1_24:  ; =>This Inner Loop Header: Depth=1:
vmovups	ymm0, yword [r12 + 4*r14]
vmulps	ymm18, ymm0, ymm25
vmovups	ymm19, yword [r13 + 4*r14]
vfmadd231ps	ymm18, ymm19, ymm12  ; ymm18 = (ymm19 * ymm12) + ymm18
vmovups	ymm20, yword [r11 + 4*r14]
vfmadd231ps	ymm18, ymm20, ymm11  ; ymm18 = (ymm20 * ymm11) + ymm18
vrndscaleps	ymm21, ymm18, 12
vmulps	ymm22, ymm0, ymm13
vfmadd231ps	ymm22, ymm19, ymm14  ; ymm22 = (ymm19 * ymm14) + ymm22
vfmadd231ps	ymm22, ymm20, ymm15  ; ymm22 = (ymm20 * ymm15) + ymm22
vrndscaleps	ymm23, ymm22, 12
vmulps	ymm0, ymm8, ymm0
vfmadd231ps	ymm0, ymm9, ymm19  ; ymm0 = (ymm9 * ymm19) + ymm0
vfmadd231ps	ymm0, ymm10, ymm20  ; ymm0 = (ymm10 * ymm20) + ymm0
vrndscaleps	ymm19, ymm0, 12
vsubps	ymm18, ymm18, ymm21
vmulps	ymm18, ymm18, ymm18
vsubps	ymm20, ymm22, ymm23
vfmadd213ps	ymm20, ymm20, ymm18  ; ymm20 = (ymm20 * ymm20) + ymm18
vsubps	ymm0, ymm0, ymm19
vfmadd213ps	ymm0, ymm0, ymm20  ; ymm0 = (ymm0 * ymm0) + ymm20
vcmpleps	k0, ymm16, ymm0
vcmpltps	k1, ymm0, ymm16
vmovups	ymm18 {k1} {z}, yword [rax + 4*r14]
vcmpleps	k2 {k1}, ymm18, ymm0
korb	k2, k2, k0
vmovdqu32	ymm19 {k2} {z}, yword [rdi + 4*r14]
vpcmpeqd	k0, ymm19, ymm17
kandb	k3, k2, k0
vmovdqu32	yword [rdi + 4*r14] {k3}, ymm7
vcmpltps	k1 {k1}, ymm0, ymm18
vmovdqu32	yword [rdi + 4*r14] {k1}, ymm17
vmovups	yword [rax + 4*r14] {k1}, ymm0
knotb	k1, k2
korb	k0, k1, k0
kandnb	k0, k3, k0
vpmovm2d	ymm0, k0
vpsubd	ymm6, ymm6, ymm0
add	r14, 8
cmp	r15, r14
jne	BB1_24
vextracti128	xmm0, ymm6, 1
vpaddd	xmm0, xmm6, xmm0
vpshufd	xmm6, xmm0, 238  ; xmm6 = xmm0[2,3,2,3]
vpaddd	xmm0, xmm0, xmm6
vpshufd	xmm6, xmm0, 85  ; xmm6 = xmm0[1,1,1,1]
vpaddd	xmm0, xmm0, xmm6
vmovd	eax, xmm0
cmp	qword [rsp - 112], 0  ; 8-byte Folded Reload
jne	BB1_26
BB1_36:
add	rsp, 24
pop	rbx
pop	r12
pop	r13
pop	r14
pop	r15
pop	rbp
vzeroupper
ret
BB1_13:
mov	ebp, dword [rsp + 80]
jmp	BB1_26
BB1_37:
add	rbx, r14
vmovaps	xmm24, oword [rsp - 112]  ; 16-byte Reload
mov	ebp, dword [rsp + 80]
jmp	BB1_26
BB1_11:
mov	ebp, dword [rsp + 80]
jmp	BB1_26
BB1_9:
mov	ebp, dword [rsp + 80]
jmp	BB1_26
BB1_5:
mov	ebp, dword [rsp + 80]
jmp	BB1_26
BB1_7:
mov	ebp, dword [rsp + 80]
jmp	BB1_26
align 4
BB1_28:  ; in Loop: Header=BB1_26 Depth=1:
mov	dword [r9 + 4*rbx], ebp
vmovss	dword [r8 + 4*rbx], xmm6
inc	eax
BB1_35:  ; in Loop: Header=BB1_26 Depth=1:
inc	rbx
cmp	r10, rbx
je	BB1_36
BB1_26:  ; =>This Inner Loop Header: Depth=1:
vbroadcastss	xmm0, dword [rdx + 4*rbx]
vbroadcastss	xmm6, dword [rcx + 4*rbx]
vinsertps	xmm7, xmm0, xmm6, 28  ; xmm7 = xmm0[0],xmm6[0],zero,zero
vmulps	xmm7, xmm7, xmm2
vbroadcastss	xmm8, dword [rsi + 4*rbx]
vmovaps	xmm9, xmm1
vfmadd213ss	xmm9, xmm8, xmm7  ; xmm9 = (xmm8 * xmm9) + xmm7
vmovshdup	xmm7, xmm7  ; xmm7 = xmm7[1,1,3,3]
vaddss	xmm7, xmm9, xmm7
vroundss	xmm9, xmm7, xmm7, 12
vsubss	xmm7, xmm7, xmm9
vmulps	xmm8, xmm8, xmm3
vfmadd231ps	xmm8, xmm4, xmm0  ; xmm8 = (xmm4 * xmm0) + xmm8
vfmadd231ps	xmm8, xmm5, xmm6  ; xmm8 = (xmm5 * xmm6) + xmm8
vroundps	xmm0, xmm8, 12
vsubps	xmm0, xmm8, xmm0
vmulps	xmm0, xmm0, xmm0
vfmadd213ss	xmm7, xmm7, xmm0  ; xmm7 = (xmm7 * xmm7) + xmm0
vmovshdup	xmm0, xmm0  ; xmm0 = xmm0[1,1,3,3]
vaddss	xmm6, xmm7, xmm0
vucomiss	xmm6, xmm24
jae	BB1_33
;  ; in Loop: Header=BB1_26 Depth=1:
vucomiss	xmm6, dword [r8 + 4*rbx]
jb	BB1_28
BB1_33:  ; in Loop: Header=BB1_26 Depth=1:
cmp	dword [r9 + 4*rbx], ebp
jne	BB1_35
;  ; in Loop: Header=BB1_26 Depth=1:
mov	dword [r9 + 4*rbx], -1
jmp	BB1_35
func_end1:

%endif
