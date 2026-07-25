const portfolio = {
  date: '2026-07-24',
  settlementPeriods: 48,
  demandMwh: 38.4,
  renewableMwh: 26.1,
  matchedMwh: 23.7,
  greenMatchRate: 61.7,
  residualGridMwh: 14.7,
  spillMwh: 2.4,
  avoidedCarbonKg: 4790,
  hedgeMwh: 16.2,
  confidence: 82,
  status: 'healthy'
};

module.exports = (req, res) => {
  res.setHeader('Content-Type', 'application/json');
  res.setHeader('Cache-Control', 's-maxage=300, stale-while-revalidate=600');
  res.statusCode = 200;
  res.end(JSON.stringify(portfolio));
};

module.exports.portfolio = portfolio;
