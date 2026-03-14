from flask import Flask, request, jsonify, Response
from flask_cors import CORS
from datetime import datetime
import uuid
import os
import sys

# Make sure audit_data is importable from same directory
sys.path.insert(0, os.path.dirname(__file__))
from audit_data import AUDIT_MODULES, MODULE_INFO

app = Flask(__name__)
CORS(app)

# In-memory store (stateless per Vercel function invocation — fine for audit tool)
sessions = {}

# Load frontend HTML once
_html_path = os.path.join(os.path.dirname(__file__), "frontend.html")
with open(_html_path, "r", encoding="utf-8") as f:
    FRONTEND_HTML = f.read()


# ── Helpers ─────────────────────────────────────────────────────────────────
def weighted_score(module, answers):
    total_weight = 0
    secure_weight = 0
    answered = 0
    for q in module["questions"]:
        ans = answers.get(q["id"])
        if ans is None or ans == "na":
            continue
        w = q.get("weight", 1)
        total_weight += w
        answered += 1
        if q["risk_if_yes"]:
            if ans == "no":
                secure_weight += w
        else:
            if ans == "yes":
                secure_weight += w
    if total_weight == 0:
        return None, 0
    return round((secure_weight / total_weight) * 100), answered


def risk_level(score):
    if score is None:
        return "unknown"
    if score >= 75:
        return "low"
    elif score >= 45:
        return "medium"
    return "high"


def risk_label(score):
    return {
        "low": "Low Risk",
        "medium": "Moderate Risk",
        "high": "Critical Risk",
        "unknown": "Not Assessed"
    }[risk_level(score)]


def executive_summary(score, critical, moderate, modules, org):
    if score >= 75:
        posture = f"{org} demonstrates a strong IAM posture with a security score of {score}%."
        action = "Continue monitoring and schedule quarterly access reviews."
    elif score >= 45:
        posture = f"{org}'s IAM posture requires improvement with a security score of {score}%."
        action = f"Address {moderate} moderate gaps immediately and plan remediation within 90 days."
    else:
        posture = f"{org} has critical IAM vulnerabilities with a security score of {score}%."
        action = f"Immediate action required -- {critical} critical gaps pose significant breach risk. Engage InnaIT for priority remediation."
    return (
        f"{posture} The assessment identified {critical} critical and {moderate} moderate gaps "
        f"across {modules} areas requiring InnaIT module deployment. {action}"
    )


# ── Routes ───────────────────────────────────────────────────────────────────
@app.route("/", methods=["GET"])
def index():
    return Response(FRONTEND_HTML, mimetype="text/html")


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "version": "2.0.0", "timestamp": datetime.utcnow().isoformat()})


@app.route("/api/modules", methods=["GET"])
def get_modules():
    return jsonify([
        {
            "id": m["id"],
            "category": m["category"],
            "title": m["title"],
            "innait_module": m["innait_module"],
            "innait_module_id": m["innait_module_id"],
            "priority": m["priority"],
            "description": m["description"],
            "icon": m["icon"],
            "question_count": len(m["questions"]),
            "questions": m["questions"],
            "compliance_refs": m.get("compliance_refs", []),
        }
        for m in AUDIT_MODULES
    ])


@app.route("/api/session/start", methods=["POST"])
def start_session():
    data = request.json or {}
    session_id = str(uuid.uuid4())
    sessions[session_id] = {
        "id": session_id,
        **{k: data.get(k, "") for k in ["org_name", "auditor_name", "org_size", "industry"]},
        "created_at": datetime.utcnow().isoformat(),
        "answers": {},
        "status": "in_progress",
    }
    return jsonify({"session_id": session_id})


@app.route("/api/session/<session_id>/answers", methods=["PATCH"])
def update_answers(session_id):
    if session_id not in sessions:
        return jsonify({"error": "Session not found"}), 404
    sessions[session_id]["answers"].update((request.json or {}).get("answers", {}))
    return jsonify({"ok": True})


@app.route("/api/session/<session_id>/analyze", methods=["POST"])
def analyze(session_id):
    if session_id == "direct":
        data = request.json or {}
        answers = data.get("answers", {})
        meta = data
    elif session_id in sessions:
        s = sessions[session_id]
        answers = s["answers"]
        meta = s
    else:
        return jsonify({"error": "Session not found"}), 404

    results = []
    overall_weights = []
    priority_order = {"critical": 0, "high": 1, "medium": 2}

    for module in AUDIT_MODULES:
        score, answered = weighted_score(module, answers)
        rl = risk_level(score)
        needs_innait = score is not None and score < 75
        mod_info = MODULE_INFO.get(module["innait_module_id"], {})

        results.append({
            "id": module["id"],
            "category": module["category"],
            "title": module["title"],
            "innait_module": module["innait_module"],
            "innait_module_id": module["innait_module_id"],
            "innait_module_color": mod_info.get("color", "#3b82f6"),
            "priority": module["priority"],
            "score": score,
            "risk_level": rl,
            "risk_label": risk_label(score),
            "needs_innait": needs_innait,
            "questions_answered": answered,
            "questions_total": len(module["questions"]),
            "gap_description": module["gap_description"] if needs_innait else "Controls appear adequate",
            "risk": module["risk"] if needs_innait else "Minimal -- continue monitoring",
            "solution": module["solution"] if needs_innait else "Maintain current controls and schedule periodic review.",
            "compliance_refs": module.get("compliance_refs", []),
        })
        if score is not None:
            overall_weights.append(score)

    overall = round(sum(overall_weights) / len(overall_weights)) if overall_weights else 0
    critical = [r for r in results if r["risk_level"] == "high"]
    moderate = [r for r in results if r["risk_level"] == "medium"]
    low = [r for r in results if r["risk_level"] == "low"]
    needs_modules = [r for r in results if r["needs_innait"]]

    categories = {}
    for r in results:
        categories.setdefault(r["category"], []).append(r)

    remediation = []
    for r in sorted(needs_modules, key=lambda x: (priority_order.get(x["priority"], 3), x["score"] or 0)):
        remediation.append({
            "module": r["innait_module"],
            "area": r["title"],
            "score": r["score"],
            "risk_level": r["risk_level"],
            "action": r["solution"],
        })

    report = {
        "session_id": session_id,
        "org_name": meta.get("org_name", "Your Organization"),
        "auditor_name": meta.get("auditor_name", ""),
        "industry": meta.get("industry", ""),
        "org_size": meta.get("org_size", ""),
        "generated_at": datetime.utcnow().strftime("%d %b %Y, %H:%M UTC"),
        "overall_score": overall,
        "overall_risk": risk_level(overall),
        "overall_risk_label": risk_label(overall),
        "critical_count": len(critical),
        "moderate_count": len(moderate),
        "low_count": len(low),
        "modules_needed": len(needs_modules),
        "total_assessed": len(overall_weights),
        "results": results,
        "categories": categories,
        "remediation_plan": remediation,
        "executive_summary": executive_summary(
            overall, len(critical), len(moderate), len(needs_modules),
            meta.get("org_name", "your organization")
        ),
    }

    if session_id in sessions:
        sessions[session_id]["report"] = report
        sessions[session_id]["status"] = "completed"

    return jsonify(report)


# Local dev entrypoint
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"\n  InnaIT IAM Audit -- http://127.0.0.1:{port}\n")
    app.run(debug=True, port=port, host="127.0.0.1")
