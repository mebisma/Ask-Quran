from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from dataclasses import dataclass, asdict
from typing import Literal

zakat_bp = Blueprint('zakat', __name__)

# ──────────────────────────────────────────────
# ISLAMIC CONSTANTS (fixed by Sunnah)
# ──────────────────────────────────────────────
GOLD_NISAB_GRAMS   = 87.48
SILVER_NISAB_GRAMS = 612.36
TOLA_IN_GRAMS      = 11.664
ZAKAT_RATE         = 0.025
LUNAR_YEAR_DAYS    = 354

KARAT_PURITY = {
    "24k": 1.0,
    "22k": 22 / 24,
    "21k": 21 / 24,
    "18k": 18 / 24,
    "14k": 14 / 24,
}

DEFAULT_GOLD_RATE_PER_GRAM   = 40_981.0
DEFAULT_SILVER_RATE_PER_GRAM = 1_457.0


# ──────────────────────────────────────────────
# DATA CLASSES
# ──────────────────────────────────────────────

@dataclass
class MarketRates:
    gold_per_gram: float
    silver_per_gram: float


@dataclass
class CashAssets:
    cash_at_home: float = 0.0
    bank_balance: float = 0.0
    receivables: float  = 0.0
    savings: float      = 0.0
    debts_due: float    = 0.0


@dataclass
class GoldAssets:
    grams_24k: float = 0.0
    grams_22k: float = 0.0
    grams_21k: float = 0.0
    grams_18k: float = 0.0
    grams_14k: float = 0.0


@dataclass
class SilverAssets:
    grams: float = 0.0


@dataclass
class PropertyAssets:
    rental_income: float      = 0.0
    stocks_value: float       = 0.0
    business_inventory: float = 0.0
    other_investments: float  = 0.0


@dataclass
class ZakatResult:
    nisab_mode: str
    nisab_gold_pkr: float
    nisab_silver_pkr: float
    nisab_used_pkr: float
    net_cash: float
    gross_cash: float
    total_debts: float
    gold_pkr: float
    gold_grams_24k_equiv: float
    silver_pkr: float
    silver_grams: float
    property_pkr: float
    cash_at_home: float
    bank_balance: float
    receivables: float
    savings: float
    total_zakatable_wealth: float
    is_eligible: bool
    zakat_due: float
    per_month: float
    per_day: float
    shortfall: float
    notes: list


# ──────────────────────────────────────────────
# CALCULATION ENGINE
# ──────────────────────────────────────────────

def calculate_gold_value(gold: GoldAssets, gold_rate: float) -> tuple:
    grams_24k_equiv = (
        gold.grams_24k * KARAT_PURITY["24k"] +
        gold.grams_22k * KARAT_PURITY["22k"] +
        gold.grams_21k * KARAT_PURITY["21k"] +
        gold.grams_18k * KARAT_PURITY["18k"] +
        gold.grams_14k * KARAT_PURITY["14k"]
    )
    total_pkr = grams_24k_equiv * gold_rate
    return total_pkr, grams_24k_equiv


def calculate_nisab(rates: MarketRates) -> tuple:
    gold_nisab_pkr   = GOLD_NISAB_GRAMS   * rates.gold_per_gram
    silver_nisab_pkr = SILVER_NISAB_GRAMS * rates.silver_per_gram
    return gold_nisab_pkr, silver_nisab_pkr


def _generate_notes(gold, silver, cash, nisab_mode, net_cash, total_wealth, nisab_used) -> list:
    notes     = []
    has_gold   = (gold.grams_24k + gold.grams_22k + gold.grams_21k + gold.grams_18k + gold.grams_14k) > 0
    has_silver = silver.grams > 0
    has_cash   = net_cash > 0

    if nisab_mode == "gold" and (has_cash or has_silver):
        notes.append({
            "type": "warning",
            "text": ("You selected the gold nisab but hold mixed assets. "
                     "Most scholars agree the silver nisab should be used for mixed wealth.")
        })

    if has_gold:
        notes.append({
            "type": "info",
            "text": ("Gold jewellery: Zakat is due on ALL gold including women's jewellery "
                     "worn daily — Hanafi ruling followed widely in Pakistan.")
        })

    if has_silver and not has_cash and not has_gold and silver.grams < 612.36:
        notes.append({
            "type": "info",
            "text": (f"Your silver ({silver.grams:.2f}g) is below the silver nisab (612.36g). "
                     "No zakat on silver alone unless combined with other assets.")
        })

    if cash.debts_due > 0:
        notes.append({
            "type": "info",
            "text": (f"PKR {cash.debts_due:,.0f} in debts has been deducted from your cash. "
                     "Only deduct debts due within the current hawl year.")
        })

    notes.append({
        "type": "reminder",
        "text": ("Hawl: Zakat becomes obligatory only after your wealth has remained "
                 "above the nisab for one full lunar year (354 days).")
    })

    notes.append({
        "type": "reminder",
        "text": ("Many Muslims choose to pay Zakat in Ramadan for multiplied reward, "
                 "but it may be paid at any time after your hawl anniversary.")
    })

    return notes


def calculate_zakat(
    rates: MarketRates,
    cash: CashAssets,
    gold: GoldAssets,
    silver: SilverAssets,
    property: PropertyAssets,
    nisab_mode: Literal["silver", "gold"] = "silver"
) -> ZakatResult:

    gold_nisab_pkr, silver_nisab_pkr = calculate_nisab(rates)
    nisab_used = silver_nisab_pkr if nisab_mode == "silver" else gold_nisab_pkr

    gross_cash = cash.cash_at_home + cash.bank_balance + cash.receivables + cash.savings
    net_cash   = max(0.0, gross_cash - cash.debts_due)

    gold_pkr, gold_grams_24k_equiv = calculate_gold_value(gold, rates.gold_per_gram)
    silver_pkr   = silver.grams * rates.silver_per_gram
    property_pkr = (
        property.rental_income +
        property.stocks_value +
        property.business_inventory +
        property.other_investments
    )

    total_wealth = net_cash + gold_pkr + silver_pkr + property_pkr
    is_eligible  = total_wealth >= nisab_used
    zakat_due    = round(total_wealth * ZAKAT_RATE, 2) if is_eligible else 0.0
    per_month    = round(zakat_due / 12, 2)
    per_day      = round(zakat_due / LUNAR_YEAR_DAYS, 2)
    shortfall    = max(0.0, nisab_used - total_wealth)
    notes        = _generate_notes(gold, silver, cash, nisab_mode, net_cash, total_wealth, nisab_used)

    return ZakatResult(
        nisab_mode=nisab_mode,
        nisab_gold_pkr=round(gold_nisab_pkr, 2),
        nisab_silver_pkr=round(silver_nisab_pkr, 2),
        nisab_used_pkr=round(nisab_used, 2),
        net_cash=round(net_cash, 2),
        gross_cash=round(gross_cash, 2),
        total_debts=round(cash.debts_due, 2),
        gold_pkr=round(gold_pkr, 2),
        gold_grams_24k_equiv=round(gold_grams_24k_equiv, 4),
        silver_pkr=round(silver_pkr, 2),
        silver_grams=round(silver.grams, 4),
        property_pkr=round(property_pkr, 2),
        cash_at_home=round(cash.cash_at_home, 2),
        bank_balance=round(cash.bank_balance, 2),
        receivables=round(cash.receivables, 2),
        savings=round(cash.savings, 2),
        total_zakatable_wealth=round(total_wealth, 2),
        is_eligible=is_eligible,
        zakat_due=zakat_due,
        per_month=per_month,
        per_day=per_day,
        shortfall=round(shortfall, 2),
        notes=notes,
    )


# ──────────────────────────────────────────────
# HELPERS
# ──────────────────────────────────────────────

def _f(data, key, default=0.0) -> float:
    try:
        return float(data.get(key, default) or 0)
    except (ValueError, TypeError):
        return default


def parse_request_data(data: dict) -> tuple:
    rates = MarketRates(
        gold_per_gram=_f(data, "gold_rate", DEFAULT_GOLD_RATE_PER_GRAM),
        silver_per_gram=_f(data, "silver_rate", DEFAULT_SILVER_RATE_PER_GRAM),
    )
    cash = CashAssets(
        cash_at_home=_f(data, "cash_home"),
        bank_balance=_f(data, "cash_bank"),
        receivables=_f(data, "cash_recv"),
        savings=_f(data, "cash_savings"),
        debts_due=_f(data, "cash_debt"),
    )
    gold = GoldAssets(
        grams_24k=_f(data, "gold_24k"),
        grams_22k=_f(data, "gold_22k"),
        grams_21k=_f(data, "gold_21k"),
        grams_18k=_f(data, "gold_18k"),
        grams_14k=_f(data, "gold_14k"),
    )
    silver    = SilverAssets(grams=_f(data, "silver_grams"))
    prop      = PropertyAssets(
        rental_income=_f(data, "prop_rent"),
        stocks_value=_f(data, "prop_stocks"),
        business_inventory=_f(data, "prop_biz"),
        other_investments=_f(data, "prop_other"),
    )
    nisab_mode = data.get("nisab_mode", "silver")
    if nisab_mode not in ("silver", "gold"):
        nisab_mode = "silver"
    return rates, cash, gold, silver, prop, nisab_mode


# ──────────────────────────────────────────────
# ROUTES
# ──────────────────────────────────────────────

@zakat_bp.route('/calculate', methods=['POST'])
@jwt_required()
def calculate():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided.'}), 400
    try:
        rates, cash, gold, silver, prop, nisab_mode = parse_request_data(data)
        result = calculate_zakat(rates, cash, gold, silver, prop, nisab_mode)
        return jsonify({'success': True, 'result': asdict(result)}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@zakat_bp.route('/nisab', methods=['GET'])
@jwt_required()
def nisab_values():
    gold_rate   = float(request.args.get("gold_rate",   DEFAULT_GOLD_RATE_PER_GRAM))
    silver_rate = float(request.args.get("silver_rate", DEFAULT_SILVER_RATE_PER_GRAM))
    rates       = MarketRates(gold_per_gram=gold_rate, silver_per_gram=silver_rate)
    gold_nisab, silver_nisab = calculate_nisab(rates)
    return jsonify({
        "gold_nisab_pkr":     round(gold_nisab, 2),
        "silver_nisab_pkr":   round(silver_nisab, 2),
        "gold_nisab_grams":   GOLD_NISAB_GRAMS,
        "silver_nisab_grams": SILVER_NISAB_GRAMS,
        "gold_nisab_tola":    round(GOLD_NISAB_GRAMS   / TOLA_IN_GRAMS, 4),
        "silver_nisab_tola":  round(SILVER_NISAB_GRAMS / TOLA_IN_GRAMS, 4),
    }), 200


@zakat_bp.route('/convert/tola-to-grams', methods=['GET'])
@jwt_required()
def tola_to_grams():
    tola = float(request.args.get("tola", 0))
    return jsonify({"grams": round(tola * TOLA_IN_GRAMS, 4)}), 200


@zakat_bp.route('/convert/grams-to-tola', methods=['GET'])
@jwt_required()
def grams_to_tola():
    grams = float(request.args.get("grams", 0))
    return jsonify({"tola": round(grams / TOLA_IN_GRAMS, 4)}), 200


@zakat_bp.route('/rates/default', methods=['GET'])
def default_rates():
    return jsonify({
        "gold_per_gram":   DEFAULT_GOLD_RATE_PER_GRAM,
        "silver_per_gram": DEFAULT_SILVER_RATE_PER_GRAM,
        "currency":        "PKR",
        "source":          "Pakistan sarafa bazar (May 2026)",
        "gold_karat":      "24K",
        "tola_in_grams":   TOLA_IN_GRAMS,
    }), 200