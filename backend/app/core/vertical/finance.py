from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.core.agent.base import AgentContext, AgentMessage, BaseAgent


@dataclass
class FinanceAnalysisResult:
    analysis_type: str
    summary: str
    data: dict[str, Any] = field(default_factory=dict)
    recommendations: list[str] = field(default_factory=list)
    risk_level: str = "medium"
    confidence: float = 0.0


class FinanceAgent(BaseAgent):
    def __init__(self, name: str = "finance_agent") -> None:
        super().__init__(name=name)
        self._market_data: dict[str, Any] = {}

    async def think(self, context: AgentContext) -> AgentContext:
        return context

    async def run(self, context: AgentContext) -> AgentContext:
        user_message = context.messages[-1].content if context.messages else ""

        analysis = await self.analyze(user_message)

        self.add_message("assistant", analysis.summary)
        context.messages.append(AgentMessage(role="assistant", content=analysis.summary))
        return context

    async def analyze(self, query: str) -> FinanceAnalysisResult:
        query_lower = query.lower()

        if any(kw in query_lower for kw in ["stock", "price", "market", "quote"]):
            return await self._analyze_market(query)
        elif any(kw in query_lower for kw in ["portfolio", "allocation", "balance"]):
            return await self._analyze_portfolio(query)
        elif any(kw in query_lower for kw in ["risk", "exposure", "var"]):
            return await self._analyze_risk(query)
        else:
            return await self._analyze_general(query)

    async def _analyze_market(self, query: str) -> FinanceAnalysisResult:
        return FinanceAnalysisResult(
            analysis_type="market",
            summary="Market analysis requires real-time data integration. Connect a market data provider for live analysis.",
            data={"query": query, "status": "requires_data_source"},
            recommendations=["Configure a market data API key in settings", "Use the search tool for current market information"],
            risk_level="medium",
            confidence=0.5,
        )

    async def _analyze_portfolio(self, query: str) -> FinanceAnalysisResult:
        return FinanceAnalysisResult(
            analysis_type="portfolio",
            summary="Portfolio analysis requires position data. Please provide your holdings for detailed analysis.",
            data={"query": query, "status": "requires_position_data"},
            recommendations=["Upload your portfolio CSV for analysis", "Connect your brokerage account for automatic tracking"],
            risk_level="low",
            confidence=0.6,
        )

    async def _analyze_risk(self, query: str) -> FinanceAnalysisResult:
        return FinanceAnalysisResult(
            analysis_type="risk",
            summary="Risk analysis framework ready. Provide portfolio data for Value-at-Risk and exposure calculations.",
            data={"query": query, "metrics_available": ["VaR", "stress_test", "correlation"]},
            recommendations=["Diversify across asset classes", "Set stop-loss levels", "Monitor correlation changes"],
            risk_level="medium",
            confidence=0.7,
        )

    async def _analyze_general(self, query: str) -> FinanceAnalysisResult:
        return FinanceAnalysisResult(
            analysis_type="general",
            summary="Financial analysis assistant ready. I can help with market analysis, portfolio review, and risk assessment.",
            data={"query": query},
            recommendations=[
                "Ask about specific stocks or markets",
                "Request portfolio analysis",
                "Inquire about risk metrics",
            ],
            risk_level="low",
            confidence=0.8,
        )

    async def get_stock_quote(self, symbol: str) -> dict[str, Any]:
        return {
            "symbol": symbol,
            "status": "requires_data_source",
            "message": "Connect a market data provider for real-time quotes",
        }

    async def calculate_var(self, positions: list[dict[str, Any]], confidence_level: float = 0.95) -> dict[str, Any]:
        if not positions:
            return {"error": "No positions provided"}

        total_value = sum(p.get("value", 0) for p in positions)
        return {
            "var_estimate": total_value * 0.02 * (1.0 + (1.0 - confidence_level) * 10),
            "confidence_level": confidence_level,
            "positions_analyzed": len(positions),
            "total_value": total_value,
            "method": "parametric",
            "note": "Simplified VaR calculation. Connect real data for accurate results.",
        }
