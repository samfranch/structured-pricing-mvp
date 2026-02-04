# Structured Pricing MVP

MVP pedagogique pour pricer :
- obligation zero-coupon,
- call europeen,
- put europeen,
- autocall simplifie.

L'application permet aussi :
- la saisie manuelle des parametres de marche,
- le chargement automatique du spot/volatilite via Yahoo Finance (`yfinance`),
- l'affichage de profils de payoff.
- Décomposition pédagogique du prix des options vanilles :
  - **Valeur intrinsèque**
  - **Valeur temps**
- Formules affichées en cohérence avec Black-Scholes :
  - Call : `max(S0 - K, 0)` ; `Valeur temps = Prix call - Valeur intrinsèque`
  - Put : `max(K - S0, 0)` ; `Valeur temps = Prix put - Valeur intrinsèque`
- UX améliorée :
  - Produit par défaut : **Option Call européenne**
  - Chargement des données marché via Yahoo Finance (spot + volatilité estimée)
  - Graphiques de payoff pour Call, Put et Autocall simplifié

## Lancer le projet

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## Structure

- `app.py` : interface utilisateur Streamlit.
- `structured_pricing/black_scholes.py` : briques Black-Scholes (d1, d2, call, put, digital call).
- `structured_pricing/bonds.py` : zero-coupon.
- `structured_pricing/products.py` : autocall simplifie.
- `structured_pricing/market_data.py` : recuperation de spot/volatilite depuis Yahoo Finance.

## Note

Ce projet est volontairement simplifie pour un usage de comprehension/theorie.
