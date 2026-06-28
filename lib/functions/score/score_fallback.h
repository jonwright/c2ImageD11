/* score_fallback.h -- fallback for non-x86 platforms: call original C score() */
#ifndef SCORE_FALLBACK_H
#define SCORE_FALLBACK_H

#if !defined(__x86_64__) && !defined(_M_X64)

/* Original C score function from score.c */
extern int score(const double ubi[3][3], const double gv[], double tol, intptr_t ng);

#endif
#endif
