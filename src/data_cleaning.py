import numpy as np
import pandas as pd

def clean_option_data(options,rate_table,S0,q):
    '''
    Clean AAPL option data and prepare it for implied volatility calculation.
    
    Parameters
    --------------
    options: DataFrame of option data
    rate_table: DataFrame of risk free rate with different lifespan T
    S0: float, current underlying stock price
    q: float, continous dividend yield
    ---------------
    return: DataFrame, DataFrame
        processed option data, otm option data
    '''

    df=options.copy()

    # Step 1
    # Convert data types
    df['expiration']=pd.to_datetime(df['expiration'],errors='coerce').dt.strftime('%Y-%m-%d')
    df['option_type']=df['option_type'].str.lower().str.strip()
    
    numeric_columns=[
        'strike','bid','ask','volume','openInterest','impliedVolatility'
    ]
    for column in numeric_columns:
        df[column]=pd.to_numeric(df[column],errors='coerce')

    # Remove missing essential values
    df=df.dropna(subset=['strike','bid','ask','expiration','option_type'])

    # Remove duplicated contracts
    df=df.drop_duplicates(subset='contractSymbol',keep='last')

    # Keep only call and put
    df=df.loc[df['option_type'].isin(['call','put'])].copy()
    

    # Step 2
    # Filter valid strike, bid and ask 
    df=df.loc[(df['strike']>0) & (df['bid']>0) & (df['ask']>=df['bid'])].copy()

    # Calculate valid spread price
    df['mid_price']=(df['bid']+df['ask'])/2
    df['spread_price']=df['ask']-df['bid']
    df['relative_spread']=df['spread_price']/df['mid_price']
    

    # Rename yahoo's implied volatility
    df=df.rename(
        columns={'impliedVolatility':'iv_yahoo'}
    )


    # Step 3
    # Merge r, T
    rate=rate_table[['expiration','T','r']].copy()
    rate['expiration']=pd.to_datetime(rate['expiration'],errors='coerce').dt.strftime('%Y-%m-%d')
        

    df=df.merge(rate,on='expiration',how='left')
    df=df.dropna(subset=['r','T'])

    # Step 4
    df['S0']=S0
    df['q']=q

    # Calculate forward price F_T and moneyness
    df['forward_price']=S0*np.exp((df['r']-q)*df['T'])
    df['moneyness']=df['strike']/df['forward_price']
    df['log_moneyness']=np.log(df['moneyness'])

    # Step 5
    # Select otm options: call: K>=F_T; put: K<F_T
    selected_set=(
        ((df['option_type']=='call')& (df['strike']>=df['forward_price']))
        |
        ((df['option_type']=='put')& (df['strike']<df['forward_price']))
    )
    otm_option=df.loc[selected_set].copy()

    return df,otm_option
