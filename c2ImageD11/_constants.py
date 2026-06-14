"""Blob property constants from ImageD11/src/blobs.h enum values.

These are compile-time C enum values that are hardcoded here
until c2py23 supports a 'constants:' section in .c2py files.
"""

# NPROPERTY enum - 3D blob properties (s_1..NPROPERTY = 35)
s_1 = 0
s_I = 1
s_I2 = 2
s_fI = 3
s_ffI = 4
s_sI = 5
s_ssI = 6
s_sfI = 7
s_oI = 8
s_ooI = 9
s_soI = 10
s_foI = 11
mx_I = 12
mx_I_f = 13
mx_I_s = 14
mx_I_o = 15
bb_mx_f = 16
bb_mx_s = 17
bb_mx_o = 18
bb_mn_f = 19
bb_mn_s = 20
bb_mn_o = 21
avg_i = 22
f_raw = 23
s_raw = 24
o_raw = 25
m_ss = 26
m_ff = 27
m_oo = 28
m_sf = 29
m_so = 30
m_fo = 31
f_cen = 32
s_cen = 33
dety = 34
detz = 35
NPROPERTY = 35

# NPROPERTY2D enum - 2D blob properties (s2D_1..NPROPERTY2D = 11)
s2D_1 = 0
s2D_I = 1
s2D_fI = 2
s2D_sI = 3
s2D_ffI = 4
s2D_sfI = 5
s2D_ssI = 6
s2D_bb_mx_f = 7
s2D_bb_mx_s = 8
s2D_bb_mn_f = 9
s2D_bb_mn_s = 10
NPROPERTY2D = 11
