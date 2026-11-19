# AAPL Implied Volatility Surface

A Python learning project that builds and visualizes an approximate implied-volatility surface from AAPL option-chain quotes. The workflow covers option-data cleaning, Black–Scholes implied-volatility inversion, equity volatility skew, ATM-forward term structure, bid–ask spread sensitivity, and a linearly interpolated 3D surface.

This project is part of my preparation for **quantitative research (QR)**. My academic background is in applied analysis and PDEs, and this project is intended to connect mathematical modeling and numerical analysis with practical financial data. It is a research-oriented learning project, not a production pricing or trading system.

## Project questions

1. How does AAPL implied volatility vary with log-moneyness at a fixed maturity?
2. Does the option chain exhibit the negative skew commonly observed in equity options?
3. How does ATM-forward implied volatility vary with time to maturity?
4. How sensitive are the results to the bid–ask relative-spread filter?
5. How can the observed smiles be combined into a 3D implied-volatility surface?

## Dataset and market inputs

- **Underlying:** Apple Inc. (AAPL)
- **Option-chain snapshot:** 2026-11-06
- **Expirations:** 16 dates, from 21 to 805 calendar days after the valuation date
- **Original option contracts:** 2,152
- **Contracts after basic cleaning:** 1,945
- **OTM contracts before spread filtering:** 984
- **Stock reference price:** \(S_0=\$342.37\), consistent with Yahoo Finance's regular-market price and the 2026-11-06 15:59 one-minute close (approximately \$342.365)
- **Continuous dividend yield:** \(q=0.00315\), based on an assumed annual dividend of \$1.08
- **Risk-free rates:** maturity-dependent estimates derived from the daily U.S. Treasury yield data

The project uses option bid and ask quotes to calculate the midpoint:

\[
P_{\mathrm{mid}}=\frac{\mathrm{bid}+\mathrm{ask}}{2}.
\]

The relative bid–ask spread is defined as:

\[
\mathrm{RelativeSpread}
=\frac{\mathrm{ask}-\mathrm{bid}}{P_{\mathrm{mid}}}.
\]

The main plots use a **20% relative-spread threshold**. This is a practical choice for balancing quote filtering and data coverage, not a universal optimal threshold.

## Methodology

### 1. Data cleaning and forward moneyness

The cleaning module removes invalid or unusable quotes, calculates midpoint prices and relative spreads, attaches maturity-dependent risk-free rates, and constructs approximate forward prices and log-moneyness:

\[
F_T=S_0e^{(r-q)T},
\qquad
k=\ln\left(\frac{K}{F_T}\right).
\]

For the smile analysis, the OTM sample consists of puts with \(k<0\) and calls with \(k\geq 0\).

### 2. Black–Scholes implied volatility

For each eligible option, implied volatility is obtained by solving:

\[
V_{\mathrm{BS}}(S_0,K,T,r,q,\sigma_{\mathrm{IV}})
=P_{\mathrm{mid}}.
\]

The implementation uses `scipy.optimize.brentq` and checks price bounds before root finding. Both calls and puts are supported.

### 3. Volatility smile

For each expiration, plot implied volatility against log-moneyness. OTM puts and OTM calls are shown separately, with \(k=0\) marking the ATM-forward reference.

### 4. ATM-forward term structure

For each expiration, estimate \(\sigma_{\mathrm{IV}}(k=0,T)\) by linear interpolation between nearby observations that bracket \(k=0\). No extrapolation is used when the available observations do not cover the target moneyness.

### 5. 3D implied-volatility surface

Construct a regular \((k,T)\) grid and interpolate the irregularly spaced IV observations using:

```python
scipy.interpolate.griddata(..., method="linear")
```

The original aggregated observations are plotted together with the interpolated surface. Linear interpolation is used for visualization; the result is not constrained to be arbitrage-free.

## Results

### Data and IV inversion

| Stage | Number of contracts |
|---|---:|
| Original option chain | 2,152 |
| After basic cleaning | 1,945 |
| OTM contracts before spread filter | 984 |
| All cleaned contracts passing 30% spread filter | 1,545 |
| Successful IV solutions among those contracts | 1,521 |
| IV success rate for the filtered cleaned sample | 98.45% |
| OTM contracts passing 30% spread filter | 584 |
| Successful OTM IV solutions | 584 (100%) |

The main plots use the OTM sample with a 20% spread limit, retaining **500 observations**.

### Main findings

- **Equity skew:** Most expirations show a negative skew: lower-log-moneyness OTM puts generally have higher IV than higher-log-moneyness OTM calls.
- **ATM-forward term structure:** The estimated ATM IV is approximately **26.09%** at 21 days, reaches a local low of approximately **25.76%** at 70 days, and generally rises to approximately **28.83%** at 805 days. The curve is not monotonic and has local fluctuations.
- **Spread sensitivity:** The OTM sample contains 344, 434, 500, and 584 contracts under 10%, 15%, 20%, and 30% spread limits, respectively. The ATM-forward term structures under 15%, 20%, and 30% are identical for most expirations. For 2026-12-11, the estimate is approximately 25.65% under 15%, compared with approximately 25.86% under 20% and 30%.
- **3D surface:** The interpolated surface visualizes the joint dependence of IV on log-moneyness and maturity. Local facets and sharp features can reflect uneven quote coverage and the piecewise-linear interpolation method.

These are descriptive findings from one option-chain snapshot, not trading signals or forecasts of realized volatility.

## Repository structure

```text
volatility-surface/
├── data/
│   ├── raw/                     # Saved AAPL option and Treasury snapshots
│   └── processed/               # Cleaned and OTM option datasets
├── src/
│   ├── data_loader.py           # Option data, market inputs, Treasury rates
│   ├── data_cleaning.py         # Quote filters, forward and log-moneyness
│   ├── implied_volatility.py    # Black–Scholes pricing and IV inversion
│   └── volatility_surface.py   # Smile, term structure, and 3D plots
├── figures/
│   ├── volatility_smile.png
│   ├── term_structure.png
│   └── volatility_surface.png
├── experiments.ipynb
├── requirements.txt
├── .gitignore
└── README.md
```

## Setup and usage

Run commands from the repository root.

### 1. Create and activate a virtual environment

Windows PowerShell:

```bash
python -m venv .venv
.venv\Scripts\Activate.ps1
```

macOS / Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install dependencies

```bash
python -m pip install -r requirements.txt
```

### 3. Prepare the data

The experiment notebook expects the following snapshot files under `data/raw/`:

- `AAPL_options_20261106.csv`
- `daily-treasury-rates_20261106.csv`

The notebook derives `risk_free_rate_20261106.csv` from the Treasury data and writes cleaned datasets under `data/processed/`.

The option-download cell is disabled by default because the historical snapshot has already been saved. To refresh the data, enable the relevant download cell and update the valuation date and filenames consistently.

### 4. Run the notebook

```bash
jupyter lab
```

Open `experiments.ipynb` and run the cells from top to bottom.

## Dependencies

The main third-party dependencies are:

- NumPy
- pandas
- SciPy
- Matplotlib
- yfinance
- JupyterLab

Python standard-library modules such as `pathlib`, `math`, and `datetime` do not need to be listed in `requirements.txt`.

## Assumptions and limitations

1. **American versus European exercise:** Listed AAPL equity options are American-style, while the IV calculation uses the European Black–Scholes formula as an approximation. Early exercise is not modeled.
2. **Dividend approximation:** The experiment uses a constant continuous dividend yield \(q=0.00315\), based on an assumed annual dividend of \$1.08, rather than explicitly modeling each discrete dividend payment.
3. **Risk-free rates:** The maturity-dependent inputs are derived from Treasury par yields and are not a bootstrapped zero-coupon spot curve. For the 21- and 28-day maturities, which are shorter than the shortest available Treasury tenor, the current interpolation routine uses the first tenor's rate.
4. **Quote synchronization:** The selected stock reference price agrees closely with the 2026-11-06 15:59 stock close, but the data source does not provide a reliable per-contract timestamp for every option bid and ask. Exact stock/option quote synchronization cannot be guaranteed.
5. **Liquidity and filtering:** A successful numerical IV solution does not imply that the quote is liquid or reliable. Relative-spread filtering reduces, but does not eliminate, noisy observations.
6. **Interpolation:** The 3D surface is a piecewise-linear visualization of observed IVs. It is not an arbitrage-free calibration and should not be interpreted as a complete pricing model.

## Possible extensions

- Compare term structures at fixed log-moneyness values such as \(k=-0.05, 0, 0.05\).
- Add a 2D heatmap and a plot of observation density.
- Compare call and put IVs at matched strikes and maturities.
- Compare surfaces across multiple consistently timestamped trading-day snapshots.
- Explore SVI or other arbitrage-aware parameterizations after validating the data and basic interpolation results.

## Learning takeaway

This project connects mathematical finance, numerical root finding, data cleaning, and visualization. The central practical lesson is that **a numerically successful IV inversion is not automatically a reliable market estimate**: quote quality, timestamps, model assumptions, and observation coverage all matter when constructing and interpreting an implied-volatility surface.
