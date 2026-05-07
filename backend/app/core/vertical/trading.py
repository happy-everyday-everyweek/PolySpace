from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.core.agent.base import AgentContext, AgentMessage, BaseAgent


@dataclass
class TradingResult:
    action: str
    content: str
    data: dict[str, Any] = field(default_factory=dict)
    risk_level: str = "medium"
    confidence: float = 0.0


class TradingAgent(BaseAgent):
    def __init__(self, name: str = "trading_agent") -> None:
        super().__init__(name=name)
        self._vibe_trading_url: str = ""

    def configure(self, vibe_trading_url: str = "http://localhost:8899") -> None:
        self._vibe_trading_url = vibe_trading_url.rstrip("/")

    async def think(self, context: AgentContext) -> AgentContext:
        return context

    async def run(self, context: AgentContext) -> AgentContext:
        user_message = context.messages[-1].content if context.messages else ""
        result = await self.process_trading_request(user_message)
        self.add_message("assistant", result.content)
        context.messages.append(AgentMessage(role="assistant", content=result.content))
        return context

    async def process_trading_request(self, query: str) -> TradingResult:
        query_lower = query.lower()
        if any(kw in query_lower for kw in ["backtest", "strategy", "test strategy"]):
            return await self._backtest_strategy(query)
        elif any(kw in query_lower for kw in ["factor", "ic", "ir", "alpha"]):
            return await self._factor_analysis(query)
        elif any(kw in query_lower for kw in ["option", "greeks", "black-scholes", "pricing"]):
            return await self._options_analysis(query)
        elif any(kw in query_lower for kw in ["pattern", "technical", "chart", "candlestick"]):
            return await self._pattern_recognition(query)
        elif any(kw in query_lower for kw in ["portfolio", "allocation", "optimize", "mvo"]):
            return await self._portfolio_optimization(query)
        elif any(kw in query_lower for kw in ["correlation", "cross-asset", "relationship"]):
            return await self._correlation_analysis(query)
        elif any(kw in query_lower for kw in ["swarm", "team", "committee", "multi-agent"]):
            return await self._swarm_team(query)
        elif any(kw in query_lower for kw in ["export", "pine", "tradingview", "metatrader"]):
            return await self._export_strategy(query)
        elif any(kw in query_lower for kw in ["market", "price", "quote", "data"]):
            return await self._market_data(query)
        else:
            return TradingResult(
                action="guide",
                content="I am your AI trading assistant powered by Vibe-Trading. I can help you:\n"
                "- Design and backtest trading strategies\n"
                "- Factor analysis (IC/IR + layered backtest)\n"
                "- Options pricing (Black-Scholes + Greeks)\n"
                "- Technical pattern recognition\n"
                "- Portfolio optimization (MVO, risk parity, etc.)\n"
                "- Cross-asset correlation analysis\n"
                "- Multi-agent Swarm teams (29 presets)\n"
                "- Export to TradingView/MetaTrader/TongDaXin\n"
                "- Get market data (A-share, HK/US, crypto, futures, forex)\n\n"
                "DISCLAIMER: All analysis is for reference only. Past performance does not guarantee future results. "
                "Always do your own research and consider risk tolerance.",
                risk_level="low",
                confidence=0.9,
            )

    async def _backtest_strategy(self, query: str) -> TradingResult:
        return TradingResult(
            action="backtest",
            content="Strategy backtest initiated. Vibe-Trading supports 7 market engines:\n"
            "- ChinaAEngine (A-share)\n- GlobalEquityEngine (HK/US stocks)\n"
            "- CryptoEngine (crypto)\n- ChinaFuturesEngine (domestic futures)\n"
            "- GlobalFuturesEngine (global futures)\n- ForexEngine (forex)\n"
            "- OptionsPortfolioEngine (options)\n\n"
            "Data sources auto-fallback: Tushare -> AKShare -> yfinance -> OKX/CCXT\n"
            "Statistical validation: Monte Carlo, Bootstrap CI, Walk-Forward\n\n"
            "Please specify: market, ticker, strategy logic, date range.",
            data={"engines": 7, "data_sources": ["tushare", "akshare", "yfinance", "okx", "ccxt", "futu"]},
            risk_level="medium",
            confidence=0.7,
        )

    async def _factor_analysis(self, query: str) -> TradingResult:
        return TradingResult(
            action="factor_analysis",
            content="Factor analysis available:\n"
            "- IC (Information Coefficient) analysis\n"
            "- IR (Information Ratio) analysis\n"
            "- Layered backtest by factor quantiles\n"
            "- Factor decay analysis\n"
            "- Cross-sectional regression",
            data={"metrics": ["IC", "IR", "layered_backtest", "decay", "regression"]},
            risk_level="low",
            confidence=0.8,
        )

    async def _options_analysis(self, query: str) -> TradingResult:
        return TradingResult(
            action="options_analysis",
            content="Options pricing and analysis:\n"
            "- Black-Scholes pricing model\n"
            "- Greeks calculation (Delta, Gamma, Theta, Vega, Rho)\n"
            "- Implied volatility estimation\n"
            "- Options strategy payoff diagrams\n"
            "- Portfolio-level options risk assessment",
            data={"models": ["black_scholes"], "greeks": ["delta", "gamma", "theta", "vega", "rho"]},
            risk_level="medium",
            confidence=0.8,
        )

    async def _pattern_recognition(self, query: str) -> TradingResult:
        return TradingResult(
            action="pattern_recognition",
            content="Technical pattern recognition available:\n"
            "- Classic chart patterns (head-shoulders, double-top/bottom, triangles, etc.)\n"
            "- Candlestick patterns (doji, hammer, engulfing, etc.)\n"
            "- Support/resistance level detection\n"
            "- Trend line identification",
            data={"pattern_types": ["chart", "candlestick", "support_resistance", "trend"]},
            risk_level="medium",
            confidence=0.6,
        )

    async def _portfolio_optimization(self, query: str) -> TradingResult:
        return TradingResult(
            action="portfolio_optimization",
            content="Portfolio optimization methods:\n"
            "- Mean-Variance Optimization (MVO)\n"
            "- Risk Parity\n"
            "- Equal Volatility\n"
            "- Maximum Diversification\n"
            "- Black-Litterman\n\n"
            "Please provide your holdings or target allocation for analysis.",
            data={"methods": ["MVO", "risk_parity", "equal_vol", "max_div", "black_litterman"]},
            risk_level="low",
            confidence=0.7,
        )

    async def _correlation_analysis(self, query: str) -> TradingResult:
        return TradingResult(
            action="correlation_analysis",
            content="Cross-asset correlation analysis:\n"
            "- Pairwise correlation matrix\n"
            "- Rolling correlation\n"
            "- Regime-dependent correlation\n"
            "- Correlation clustering\n\n"
            "Specify the assets or markets you want to analyze.",
            data={"types": ["pairwise", "rolling", "regime", "clustering"]},
            risk_level="low",
            confidence=0.8,
        )

    async def _swarm_team(self, query: str) -> TradingResult:
        return TradingResult(
            action="swarm_team",
            content="Multi-agent Swarm teams available (29 presets):\n"
            "- investment_committee: Long-short debate -> Risk control -> PM decision\n"
            "- macro_research: Economic indicators -> Policy analysis -> Market impact\n"
            "- quant_team: Factor mining -> Strategy design -> Backtest -> Deployment\n\n"
            "Teams use DAG workflow with parallel execution where possible.",
            data={"preset_count": 29, "workflow": "DAG"},
            risk_level="medium",
            confidence=0.6,
        )

    async def _export_strategy(self, query: str) -> TradingResult:
        return TradingResult(
            action="export_strategy",
            content="Strategy export formats:\n"
            "- TradingView Pine Script v6\n"
            "- TongDaXin / TongHuaShun / DongFangCaiFu\n"
            "- MetaTrader 5 (MQL5)\n\n"
            "Specify which platform you want to export to.",
            data={"platforms": ["tradingview", "tongdaxin", "metatrader5"]},
            risk_level="low",
            confidence=0.9,
        )

    async def _market_data(self, query: str) -> TradingResult:
        return TradingResult(
            action="market_data",
            content="Market data available with auto-fallback:\n"
            "- A-share: Tushare -> AKShare (free) -> Futu\n"
            "- HK/US stocks: yfinance (free)\n"
            "- Crypto: OKX (free) -> CCXT\n"
            "- Futures: Tushare -> AKShare\n"
            "- Forex: CCXT\n\n"
            "Specify the ticker and date range you need.",
            data={"markets": ["a_share", "hk_us", "crypto", "futures", "forex"]},
            risk_level="low",
            confidence=0.8,
        )
