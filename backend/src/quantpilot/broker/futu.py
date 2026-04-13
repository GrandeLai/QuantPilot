"""Futu OpenAPI trading provider.

当前阶段目标：
- 占住 unified trading broker 主线中的正式 provider 位置
- 显式暴露配置 / SDK / OpenD 可用性
- 在环境未就绪时给出结构化失败，而不是伪装成其他 provider
"""

from __future__ import annotations

from dataclasses import dataclass

from quantpilot.broker.types import (
    TradingAccountOverview,
    TradingAssetType,
    TradingCancelResult,
    TradingCapability,
    TradingCashFlow,
    TradingExecution,
    TradingMarket,
    TradingMode,
    TradingOrder,
    TradingOrderEstimate,
    TradingOrderEstimateRequest,
    TradingOrderRequest,
    TradingPosition,
    TradingProviderError,
    TradingProviderKind,
    TradingProviderStatus,
    TradingQuote,
    TradingSecurity,
    TradingSubmitResult,
)
from quantpilot.config import get_settings


@dataclass(frozen=True, slots=True)
class FutuProviderAvailability:
    """Availability snapshot for Futu provider startup."""

    configured: bool
    reason: str | None


class FutuTradingProvider:
    """Futu provider with explicit availability reporting."""

    def __init__(self) -> None:
        self._settings = get_settings()
        self._sdk = None
        self._sdk_import_error: str | None = None
        try:
            import futu as futu_sdk  # type: ignore
        except Exception as exc:  # pragma: no cover - depends on local environment
            self._sdk_import_error = str(exc)
        else:  # pragma: no cover - depends on local environment
            self._sdk = futu_sdk

        self._availability = self._resolve_availability()

    def get_status(self) -> TradingProviderStatus:
        notes = [
            "当前阶段富途 provider 先完成 broker 占位与状态暴露，完整交易能力将在后续阶段逐步补齐。",
            "若本机未安装 futu SDK、未配置 OpenD 地址，或 OpenD 未启动，交易接口会返回结构化不可用错误。",
        ]
        if self._settings.futu_market:
            notes.append(f"当前市场偏好：{self._settings.futu_market}")
        return TradingProviderStatus(
            provider=TradingProviderKind.FUTU,
            mode=TradingMode.PAPER,
            configured=self._availability.configured,
            reason=self._availability.reason,
            capabilities=TradingCapability(
                supported_markets=[TradingMarket.US, TradingMarket.HK],
                supported_asset_types=[
                    TradingAssetType.STOCK,
                    TradingAssetType.ETF,
                    TradingAssetType.WARRANT,
                    TradingAssetType.OPTION,
                ],
                supported_order_types=[],
                supports_us_short_selling=False,
                supports_otc=False,
                supports_us_prepost=False,
                supports_options=True,
                notes=notes,
            ),
        )

    def search_securities(self, query: str, *, limit: int = 20) -> list[TradingSecurity]:
        self._raise_unavailable("标的搜索")

    def get_quotes(self, symbols: list[str]) -> list[TradingQuote]:
        self._raise_unavailable("行情查询")

    def get_account_overview(self) -> TradingAccountOverview:
        self._raise_unavailable("账户查询")

    def get_positions(self) -> list[TradingPosition]:
        self._raise_unavailable("持仓查询")

    def get_today_orders(self) -> list[TradingOrder]:
        self._raise_unavailable("当日委托查询")

    def get_history_orders(self) -> list[TradingOrder]:
        self._raise_unavailable("历史委托查询")

    def get_order_detail(self, order_id: str) -> TradingOrder:
        self._raise_unavailable("订单详情查询")

    def estimate_order(self, request: TradingOrderEstimateRequest) -> TradingOrderEstimate:
        self._raise_unavailable("下单估算")

    def submit_order(self, request: TradingOrderRequest) -> TradingSubmitResult:
        self._raise_unavailable("提交订单")

    def cancel_order(self, order_id: str) -> TradingCancelResult:
        self._raise_unavailable("撤单")

    def get_today_executions(self) -> list[TradingExecution]:
        self._raise_unavailable("当日成交查询")

    def get_history_executions(self) -> list[TradingExecution]:
        self._raise_unavailable("历史成交查询")

    def get_cash_flows(self) -> list[TradingCashFlow]:
        self._raise_unavailable("资金流水查询")

    def _resolve_availability(self) -> FutuProviderAvailability:
        if self._sdk is None:
            return FutuProviderAvailability(
                configured=False,
                reason=f"Futu provider unavailable: futu SDK not installed ({self._sdk_import_error})",
            )
        if not self._settings.futu_host or not self._settings.futu_port:
            return FutuProviderAvailability(
                configured=False,
                reason="Futu provider unavailable: QUANTPILOT_FUTU_HOST / QUANTPILOT_FUTU_PORT 未配置",
            )
        return FutuProviderAvailability(configured=True, reason=None)

    def _raise_unavailable(self, action: str) -> None:
        if self._availability.configured:
            raise TradingProviderError(
                f"Futu provider ready for {action} wiring, but this capability is not implemented in the current phase",
                code="futu_not_implemented",
                status_code=501,
            )
        raise TradingProviderError(
            f"{action}失败: {self._availability.reason}",
            code="futu_unavailable",
            status_code=503,
        )
