import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.legend_handler import HandlerBase
from matplotlib.text import Text
import seaborn as sns
import numpy as np
import scipy.stats as stats

sns.set_style('whitegrid')
sns.set_palette('colorblind')

def camel_plot(df, ax, has_blank=False, overall=False, axis_sci_limits=(4, -4)):
    """This is the function used to plot the probability distribution of exposure age data. 
    The function is inspired by Greg Balco's Matlab code (https://cosmognosis.wordpress.com/2009/07/13/matlab-code-for-camel-diagrams/)

    Reference:
    [1] Kelly, Meredith A., et al. Quaternary Science Reviews (2008).
    [2] What is a camel diagram anyway? https://cosmognosis.wordpress.com/2011/07/25/what-is-a-camel-diagram-anyway/
    
    Arguments:
        df {Pandas DataFrame} -- The DataFrame should contain at least 3 columns with names "age", "uncertainty", and "group". 
                                The "group" input will be used to annotate different samples. 
                                If you have a blank sample, the "group" name for the blank sample should be "blank".
        
        ax {<class 'matplotlib.axes._subplots.AxesSubplot'>} -- This allows you to define on which axis to plot the camel plot, 
                                                                in case the camel plot is only one among many subplots. 
    
    Keyword Arguments:
        has_blank {bool} -- If the input DataFrame contains a blank. (default: {False})
        overall {bool} -- Whether you want to produce the overall kernel density on top of individual samples (default: {False})
        axis_sci_limits {tuple} -- The exponential of the scientific notation (default: {(4, -4)})
    
    Returns:
        None
    """


    class TextHandler(HandlerBase):
        def create_artists(self, legend,tup ,xdescent, ydescent, width, height, fontsize,trans):
            tx = Text(width/2.,height/2,tup[0], fontsize=fontsize, ha="center", va="center", color=tup[1], fontweight="bold")
            return [tx]
    
    if has_blank == True:
        df_no_blank = df.loc[df['group'] != 'blank']
        
    else:
        df_no_blank = df
    
    num_samples = len(df)
    
    handles = []
    labels = []
    
    data_cache = []

    for i, row in df.iterrows():
        mu, sigma, group = row['age'], row['uncertainty'], row['group']        
        x = np.linspace(mu - 4*sigma, mu + 4*sigma, 100)
        data = stats.norm.pdf(x, mu, sigma)
        
        if group == 'blank':
            ax = ax.fill_between(x, data/num_samples, color='gray', label=group, alpha=0.3, zorder=1)
            color = ax.get_facecolor()[0] #fetch color of fill
        else:
            ax = sns.lineplot(x=x, y=data/num_samples, label=group, alpha=0.7, ax=ax, zorder=2)
            color = ax.get_lines()[-1].get_c() #fetch color of line
            #collect the pseudo data to be used for production of overall curve
            pseudo_data = stats.norm.rvs(size=len(x), loc=mu, scale=sigma)
            data_cache.append(pseudo_data)
        
        handles.append(("{}:".format(group), color[:3]))
        labels.append("{} $\pm$ {} yr".format(mu, sigma))
        
        #add annotations
        ax1 = plt.gca()
        ax1.text(mu*1.05, max(data/num_samples), group, fontsize=16, color=color[:3]) 
        #only retrieve RGB so blank text is not too light      
        
    if overall == True:
        data_cache = np.array(data_cache).ravel()
        ax=sns.kdeplot(data_cache, cut=4, linewidth=2, color='black', label="overall")
        
    mu_all = np.mean(df_no_blank['age'])
    sigma_all = np.sqrt(np.power(df['uncertainty'], 2).sum())
    
    #allows legends to be customized text with colors corresponding to lines
    handles.append(("Mean :", 'black'))
    labels.append("{0:.0f} $\pm$ {1:.0f} yr".format(mu_all, sigma_all))        
    leg = ax.legend(handles=handles, labels=labels, handler_map={tuple : TextHandler()},
                      facecolor='white', edgecolor='black', borderpad=0.9, framealpha=1, 
                      fontsize=16, handlelength=3)

    for h, t in zip(leg.legendHandles, leg.get_texts()):
        t.set_color(h.get_color()) 
    
    #setting the axis, labels, ticklabels
    ax.set_ylim(bottom=0)
    ax.set_ylabel('Probability', fontsize=20)
    ax.set_xlabel('Exposure age (yr)', fontsize=20)
    ax.ticklabel_format(axis='both', scilimits=axis_sci_limits)
    ax.yaxis.get_offset_text().set_fontsize(16)
    ax.xaxis.get_offset_text().set_fontsize(16)
    ax.tick_params(labelsize=16)

#test
df = pd.DataFrame({'age': [21000, 16900, 18200, 62000, 68000, 7500], 
                    'uncertainty':[3000, 2100, 1200, 4000, 3500, 2000], 
                    'group':['a', 'b', 'c', 'd', 'e', 'blank']})
    
fig, ax = plt.subplots(figsize=(12,8))
camel_plot(df, ax=ax, has_blank=True, overall=True)
fig.show()