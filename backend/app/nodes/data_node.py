from typing import Dict, Any, Optional, List
import yfinance as yf
import pandas as pd
import asyncio
import time
import hashlib
import json
from datetime import datetime, timedelta
from .base import BaseNode
from app.services.encryption import EncryptionService
from app.core.config import settings

class DataFetcherNode(BaseNode):
    """Node for fetching financial market data from multiple sources"""

    display_name = "Data Fetcher"
    description = "Fetch financial data from Yahoo Finance, Alpha Vantage, Binance, Bybit, MetaTrader5"
    category = "data"

    # Supported data sources
    SOURCES = {
        "yahoo_finance": {
            "name": "Yahoo Finance",
            "description": "Free stock, crypto, forex data",
            "features": ["price", "financials", "balance_sheet", "cash_flow", "income_stmt"]
        },
        "alpha_vantage": {
            "name": "Alpha Vantage",
            "description": "Stock, crypto, forex, technical indicators",
            "features": ["price", "indicators"]
        },
        "binance": {
            "name": "Binance",
            "description": "Cryptocurrency exchange data",
            "features": ["price", "klines", "ticker", "depth"]
        },
        "bybit": {
            "name": "Bybit",
            "description": "Crypto derivatives exchange",
            "features": ["price", "klines", "ticker", "funding_rate"]
        },
        "mt5": {
            "name": "MetaTrader 5",
            "description": "Forex, stocks, futures from MT5",
            "features": ["price", "ticks", "rates", "positions"]
        }
    }

    def __init__(self, node_id: str, config: Dict[str, Any]):
        super().__init__(node_id, config)
        self.source = config.get("source", "yahoo_finance")
        self.symbol = config.get("symbol", "")
        self.interval = config.get("interval", "1d")
        self.period = config.get("period", "1mo")
        self.start_date = config.get("start_date", "")
        self.end_date = config.get("end_date", "")

        # Financial statements flags (Yahoo Finance)
        self.fetch_balance_sheet = config.get("fetch_balance_sheet", False)
        self.fetch_cash_flow = config.get("fetch_cash_flow", False)
        self.fetch_income_stmt = config.get("fetch_income_stmt", False)

        # Technical indicators (Alpha Vantage, etc.)
        self.indicators = config.get("indicators", [])  # List of indicators to fetch
        self.indicator_interval = config.get("indicator_interval", "daily")

        # Crypto exchange specific
        self.market_type = config.get("market_type", "spot")  # spot, futures, options
        self.limit = config.get("limit", 500)  # Number of records

        # MT5 specific
        self.mt5_timeframe = config.get("mt5_timeframe", "TIMEFRAME_D1")
        self.mt5_symbol_info = config.get("mt5_symbol_info", False)

        # Caching
        self.cache_ttl = config.get("cache_ttl", 3600)  # seconds
        self.cache: Dict[str, Dict[str, Any]] = {}

        # WebSocket support
        self.ws_connections: List[Any] = []
        self.user_id = config.get("user_id")  # For API key lookup

        # Validate source
        if self.source not in self.SOURCES:
            raise ValueError(f"Unsupported data source: {self.source}. Supported: {list(self.SOURCES.keys())}")

    def _calculate_since(self) -> Optional[int]:
        """Calculate timestamp based on period or date range (for crypto exchanges)"""
        # If using date range, calculate since from start_date
        if self.start_date:
            try:
                start_dt = datetime.strptime(self.start_date, "%Y-%m-%d")
                return int(start_dt.timestamp() * 1000)
            except ValueError:
                self._log(f"Invalid start_date format: {self.start_date}", "warning")
        # If no start_date, calculate since based on period
        period_to_days = {
            "1d": 1, "5d": 5, "1mo": 30, "3mo": 90,
            "6mo": 180, "1y": 365, "2y": 730, "5y": 1825
        }
        days = period_to_days.get(self.period, 30)
        since_date = datetime.now() - timedelta(days=days)
        return int(since_date.timestamp() * 1000) # CCXT expects milliseconds

    async def execute(self, inputs: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute data fetch"""
        # Store user_id for API key lookup
        self.user_id = context.get("user_id")

        # Allow symbol to come from input
        symbol = inputs.get("symbol", self.symbol)
        if not symbol:
            raise ValueError("Symbol is required (either in config or from input)")

        # Check cache first
        cache_key = self._get_cache_key(symbol=symbol)
        cached_data = self._get_from_cache(cache_key)
        if cached_data is not None:
            self._log(f"Returning cached data for {symbol}", "debug")
            return cached_data

        if self.source == "yahoo_finance":
            result = await self._fetch_yahoo_finance(symbol)
        elif self.source == "alpha_vantage":
            result = await self._fetch_alpha_vantage(symbol, context.get("db"))
        elif self.source == "binance":
            result = await self._fetch_binance(symbol)
        elif self.source == "bybit":
            result = await self._fetch_bybit(symbol)
        elif self.source == "mt5":
            result = await self._fetch_mt5(symbol, context.get("db"))
        else:
            raise ValueError(f"Data source {self.source} not implemented")

        # Store in cache
        self._store_in_cache(cache_key, result)

        return result

    def _get_cache_key(self, **kwargs) -> str:
        """Generate cache key from parameters"""
        cache_data = {
            "source": self.source,
            "symbol": kwargs.get("symbol", self.symbol),
            "interval": self.interval,
            "period": self.period,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "indicators": sorted(self.indicators) if self.indicators else []
        }
        key_str = json.dumps(cache_data, sort_keys=True)
        return hashlib.md5(key_str.encode()).hexdigest()

    def _get_from_cache(self, key: str) -> Optional[Dict[str, Any]]:
        """Get data from cache if not expired"""
        if key in self.cache:
            cached = self.cache[key]
            if time.time() - cached["timestamp"] < self.cache_ttl:
                return cached["data"]
        return None

    def _store_in_cache(self, key: str, data: Dict[str, Any]):
        """Store data in cache"""
        self.cache[key] = {
            "data": data,
            "timestamp": time.time()
        }
        # Clean expired entries
        self._clean_cache()

    def _clean_cache(self):
        """Remove expired cache entries"""
        now = time.time()
        expired = [k for k, v in self.cache.items() if now - v["timestamp"] > self.cache_ttl]
        for k in expired:
            del self.cache[k]

    async def _fetch_yahoo_finance(self, symbol: str) -> Dict[str, Any]:
        """Fetch comprehensive data from Yahoo Finance"""
        try:
            ticker = yf.Ticker(symbol)

            # Get historical data
            if self.start_date and self.end_date:
                hist = ticker.history(start=self.start_date, end=self.end_date, interval=self.interval)
            else:
                hist = ticker.history(period=self.period, interval=self.interval)

            # Get basic info
            info = ticker.info

            result = {
                "source": "yahoo_finance",
                "symbol": symbol,
                "data": hist.reset_index().to_dict(orient='records') if not hist.empty else [],
                "latest_price": hist['Close'].iloc[-1] if len(hist) > 0 else None,
                "info": {
                    "name": info.get("longName", ""),
                    "currency": info.get("currency", ""),
                    "market_cap": info.get("marketCap", None),
                    "sector": info.get("sector", ""),
                    "industry": info.get("industry", ""),
                    "exchange": info.get("exchange", ""),
                    "country": info.get("country", "")
                },
                "metadata": {
                    "period": self.period,
                    "interval": self.interval,
                    "start_date": self.start_date,
                    "end_date": self.end_date,
                    "rows": len(hist)
                }
            }

            # Fetch financial statements if requested
            if self.fetch_balance_sheet:
                try:
                    balance_sheet = ticker.balance_sheet
                    if not balance_sheet.empty:
                        result["balance_sheet"] = balance_sheet.reset_index().to_dict(orient='records')
                        result["balance_sheet_columns"] = list(balance_sheet.columns)
                except Exception as e:
                    result["balance_sheet_error"] = str(e)

            if self.fetch_cash_flow:
                try:
                    cash_flow = ticker.cashflow
                    if not cash_flow.empty:
                        result["cash_flow"] = cash_flow.reset_index().to_dict(orient='records')
                        result["cash_flow_columns"] = list(cash_flow.columns)
                except Exception as e:
                    result["cash_flow_error"] = str(e)

            if self.fetch_income_stmt:
                try:
                    income_stmt = ticker.income_stmt
                    if not income_stmt.empty:
                        result["income_stmt"] = income_stmt.reset_index().to_dict(orient='records')
                        result["income_stmt_columns"] = list(income_stmt.columns)
                except Exception as e:
                    result["income_stmt_error"] = str(e)

            return result

        except Exception as e:
            raise RuntimeError(f"Failed to fetch data from Yahoo Finance: {str(e)}")

    async def _fetch_alpha_vantage(self, symbol: str, db) -> Dict[str, Any]:
        """Fetch data and technical indicators from Alpha Vantage"""
        try:
            from alpha_vantage.timeseries import TimeSeries
            from alpha_vantage.techindicators import TechIndicators

            # Get API key with improved error handling
            api_key = await self._get_api_key(db, "alpha_vantage")

            result = {
                "source": "alpha_vantage",
                "symbol": symbol,
                "data": [],
                "indicators": {}
            }

            # Fetch price data
            ts = TimeSeries(key=api_key, output_format='pandas')
            if self.interval == "daily":
                data, meta_data = await asyncio.to_thread(ts.get_daily_adjusted, symbol=symbol, outputsize=self.period)
            elif self.interval == "intraday":
                data, meta_data = await asyncio.to_thread(ts.get_intraday, symbol=symbol, interval=self.indicator_interval)
            else:
                data, meta_data = await asyncio.to_thread(ts.get_daily_adjusted, symbol=symbol, outputsize="compact")

            result["data"] = data.reset_index().to_dict(orient='records')
            result["latest_price"] = data['4. close'].iloc[-1] if len(data) > 0 else None
            result["metadata"] = meta_data

            # Fetch technical indicators if requested
            if self.indicators:
                ti = TechIndicators(key=api_key, output_format='pandas')
                indicator_data = {}

                for indicator in self.indicators:
                    try:
                        if indicator == "SMA":
                            data_ind, meta = await asyncio.to_thread(
                                ti.get_sma, symbol=symbol, interval=self.indicator_interval, time_period=20
                            )
                        elif indicator == "EMA":
                            data_ind, meta = await asyncio.to_thread(
                                ti.get_ema, symbol=symbol, interval=self.indicator_interval, time_period=20
                            )
                        elif indicator == "RSI":
                            data_ind, meta = await asyncio.to_thread(
                                ti.get_rsi, symbol=symbol, interval=self.indicator_interval, time_period=14
                            )
                        elif indicator == "MACD":
                            data_ind, meta = await asyncio.to_thread(
                                ti.get_macd, symbol=symbol, interval=self.indicator_interval
                            )
                        elif indicator == "BBANDS":
                            data_ind, meta = await asyncio.to_thread(
                                ti.get_bbands, symbol=symbol, interval=self.indicator_interval, time_period=20
                            )
                        elif indicator == "STOCH":
                            data_ind, meta = await asyncio.to_thread(
                                ti.get_stoch, symbol=symbol, interval=self.indicator_interval
                            )
                        elif indicator == "ADX":
                            data_ind, meta = await asyncio.to_thread(
                                ti.get_adx, symbol=symbol, interval=self.indicator_interval, time_period=14
                            )
                        else:
                            continue

                        indicator_data[indicator] = {
                            "data": data_ind.reset_index().to_dict(orient='records'),
                            "meta": meta
                        }
                    except Exception as e:
                        indicator_data[indicator] = {"error": str(e)}

                result["indicators"] = indicator_data

            return result

        except ImportError:
            raise RuntimeError("Alpha Vantage package not installed. Install with: pip install alpha-vantage")
        except Exception as e:
            raise RuntimeError(f"Failed to fetch data from Alpha Vantage: {str(e)}")

    async def _fetch_binance(self, symbol: str) -> Dict[str, Any]:
        """Fetch data from Binance"""
        try:
            import ccxt.async_support as ccxt

            # Initialize Binance client
            exchange = ccxt.binance({
                'enableRateLimit': True,
            })

            # Calculate since timestamp based on period
            since = self._calculate_since()

            # Fetch klines (candlestick data)
            all_ohlcv = []

            try:
                ohlcv = await exchange.fetch_ohlcv(symbol, self.interval, since, self.limit)
                all_ohlcv.extend(ohlcv)
            except Exception as e:
                raise RuntimeError(f"Failed to fetch OHLCV data: {str(e)}")
            finally:
                await exchange.close()

            # Format data
            formatted_data = []
            for candle in all_ohlcv:
                formatted_data.append({
                    "timestamp": candle[0],
                    "open": candle[1],
                    "high": candle[2],
                    "low": candle[3],
                    "close": candle[4],
                    "volume": candle[5]
                })

            return {
                "source": "binance",
                "symbol": symbol,
                "data": formatted_data,
                "latest_price": formatted_data[-1]["close"] if formatted_data else None,
                "metadata": {
                    "interval": self.interval,
                    "count": len(formatted_data),
                    "market_type": self.market_type
                }
            }

        except ImportError:
            raise RuntimeError("CCXT package not installed. Install with: pip install ccxt")
        except Exception as e:
            raise RuntimeError(f"Failed to fetch data from Binance: {str(e)}")

    async def _fetch_bybit(self, symbol: str) -> Dict[str, Any]:
        """Fetch data from Bybit"""
        try:
            import ccxt.async_support as ccxt

            # Initialize Bybit client
            exchange = ccxt.bybit({
                'enableRateLimit': True,
            })

            # Calculate since timestamp based on period
            since = self._calculate_since()

            # Fetch klines
            all_ohlcv = []

            try:
                ohlcv = await exchange.fetch_ohlcv(symbol, self.interval, since, self.limit)
                all_ohlcv.extend(ohlcv)
            except Exception as e:
                raise RuntimeError(f"Failed to fetch OHLCV data: {str(e)}")
            finally:
                await exchange.close()

            # Format data
            formatted_data = []
            for candle in all_ohlcv:
                formatted_data.append({
                    "timestamp": candle[0],
                    "open": candle[1],
                    "high": candle[2],
                    "low": candle[3],
                    "close": candle[4],
                    "volume": candle[5]
                })

            # Also fetch funding rate if futures
            funding_rate = None
            if self.market_type == "futures":
                try:
                    # Re-open exchange for funding rate
                    exchange = ccxt.bybit({'enableRateLimit': True})
                    funding = await exchange.fetch_funding_rate(symbol)
                    funding_rate = funding['fundingRate']
                    await exchange.close()
                except:
                    pass

            return {
                "source": "bybit",
                "symbol": symbol,
                "data": formatted_data,
                "latest_price": formatted_data[-1]["close"] if formatted_data else None,
                "funding_rate": funding_rate,
                "metadata": {
                    "interval": self.interval,
                    "count": len(formatted_data),
                    "market_type": self.market_type
                }
            }

        except ImportError:
            raise RuntimeError("CCXT package not installed. Install with: pip install ccxt")
        except Exception as e:
            raise RuntimeError(f"Failed to fetch data from Bybit: {str(e)}")

    async def _fetch_mt5(self, symbol: str, db) -> Dict[str, Any]:
        """Fetch data from MetaTrader 5"""
        try:
            import MetaTrader5 as mt5

            # Initialize MT5
            if not mt5.initialize():
                raise RuntimeError("Failed to initialize MetaTrader 5. Is MT5 installed and running?")

            try:
                # Get symbol info if requested
                symbol_info = None
                if self.mt5_symbol_info:
                    symbol_info = mt5.symbol_info(symbol)
                    if symbol_info is None:
                        raise ValueError(f"Symbol {symbol} not found in MT5")

                # Determine timeframe
                timeframe_map = {
                    "1m": mt5.TIMEFRAME_M1,
                    "5m": mt5.TIMEFRAME_M5,
                    "15m": mt5.TIMEFRAME_M15,
                    "30m": mt5.TIMEFRAME_M30,
                    "1h": mt5.TIMEFRAME_H1,
                    "4h": mt5.TIMEFRAME_H4,
                    "1d": mt5.TIMEFRAME_D1,
                    "1w": mt5.TIMEFRAME_W1,
                    "1mo": mt5.TIMEFRAME_MN1
                }
                mt5_timeframe = timeframe_map.get(self.interval, mt5.TIMEFRAME_D1)

                # Get rates
                if self.start_date and self.end_date:
                    from datetime import datetime
                    start_dt = datetime.strptime(self.start_date, "%Y-%m-%d")
                    end_dt = datetime.strptime(self.end_date, "%Y-%m-%d")
                    rates = mt5.copy_rates_range(symbol, mt5_timeframe, start_dt, end_dt)
                else:
                    # Get last N bars based on period
                    period_map = {
                        "1d": 1, "5d": 5, "1mo": 30, "3mo": 90,
                        "6mo": 180, "1y": 365, "2y": 730, "5y": 1825
                    }
                    count = period_map.get(self.period, 100)
                    rates = mt5.copy_rates_from_pos(symbol, mt5_timeframe, 0, count)

                if rates is None or len(rates) == 0:
                    raise ValueError(f"No data received for symbol {symbol}")

                # Convert to list of dicts
                data = []
                for rate in rates:
                    data.append({
                        "timestamp": int(rate[0]),
                        "open": float(rate[1]),
                        "high": float(rate[2]),
                        "low": float(rate[3]),
                        "close": float(rate[4]),
                        "volume": float(rate[5]),
                        "spread": float(rate[6]) if len(rate) > 6 else 0
                    })

                result = {
                    "source": "mt5",
                    "symbol": symbol,
                    "data": data,
                    "latest_price": data[-1]["close"] if data else None,
                    "metadata": {
                        "interval": self.interval,
                        "count": len(data),
                        "timeframe": self.mt5_timeframe
                    }
                }

                if symbol_info:
                    result["symbol_info"] = {
                        "description": symbol_info.description,
                        "currency_base": symbol_info.currency_base,
                        "currency_profit": symbol_info.currency_profit,
                        "digits": symbol_info.digits,
                        "trade_mode": symbol_info.trade_mode,
                        "start": symbol_info.start,
                        "expiration": symbol_info.expiration
                    }

                return result

            finally:
                mt5.shutdown()

        except ImportError:
            raise RuntimeError("MetaTrader5 package not installed. Install with: pip install MetaTrader5")
        except Exception as e:
            raise RuntimeError(f"Failed to fetch data from MetaTrader 5: {str(e)}")

    async def _get_api_key(self, db, service: str) -> str:
        """Get encrypted API key with better error handling"""
        try:
            from app.models.api_key import APIKey

            if not db:
                raise ValueError("Database session required")

            # Build query
            query = db.query(APIKey).filter(
                APIKey.service == service,
                APIKey.is_active == True
            )

            # Filter by user_id if available
            if hasattr(self, 'user_id') and self.user_id:
                query = query.filter(APIKey.owner_id == self.user_id)

            api_key_record = query.first()

            if not api_key_record:
                # Log available services for debugging
                available = db.query(APIKey.service).distinct().all()
                self._log(f"Available API keys: {[s[0] for s in available]}", "debug")
                raise ValueError(f"No active API key for service: {service}. Please add one in settings.")

            encryption_service = EncryptionService(settings.ENCRYPTION_KEY)
            return encryption_service.decrypt(api_key_record.encrypted_key)

        except Exception as e:
            self._log(f"API key error for {service}: {str(e)}", "error")
            raise

    @classmethod
    def get_ui_schema(cls) -> Dict[str, Any]:
        """Return UI schema for Data Fetcher node configuration"""
        return {
            "parameters": [
                {
                    "name": "source",
                    "type": "select",
                    "title": "Data Source",
                    "default": "yahoo_finance",
                    "options": [
                        {"value": "yahoo_finance", "label": "Yahoo Finance (Free)"},
                        {"value": "alpha_vantage", "label": "Alpha Vantage (API Key)"},
                        {"value": "binance", "label": "Binance (Crypto)"},
                        {"value": "bybit", "label": "Bybit (Crypto Derivatives)"},
                        {"value": "mt5", "label": "MetaTrader 5 (Forex/Stocks)"}
                    ],
                    "description": "Source of market data"
                },
                {
                    "name": "symbol",
                    "type": "string",
                    "title": "Symbol",
                    "default": "AAPL",
                    "description": "Ticker symbol (e.g., AAPL, BTC/USDT, EURUSD, XAUUSD)"
                },
                {
                    "name": "interval",
                    "type": "select",
                    "title": "Interval",
                    "default": "1d",
                    "options": [
                        {"value": "1m", "label": "1 Minute"},
                        {"value": "5m", "label": "5 Minutes"},
                        {"value": "15m", "label": "15 Minutes"},
                        {"value": "30m", "label": "30 Minutes"},
                        {"value": "60m", "label": "60 Minutes"},
                        {"value": "1h", "label": "1 Hour"},
                        {"value": "4h", "label": "4 Hours"},
                        {"value": "1d", "label": "1 Day"},
                        {"value": "1wk", "label": "1 Week"},
                        {"value": "1mo", "label": "1 Month"}
                    ],
                    "description": "Candlestick interval"
                },
                {
                    "name": "period",
                    "type": "select",
                    "title": "Period (Yahoo Finance)",
                    "default": "1mo",
                    "options": [
                        {"value": "1d", "label": "1 Day"},
                        {"value": "5d", "label": "5 Days"},
                        {"value": "1mo", "label": "1 Month"},
                        {"value": "3mo", "label": "3 Months"},
                        {"value": "6mo", "label": "6 Months"},
                        {"value": "1y", "label": "1 Year"},
                        {"value": "2y", "label": "2 Years"},
                        {"value": "5y", "label": "5 Years"},
                        {"value": "10y", "label": "10 Years"},
                        {"value": "ytd", "label": "YTD"},
                        {"value": "max", "label": "Max"}
                    ],
                    "description": "Historical data period (Yahoo Finance only)"
                },
                {
                    "name": "start_date",
                    "type": "string",
                    "title": "Start Date (optional)",
                    "default": "",
                    "placeholder": "YYYY-MM-DD",
                    "description": "Start date for custom range"
                },
                {
                    "name": "end_date",
                    "type": "string",
                    "title": "End Date (optional)",
                    "default": "",
                    "placeholder": "YYYY-MM-DD",
                    "description": "End date for custom range"
                },
                {
                    "name": "market_type",
                    "type": "select",
                    "title": "Market Type (Crypto Exchanges)",
                    "default": "spot",
                    "options": [
                        {"value": "spot", "label": "Spot"},
                        {"value": "futures", "label": "Futures"},
                        {"value": "options", "label": "Options"}
                    ],
                    "description": "Market type for Binance/Bybit"
                },
                {
                    "name": "limit",
                    "type": "number",
                    "title": "Record Limit",
                    "default": 500,
                    "minimum": 1,
                    "maximum": 10000,
                    "description": "Maximum number of candles to fetch"
                },
                {
                    "name": "fetch_balance_sheet",
                    "type": "boolean",
                    "title": "Fetch Balance Sheet",
                    "default": False,
                    "description": "Include balance sheet (Yahoo Finance only)"
                },
                {
                    "name": "fetch_cash_flow",
                    "type": "boolean",
                    "title": "Fetch Cash Flow",
                    "default": False,
                    "description": "Include cash flow statement (Yahoo Finance only)"
                },
                {
                    "name": "fetch_income_stmt",
                    "type": "boolean",
                    "title": "Fetch Income Statement",
                    "default": False,
                    "description": "Include income statement (Yahoo Finance only)"
                },
                {
                    "name": "indicators",
                    "type": "multi_select",
                    "title": "Technical Indicators (Alpha Vantage)",
                    "default": [],
                    "options": [
                        {"value": "SMA", "label": "Simple Moving Average (SMA)"},
                        {"value": "EMA", "label": "Exponential Moving Average (EMA)"},
                        {"value": "RSI", "label": "Relative Strength Index (RSI)"},
                        {"value": "MACD", "label": "MACD"},
                        {"value": "BBANDS", "label": "Bollinger Bands"},
                        {"value": "STOCH", "label": "Stochastic Oscillator"},
                        {"value": "ADX", "label": "Average Directional Index (ADX)"}
                    ],
                    "description": "Technical indicators to calculate"
                },
                {
                    "name": "indicator_interval",
                    "type": "select",
                    "title": "Indicator Interval",
                    "default": "daily",
                    "options": [
                        {"value": "1min", "label": "1 min"},
                        {"value": "5min", "label": "5 min"},
                        {"value": "15min", "label": "15 min"},
                        {"value": "30min", "label": "30 min"},
                        {"value": "60min", "label": "60 min"},
                        {"value": "daily", "label": "Daily"},
                        {"value": "weekly", "label": "Weekly"},
                        {"value": "monthly", "label": "Monthly"}
                    ],
                    "description": "Interval for technical indicators"
                },
                {
                    "name": "mt5_symbol_info",
                    "type": "boolean",
                    "title": "Fetch Symbol Info (MT5)",
                    "default": False,
                    "description": "Include detailed symbol information from MT5"
                },
                {
                    "name": "cache_ttl",
                    "type": "number",
                    "title": "Cache TTL (seconds)",
                    "default": 3600,
                    "minimum": 0,
                    "description": "How long to cache results (0 = no cache)"
                }
            ],
            "outputs": [
                {"name": "data", "type": "array", "description": "Price/candlestick data"},
                {"name": "latest_price", "type": "number", "description": "Latest price"},
                {"name": "info", "type": "object", "description": "Asset information (Yahoo Finance)"},
                {"name": "balance_sheet", "type": "array", "description": "Balance sheet data"},
                {"name": "cash_flow", "type": "array", "description": "Cash flow statement"},
                {"name": "income_stmt", "type": "array", "description": "Income statement"},
                {"name": "indicators", "type": "object", "description": "Technical indicators data"},
                {"name": "symbol_info", "type": "object", "description": "MT5 symbol information"},
                {"name": "funding_rate", "type": "number", "description": "Funding rate (Bybit futures)"}
            ]
        }