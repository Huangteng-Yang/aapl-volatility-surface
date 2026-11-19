import numpy as np
import pandas as pd

from scipy.stats import norm 
from scipy.optimize import brentq


def black_scholes_calculator(S0,K,T,r,q,sigma,option_type):
    '''
    Calculate option price with continuous dividend yield based on Black Scholes formula
    '''
    if (S0<=0) or (K<=0) or (T<=0):
        raise ValueError('Invalid market parameters')
    d1=(np.log(S0/K)+(r-q+0.5*sigma**2)*T)/(sigma*np.sqrt(T))
    d2=d1-sigma*np.sqrt(T)

    # Calculate
    if option_type=='call':
        c=S0*np.exp(-q*T)*norm.cdf(d1)-K*np.exp(-r*T)*norm.cdf(d2)
        return c
    elif option_type=='put':
        p=K*np.exp(-r*T)*norm.cdf(-d2)-S0*np.exp(-q*T)*norm.cdf(-d1)
        return p 
    else:
        raise ValueError('Invalid option type')


def implied_volatility_calculator(S0,K,T,r,q,price,option_type):
    if (S0<=0) or (K<=0) or (T<=0) or (price<=0) or not np.isfinite(price):
        return np.nan

    # Check price interval
    discount_S=S0*np.exp(-q*T)
    discount_K=K*np.exp(-r*T)
    if option_type=='call':
        lower=max(discount_S-discount_K,0)
        upper=discount_S
    elif option_type=='put':
        lower=max(discount_K-discount_S,0)
        upper=discount_K
    else:
        return np.nan

    if not (lower<price<upper):
        return np.nan 

    def objective(sigma):
        return black_scholes_calculator(S0,K,T,r,q,sigma,option_type)-price

    sigma_min=1e-6
    sigma_max=5

    if not objective(sigma_min)*objective(sigma_max)<0:
        return np.nan 

    try:
        return brentq(objective,sigma_min,sigma_max,xtol=1e-10)
    
    except ValueError:
        return np.nan 


def calculate_iv_surface(options,max_spread=0.3):
    df=options.copy()

    # Filter overfull spread price
    if max_spread is not None:
        df=df.loc[df['relative_spread']<=max_spread]

    df['iv_bs']=df.apply(
        lambda row:
        implied_volatility_calculator(
            row['S0'],
            row['strike'],
            row['T'],
            row['r'],
            row['q'],
            row['mid_price'],
            row['option_type']
        ),axis=1
    )

    # Check numerical results
    total=len(df)
    success=df['iv_bs'].notna().sum()

    print('Contracts after spread filtering:',total)
    print('Sucessful IV calculations:',success)
    print('Success rate:',f'{success/total:.2%}' if total else 'N/A')

    return df 

