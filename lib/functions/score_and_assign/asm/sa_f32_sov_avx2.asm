SECTION .note.GNU-stack noalloc noexec nowrite progbits
%include "c2_abi.asm"
SECTION .text

%ifidn __OUTPUT_FORMAT__, win64
global sa_inner_f32_sov_avx2
call_sa_inner_f32_sov_avx2:  ; @call_sa_inner_f32_sov_avx2:
jmp	sa_inner_f32_sov_avx2
SECTION .text
align 4
CPI1_0:
dd	27  ; 0x1b
dd	30  ; 0x1e
dd	29  ; 0x1d
dd	28  ; 0x1c
times 16 db 0
CPI1_1:
times 32 db 255
SECTION .text
align 4
sa_inner_f32_sov_avx2:  ; @sa_inner_f32_sov_avx2:
push	r15
push	r14
push	r13
push	r12
push	rsi
push	rdi
push	rbp
push	rbx
sub	rsp, 456
vmovaps	oword [rsp + 432], xmm15  ; 16-byte Spill
vmovdqa	oword [rsp + 416], xmm14  ; 16-byte Spill
vmovdqa	oword [rsp + 400], xmm13  ; 16-byte Spill
vmovdqa	oword [rsp + 384], xmm12  ; 16-byte Spill
vmovdqa	oword [rsp + 368], xmm11  ; 16-byte Spill
vmovaps	oword [rsp + 352], xmm10  ; 16-byte Spill
vmovaps	oword [rsp + 336], xmm9  ; 16-byte Spill
vmovaps	oword [rsp + 320], xmm8  ; 16-byte Spill
vmovaps	oword [rsp + 304], xmm7  ; 16-byte Spill
vmovaps	oword [rsp + 288], xmm6  ; 16-byte Spill
mov	r10, qword [rsp + 592]
mov	r11d, dword [rsp + 584]
mov	rsi, qword [rsp + 576]
mov	rdi, qword [rsp + 568]
vmovsd	xmm0, qword [rsp + 560]  ; xmm0 = mem[0],zero
vmulsd	xmm0, xmm0, xmm0
vcvtsd2ss	xmm0, xmm0, xmm0
vmovaps	oword [rsp + 16], xmm0  ; 16-byte Spill
vbroadcastss	ymm1, xmm0
cmp	r10, 8
jge	BB1_25
xor	r14d, r14d
xor	eax, eax
BB1_2:
mov	rbx, r10
sub	rbx, r14
jle	BB1_32
vmovsd	xmm0, qword [rcx]  ; xmm0 = mem[0],zero
vcvtsd2ss	xmm2, xmm0, xmm0
vcvtpd2ps	xmm3, oword [rcx + 8]
vmovsd	xmm0, qword [rcx + 24]  ; xmm0 = mem[0],zero
vmovhpd	xmm0, xmm0, qword [rcx + 48]  ; xmm0 = xmm0[0],mem[0]
vcvtpd2ps	xmm4, xmm0
vmovsd	xmm0, qword [rcx + 32]  ; xmm0 = mem[0],zero
vmovhpd	xmm0, xmm0, qword [rcx + 56]  ; xmm0 = xmm0[0],mem[0]
vcvtpd2ps	xmm5, xmm0
vmovsd	xmm0, qword [rcx + 40]  ; xmm0 = mem[0],zero
vmovhpd	xmm0, xmm0, qword [rcx + 64]  ; xmm0 = xmm0[0],mem[0]
vcvtpd2ps	xmm6, xmm0
cmp	rbx, 16
jae	BB1_5
mov	rbx, r14
vmovdqa	xmm10, oword [rsp + 16]  ; 16-byte Reload
jmp	BB1_22
BB1_25:
vmovsd	xmm0, qword [rcx]  ; xmm0 = mem[0],zero
vmovsd	xmm2, qword [rcx + 8]  ; xmm2 = mem[0],zero
vcvtsd2ss	xmm0, xmm0, xmm0
vcvtsd2ss	xmm3, xmm2, xmm2
vbroadcastss	ymm2, xmm0
vmovsd	xmm0, qword [rcx + 16]  ; xmm0 = mem[0],zero
vcvtsd2ss	xmm0, xmm0, xmm0
vbroadcastss	ymm3, xmm3
vmovsd	xmm4, qword [rcx + 24]  ; xmm4 = mem[0],zero
vcvtsd2ss	xmm5, xmm4, xmm4
vbroadcastss	ymm4, xmm0
vmovsd	xmm0, qword [rcx + 32]  ; xmm0 = mem[0],zero
vcvtsd2ss	xmm0, xmm0, xmm0
vbroadcastss	ymm5, xmm5
vmovsd	xmm6, qword [rcx + 40]  ; xmm6 = mem[0],zero
vcvtsd2ss	xmm7, xmm6, xmm6
vbroadcastss	ymm6, xmm0
vmovsd	xmm0, qword [rcx + 48]  ; xmm0 = mem[0],zero
vcvtsd2ss	xmm0, xmm0, xmm0
vbroadcastss	ymm7, xmm7
vmovsd	xmm8, qword [rcx + 56]  ; xmm8 = mem[0],zero
vcvtsd2ss	xmm9, xmm8, xmm8
vbroadcastss	ymm8, xmm0
vmovsd	xmm0, qword [rcx + 64]  ; xmm0 = mem[0],zero
vcvtsd2ss	xmm0, xmm0, xmm0
vbroadcastss	ymm9, xmm9
vbroadcastss	ymm10, xmm0
vmovd	xmm0, r11d
vpbroadcastd	ymm11, xmm0
xor	ebx, ebx
xor	eax, eax
jmp	BB1_26
align 4
BB1_28:  ; in Loop: Header=BB1_26 Depth=1:
vmovdqu	ymm0, yword [rsi + 4*rbx]
vpcmpeqd	ymm14, ymm11, ymm0
movsx	r14d, bpl
sar	r14d, 7
mov	r15d, ebp
shl	r15d, 25
sar	r15d, 31
mov	r12d, ebp
shl	r12d, 26
sar	r12d, 31
vmovd	xmm12, ebp
vpbroadcastd	xmm12, xmm12
vpsllvd	xmm12, xmm12, oword [rel CPI1_0]
and	ebp, 1
neg	ebp
vmovd	xmm13, ebp
vpsrad	xmm12, xmm12, 31
vpermq	ymm12, ymm12, 196  ; ymm12 = ymm12[0,1,0,3]
vpblendd	ymm12, ymm12, ymm13, 1  ; ymm12 = ymm13[0],ymm12[1,2,3,4,5,6,7]
vmovd	xmm13, r12d
vpbroadcastd	ymm13, xmm13
vpblendd	ymm12, ymm12, ymm13, 32  ; ymm12 = ymm12[0,1,2,3,4],ymm13[5],ymm12[6,7]
vmovd	xmm13, r15d
vpbroadcastd	ymm13, xmm13
vpblendd	ymm12, ymm12, ymm13, 64  ; ymm12 = ymm12[0,1,2,3,4,5],ymm13[6],ymm12[7]
vmovd	xmm13, r14d
vpbroadcastd	ymm13, xmm13
vpblendd	ymm12, ymm12, ymm13, 128  ; ymm12 = ymm12[0,1,2,3,4,5,6],ymm13[7]
vpblendvb	ymm0, ymm0, ymm11, ymm12
vpandn	ymm12, ymm12, ymm14
vpblendvb	ymm0, ymm0, yword [rel CPI1_1], ymm12
vmovdqu	yword [rsi + 4*rbx], ymm0
lea	r14, [rbx + 8]
add	rbx, 16
cmp	rbx, r10
mov	rbx, r14
jg	BB1_2
BB1_26:  ; =>This Inner Loop Header: Depth=1:
vmovups	ymm0, yword [rdx + 4*rbx]
vmovups	ymm14, yword [r8 + 4*rbx]
vmovups	ymm15, yword [r9 + 4*rbx]
vmulps	ymm12, ymm15, ymm4
vfmadd231ps	ymm12, ymm3, ymm14  ; ymm12 = (ymm3 * ymm14) + ymm12
vfmadd231ps	ymm12, ymm2, ymm0  ; ymm12 = (ymm2 * ymm0) + ymm12
vmulps	ymm13, ymm15, ymm7
vfmadd231ps	ymm13, ymm6, ymm14  ; ymm13 = (ymm6 * ymm14) + ymm13
vfmadd231ps	ymm13, ymm5, ymm0  ; ymm13 = (ymm5 * ymm0) + ymm13
vmulps	ymm15, ymm15, ymm10
vfmadd231ps	ymm15, ymm9, ymm14  ; ymm15 = (ymm9 * ymm14) + ymm15
vfmadd231ps	ymm15, ymm8, ymm0  ; ymm15 = (ymm8 * ymm0) + ymm15
vroundps	ymm0, ymm12, 8
vsubps	ymm12, ymm12, ymm0
vroundps	ymm0, ymm13, 8
vsubps	ymm13, ymm13, ymm0
vroundps	ymm0, ymm15, 8
vsubps	ymm0, ymm15, ymm0
vmulps	ymm0, ymm0, ymm0
vfmadd231ps	ymm0, ymm13, ymm13  ; ymm0 = (ymm13 * ymm13) + ymm0
vfmadd231ps	ymm0, ymm12, ymm12  ; ymm0 = (ymm12 * ymm12) + ymm0
vmovups	ymm14, yword [rdi + 4*rbx]
vcmpltps	ymm12, ymm0, ymm14
vcmpltps	ymm13, ymm0, ymm1
vandps	ymm15, ymm13, ymm12
vmovmskps	ebp, ymm15
test	ebp, ebp
je	BB1_28
;  ; in Loop: Header=BB1_26 Depth=1:
vextractf128	xmm12, ymm15, 1
vpackssdw	xmm12, xmm15, xmm12
popcnt	r14d, ebp
add	eax, r14d
vpmovsxwd	ymm12, xmm12
vblendvps	ymm0, ymm14, ymm0, ymm12
vmovups	yword [rdi + 4*rbx], ymm0
jmp	BB1_28
BB1_5:
lea	r13, [rsi + 4*r14]
lea	r12, [rsi + 4*r10]
lea	r15, [rdi + 4*r14]
lea	rbp, [rdi + 4*r10]
lea	rcx, [rdx + 4*r14]
mov	qword [rsp + 32], rcx  ; 8-byte Spill
lea	rcx, [rdx + 4*r10]
lea	r11, [r8 + 4*r14]
mov	qword [rsp + 64], r11  ; 8-byte Spill
lea	r11, [r8 + 4*r10]
mov	qword [rsp + 96], r11  ; 8-byte Spill
lea	r11, [r9 + 4*r10]
mov	qword [rsp + 192], r11  ; 8-byte Spill
cmp	r13, rbp
setb	byte [rsp + 256]  ; 1-byte Folded Spill
cmp	r15, r12
setb	byte [rsp + 224]  ; 1-byte Folded Spill
cmp	r13, rcx
setb	byte [rsp + 160]  ; 1-byte Folded Spill
cmp	qword [rsp + 32], r12  ; 8-byte Folded Reload
setb	byte [rsp + 128]  ; 1-byte Folded Spill
cmp	r13, qword [rsp + 96]  ; 8-byte Folded Reload
setb	byte [rsp + 15]  ; 1-byte Folded Spill
cmp	qword [rsp + 64], r12  ; 8-byte Folded Reload
setb	byte [rsp + 14]  ; 1-byte Folded Spill
mov	r11, qword [rsp + 192]  ; 8-byte Reload
cmp	r13, r11
lea	r13, [r9 + 4*r14]
setb	byte [rsp + 13]  ; 1-byte Folded Spill
cmp	r13, r12
setb	byte [rsp + 12]  ; 1-byte Folded Spill
cmp	r15, rcx
setb	byte [rsp + 11]  ; 1-byte Folded Spill
cmp	qword [rsp + 32], rbp  ; 8-byte Folded Reload
setb	byte [rsp + 32]  ; 1-byte Folded Spill
cmp	r15, qword [rsp + 96]  ; 8-byte Folded Reload
setb	r12b
cmp	qword [rsp + 64], rbp  ; 8-byte Folded Reload
setb	byte [rsp + 64]  ; 1-byte Folded Spill
cmp	r15, r11
setb	r15b
cmp	r13, rbp
setb	cl
movzx	r11d, byte [rsp + 224]  ; 1-byte Folded Reload
test	byte [rsp + 256], r11b  ; 1-byte Folded Reload
vmovdqa	xmm10, oword [rsp + 16]  ; 16-byte Reload
jne	BB1_6
movzx	r11d, byte [rsp + 128]  ; 1-byte Folded Reload
and	byte [rsp + 160], r11b  ; 1-byte Folded Spill
mov	r11d, dword [rsp + 584]
jne	BB1_8
movzx	r13d, byte [rsp + 14]  ; 1-byte Folded Reload
and	byte [rsp + 15], r13b  ; 1-byte Folded Spill
jne	BB1_10
movzx	r13d, byte [rsp + 12]  ; 1-byte Folded Reload
and	byte [rsp + 13], r13b  ; 1-byte Folded Spill
jne	BB1_12
movzx	ebp, byte [rsp + 11]  ; 1-byte Folded Reload
and	bpl, byte [rsp + 32]  ; 1-byte Folded Reload
jne	BB1_14
and	r12b, byte [rsp + 64]  ; 1-byte Folded Reload
jne	BB1_16
and	r15b, cl
jne	BB1_18
mov	ecx, r10d
and	ecx, 7
sub	rbx, rcx
add	rbx, r14
vmovd	xmm7, eax
vbroadcastss	ymm0, xmm2
vmovups	yword [rsp + 64], ymm0  ; 32-byte Spill
vbroadcastss	ymm0, xmm3
vmovupd	yword [rsp + 32], ymm0  ; 32-byte Spill
vmovshdup	xmm0, xmm3  ; xmm0 = xmm3[1,1,3,3]
vbroadcastsd	ymm0, xmm0
vmovups	yword [rsp + 96], ymm0  ; 32-byte Spill
vbroadcastss	ymm0, xmm4
vmovupd	yword [rsp + 256], ymm0  ; 32-byte Spill
vbroadcastss	ymm0, xmm5
vmovupd	yword [rsp + 224], ymm0  ; 32-byte Spill
vbroadcastss	ymm0, xmm6
vmovupd	yword [rsp + 192], ymm0  ; 32-byte Spill
vmovshdup	xmm0, xmm4  ; xmm0 = xmm4[1,1,3,3]
vbroadcastsd	ymm0, xmm0
vmovups	yword [rsp + 160], ymm0  ; 32-byte Spill
vmovshdup	xmm0, xmm5  ; xmm0 = xmm5[1,1,3,3]
vbroadcastsd	ymm0, xmm0
vmovups	yword [rsp + 128], ymm0  ; 32-byte Spill
vmovshdup	xmm0, xmm6  ; xmm0 = xmm6[1,1,3,3]
vbroadcastsd	ymm0, xmm0
vmovd	xmm8, r11d
vpbroadcastd	ymm8, xmm8
vpcmpeqd	ymm9, ymm9, ymm9
align 4
BB1_20:  ; =>This Inner Loop Header: Depth=1:
vmovups	ymm10, yword [rdx + 4*r14]
vmulps	ymm11, ymm10, yword [rsp + 64]  ; 32-byte Folded Reload
vmovups	ymm12, yword [r8 + 4*r14]
vfmadd231ps	ymm11, ymm12, yword [rsp + 32]  ; 32-byte Folded Reload
  ; ymm11 = (ymm12 * mem) + ymm11
vmovups	ymm13, yword [r9 + 4*r14]
vfmadd231ps	ymm11, ymm13, yword [rsp + 96]  ; 32-byte Folded Reload
  ; ymm11 = (ymm13 * mem) + ymm11
vroundps	ymm14, ymm11, 12
vsubps	ymm11, ymm11, ymm14
vmulps	ymm14, ymm10, yword [rsp + 256]  ; 32-byte Folded Reload
vfmadd231ps	ymm14, ymm12, yword [rsp + 224]  ; 32-byte Folded Reload
  ; ymm14 = (ymm12 * mem) + ymm14
vfmadd231ps	ymm14, ymm13, yword [rsp + 192]  ; 32-byte Folded Reload
  ; ymm14 = (ymm13 * mem) + ymm14
vroundps	ymm15, ymm14, 12
vsubps	ymm14, ymm14, ymm15
vmulps	ymm10, ymm10, yword [rsp + 160]  ; 32-byte Folded Reload
vfmadd231ps	ymm10, ymm12, yword [rsp + 128]  ; 32-byte Folded Reload
  ; ymm10 = (ymm12 * mem) + ymm10
vfmadd231ps	ymm10, ymm0, ymm13  ; ymm10 = (ymm0 * ymm13) + ymm10
vroundps	ymm12, ymm10, 12
vsubps	ymm10, ymm10, ymm12
vmulps	ymm11, ymm11, ymm11
vfmadd231ps	ymm11, ymm14, ymm14  ; ymm11 = (ymm14 * ymm14) + ymm11
vfmadd231ps	ymm11, ymm10, ymm10  ; ymm11 = (ymm10 * ymm10) + ymm11
vcmpltps	ymm10, ymm11, ymm1
vmaskmovps	ymm12, ymm10, yword [rdi + 4*r14]
vcmpleps	ymm13, ymm1, ymm11
vcmpleps	ymm14, ymm12, ymm11
vandps	ymm14, ymm10, ymm14
vorps	ymm13, ymm14, ymm13
vpmaskmovd	ymm14, ymm13, yword [rsi + 4*r14]
vcmpltps	ymm12, ymm11, ymm12
vpcmpeqd	ymm14, ymm14, ymm8
vandps	ymm10, ymm10, ymm12
vpand	ymm12, ymm13, ymm14
vpmaskmovd	yword [rsi + 4*r14], ymm12, ymm9
vpmaskmovd	yword [rsi + 4*r14], ymm10, ymm8
vmaskmovps	yword [rdi + 4*r14], ymm10, ymm11
vpxor	ymm10, ymm13, ymm9
vpor	ymm10, ymm10, ymm14
vpandn	ymm10, ymm12, ymm10
vpsubd	ymm7, ymm7, ymm10
add	r14, 8
cmp	rbx, r14
jne	BB1_20
vextracti128	xmm0, ymm7, 1
vpaddd	xmm0, xmm7, xmm0
vpshufd	xmm1, xmm0, 238  ; xmm1 = xmm0[2,3,2,3]
vpaddd	xmm0, xmm0, xmm1
vpshufd	xmm1, xmm0, 85  ; xmm1 = xmm0[1,1,1,1]
vpaddd	xmm0, xmm0, xmm1
vmovd	eax, xmm0
test	rcx, rcx
vmovdqa	xmm10, oword [rsp + 16]  ; 16-byte Reload
jne	BB1_22
BB1_32:
vmovaps	xmm6, oword [rsp + 288]  ; 16-byte Reload
vmovaps	xmm7, oword [rsp + 304]  ; 16-byte Reload
vmovaps	xmm8, oword [rsp + 320]  ; 16-byte Reload
vmovaps	xmm9, oword [rsp + 336]  ; 16-byte Reload
vmovaps	xmm10, oword [rsp + 352]  ; 16-byte Reload
vmovaps	xmm11, oword [rsp + 368]  ; 16-byte Reload
vmovaps	xmm12, oword [rsp + 384]  ; 16-byte Reload
vmovaps	xmm13, oword [rsp + 400]  ; 16-byte Reload
vmovaps	xmm14, oword [rsp + 416]  ; 16-byte Reload
vmovaps	xmm15, oword [rsp + 432]  ; 16-byte Reload
add	rsp, 456
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
BB1_18:
mov	rbx, r14
jmp	BB1_22
BB1_16:
mov	rbx, r14
jmp	BB1_22
BB1_14:
mov	rbx, r14
jmp	BB1_22
BB1_12:
mov	rbx, r14
jmp	BB1_22
BB1_10:
mov	rbx, r14
jmp	BB1_22
BB1_6:
mov	rbx, r14
mov	r11d, dword [rsp + 584]
jmp	BB1_22
BB1_8:
mov	rbx, r14
jmp	BB1_22
align 4
BB1_24:  ; in Loop: Header=BB1_22 Depth=1:
mov	dword [rsi + 4*rbx], r11d
vmovss	dword [rdi + 4*rbx], xmm0
inc	eax
BB1_31:  ; in Loop: Header=BB1_22 Depth=1:
inc	rbx
cmp	r10, rbx
je	BB1_32
BB1_22:  ; =>This Inner Loop Header: Depth=1:
vbroadcastss	xmm0, dword [r8 + 4*rbx]
vbroadcastss	xmm1, dword [r9 + 4*rbx]
vinsertps	xmm7, xmm0, xmm1, 28  ; xmm7 = xmm0[0],xmm1[0],zero,zero
vmulps	xmm7, xmm7, xmm3
vbroadcastss	xmm8, dword [rdx + 4*rbx]
vmovaps	xmm9, xmm2
vfmadd213ss	xmm9, xmm8, xmm7  ; xmm9 = (xmm8 * xmm9) + xmm7
vmovshdup	xmm7, xmm7  ; xmm7 = xmm7[1,1,3,3]
vaddss	xmm7, xmm9, xmm7
vroundss	xmm9, xmm7, xmm7, 12
vsubss	xmm7, xmm7, xmm9
vmulps	xmm8, xmm8, xmm4
vfmadd231ps	xmm8, xmm5, xmm0  ; xmm8 = (xmm5 * xmm0) + xmm8
vfmadd231ps	xmm8, xmm6, xmm1  ; xmm8 = (xmm6 * xmm1) + xmm8
vroundps	xmm0, xmm8, 12
vsubps	xmm0, xmm8, xmm0
vmulps	xmm0, xmm0, xmm0
vfmadd213ss	xmm7, xmm7, xmm0  ; xmm7 = (xmm7 * xmm7) + xmm0
vmovshdup	xmm0, xmm0  ; xmm0 = xmm0[1,1,3,3]
vaddss	xmm0, xmm7, xmm0
vucomiss	xmm0, xmm10
jae	BB1_29
;  ; in Loop: Header=BB1_22 Depth=1:
vucomiss	xmm0, dword [rdi + 4*rbx]
jb	BB1_24
BB1_29:  ; in Loop: Header=BB1_22 Depth=1:
cmp	dword [rsi + 4*rbx], r11d
jne	BB1_31
;  ; in Loop: Header=BB1_22 Depth=1:
mov	dword [rsi + 4*rbx], -1
jmp	BB1_31

%else
global sa_inner_f32_sov_avx2
call_sa_inner_f32_sov_avx2:  ; @call_sa_inner_f32_sov_avx2:
jmp	sa_inner_f32_sov_avx2
func_end0:
SECTION .rodata
align 4
CPI1_0:
dd	27  ; 0x1b
dd	30  ; 0x1e
dd	29  ; 0x1d
dd	28  ; 0x1c
SECTION .rodata
align 4
CPI1_1:
times 32 db 255
SECTION .text
align 4
sa_inner_f32_sov_avx2:  ; @sa_inner_f32_sov_avx2:
push	rbp
push	r15
push	r14
push	r13
push	r12
push	rbx
sub	rsp, 168
mov	r10, qword [rsp + 232]
mov	r11d, dword [rsp + 224]
vmulsd	xmm0, xmm0, xmm0
vcvtsd2ss	xmm0, xmm0, xmm0
vmovaps	oword [rsp - 112], xmm0  ; 16-byte Spill
vbroadcastss	ymm1, xmm0
cmp	r10, 8
jge	BB1_25
xor	r14d, r14d
xor	eax, eax
BB1_2:
mov	rbx, r10
sub	rbx, r14
jle	BB1_32
vmovsd	xmm0, qword [rdi]  ; xmm0 = mem[0],zero
vcvtsd2ss	xmm2, xmm0, xmm0
vcvtpd2ps	xmm3, oword [rdi + 8]
vmovsd	xmm0, qword [rdi + 24]  ; xmm0 = mem[0],zero
vmovhpd	xmm0, xmm0, qword [rdi + 48]  ; xmm0 = xmm0[0],mem[0]
vcvtpd2ps	xmm4, xmm0
vmovsd	xmm0, qword [rdi + 32]  ; xmm0 = mem[0],zero
vmovhpd	xmm0, xmm0, qword [rdi + 56]  ; xmm0 = xmm0[0],mem[0]
vcvtpd2ps	xmm5, xmm0
vmovsd	xmm0, qword [rdi + 40]  ; xmm0 = mem[0],zero
vmovhpd	xmm0, xmm0, qword [rdi + 64]  ; xmm0 = xmm0[0],mem[0]
vcvtpd2ps	xmm6, xmm0
cmp	rbx, 16
jae	BB1_5
mov	rbx, r14
vmovdqa	xmm10, oword [rsp - 112]  ; 16-byte Reload
jmp	BB1_22
BB1_25:
vmovsd	xmm0, qword [rdi]  ; xmm0 = mem[0],zero
vmovsd	xmm2, qword [rdi + 8]  ; xmm2 = mem[0],zero
vcvtsd2ss	xmm0, xmm0, xmm0
vcvtsd2ss	xmm3, xmm2, xmm2
vbroadcastss	ymm2, xmm0
vmovsd	xmm0, qword [rdi + 16]  ; xmm0 = mem[0],zero
vcvtsd2ss	xmm0, xmm0, xmm0
vbroadcastss	ymm3, xmm3
vmovsd	xmm4, qword [rdi + 24]  ; xmm4 = mem[0],zero
vcvtsd2ss	xmm5, xmm4, xmm4
vbroadcastss	ymm4, xmm0
vmovsd	xmm0, qword [rdi + 32]  ; xmm0 = mem[0],zero
vcvtsd2ss	xmm0, xmm0, xmm0
vbroadcastss	ymm5, xmm5
vmovsd	xmm6, qword [rdi + 40]  ; xmm6 = mem[0],zero
vcvtsd2ss	xmm7, xmm6, xmm6
vbroadcastss	ymm6, xmm0
vmovsd	xmm0, qword [rdi + 48]  ; xmm0 = mem[0],zero
vcvtsd2ss	xmm0, xmm0, xmm0
vbroadcastss	ymm7, xmm7
vmovsd	xmm8, qword [rdi + 56]  ; xmm8 = mem[0],zero
vcvtsd2ss	xmm9, xmm8, xmm8
vbroadcastss	ymm8, xmm0
vmovsd	xmm0, qword [rdi + 64]  ; xmm0 = mem[0],zero
vcvtsd2ss	xmm0, xmm0, xmm0
vbroadcastss	ymm9, xmm9
vbroadcastss	ymm10, xmm0
vmovd	xmm0, r11d
vpbroadcastd	ymm11, xmm0
xor	ebx, ebx
xor	eax, eax
jmp	BB1_26
align 4
BB1_28:  ; in Loop: Header=BB1_26 Depth=1:
vmovdqu	ymm0, yword [r9 + 4*rbx]
vpcmpeqd	ymm14, ymm11, ymm0
movsx	r14d, bpl
sar	r14d, 7
mov	r15d, ebp
shl	r15d, 25
sar	r15d, 31
mov	r12d, ebp
shl	r12d, 26
sar	r12d, 31
vmovd	xmm12, ebp
vpbroadcastd	xmm12, xmm12
vpsllvd	xmm12, xmm12, oword [rel CPI1_0]
and	ebp, 1
neg	ebp
vmovd	xmm13, ebp
vpsrad	xmm12, xmm12, 31
vpermq	ymm12, ymm12, 196  ; ymm12 = ymm12[0,1,0,3]
vpblendd	ymm12, ymm12, ymm13, 1  ; ymm12 = ymm13[0],ymm12[1,2,3,4,5,6,7]
vmovd	xmm13, r12d
vpbroadcastd	ymm13, xmm13
vpblendd	ymm12, ymm12, ymm13, 32  ; ymm12 = ymm12[0,1,2,3,4],ymm13[5],ymm12[6,7]
vmovd	xmm13, r15d
vpbroadcastd	ymm13, xmm13
vpblendd	ymm12, ymm12, ymm13, 64  ; ymm12 = ymm12[0,1,2,3,4,5],ymm13[6],ymm12[7]
vmovd	xmm13, r14d
vpbroadcastd	ymm13, xmm13
vpblendd	ymm12, ymm12, ymm13, 128  ; ymm12 = ymm12[0,1,2,3,4,5,6],ymm13[7]
vpblendvb	ymm0, ymm0, ymm11, ymm12
vpandn	ymm12, ymm12, ymm14
vpblendvb	ymm0, ymm0, yword [rel CPI1_1], ymm12
vmovdqu	yword [r9 + 4*rbx], ymm0
lea	r14, [rbx + 8]
add	rbx, 16
cmp	rbx, r10
mov	rbx, r14
jg	BB1_2
BB1_26:  ; =>This Inner Loop Header: Depth=1:
vmovups	ymm0, yword [rsi + 4*rbx]
vmovups	ymm14, yword [rdx + 4*rbx]
vmovups	ymm15, yword [rcx + 4*rbx]
vmulps	ymm12, ymm15, ymm4
vfmadd231ps	ymm12, ymm3, ymm14  ; ymm12 = (ymm3 * ymm14) + ymm12
vfmadd231ps	ymm12, ymm2, ymm0  ; ymm12 = (ymm2 * ymm0) + ymm12
vmulps	ymm13, ymm15, ymm7
vfmadd231ps	ymm13, ymm6, ymm14  ; ymm13 = (ymm6 * ymm14) + ymm13
vfmadd231ps	ymm13, ymm5, ymm0  ; ymm13 = (ymm5 * ymm0) + ymm13
vmulps	ymm15, ymm15, ymm10
vfmadd231ps	ymm15, ymm9, ymm14  ; ymm15 = (ymm9 * ymm14) + ymm15
vfmadd231ps	ymm15, ymm8, ymm0  ; ymm15 = (ymm8 * ymm0) + ymm15
vroundps	ymm0, ymm12, 8
vsubps	ymm12, ymm12, ymm0
vroundps	ymm0, ymm13, 8
vsubps	ymm13, ymm13, ymm0
vroundps	ymm0, ymm15, 8
vsubps	ymm0, ymm15, ymm0
vmulps	ymm0, ymm0, ymm0
vfmadd231ps	ymm0, ymm13, ymm13  ; ymm0 = (ymm13 * ymm13) + ymm0
vfmadd231ps	ymm0, ymm12, ymm12  ; ymm0 = (ymm12 * ymm12) + ymm0
vmovups	ymm14, yword [r8 + 4*rbx]
vcmpltps	ymm12, ymm0, ymm14
vcmpltps	ymm13, ymm0, ymm1
vandps	ymm15, ymm13, ymm12
vmovmskps	ebp, ymm15
test	ebp, ebp
je	BB1_28
;  ; in Loop: Header=BB1_26 Depth=1:
vextractf128	xmm12, ymm15, 1
vpackssdw	xmm12, xmm15, xmm12
popcnt	r14d, ebp
add	eax, r14d
vpmovsxwd	ymm12, xmm12
vblendvps	ymm0, ymm14, ymm0, ymm12
vmovups	yword [r8 + 4*rbx], ymm0
jmp	BB1_28
BB1_5:
lea	r13, [r9 + 4*r14]
lea	r12, [r9 + 4*r10]
lea	r15, [r8 + 4*r14]
lea	rbp, [r8 + 4*r10]
lea	rdi, [rsi + 4*r14]
mov	qword [rsp - 96], rdi  ; 8-byte Spill
lea	rdi, [rsi + 4*r10]
lea	r11, [rdx + 4*r14]
mov	qword [rsp - 64], r11  ; 8-byte Spill
lea	r11, [rdx + 4*r10]
mov	qword [rsp - 32], r11  ; 8-byte Spill
lea	r11, [rcx + 4*r10]
mov	qword [rsp + 64], r11  ; 8-byte Spill
cmp	r13, rbp
setb	byte [rsp + 128]  ; 1-byte Folded Spill
cmp	r15, r12
setb	byte [rsp + 96]  ; 1-byte Folded Spill
cmp	r13, rdi
setb	byte [rsp + 32]  ; 1-byte Folded Spill
cmp	qword [rsp - 96], r12  ; 8-byte Folded Reload
setb	byte [rsp]  ; 1-byte Folded Spill
cmp	r13, qword [rsp - 32]  ; 8-byte Folded Reload
setb	byte [rsp - 113]  ; 1-byte Folded Spill
cmp	qword [rsp - 64], r12  ; 8-byte Folded Reload
setb	byte [rsp - 114]  ; 1-byte Folded Spill
mov	r11, qword [rsp + 64]  ; 8-byte Reload
cmp	r13, r11
lea	r13, [rcx + 4*r14]
setb	byte [rsp - 115]  ; 1-byte Folded Spill
cmp	r13, r12
setb	byte [rsp - 116]  ; 1-byte Folded Spill
cmp	r15, rdi
setb	byte [rsp - 117]  ; 1-byte Folded Spill
cmp	qword [rsp - 96], rbp  ; 8-byte Folded Reload
setb	byte [rsp - 96]  ; 1-byte Folded Spill
cmp	r15, qword [rsp - 32]  ; 8-byte Folded Reload
setb	r12b
cmp	qword [rsp - 64], rbp  ; 8-byte Folded Reload
setb	byte [rsp - 64]  ; 1-byte Folded Spill
cmp	r15, r11
setb	r15b
cmp	r13, rbp
setb	dil
movzx	r11d, byte [rsp + 96]  ; 1-byte Folded Reload
test	byte [rsp + 128], r11b  ; 1-byte Folded Reload
vmovdqa	xmm10, oword [rsp - 112]  ; 16-byte Reload
jne	BB1_6
movzx	r11d, byte [rsp]  ; 1-byte Folded Reload
and	byte [rsp + 32], r11b  ; 1-byte Folded Spill
mov	r11d, dword [rsp + 224]
jne	BB1_8
movzx	r13d, byte [rsp - 114]  ; 1-byte Folded Reload
and	byte [rsp - 113], r13b  ; 1-byte Folded Spill
jne	BB1_10
movzx	r13d, byte [rsp - 116]  ; 1-byte Folded Reload
and	byte [rsp - 115], r13b  ; 1-byte Folded Spill
jne	BB1_12
movzx	ebp, byte [rsp - 117]  ; 1-byte Folded Reload
and	bpl, byte [rsp - 96]  ; 1-byte Folded Reload
jne	BB1_14
and	r12b, byte [rsp - 64]  ; 1-byte Folded Reload
jne	BB1_16
and	r15b, dil
jne	BB1_18
mov	edi, r10d
and	edi, 7
sub	rbx, rdi
add	rbx, r14
vmovd	xmm7, eax
vbroadcastss	ymm0, xmm2
vmovups	yword [rsp - 64], ymm0  ; 32-byte Spill
vbroadcastss	ymm0, xmm3
vmovupd	yword [rsp - 96], ymm0  ; 32-byte Spill
vmovshdup	xmm0, xmm3  ; xmm0 = xmm3[1,1,3,3]
vbroadcastsd	ymm0, xmm0
vmovups	yword [rsp - 32], ymm0  ; 32-byte Spill
vbroadcastss	ymm0, xmm4
vmovupd	yword [rsp + 128], ymm0  ; 32-byte Spill
vbroadcastss	ymm0, xmm5
vmovupd	yword [rsp + 96], ymm0  ; 32-byte Spill
vbroadcastss	ymm0, xmm6
vmovupd	yword [rsp + 64], ymm0  ; 32-byte Spill
vmovshdup	xmm0, xmm4  ; xmm0 = xmm4[1,1,3,3]
vbroadcastsd	ymm0, xmm0
vmovups	yword [rsp + 32], ymm0  ; 32-byte Spill
vmovshdup	xmm0, xmm5  ; xmm0 = xmm5[1,1,3,3]
vbroadcastsd	ymm0, xmm0
vmovups	yword [rsp], ymm0  ; 32-byte Spill
vmovshdup	xmm0, xmm6  ; xmm0 = xmm6[1,1,3,3]
vbroadcastsd	ymm0, xmm0
vmovd	xmm8, r11d
vpbroadcastd	ymm8, xmm8
vpcmpeqd	ymm9, ymm9, ymm9
align 4
BB1_20:  ; =>This Inner Loop Header: Depth=1:
vmovups	ymm10, yword [rsi + 4*r14]
vmulps	ymm11, ymm10, yword [rsp - 64]  ; 32-byte Folded Reload
vmovups	ymm12, yword [rdx + 4*r14]
vfmadd231ps	ymm11, ymm12, yword [rsp - 96]  ; 32-byte Folded Reload
  ; ymm11 = (ymm12 * mem) + ymm11
vmovups	ymm13, yword [rcx + 4*r14]
vfmadd231ps	ymm11, ymm13, yword [rsp - 32]  ; 32-byte Folded Reload
  ; ymm11 = (ymm13 * mem) + ymm11
vroundps	ymm14, ymm11, 12
vsubps	ymm11, ymm11, ymm14
vmulps	ymm14, ymm10, yword [rsp + 128]  ; 32-byte Folded Reload
vfmadd231ps	ymm14, ymm12, yword [rsp + 96]  ; 32-byte Folded Reload
  ; ymm14 = (ymm12 * mem) + ymm14
vfmadd231ps	ymm14, ymm13, yword [rsp + 64]  ; 32-byte Folded Reload
  ; ymm14 = (ymm13 * mem) + ymm14
vroundps	ymm15, ymm14, 12
vsubps	ymm14, ymm14, ymm15
vmulps	ymm10, ymm10, yword [rsp + 32]  ; 32-byte Folded Reload
vfmadd231ps	ymm10, ymm12, yword [rsp]  ; 32-byte Folded Reload
  ; ymm10 = (ymm12 * mem) + ymm10
vfmadd231ps	ymm10, ymm0, ymm13  ; ymm10 = (ymm0 * ymm13) + ymm10
vroundps	ymm12, ymm10, 12
vsubps	ymm10, ymm10, ymm12
vmulps	ymm11, ymm11, ymm11
vfmadd231ps	ymm11, ymm14, ymm14  ; ymm11 = (ymm14 * ymm14) + ymm11
vfmadd231ps	ymm11, ymm10, ymm10  ; ymm11 = (ymm10 * ymm10) + ymm11
vcmpltps	ymm10, ymm11, ymm1
vmaskmovps	ymm12, ymm10, yword [r8 + 4*r14]
vcmpleps	ymm13, ymm1, ymm11
vcmpleps	ymm14, ymm12, ymm11
vandps	ymm14, ymm10, ymm14
vorps	ymm13, ymm14, ymm13
vpmaskmovd	ymm14, ymm13, yword [r9 + 4*r14]
vcmpltps	ymm12, ymm11, ymm12
vpcmpeqd	ymm14, ymm14, ymm8
vandps	ymm10, ymm10, ymm12
vpand	ymm12, ymm13, ymm14
vpmaskmovd	yword [r9 + 4*r14], ymm12, ymm9
vpmaskmovd	yword [r9 + 4*r14], ymm10, ymm8
vmaskmovps	yword [r8 + 4*r14], ymm10, ymm11
vpxor	ymm10, ymm13, ymm9
vpor	ymm10, ymm10, ymm14
vpandn	ymm10, ymm12, ymm10
vpsubd	ymm7, ymm7, ymm10
add	r14, 8
cmp	rbx, r14
jne	BB1_20
vextracti128	xmm0, ymm7, 1
vpaddd	xmm0, xmm7, xmm0
vpshufd	xmm1, xmm0, 238  ; xmm1 = xmm0[2,3,2,3]
vpaddd	xmm0, xmm0, xmm1
vpshufd	xmm1, xmm0, 85  ; xmm1 = xmm0[1,1,1,1]
vpaddd	xmm0, xmm0, xmm1
vmovd	eax, xmm0
test	rdi, rdi
vmovdqa	xmm10, oword [rsp - 112]  ; 16-byte Reload
jne	BB1_22
BB1_32:
add	rsp, 168
pop	rbx
pop	r12
pop	r13
pop	r14
pop	r15
pop	rbp
vzeroupper
ret
BB1_18:
mov	rbx, r14
jmp	BB1_22
BB1_16:
mov	rbx, r14
jmp	BB1_22
BB1_14:
mov	rbx, r14
jmp	BB1_22
BB1_12:
mov	rbx, r14
jmp	BB1_22
BB1_10:
mov	rbx, r14
jmp	BB1_22
BB1_6:
mov	rbx, r14
mov	r11d, dword [rsp + 224]
jmp	BB1_22
BB1_8:
mov	rbx, r14
jmp	BB1_22
align 4
BB1_24:  ; in Loop: Header=BB1_22 Depth=1:
mov	dword [r9 + 4*rbx], r11d
vmovss	dword [r8 + 4*rbx], xmm0
inc	eax
BB1_31:  ; in Loop: Header=BB1_22 Depth=1:
inc	rbx
cmp	r10, rbx
je	BB1_32
BB1_22:  ; =>This Inner Loop Header: Depth=1:
vbroadcastss	xmm0, dword [rdx + 4*rbx]
vbroadcastss	xmm1, dword [rcx + 4*rbx]
vinsertps	xmm7, xmm0, xmm1, 28  ; xmm7 = xmm0[0],xmm1[0],zero,zero
vmulps	xmm7, xmm7, xmm3
vbroadcastss	xmm8, dword [rsi + 4*rbx]
vmovaps	xmm9, xmm2
vfmadd213ss	xmm9, xmm8, xmm7  ; xmm9 = (xmm8 * xmm9) + xmm7
vmovshdup	xmm7, xmm7  ; xmm7 = xmm7[1,1,3,3]
vaddss	xmm7, xmm9, xmm7
vroundss	xmm9, xmm7, xmm7, 12
vsubss	xmm7, xmm7, xmm9
vmulps	xmm8, xmm8, xmm4
vfmadd231ps	xmm8, xmm5, xmm0  ; xmm8 = (xmm5 * xmm0) + xmm8
vfmadd231ps	xmm8, xmm6, xmm1  ; xmm8 = (xmm6 * xmm1) + xmm8
vroundps	xmm0, xmm8, 12
vsubps	xmm0, xmm8, xmm0
vmulps	xmm0, xmm0, xmm0
vfmadd213ss	xmm7, xmm7, xmm0  ; xmm7 = (xmm7 * xmm7) + xmm0
vmovshdup	xmm0, xmm0  ; xmm0 = xmm0[1,1,3,3]
vaddss	xmm0, xmm7, xmm0
vucomiss	xmm0, xmm10
jae	BB1_29
;  ; in Loop: Header=BB1_22 Depth=1:
vucomiss	xmm0, dword [r8 + 4*rbx]
jb	BB1_24
BB1_29:  ; in Loop: Header=BB1_22 Depth=1:
cmp	dword [r9 + 4*rbx], r11d
jne	BB1_31
;  ; in Loop: Header=BB1_22 Depth=1:
mov	dword [r9 + 4*rbx], -1
jmp	BB1_31
func_end1:

%endif
