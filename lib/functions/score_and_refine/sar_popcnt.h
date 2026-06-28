/* sar_popcnt.h -- portable 32-bit popcount */
#ifndef SAR_POPCNT_H
#define SAR_POPCNT_H

static int popcnt32(unsigned int x) {
#ifdef _MSC_VER
    return __popcnt(x);
#else
    return __builtin_popcount(x);
#endif
}

#endif
