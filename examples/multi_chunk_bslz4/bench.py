#!/usr/bin/env python
"""Unified benchmark: dataset × SIMD × quantization × batch size.

Also includes a Python baseline using scipy.sparse CSC dot product.
"""

from __future__ import print_function
import os, sys, time
import numpy as np
import c2ImageD11._cImageD11 as _m
from c2ImageD11.csc_convert import generate_csc, to_1d_padded, quantize_weights
import h5py
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

_HOME = os.environ.get("HOME", "/home/worker")
EXDIR = os.path.dirname(os.path.abspath(__file__))
PONIFILE = os.path.join(EXDIR, "example.poni")
NREPEAT = 3
BATCH_SIZES = [1, 2, 4, 8, 16, 32]
VARIANTS = ['kcb_avx512', 'kcb_avx2', 'kcb_sse42']

def get_offsets(h5path, ds_path, nframes):
    offs = np.full(nframes, -1, dtype=np.int64); lens = np.full(nframes, -1, dtype=np.int32)
    with h5py.File(h5path, "r") as hf:
        ds = hf[ds_path]
        def cb(si):
            lo,_,fl,sz=si
            if lo[0] < nframes:
                offs[lo[0]]=fl
                lens[lo[0]]=sz
        ds.id.chunk_iter(cb)
    if (offs < 0).any() or (lens < 0).any(): raise RuntimeError("Missing chunk offsets")
    return offs, lens

def load_csc(nout):
    d,i,ip,_,_ = generate_csc(PONIFILE, nout)
    ma = np.load(os.path.join(_HOME, "test_data", "eiger_mask.npy"))
    ma = (1-ma).astype(np.uint8); fm = ma.ravel()
    cf,fb,ep = to_1d_padded(d,i,ip,ma)
    cu8  = quantize_weights(cf, 255,   np.uint8,  mask=fm, entries_per_pixel=ep)
    cu16 = quantize_weights(cf, 32768, np.uint16, mask=fm, entries_per_pixel=ep)
    cu32 = quantize_weights(cf, 1<<31, np.uint32, mask=fm, entries_per_pixel=ep)
    return cf,fb,ep,cu8,cu16,cu32,d,i,ip,ma,fm

def run_one(h5path, ds_path, nframes, nout, label):
    print("\n=== %s (%d frames, %d bins) ===" % (label, nframes, nout)); sys.stdout.flush()
    offs,lens = get_offsets(h5path,ds_path,nframes)
    mm = np.memmap(h5path,dtype="B",mode="r")
    ma = np.load(os.path.join(_HOME,"test_data","eiger_mask.npy"))
    flat=(1-ma.ravel()).astype(np.uint8); NIJ=len(flat)
    cf,fb,ep,cu8,cu16,cu32,ds3,is3,ip3,ma2,fm = load_csc(nout)
    maxb=max(BATCH_SIZES); ox=np.zeros(maxb*NIJ,np.uint16); oa=np.zeros(maxb*NIJ,np.uint32)

    print("  warmup...",end=" "); sys.stdout.flush()
    for b in range(0,min(32,nframes),4):
        bn=min(4,nframes-b); npc=np.zeros(bn,np.int32)
        _m.bslz4_csc_u16(mm,flat,ox,oa,50,np.zeros(bn*nout),ds3,is3,ip3,offs[b:b+bn],lens[b:b+bn],npc)
    print("done"); sys.stdout.flush()

    # ---- Python baseline (single frame via scipy.sparse CSC) ----
    print("  Python baseline (scipy CSC dot)...", end=" "); sys.stdout.flush()
    try:
        from scipy.sparse import csc_matrix
        import gc
        # Build the whole scipy CSC matrix once
        scipy_csc = csc_matrix((ds3, is3, ip3), shape=(nout, NIJ))
        # Time one frame
        raw0 = None
        with h5py.File(os.path.join(EXDIR if nframes==32 else _HOME+"/test_data","testdata_poisson.h5" if nframes==32 else "eiger_0000.h5"),"r") as hf:
            raw0 = hf["data" if nframes==32 else "entry_0000/ESRF-ID11/eiger/data"][0].ravel().astype(np.float64)
        gc.collect()
        t0=time.perf_counter()
        py_powder = scipy_csc.dot(raw0)
        py_time = time.perf_counter()-t0
        py_fps = 1.0/py_time
        print("done: %.2f FPS (%.0f ms/frame)" % (py_fps, py_time*1000)); sys.stdout.flush()
    except Exception as e:
        print("SKIP: %s" % e); sys.stdout.flush()
        py_fps = 0

    # ---- Benchmark all C variants ----
    print("%-7s %-12s %-4s %2s %-12s %8s %8s" % ("ds","fmt","dtype","bs","variant","best","2nd")); print("-"*70)
    for bs in BATCH_SIZES:
        # std_f32
        for v in VARIANTS:
            _m._rebind_bslz4_csc_u16(v); fps=[]
            for _ in range(NREPEAT):
                t0=time.perf_counter()
                for b in range(0,nframes,bs):
                    bn=min(bs,nframes-b); npc=np.zeros(bn,np.int32)
                    _m.bslz4_csc_u16(mm,flat,ox,oa,50,np.zeros(bn*nout),ds3,is3,ip3,offs[b:b+bn],lens[b:b+bn],npc)
                fps.append(nframes/(time.perf_counter()-t0))
            fps.sort(reverse=True)
            s=fps[1] if len(fps)>1 else 0
            print("%-7s %-12s %-4s %2d %-12s %8.1f %8.1f"%(label,"std_f32","f32",bs,v[:12],fps[0],s)); sys.stdout.flush()
        # csc1d f32 + quantized
        for qlabel,fn,reb,qarr,sf in [
            ("f32",_m.bslz4_csc1d_u16,_m._rebind_bslz4_csc1d_u16,cf,None),
            ("u8",_m.bslz4_csc1d_u16_cu8,_m._rebind_bslz4_csc1d_u16_cu8,cu8,255),
            ("u16",_m.bslz4_csc1d_u16_cu16,_m._rebind_bslz4_csc1d_u16_cu16,cu16,32768),
            ("u32",_m.bslz4_csc1d_u16_cu32,_m._rebind_bslz4_csc1d_u16_cu32,cu32,1<<31),
        ]:
            for v in VARIANTS:
                reb(v); fps=[]
                for _ in range(NREPEAT):
                    t0=time.perf_counter()
                    for b in range(0,nframes,bs):
                        bn=min(bs,nframes-b); npc=np.zeros(bn,np.int32)
                        pw=np.zeros(bn*nout,dtype=np.float64 if sf is None else np.uint64)
                        fn(mm,flat,ox,oa,50,pw,qarr,fb,ep,0,offs[b:b+bn],lens[b:b+bn],npc)
                    fps.append(nframes/(time.perf_counter()-t0))
                fps.sort(reverse=True)
                s=fps[1] if len(fps)>1 else 0
                print("%-7s %-12s %-4s %2d %-12s %8.1f %8.1f"%(label,"csc1d_"+qlabel,qlabel,bs,v[:12],fps[0],s)); sys.stdout.flush()
    return py_fps

# ===== Run =====
py_fps_poisson = run_one(os.path.join(EXDIR,"testdata_poisson.h5"),"data",32,2500,"poisson")
py_fps_eiger   = run_one(os.path.join(_HOME,"test_data","eiger_0000.h5"),"entry_0000/ESRF-ID11/eiger/data",100,1500,"eiger")

print("\n===== Python baseline (scipy CSC, 1 frame) =====")
print("  Poisson: %.1f FPS" % py_fps_poisson if py_fps_poisson else "  Poisson: N/A")
print("  Eiger:   %.1f FPS" % py_fps_eiger if py_fps_eiger else "  Eiger:   N/A")
print("Done.")
