import pandas as pd
import streamlit as st

from structured_pricing.black_scholes import price_call_bs, price_digital_call_bs, price_put_bs
from structured_pricing.bonds import zero_coupon_price
from structured_pricing.market_data import fetch_market_snapshot
from structured_pricing.products import price_autocall_simplified


st.set_page_config(page_title="Structured Pricing MVP", page_icon="📈", layout="centered")

st.title("Moteur simplifié de pricing")
st.caption("Black-Scholes + décomposition des payoffs")

if "spot" not in st.session_state:
    st.session_state.spot = 100.0
if "rate" not in st.session_state:
    st.session_state.rate = 0.02
if "volatility" not in st.session_state:
    st.session_state.volatility = 0.20
if "maturity" not in st.session_state:
    st.session_state.maturity = 1.0

st.subheader("Données de marché")
data_mode = st.radio(
    "Source",
    ("Saisie manuelle", "Yahoo Finance (auto)"),
    horizontal=True,
)
if data_mode == "Yahoo Finance (auto)":
    col_ticker, col_days, col_fetch = st.columns([2, 1, 1])
    with col_ticker:
        ticker = st.text_input("Ticker", value="AAPL")
    with col_days:
        lookback_days = st.number_input("Jours histo", min_value=30, value=252, step=21)
    with col_fetch:
        st.write("")
        if st.button("Charger", use_container_width=True):
            try:
                snapshot = fetch_market_snapshot(ticker=ticker, lookback_days=lookback_days)
                st.session_state.spot = snapshot.spot
                st.session_state.volatility = snapshot.annualized_volatility
                st.success(
                    f"{snapshot.ticker} charge: spot={snapshot.spot:.4f}, sigma={snapshot.annualized_volatility:.4f}"
                )
            except Exception as exc:
                st.error(f"Erreur de chargement: {exc}")

product = st.selectbox(
    "Que voulez-vous pricer ?",
    (
        "Obligation zéro-coupon",
        "Option Call européenne",
        "Option Put européenne",
        "Autocall simplifié",
    ),
)

st.subheader("Paramètres de marche")
spot = st.number_input("Spot (S0)", min_value=0.0001, step=1.0, key="spot")
rate = st.number_input("Taux sans risque r (ex: 0.02)", step=0.005, format="%.4f", key="rate")
volatility = st.number_input("Volatilité sigma (ex: 0.20)", min_value=0.0001, step=0.01, format="%.4f", key="volatility")
maturity = st.number_input("maturité T (années)", min_value=0.0001, step=0.25, format="%.4f", key="maturity")

result = None

if product == "Obligation zéro-coupon":
    if st.button("Calculer le prix"):
        result = zero_coupon_price(rate=rate, maturity=maturity)
        st.success(f"Prix théorique (par nominal 1): {result:.6f}")
        st.info("Interprétation: coût aujourd'hui d'un paiement certain de 1 a maturité.")

elif product == "Option Call européenne":
    strike = st.number_input("Strike K", min_value=0.0001, value=100.0, step=1.0)
    if st.button("Calculer le prix"):
        result = price_call_bs(
            spot=spot,
            strike=strike,
            rate=rate,
            volatility=volatility,
            maturity=maturity,
        )
        st.success(f"Prix théorique du call: {result:.6f}")
        st.info("Décomposition payoff: max(S_T - K, 0).")

        st.markdown("**Profil de payoff a maturité**")
        prices = [0.5 * spot + i * (spot / 15.0) for i in range(31)]
        payoffs = [max(p - strike, 0.0) for p in prices]
        chart_df = pd.DataFrame({"S_T": prices, "Payoff": payoffs})
        st.line_chart(chart_df, x="S_T", y="Payoff", use_container_width=True)

elif product == "Option Put européenne":
    strike = st.number_input("Strike K", min_value=0.0001, value=100.0, step=1.0)
    if st.button("Calculer le prix"):
        result = price_put_bs(
            spot=spot,
            strike=strike,
            rate=rate,
            volatility=volatility,
            maturity=maturity,
        )
        st.success(f"Prix théorique du put: {result:.6f}")
        st.info("Decomposition payoff: max(K - S_T, 0).")

        st.markdown("**Profil de payoff a maturité**")
        prices = [0.5 * spot + i * (spot / 15.0) for i in range(31)]
        payoffs = [max(strike - p, 0.0) for p in prices]
        chart_df = pd.DataFrame({"S_T": prices, "Payoff": payoffs})
        st.line_chart(chart_df, x="S_T", y="Payoff", use_container_width=True)

elif product == "Autocall simplifie":
    strike_call = st.number_input("Barriere haute / strike call", min_value=0.0001, value=105.0, step=1.0)
    strike_put = st.number_input("Barriere basse / strike put", min_value=0.0001, value=80.0, step=1.0)
    coupon_rate = st.number_input("Coupon (ex: 0.08 pour 8%)", min_value=0.0, value=0.08, step=0.01, format="%.4f")
    nominal = st.number_input("Nominal", min_value=0.01, value=100.0, step=10.0)

    if st.button("Calculer le prix"):
        result = price_autocall_simplified(
            spot=spot,
            strike_call=strike_call,
            strike_put=strike_put,
            rate=rate,
            volatility=volatility,
            maturity=maturity,
            coupon_rate=coupon_rate,
            nominal=nominal,
        )
        st.success(f"Prix théorique de l'autocall simplifié: {result:.6f}")

        zc_value = nominal * zero_coupon_price(rate=rate, maturity=maturity)
        digital_call_value = price_digital_call_bs(
            spot=spot,
            strike=strike_call,
            rate=rate,
            volatility=volatility,
            maturity=maturity,
            payoff=nominal * coupon_rate,
        )
        put_sold_cost = price_put_bs(
            spot=spot,
            strike=strike_put,
            rate=rate,
            volatility=volatility,
            maturity=maturity,
        )
        st.markdown("**Decomposition du prix**")
        col1, col2, col3 = st.columns(3)
        col1.metric("Composante ZC", f"{zc_value:.4f}")
        col2.metric("Digitale call", f"{digital_call_value:.4f}")
        col3.metric("Put vendue", f"-{put_sold_cost:.4f}")

        st.markdown("**Profil de payoff simplifié a maturité**")
        prices = [0.5 * spot + i * (spot / 15.0) for i in range(31)]
        payoffs = []
        for p in prices:
            if p >= strike_call:
                payoffs.append(nominal * (1.0 + coupon_rate))
            elif p >= strike_put:
                payoffs.append(nominal)
            else:
                payoffs.append(nominal * (p / spot))
        chart_df = pd.DataFrame({"S_T": prices, "Payoff": payoffs})
        st.line_chart(chart_df, x="S_T", y="Payoff", use_container_width=True)

st.divider()
st.markdown(
    "Cette interface est un MVP pédagogique. Les résultats sont théoriques et bases sur des hypothèses simplificatrices."
)
