#ifndef MUNI_RUNTIME_H
#define MUNI_RUNTIME_H
#ifdef __cplusplus
extern "C" {
#endif
void muni_baseline(int n, const float *a, const float *b, float *c);
void muni_neon(int n, const float *a, const float *b, float *c);
const char *muni_backend(void);
const char *muni_version(void);
#ifdef __cplusplus
}
#endif
#endif
