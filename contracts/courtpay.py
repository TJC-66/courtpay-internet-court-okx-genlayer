# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }
import json
import genlayer as gl
from dataclasses import dataclass
from genlayer.storage import allow as allow_storage

@allow_storage
@dataclass
class Case:
    case_id: str
    receipt_json: str
    terms_json: str
    evidence_json: str
    status: str
    verdict_json: str

class CourtPay(gl.contract.Contract):
    cases: gl.storage.TreeMap[str, Case]
    case_count: gl.u256

    def __init__(self):
        self.case_count = gl.u256(0)

    @gl.public.write
    def open_case(self, case_id: str, receipt_json: str, terms_json: str, evidence_json: str) -> None:
        if not case_id or len(case_id) > 96:
            raise gl.vm.UserError("Invalid case id")
        if case_id in self.cases:
            raise gl.vm.UserError("Case already exists")
        receipt, terms, evidence = json.loads(receipt_json), json.loads(terms_json), json.loads(evidence_json)
        required = ["payment_id", "payer", "payee", "amount", "asset", "authorization"]
        if any(field not in receipt for field in required):
            raise gl.vm.UserError("Incomplete payment receipt")
        if not isinstance(terms.get("claims"), list) or not terms["claims"]:
            raise gl.vm.UserError("At least one service claim is required")
        if not isinstance(evidence.get("items"), list):
            raise gl.vm.UserError("Evidence items must be a list")
        self.cases[case_id] = Case(case_id, json.dumps(receipt, sort_keys=True), json.dumps(terms, sort_keys=True), json.dumps(evidence, sort_keys=True), "OPEN", "")
        self.case_count = gl.u256(int(self.case_count) + 1)

    def _judge(self, case: Case) -> str:
        def leader() -> str:
            prompt = f"""Review this Internet Court dispute for an autonomous-agent payment. Use only the record; do not invent evidence.
OKX receipt: {case.receipt_json}
Service claims: {case.terms_json}
Delivery evidence: {case.evidence_json}
Return only JSON with verdict RELEASE, HOLD, or REFUND; evidence_score 0..100; supported_claims; total_claims; reason; next_action. RELEASE requires every material claim. HOLD means missing evidence can still be supplied. REFUND requires contradiction or proven non-delivery."""
            return json.dumps(gl.nondet.exec_prompt(prompt, response_format="json"), sort_keys=True)
        return gl.eq_principle.strict_eq(leader)

    @gl.public.write
    def resolve_case(self, case_id: str) -> dict:
        if case_id not in self.cases:
            raise gl.vm.UserError("Unknown case")
        case = self.cases[case_id]
        if case.status != "OPEN":
            raise gl.vm.UserError("Case already resolved")
        verdict = json.loads(self._judge(case))
        required = {"verdict","evidence_score","supported_claims","total_claims","reason","next_action"}
        if set(verdict.keys()) != required or verdict["verdict"] not in ["RELEASE","HOLD","REFUND"]:
            raise gl.vm.UserError("Malformed verdict")
        if not 0 <= int(verdict["evidence_score"]) <= 100:
            raise gl.vm.UserError("Invalid evidence score")
        case.status, case.verdict_json = verdict["verdict"], json.dumps(verdict, sort_keys=True)
        return verdict

    @gl.public.view
    def get_case(self, case_id: str) -> dict:
        if case_id not in self.cases:
            raise gl.vm.UserError("Unknown case")
        case = self.cases[case_id]
        return {"case_id":case.case_id,"receipt":json.loads(case.receipt_json),"terms":json.loads(case.terms_json),"evidence":json.loads(case.evidence_json),"status":case.status,"verdict":json.loads(case.verdict_json) if case.verdict_json else None}
