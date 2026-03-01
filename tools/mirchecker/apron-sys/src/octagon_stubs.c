#include <stddef.h>

/*
 * Fallback stubs for snapshots that miss apron/octagons sources.
 * These functions satisfy linkage for non-octagon domains.
 */
void *oct_manager_alloc(void) { return NULL; }

void *ap_abstract0_oct_narrowing(void *man, void *a1, void *a2) {
    (void)man;
    (void)a1;
    return a2;
}
