#!/usr/bin/env python3
"""gas_to_nasm.py — convert Clang GAS-Intel syntax assembly to NASM format.

Usage: clang-18 -O3 -ffast-math ... -masm=intel -S -o - foo.c | python3 gas_to_nasm.py > foo.asm
"""

from __future__ import absolute_import, division, print_function, unicode_literals
import sys, re

def convert(text):
    lines_out = []
    
    for line in text.split('\n'):
        stripped = line.strip()
        
        if not stripped:
            continue
        
        # Skip .cfi_* directives
        if stripped.startswith('.cfi_'):
            continue
        
        # Skip .seh_* directives (Windows exception handling)
        if stripped.startswith('.seh_'):
            continue
        
        # Skip Windows-specific directives from MinGW target
        if stripped.startswith('.def') or stripped.startswith('.scl') or stripped.startswith('.endef') or stripped.startswith('.set '):
            continue
        if stripped.startswith('.rva') or stripped.startswith('.long') and 'feat' in stripped.lower():
            continue
        
        # Skip file/ident/addrsig directives
        if stripped.startswith('.file') or stripped.startswith('.ident') or stripped.startswith('.addrsig'):
            continue
        if stripped.startswith('.section') and 'note.GNU-stack' in stripped:
            continue
            
        # Skip object size info
        if stripped.startswith('.size'):
            continue
        
        # Convert # comments to ; comments (NASM)
        if '#' in stripped:
            # Replace only comment #, not data # like # -- End
            stripped = re.sub(r'\s*#\s*', '  ; ', stripped)
            # Remove # %bb.x: markers entirely (they're not useful)
            stripped = re.sub(r';\s*%bb\.\d+:', ';', stripped)
        
        # Handle .section rodata
        if stripped.startswith('.section'):
            stripped = 'SECTION .rodata' if 'rodata' in stripped else 'SECTION .text'
            lines_out.append(stripped)
            continue
            
        # Handle .text 
        if stripped == '.text':
            lines_out.append('SECTION .text')
            continue
            
        # Handle .globl
        if stripped.startswith('.globl') or stripped.startswith('.global'):
            func = stripped.split()[-1]
            lines_out.append('global ' + func)
            continue
            
        # Handle .type
        if stripped.startswith('.type'):
            continue
            
        # Handle .align / .p2align
        if stripped.startswith('.align') or stripped.startswith('.p2align'):
            nums = [int(x) for x in re.findall(r'(\d+)', stripped)]
            if nums:
                lines_out.append('align ' + str(min(2**nums[0], 64)))
            continue
        
        # Handle .intel_syntax noprefix
        if '.intel_syntax' in stripped:
            lines_out.append('; Intel syntax (NASM default)')
            continue
            
        # Handle .L* labels — keep as NASM local labels (single colon)
        if stripped.startswith('.L'):
            label = re.sub(r'^\.L', '', stripped)  # remove .L prefix
            label = re.sub(r'::$', ':', label)
            if not label.endswith(':'):
                label += ':'
            lines_out.append(label)
            continue
            
        # Handle function label (ends with colon)
        if ':' in stripped and not stripped.startswith('.') and not stripped.startswith('"'):
            parts = stripped.split('#', 1)
            label = parts[0].strip()
            if not re.search(r'[\[\]+\-]', label):  # not an instruction
                # Fix :: -> :
                label = re.sub(r'::$', ':', label)
                if not label.endswith(':'):
                    label += ':'
                lines_out.append(label)
                continue
        
        # Clean instruction lines
        clean = stripped
        
        # Remove .L prefix from embedded labels
        clean = re.sub(r'\.L(?=[A-Za-z])', '', clean)
        
        # NASM uses 'byte', 'word', 'dword', 'qword' without 'ptr'
        clean = re.sub(r'\bbyte ptr\b', 'byte', clean)
        clean = re.sub(r'\bdword ptr\b', 'dword', clean)
        clean = re.sub(r'\bqword ptr\b', 'qword', clean)
        clean = re.sub(r'\bxword ptr\b', 'xword', clean)
        clean = re.sub(r'\bword ptr\b', 'word', clean)
        clean = re.sub(r'\boword ptr\b', 'oword', clean)
        clean = re.sub(r'\byword ptr\b', 'yword', clean)
        clean = re.sub(r'\bzword ptr\b', 'zword', clean)
        clean = re.sub(r'\bxmmword ptr\b', 'oword', clean)
        clean = re.sub(r'\bymmword ptr\b', 'yword', clean)
        clean = re.sub(r'\bzmmword ptr\b', 'zword', clean)
        # Also handle stray "ptr" alone
        clean = re.sub(r'\s+ptr\b', '', clean)
        
        # Handle `; TAILCALL` or similar noise from comments
        clean = re.sub(r'\s*;\s*TAILCALL\s*$', '', clean)
        clean = re.sub(r'\s*;\s*-- End function\s*$', '', clean)
        
        # Remove leftover empty comments
        clean = re.sub(r'\s*;\s*$', '', clean)
        
        # NASM doesn't need OFFSET
        clean = re.sub(r'\boffset\b\s*', '', clean)
        
        # Fix RIP-relative: [rip + ...] → [rel ...]
        clean = re.sub(r'\[rip\s*\+\s*', '[rel ', clean)
        if '[rip]' in clean:
            clean = clean.replace('[rip]', '[rel 0]')
        
        # Fix GOTPCREL references
        clean = re.sub(r'\[rip\s*\+\s*(\w+)@GOTPCREL\]', r'[rel \1 wrt ..got]', clean)
        
        # Fix :: in instruction operands (from local labels)
        clean = re.sub(r'(\w+)::', r'\1:', clean)
        
        if clean and not clean.isspace():
            lines_out.append(clean)
    
    # Post-process: convert GAS data directives to NASM equivalents
    result = '\n'.join(lines_out)
    result = re.sub(r'^\s*\.long\b', 'dd', result, flags=re.M)
    result = re.sub(r'^\s*\.quad\b', 'dq', result, flags=re.M)
    result = re.sub(r'^\s*\.byte\b', 'db', result, flags=re.M)
    result = re.sub(r'^\s*\.short\b', 'dw', result, flags=re.M)
    result = re.sub(r'^\s*\.word\b', 'dw', result, flags=re.M)
    # Convert .zero N, V to times N db V
    result = re.sub(r'\.zero\s+(\d+)\s*,\s*(\d+)', r'times \1 db \2', result)
    result = re.sub(r'\.zero\s+(\d+)', r'times \1 db 0', result)
    
    return result

if __name__ == '__main__':
    text = sys.stdin.read()
    result = convert(text)
    print(result)
