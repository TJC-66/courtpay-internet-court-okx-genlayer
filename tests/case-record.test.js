import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const fixtureUrl = new URL("../cases/logo-delivery-dispute.json", import.meta.url);

test("demo fixture contains a reproducible payment dispute", async () => {
  const fixture = JSON.parse(await readFile(fixtureUrl, "utf8"));
  assert.equal(fixture.case_id, "courtpay-demo-001");
  assert.equal(fixture.receipt.asset, "USDC");
  assert.equal(fixture.receipt.amount, "12.00");
  assert.equal(fixture.terms.claims.length, 5);
  assert.equal(fixture.evidence.items.length, 3);
});

test("sample outcome follows the documented HOLD policy", async () => {
  const fixture = JSON.parse(await readFile(fixtureUrl, "utf8"));
  const score = Math.round((fixture.evidence.items.length / fixture.terms.claims.length) * 100);
  assert.equal(score, 60);
  assert.equal(fixture.expected_demo_verdict.verdict, "HOLD");
  assert.equal(fixture.expected_demo_verdict.evidence_score, score);
});
