#include <stdint.h>
#include "ImageD11_cmath.h"

void assign(double ubi[9], double gv[][3], double tol, double drlv2[],
            int labels[], int ig, intptr_t n);

void compute_gv(double xlylzl[][3], double omega[], double omegasign,
                double wvln, double wedge, double chi, double t[3],
                double gv[][3], intptr_t n);

void compute_xlylzl(double s[], double f[], double p[4], double r[9],
                    double dist[3], double xlylzl[][3], intptr_t n);

void compute_xlylzl_xpos_variable(double s[], double f[], double p[4], double r[9],
    double dist[3], double xpos[],
    double xlylzl[][3], intptr_t n);