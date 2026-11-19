"""
data_loader.py
Download AAPL option-chain data for the volatility smile / surface project.

Run from the project, or import the functions in experiments.ipynb.
"""

from pathlib import Path 
import yfinance as yf
import numpy as np
import pandas as pd


# Project folders
PROJECT_DIR=Path.cwd()
RAW_DATA_DIR=PROJECT_DIR/'data'/'raw'
RAW_DATA_DIR.mkdir(parents=True,exist_ok=True)

# Basic project settings
SYMBOL='AAPL'

SELECTED_EXPIRATIONS=[
    '2026-11-27',
    '2026-12-04',
    '2026-12-11',
    '2026-12-18',
    '2027-01-15',
    '2027-02-19',
    '2027-03-19',
    '2027-04-16',
    '2027-06-17',
    '2027-09-17',
    '2027-12-17',
    '2028-01-21',
    '2028-03-17',
    '2028-06-16',
    '2028-12-15',
    '2029-01-19',
]


def download_option_data(proxy=None):
    """
    Download Calls and Puts for the selected expiration dates.

    Return a DataFrame with one row per option contract and saves it to 
    data/raw/AAPL.options.csv.

    If your network needs Clash, pass proxy='http://127.0.0.1:7897'.
    """
    if proxy is not None:
        yf.config.network.proxy=proxy 

    ticker=yf.Ticker(SYMBOL)
    available_expirations=ticker.options 

    all_options=[]
    download_time=pd.Timestamp.now(tz='UTC')

    for expiration in SELECTED_EXPIRATIONS:
        if expiration not in available_expirations:
            print(f'Skip unavailable expiration: {expiration}')
            continue 

        chain=ticker.option_chain(expiration)

        calls=chain.calls.copy()
        calls['expiration']=expiration
        calls['option_type']='call'

        puts=chain.puts.copy()
        puts['expiration']=expiration
        puts['option_type']='put'

        all_options.extend([calls,puts])

    if not all_options:
        raise ValueError('No option data were downloaded.')

    options=pd.concat(all_options,ignore_index=True)
    options['download_at']=download_time

    file_path=RAW_DATA_DIR/f'{SYMBOL}_options.csv'
    options.to_csv(file_path,index=False)

    print(f'Download {len(options)} option contracts.')
    print(f'Saved to: {file_path}')

    return options


def get_market_parameters(S0=342.37,annual_dividend=1.08):
    """
    Return the underlying price and continuous dividend-yield approximation.

    For the 2026-11-06 data snapshot:
        S0=342.37
        annual_dividend=1.08

    q is the approximated by annual_dividend / S0.
    The risk-free rate r is selected seperately from Treasury data.
    """

    q=annual_dividend / S0

    return {
        'S0':S0,
        'annual_dividend':annual_dividend,
        'q':q,
    }


def get_risk_free_rate(
        treasury_file,expirations,valuation_date
):
    """
    Calculate risk-free rates for different option maturities.

    Parameters
    ----------------------
    treasury_file: str
        Path to the Treasury yield CSV file.

    expirations: list
        Option expiration dates.

    valuation_date: str
        Valuation date, e.g. '2026-11-06'.

    Returns
    --------------
    DataFrame containing expiration, T, and r.
    """

    # Read Treasury data
    treasury=pd.read_csv(treasury_file)

    # Select the Treasury curve on valuation_date

    treasury['Date']=pd.to_datetime(treasury['Date'])

    date=pd.Timestamp(valuation_date)

    row=treasury.loc[treasury['Date']==date].iloc[0]

    # Treasury maturity nodes (in years)
    tenors={
        '1 Mo': 1/12,
        '1.5 Month': 1.5/12,
        '2 Mo': 2/12,
        '3 Mo': 3/12,
        '4 Mo': 4/12,
        '6 Mo': 6/12,
        '1 Yr': 1.0,
        '2 Yr': 2.0,
        '3 Yr': 3.0
    }

    # Convert Treasury yields into continous rates
    T_nodes=[]
    r_nodes=[]

    for column,T_node in tenors.items():
        y=row[column]/100
        r=2*np.log(1+y/2)

        T_nodes.append(T_node)
        r_nodes.append(r)

    # Calculate rates for each expiration

    results=[]
    for expiration in expirations:
        days=(pd.Timestamp(expiration)-date).days 

        T=days/365

        # Linear interpolation
        r=np.interp(T,T_nodes,r_nodes)

        results.append({
            'expiration':expiration,
            'days':days,
            'T':T,
            'r':r
        })

    return pd.DataFrame(results)



if __name__=='__main__':
    options=download_option_data()
    market_parameters=get_market_parameters()
    print(market_parameters)