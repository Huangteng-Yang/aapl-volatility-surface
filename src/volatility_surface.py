import numpy as np 
import pandas as pd
import matplotlib.pyplot as plt

from scipy.interpolate import griddata
from math import ceil 


#========================
# 1. Prepare data
#========================

def prepare_surface_data(df,spread_limit=0.15,iv_col='iv_bs',otm_only=True):
    '''
    Prepare option data for volatility surface analysis.
    -------------------
    spread_limit: float or None
        Maximum relative bis-ask spread. None means no spread filtering

    iv_col: str
        Implied volatility column.

    Returns: DataFrame
        Filtered option data.
    '''
    df=df.copy()

    # Filter bid-ask spread
    if spread_limit is not None:
        df=df[df['relative_spread']<=spread_limit].copy()

    # Remove invalid IV observations
    df=df.dropna(subset=['log_moneyness','T',iv_col])
    df=df[df[iv_col]>0].copy()

    # Select OTM options
    if otm_only:
        otm_mask=(
            ((df['option_type']=='call') & (df['log_moneyness']>=0))|
            ((df['option_type']=='put') &  (df['log_moneyness']<0))
        )

        df=df.loc[otm_mask].copy()

    return df 


#========================
# 2. Plot Volatility Smile
#========================

def plot_smile(df,spread_limit=0.15,iv_col='iv_bs',otm_only=True):
    '''
    Plot volatility smile for different expiration dates.

    X-axis: Log_moneyness
    Y_axis: Implied volatility
    '''

    data=prepare_surface_data(df,spread_limit=spread_limit,iv_col=iv_col,otm_only=otm_only)

    expirations=sorted(data['expiration'].unique())

    n=len(expirations)
    ncols=min(4,n)
    nrows=ceil(n/ncols)

    fig,axes=plt.subplots(
        nrows,ncols,figsize=(4*ncols,4*nrows),sharey=True,squeeze=False
    )

    for ax,expiration in zip(axes.flat,expirations):
        subset=data[data['expiration']==expiration]

        # Plot call and Put separately
        for option_type,group in subset.groupby('option_type'):
            ax.scatter(group['log_moneyness'],group[iv_col],label=option_type,s=30)

        # ATM-forward reference
        ax.axvline(0,linestyle='--',linewidth=1)

        ax.set_title(str(expiration))
        ax.set_xlabel('Log_moneyness')
        ax.grid(alpha=0.3)
        ax.legend()

    # Hide unused subplots
    for ax in list(axes.flat)[n:]:
        ax.set_visible(False)

    for i in range(nrows):
        axes[i,0].set_ylabel('Implied Volatility')

    fig.suptitle('AAPL Implied Volatility Smile',fontsize=14)

    fig.tight_layout()

    return fig,axes 

#========================
# 3. Plot Volatility Term Structure
#========================

def plot_term_structure(df,target_k=0,spread_limit=0.15,iv_col='iv_bs',otm_only=True):
    '''
    Calculate and plot volatility term structure at a fixed log-moneyness.

    Default target_k=0 means ATM-forward.
    '''

    data=prepare_surface_data(df,spread_limit=spread_limit,iv_col=iv_col,otm_only=otm_only)

    results=[]

    for expiration,group in data.groupby('expiration'):

        # Combine duplicated moneyness observations
        curve=(
            group.groupby('log_moneyness')[iv_col].median().reset_index().sort_values('log_moneyness')
        )

        x=curve['log_moneyness'].to_numpy()
        y=curve[iv_col].to_numpy()

        # Avoid extrapolation
        if target_k<x.min() or target_k>x.max():
            atm_iv=np.nan 
        else:
            atm_iv=np.interp(target_k,x,y)

        results.append({
            'expiration':expiration,
            'T':group['T'].median(),
            'implied_volatility':atm_iv
        })

    term_structure=pd.DataFrame(results)

    term_structure=term_structure.sort_values('T').dropna(subset=['implied_volatility'])

    fig,ax=plt.subplots(figsize=(9,5))

    ax.plot(term_structure['T'],term_structure['implied_volatility'],marker='o')

    ax.set_xlabel('Time to Maturity (Years)')
    ax.set_ylabel('Implied volatility')

    ax.set_title(f'Volatility Term Structure (k={target_k})')

    ax.grid(alpha=0.3)

    fig.tight_layout()

    return fig,ax,term_structure

#========================
# 4. Plot Volatility Surface 
#========================

def plot_volatility_surface(df,spread_limit=0.15,iv_col='iv_bs',otm_only=True,grid_size=60):
    """
    Interpolate and plot 3D implied Volatility surface.

    X-axis: Log-moneyness
    Y-axis: Time to maturity
    Z-axis: Implied Volatility

    Linear interpolation is used. No extrapolation outside the data convex hull.
    """

    data=prepare_surface_data(
        df,spread_limit=spread_limit,iv_col=iv_col,otm_only=otm_only
    )

    # Combine duplicate coordinate
    points_data=data.groupby(['log_moneyness','T'],as_index=False)[iv_col].median()

    k=points_data['log_moneyness'].to_numpy()
    T=points_data['T'].to_numpy()
    iv=points_data[iv_col].to_numpy()

    if len(points_data)<3:
        raise ValueError('Not enough observations for 3D interpolation.')

    # Construct regular grid
    k_grid=np.linspace(k.min(),k.max(),grid_size)
    T_grid=np.linspace(T.min(),T.max(),grid_size)

    K_mesh,T_mesh=np.meshgrid(k_grid,T_grid)

    #  Interpolate IV on the regular grid 
    IV_mesh=griddata(points=(k,T),values=iv,xi=(K_mesh,T_mesh),method='linear')

    if np.all(np.isnan(IV_mesh)):
        raise ValueError(
    'Surface interpolation failed. '
    'Check the distribution of observations.'
)

    # Create 3D figure
    fig=plt.figure(figsize=(11,8))

    ax=fig.add_subplot(111,projection='3d')

    # Draw surface
    surface=ax.plot_surface(K_mesh,T_mesh,IV_mesh,cmap='viridis',alpha=0.85,linewidth=0)

    # Show original market observations
    ax.scatter(k,T,iv,color='red',s=10,label='Aggregated observations')

    ax.set_xlabel('Log-moneyness (k)')
    ax.set_ylabel('Time to Maturity (T)')
    ax.set_zlabel('Implied Volatility')
    ax.set_title('AAPL Implied Volatility Surface')

    ax.view_init(elev=25,azim=-135)

    fig.colorbar(surface,ax=ax,shrink=0.65,label='Implied Volatility')

    ax.legend()

    fig.tight_layout()

    return fig,ax,points_data
