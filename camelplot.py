import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.legend_handler import HandlerBase
from matplotlib.text import Text
import seaborn as sns
import numpy as np
import scipy.stats as stats

sns.set_style('whitegrid')
sns.set_palette('colorblind')

%matplotlib inline

df = pd.DataFrame({'age': [21000, 16900, 18200, 32000, 35000, 7500], 'uncertainty':[3000, 2100, 1500, 3000, 2500, 2000], 'group':['a', 'b', 'c', 'd', 'e', 'blank']})

class TextHandler(HandlerBase):
    def create_artists(self, legend,tup ,xdescent, ydescent, width, height, fontsize,trans):
        tx = Text(width/2.,height/2,tup[0], fontsize=fontsize, ha="center", va="center", color=tup[1], fontweight="bold")
        return [tx]


def camel_plot(df, ax, has_blank=False, overall=False, axis_sci_limits=(4, -4)):     
    
    if has_blank == True:
        df_no_blank = df.loc[df['group'] != 'blank']
        
    else:
        df_no_blank = df
    
    num_samples = len(df_no_blank)
    
    handles = []
    labels = []

    for i, row in df.iterrows():
        mu, sigma, group = row['age'], row['uncertainty'], row['group']        
        x = np.linspace(mu - 4*sigma, mu + 4*sigma, 100)
        if group == 'blank':
            ax = ax.fill_between(x, stats.norm.pdf(x, mu, sigma)/num_samples, color='gray', label=group, alpha=0.3, zorder=1)
            color = ax.get_facecolor()[0] #fetch color of fill
        else:
            ax = sns.lineplot(x, stats.norm.pdf(x, mu, sigma)/num_samples, label=group, alpha=0.7, ax=ax, zorder=2)
            color = ax.get_lines()[-1].get_c() #fetch color of line
        
        handles.append(("{}:".format(group), color[:3]))
        labels.append("{} $\pm$ {} yr".format(mu, sigma))
        
        #add annotations
        ax1 = plt.gca()
        ax1.text(mu*1.05, max(stats.norm.pdf(x, mu, sigma)/num_samples), group, fontsize=16, color=color[:3]) #only retrieve RGB so blank text is not too light      
        
    if overall == True:
        ax=sns.kdeplot(df_no_blank['age'], cut=4, linewidth=2, color='black', label="overall")
        
    mu_all = np.mean(df_no_blank['age'])
    sigma_all = np.sqrt(np.power(df['uncertainty'], 2).sum())
    
    handles.append(("Mean :", 'black'))
    labels.append("{0:.0f} $\pm$ {1:.0f} yr".format(mu_all, sigma_all))
        
    leg = ax.legend(handles=handles, labels=labels, handler_map={tuple : TextHandler()},
                      facecolor='white', edgecolor='black', borderpad=0.9, framealpha=1, 
                      fontsize=16, handlelength=3)

    for h, t in zip(leg.legendHandles, leg.get_texts()):
        t.set_color(h.get_color()) 
    
    ax.set_ylim(bottom=0)
    ax.set_ylabel('Probability', fontsize=20)
    ax.set_xlabel('Exposure age (yr)', fontsize=20)
    ax.ticklabel_format(axis='both', scilimits=axis_sci_limits)
    ax.yaxis.get_offset_text().set_fontsize(16)
    ax.xaxis.get_offset_text().set_fontsize(16)
    ax.tick_params(labelsize=16)


fig, ax = plt.subplots(figsize=(12,8))
camel_plot(df, ax=ax, has_blank=True, overall=True)

fig.show()
#fig.savefig('test.png')