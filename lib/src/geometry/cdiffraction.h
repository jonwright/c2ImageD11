#include <stdint.h>
#include "ImageD11_cmath.h"

void assign(double ubi[9], double gv[][3], double tol, double drlv2[],
            int labels[], int ig, intptr_t n);

void compute_gv(const double xlylzl[][3], const double omega[], double omegasign,
                double wvln, double wedge, double chi, const double t[3],
                double gv[][3], intptr_t n);

void compute_xlylzl(const double s[], const double f[], const double p[4], const double r[9],
                    const double dist[3], double xlylzl[][3], intptr_t n);

void compute_xlylzl_xpos_variable(const double s[], const double f[], const double p[4], const double r[9],
    const double dist[3], const double xpos[],
    double xlylzl[][3], intptr_t n);