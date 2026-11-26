"""Print the steps of an Antigravity conversation (tool calls, messages) from its SQLite store. usage: agy_steps.py <conversation_id>"""
import re, sqlite3, subprocess, sys
from pathlib import Path
db = Path.home() / ".gemini/antigravity/conversations" / f"{sys.argv[1]}.db"
con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
for idx, typ, status, payload, err in con.execute("select idx, step_type, status, step_payload, error_details from steps order by idx"):
    txt = [s for s in re.findall(rb"[\x20-\x7e\n\xc0-\xff\x80-\xbf]{6,}", payload or b"")]
    txt = [t.decode("utf8", "replace") for t in txt]
    txt = [t for t in txt if not re.match(r"^(sessionID|b\$|\$|\"\$|:\(bot|[-0-9]+H|[A-Za-z0-9_-]{20,}[!bX]?$|\s*[0-9a-f]{32}$)", t)]
    e = re.findall(rb"[\x20-\x7e]{8,}", err or b"")
    print(f"--- {idx} type={typ} status={status}  " + " | ".join(t.strip()[:240] for t in txt[:5]) + (f"  ERR: {e[0][:200].decode()}" if e else ""))
