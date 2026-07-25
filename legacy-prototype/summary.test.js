const test = require('node:test');
const assert = require('node:assert/strict');
const { portfolio } = require('../api/summary');

test('matched energy cannot exceed demand or renewable generation', () => {
  assert.ok(portfolio.matchedMwh <= portfolio.demandMwh);
  assert.ok(portfolio.matchedMwh <= portfolio.renewableMwh);
});

test('forecast supports a valid GB settlement-day period count', () => {
  assert.ok([46, 48, 50].includes(portfolio.settlementPeriods));
});
