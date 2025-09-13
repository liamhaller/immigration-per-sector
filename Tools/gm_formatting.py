import matplotlib.font_manager as fm
import matplotlib.pyplot as plt
from matplotlib.pyplot import gca
import matplotlib.image as mpimg
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
import matplotlib.dates as mdates
from .path_management import assets_dir

def gm_formatting(
        ax=None,
        title=None,
        data=None,
        color=['black', '#cabd8f', '#4e81bd', '#505c54', '#003845', '#696a6d'],
        dateformat="%b-%y",
        legend_ncol=3,
        **kwargs):
    """
    Apply GM style formatting to an existing matplotlib axes object.
    
    Parameters:
    -----------
    ax : matplotlib.axes.Axes, optional
        The axes object to format. If None, uses current axes (gca())
    title : str, optional
        Chart title to be set
    data : pandas.DataFrame, optional
        Data for legend labels and date formatting detection
    color : list, optional
        Color cycle for the chart
    dateformat : str, optional
        Date format string for x-axis when data has datetime index
    legend_ncol : int, optional
        Number of columns in legend
    **kwargs : dict
        Additional axis modifications (e.g., xlabel='X Label', ylabel='Y Label')
    
    Returns:
    --------
    matplotlib.axes.Axes
        The formatted axes object
    """
    
    # Use current axes if none provided
    if ax is None:
        ax = gca()
    
    # Use path management system
    font_path = assets_dir / 'fonts'
    img_path = assets_dir / 'img'
    
    # Set font properties
    title_fprop = fm.FontProperties(fname=str(font_path / 'EBGaramondSC.otf'), size=12)
    g_fprop = fm.FontProperties(fname=str(font_path / 'EBGaramond-VariableFont_wght.ttf'), size=10)
    
    # Set color cycle
    ax.set_prop_cycle(color=color)
    
    # Set title if provided
    if title:
        ax.set_title(title, fontproperties=title_fprop, loc='left', x=-0.1)
    
    # Apply GM styling
    plt.tick_params(axis='both', which='both', bottom=False, left=False)
    ax.spines['right'].set_visible(False)
    ax.spines['top'].set_visible(False)
    
    # Set font properties for tick labels
    for xlabel in ax.get_xticklabels():
        xlabel.set_fontproperties(g_fprop)
    for ylabel in ax.get_yticklabels():
        ylabel.set_fontproperties(g_fprop)
    
    # Format dates if data has datetime index
    if data is not None and hasattr(data, 'index') and data.index.inferred_type == 'datetime64':
        ax.xaxis.set_major_formatter(mdates.DateFormatter(dateformat))
    
    # Set up legend if data is provided
    if data is not None and hasattr(data, 'columns'):
        ax.legend(data.columns, loc='upper center', bbox_to_anchor=(0.5, -0.1), 
                 frameon=False, ncol=legend_ncol, prop=g_fprop)
    
    # Add the watermark image
    try:
        watermark = mpimg.imread(str(img_path / 'gr_img.png'))
        imagebox = OffsetImage(watermark, zoom=0.01, alpha=1)
        ab = AnnotationBbox(imagebox, (1.02, 1.05), xycoords='axes fraction', 
                           box_alignment=(1, 1), frameon=False)
        ax.add_artist(ab)
    except FileNotFoundError:
        # Skip watermark if image file not found
        pass
    
    # Set margins
    plt.margins(y=0)
    
    # Apply any additional axis modifications from kwargs
    for key, value in kwargs.items():
        method_name = f'set_{key}'
        if hasattr(ax, method_name):
            method = getattr(ax, method_name)
            if callable(method):
                if isinstance(value, (list, tuple)):
                    method(*value)  # For methods that take multiple args
                else:
                    # Apply font properties to labels
                    if key in ['ylabel', 'xlabel']:
                        method(value, fontproperties=g_fprop)
                    else:
                        method(value)
    
    return ax




def generate_gm_chart(
        data,
        title,
        save_fig_name,
        fig_size,
        color = ['black', '#cabd8f',  '#4e81bd', '#505c54', '#003845', '#696a6d'],
        dateformat = "%b-%y",
        legend_ncol = 3,
        show = True,
        plot_type = "line",
        **kwargs):

    fig, ax = plt.subplots(figsize=fig_size)

    # Use path management system
    font_path = assets_dir / 'fonts'
    img_path = assets_dir / 'img'

    # Set title font properties
    title_fprop = fm.FontProperties(fname=str(font_path / 'EBGaramondSC.otf'), size=12)
    g_fprop = fm.FontProperties(fname=str(font_path / 'EBGaramond-VariableFont_wght.ttf'), size=10)

    # Set color cycle
    ax.set_prop_cycle(color=color)

    # Set title and plot parameters
    ax.set_title(title, fontproperties=title_fprop, loc='left', x=-0.1)
    plt.tick_params(axis='both', which='both', bottom=False, left=False)
    ax.spines['right'].set_visible(False)
    ax.spines['top'].set_visible(False)

    # Add compatability for other types of charts 

    if plot_type == "line":
        ax.plot(data)
    elif plot_type == "bar":
        if len(data.columns) == 1:
            ax.bar(range(len(data)), data.iloc[:, 0], color=color[0])
        else:
            # For multiple columns, create grouped bars
            x_pos = range(len(data))
            bar_width = 0.8 / len(data.columns)
            for i, col in enumerate(data.columns):
                ax.bar([x + bar_width * i for x in x_pos], data[col],
                    bar_width, label=col, color=color[i % len(color)])
    elif plot_type == "scatter":
        for i, col in enumerate(data.columns):
            ax.scatter(data.index, data[col], color=color[i % len(color)], label=col)

    if plot_type == "bar":
        ax.set_xticks(range(len(data)))

    ### end chart compatability edits

    # Set font properties for tick labels
    for xlabel in ax.get_xticklabels():
        xlabel.set_fontproperties(g_fprop)
    for ylabel in ax.get_yticklabels():
        ylabel.set_fontproperties(g_fprop)

    if (data.index.inferred_type == 'datetime64'):
        ax.xaxis.set_major_formatter(mdates.DateFormatter(dateformat))

    ax.legend(data.columns, loc='upper center', bbox_to_anchor=(0.5, -0.1), frameon=False, ncol=legend_ncol, prop=g_fprop)

    # Add the watermark image
    watermark = mpimg.imread(str(img_path / 'gr_img.png'))
    imagebox = OffsetImage(watermark, zoom=0.005, alpha=1)
    ab = AnnotationBbox(imagebox, (1.02, 1.05), xycoords='axes fraction', box_alignment=(1, 1), frameon=False)
    ax.add_artist(ab)

    # Set margins and layout
    plt.margins(y=0)

    # Apply any additional axis modifications from kwargs
    for key, value in kwargs.items():
        method_name = f'set_{key}'
        if hasattr(ax, method_name):
            method = getattr(ax, method_name)
            if callable(method):
                if isinstance(value, (list, tuple)):
                    method(*value)  # For methods that take multiple args
                else:
                      # Apply font properties to labels
                      if key in ['ylabel', 'xlabel']:
                          method(value, fontproperties=g_fprop)
                      else:
                          method(value)



    plt.savefig(save_fig_name, dpi=400)
    if show:
            plt.show()
            return None
    else:
        return fig, ax