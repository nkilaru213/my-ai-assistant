
from flask import Flask, request, jsonify, make_response
import json, os, re
from difflib import SequenceMatcher
from db_manager import DBManager
from services.search_service import SearchService

app = Flask(__name__)
ROOT = os.path.dirname(__file__)
DB_PATH = os.path.join(ROOT, "assistant.db")
mgr = DBManager(DB_PATH)
search_svc = SearchService()

with open(os.path.join(ROOT, "kb.json")) as f:
    KB = json.load(f)

UPLOAD_DIR = os.path.join(ROOT, "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

def sim(a, b):
    return SequenceMatcher(None, a, b).ratio()

def extract_text(path: str) -> str:
    if path.lower().endswith(".txt"):
        try:
            with open(path, "r", errors="ignore") as f:
                return f.read()
        except Exception:
            return ""
    return ""

def search_files_fallback(query: str):
    query = query.lower()
    data_dir = os.path.join(os.path.dirname(ROOT), "data")
    texts = []
    if os.path.isdir(data_dir):
        for name in os.listdir(data_dir):
            if name.lower().endswith(".txt"):
                p = os.path.join(data_dir, name)
                try:
                    with open(p, "r", errors="ignore") as f:
                        texts.append((name, f.read()))
                except Exception:
                    pass
    best_file = None
    best_score = 0.0
    for fname, text in texts:
        s = sim(query, text.lower())
        if s > best_score:
            best_score = s
            best_file = (fname, text[:600])
    if best_file and best_score > 0.2:
        return f"From file {best_file[0]} (similarity={best_score:.2f}):\n{best_file[1]}"
    return None

def kb_fallback(query: str):
    query = query.lower()
    best = None
    best_score = 0.0
    for entry in KB:
        for kw in entry["keywords"]:
            s = sim(query, kw.lower())
            if s > best_score:
                best_score = s
                best = entry
    if best and best_score > 0.6:
        return best["answer"]
    return None

def cors(resp):
    resp.headers["Access-Control-Allow-Origin"] = "*"
    resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
    resp.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
    return resp

@app.route("/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        return cors(jsonify({"error": "no file uploaded"})), 400

    f = request.files["file"]

    uploads_dir = os.path.join(os.path.dirname(ROOT), "uploads")
    os.makedirs(uploads_dir, exist_ok=True)

    # Save file
    save_path = os.path.join(uploads_dir, f.filename)
    f.save(save_path)

    print("[UPLOAD] Saved to:", save_path)

    return cors(jsonify({
        "message": "uploaded",
        "filename": f.filename,
        "path": save_path
    }))


@app.route("/drive-attach", methods=["POST", "OPTIONS"])
def drive_attach():
    if request.method == "OPTIONS":
        return cors(make_response("", 204))

    data = request.get_json(silent=True) or {}
    filename = (data.get("filename") or "").strip()

    PROJECT_ROOT = os.path.abspath(os.path.join(ROOT, ".."))
    data_dir = os.path.join(PROJECT_ROOT, "data")
    path = os.path.join(data_dir, filename)

    print("Drive attach checking path:", path)

    if not os.path.exists(path):
        return cors(jsonify({"error": "file not found", "path": path})), 404

    return cors(jsonify({"path": path, "filename": filename}))


@app.route("/search-file", methods=["POST", "OPTIONS"])
def search_file():
    if request.method == "OPTIONS":
        return cors(make_response("", 204))
    data = request.get_json(silent=True) or {}
    path = data.get("path")
    query = (data.get("query") or "").strip().lower()
    if not path or not os.path.exists(path):
        return cors(jsonify({"error": "file not found"})), 404
    if not query:
        return cors(jsonify({"error": "empty query"})), 400
    text = extract_text(path).lower()
    if not text:
        return cors(jsonify({"error": "file unreadable or empty"})), 400
    if query in text:
        return cors(jsonify({"result": f'Exact match for "{query}" found in file.'}))
    words = re.findall(r"\w+", text)
    best = None
    best_score = 0.0
    for w in words:
        s = sim(query, w)
        if s > best_score:
            best_score = s
            best = w
    return cors(jsonify({
        "result": "No exact match",
        "closest_match": best,
        "score": best_score
    }))

@app.route("/db/search", methods=["POST"])
def db_search_api():
    data = request.get_json(silent=True) or {}
    q = (data.get("query") or "").lower()
    row, score = mgr.fuzzy_search_kb(q)
    if row and score > 0.35:
        return jsonify({
            "source": "database",
            "answer": row["answer"],
            "question": row["question"],
            "category": row["category"],
            "confidence": score
        })
    return jsonify({"source": "database", "answer": None, "confidence": score})

@app.route("/db/add-kb", methods=["POST"])
def db_add_kb():
    data = request.get_json(silent=True) or {}
    cat = data.get("category") or "general"
    question = data.get("question") or ""
    answer = data.get("answer") or ""
    keywords = data.get("keywords") or ""
    mgr.insert_kb(cat, question, answer, keywords)
    return jsonify({"status": "ok"})

# ---------------------------
# Vector indexing endpoints
# ---------------------------

@app.route("/vector/index/sqlite", methods=["POST"])
def vector_index_sqlite():
    try:
        result = search_svc.index_vector_from_sqlite()
        return jsonify({"ok": True, "result": result})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/vector/index/uploads", methods=["POST"])
def vector_index_uploads():
    try:
        # index both backend/uploads and repo-root /uploads
        backend_uploads = os.path.join(ROOT, "uploads")
        repo_uploads = os.path.join(os.path.dirname(ROOT), "uploads")
        res1 = search_svc.index_vector_from_dir(backend_uploads)
        res2 = search_svc.index_vector_from_dir(repo_uploads)
        return jsonify({"ok": True, "backend_uploads": res1, "repo_uploads": res2})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/ask", methods=["POST", "OPTIONS"])
def ask():

    if request.method == "OPTIONS":
        return cors(make_response("", 204))

    data = request.get_json(silent=True) or {}
    q_raw = data.get("question") or ""
    q = q_raw.lower().strip()

    # --- 1) ALWAYS SEARCH UPLOADED FILES FIRST ---
    # If user query matches content inside uploaded or drive files, return those
    file_hits = search_uploaded_files(q)
    if file_hits:
        print("[SOURCE] uploaded-file")
        return cors(jsonify({
            "answer": "Found in uploaded file:\n\n" + "\n".join(file_hits),
            "source": "uploaded-file",
            "confidence": 1.0
        }))

    # --- 2) If no uploaded-file match, search /data/*.txt and logs ---
    txt_hits = search_files_fallback(q)
    if txt_hits:
        print("[SOURCE] data-file")
        return cors(jsonify({
            "answer": "Found in data files:\n\n" + txt_hits,
            "source": "data-file",
            "confidence": 0.9
        }))

    # ---- 1) Domain keywords: only answer endpoint-style questions ----
    domain_keywords = [
        "wifi", "wi-fi", "wireless",
        "vpn", "tunnel", "remote access",
        "outlook", "email", "mail",
        "slow", "lag", "performance",
        "smart card", "piv", "badge",
        "endpoint", "device", "laptop",
        "automation", "patch", "health"
    ]

    if not any(k in q for k in domain_keywords):
        # Outside our demo domain → don’t try to be clever
        return cors(jsonify({
            "answer": (
                "This demo assistant is focused on endpoint support "
                "(WiFi, VPN, performance, Outlook, smart card, automation). "
                "Your question doesn’t look related to those topics."
            ),
            "source": "domain-filter",
            "confidence": 0.0
        }))

    # ---- 2) Explicit rule: WiFi + VPN together ----
    if ("wifi" in q or "wi-fi" in q or "wireless" in q) and "vpn" in q:
        answer = (
            "When WiFi drops only while VPN is connected, the usual causes are "
            "unstable wireless signal, power-saving on the WiFi adapter, or "
            "VPN keep-alive/timeouts.\n\n"
            "Recommended steps:\n"
            "1) Move closer to the access point or test another SSID.\n"
            "2) Test on wired (no WiFi) to see if the issue is WiFi-specific.\n"
            "3) Disable WiFi power-saving on the network adapter.\n"
            "4) Reinstall or repair the VPN client/profile.\n"
            "5) Capture exact time, device name, and VPN error messages for escalation."
        )
        print("[SOURCE] rule-wifi-vpn")
        return cors(jsonify({
            "answer": answer,
            "source": "rule-wifi-vpn",
            "confidence": 1.0
        }))

    # ---- 3) KB search (switchable backend: sqlite / postgres / vector) ----
    kb_res = search_svc.search_kb(q, where=None)
    print(f"[DEBUG] KB backend={kb_res.source} confidence={kb_res.confidence:.2f}")

    if kb_res.answer and kb_res.confidence >= 0.45:
        print("[SOURCE] " + kb_res.source)
        resp = {
            "answer": kb_res.answer,
            "source": kb_res.source,
            "confidence": kb_res.confidence
        }
        # If vector mode, include contexts to help debugging
        if kb_res.contexts is not None and kb_res.source.startswith("vector"):
            resp["contexts"] = kb_res.contexts
        return cors(jsonify(resp))

    # ---- 4) Data file search (/data/*.txt) ----
    f_text = search_files_fallback(q)
    if f_text:
        print("[SOURCE] files")
        return cors(jsonify({
            "answer": f_text,
            "source": "files",
            "confidence": 0.4
        }))

    # ---- 5) JSON kb.json fallback ----
    kb_ans = kb_fallback(q)
    if kb_ans:
        print("[SOURCE] kb-json")
        return cors(jsonify({
            "answer": kb_ans,
            "source": "kb-json",
            "confidence": 0.35
        }))

    # ---- 6) Final fallback ----
    print("[SOURCE] none")
    return cors(jsonify({
        "answer": (
            "I'm not sure. Try rephrasing the question with more detail or "
            "upload a related document to search within."
        ),
        "source": "none",
        "confidence": 0.0
    }))


@app.route("/deep-research", methods=["POST", "OPTIONS"])
def deep_research():
    if request.method == "OPTIONS":
        return cors(make_response("", 204))
    data = request.get_json(silent=True) or {}
    q = (data.get("question") or "").lower()

    kb_res = search_svc.search_kb(q, where=None, top_k=5)
    kb_answer = kb_res.answer if kb_res.answer and kb_res.confidence >= 0.3 else None

    file_snippet = search_files_fallback(q)

    health = mgr.latest_health()
    logs = mgr.recent_logs(3)

    probable_causes = []
    recommended = []
    supporting = []

    if kb_answer:
        probable_causes.append("Known pattern matched in endpoint KB.")
        recommended.append("Follow the standard steps from the KB response.")
        supporting.append("KB category: %s" % (kb_row["category"],))

    if file_snippet:
        probable_causes.append("User question appears in historical docs or runbooks.")
        supporting.append("Document snippet:\n" + file_snippet)

    if health:
        cpu = health["cpu_usage"]
        ram = health["ram_usage"]
        status = health["status"]
        supporting.append(f"Latest device health: CPU {cpu}%, RAM {ram}%, status={status}.")
        if cpu > 80 or ram > 80:
            probable_causes.append("High resource usage on the device.")
            recommended.append("Close heavy apps, reboot, and re-test after load drops.")

    if logs:
        latest_log = logs[0]["log_text"]
        supporting.append("Recent endpoint log: " + latest_log)

    if not probable_causes:
        probable_causes.append("No strong signals found; issue may be intermittent or outside endpoint scope.")
        recommended.append("Gather more details (time, app, network) and escalate to L2 support.")

    summary = "Deep research completed across the local KB, logs, health data, documents, and attached Drive/local files."
    if "vpn" in q:
        summary = "Deep research indicates this is likely a VPN connectivity or configuration issue."
    elif "wifi" in q or "wireless" in q:
        summary = "Deep research suggests unstable WiFi or local network conditions."
    elif "slow" in q or "performance" in q:
        summary = "Deep research points to device performance and resource usage as likely contributors."

    answer_text = summary + "\n\n"
    answer_text += "Probable causes:\n- " + "\n- ".join(probable_causes) + "\n\n"
    answer_text += "Recommended actions:\n- " + "\n- ".join(recommended or ["Collect more diagnostics and escalate."]) + "\n\n"
    answer_text += "Supporting signals:\n- " + "\n- ".join(supporting or ["No additional signals found."])

    return cors(jsonify({
        "answer": answer_text,
        "source": "deep-research",
        "kb_used": bool(kb_answer),
        "file_used": bool(file_snippet),
        "health_used": bool(health),
        "logs_used": bool(logs)
    }))

def search_uploaded_files(query):
    results = []
    uploads_dir = os.path.join(os.path.dirname(ROOT), "uploads")

    if not os.path.exists(uploads_dir):
        return []

    for filename in os.listdir(uploads_dir):
        path = os.path.join(uploads_dir, filename)
        if not os.path.isfile(path):
            continue
        
        with open(path, "r", errors="ignore") as f:
            for line in f:
                if query in line.lower():
                    results.append(line.strip())

    return results


if __name__ == "__main__":
    app.run(port=5050, debug=True)
