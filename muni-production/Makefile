# Build the certified kernel. IEEE flags are NOT optional.
CC      ?= gcc
CFLAGS  ?= -O3 -march=native -funroll-loops -fno-fast-math -ffp-contract=off
LDFLAGS ?= -fPIC -shared -lm

all: libmuni.so

libmuni.so: muni/_lib.c muni/kernel.c muni/kernel.h muni/kernel_agl.h
	$(CC) $(CFLAGS) $(LDFLAGS) -o $@ muni/_lib.c muni/kernel.c

test: libmuni.so
	python3 -m unittest discover -s tests -v

proof:
	cd proof && for f in *.lean; do echo "== $$f"; lean $$f || exit 1; done

evidence: libmuni.so
	python3 tools/make_evidence.py

clean:
	rm -f libmuni.so
	find . -name '__pycache__' -type d -exec rm -rf {} + 2>/dev/null || true

.PHONY: all test proof evidence clean
