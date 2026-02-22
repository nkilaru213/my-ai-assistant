
from flask import Flask, request, jsonify, make_response
import json, os
from difflib import SequenceMatcher

app = Flask(__name__)
ROOT = os.path.dirname(__file__)
with open(os.path.join(ROOT, "kb.json")) as f:
    KB = json.load(f)

def sim(a, b):
    return SequenceMatcher(None, a, b).ratio()

def find_answer(question: str):
    q = (question or "").lower()
    best = None
    best_score = 0.0
    for entry in KB:
        for kw in entry["keywords"]:
            s = sim(q, kw.lower())
            if s > best_score:
                best_score = s
                best = entry
    if best and best_score > 0.3:
        return best["answer"]
    return "This is the simple legacy backend. For full DB + files + deep research, run app_db.py."

def cors(resp):
    resp.headers["Access-Control-Allow-Origin"] = "*"
    resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
    resp.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
    return resp

@app.route("/ask", methods=["POST", "OPTIONS"])
def ask():
    if request.method == "OPTIONS":
        return cors(make_response("", 204))
    data = request.get_json(silent=True) or {}
    q = data.get("question", "")
    answer = find_answer(q)
    return cors(jsonify({"answer": answer}))

if __name__ == "__main__":
    app.run(port=5050, debug=True)
