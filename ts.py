"""Tee an agent's JSONL stdout to a file, plus a sidecar of arrival times (epoch<TAB>kind) used to pause the clock on API errors."""
import sys, time
out, ts = open(sys.argv[1], "a"), open(sys.argv[2], "a")
for line in sys.stdin:
    out.write(line); out.flush()
    kind = "fail" if '"turn.failed"' in line else "error" if '"type":"error"' in line else "event"
    ts.write(f"{time.time():.2f}\t{kind}\n"); ts.flush()
