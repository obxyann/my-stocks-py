from tkinter import ttk

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from panels.auto_scrollbar import AutoScrollbar


class RevenuePanel(ttk.Frame):
    """Revenue panel with chart and table

    Args:
        parent: Parent widget
        style_helper: Object with set_chart_style and set_axes_style methods
    """

    def __init__(self, parent, style_helper):
        super().__init__(parent)

        # for setting styles
        self.style_helper = style_helper

        # create charts at top
        self._create_charts().pack(fill='x')

        # create table below chart
        self._create_table().pack(fill='both', expand=True)

    def _create_charts(self):
        """Create charts

        Returns:
            ttk.Frame: Created frame containing charts
        """
        # container for charts
        chart_frame = ttk.Frame(self)

        # create matplotlib figure
        # figsize=(width, height) is in inches, inches * dpi = pixels
        self.fig = Figure(figsize=(7.5, 4.5), dpi=100)

        # create axes for revenue chart
        self.ax1 = self.fig.add_subplot(211)
        self.ax2 = self.ax1.twinx()

        # create axes for revenue YoY chart
        self.ax3 = self.fig.add_subplot(212)
        self.ax4 = self.ax3.twinx()

        # set style
        self._set_charts_style()

        # embed figure in tkinter
        self.canvas = FigureCanvasTkAgg(self.fig, master=chart_frame)

        self.canvas.get_tk_widget().configure(background='#1C1C1C')
        self.canvas.get_tk_widget().pack(fill='both', expand=True)

        # adjust layout
        self.fig.tight_layout()

        return chart_frame

    def _set_charts_style(self):
        """Set charts style"""
        self.style_helper.set_chart_style(self.fig, self.ax1, self.ax2)
        self.style_helper.set_chart_style(self.fig, self.ax3, self.ax4)

        self.ax1.tick_params(axis='y', labelcolor='#599FDC')
        self.ax2.tick_params(axis='y', labelcolor='#E66D5F')
        self.ax3.tick_params(axis='y', labelcolor='#A94085')
        self.ax4.tick_params(axis='y', labelcolor='#E66D5F')

        self._set_revenue_axes_style('Revenue', 'Price')
        self._set_yoy_axes_style('YoY (%)', 'Price')

    def _set_revenue_axes_style(self, label1, label2):
        """Set axes style for revenue chart

        Args:
            label1 (str): Label for the major y-axis
            label2 (str): Label for the second y-axis
        """
        self.style_helper.set_axes_style(self.ax1, self.ax2, label1, label2)

        # label beside axes
        self.ax1.set_ylabel(label1, color='#599FDC')
        # offset text of axes
        self.ax1.yaxis.get_offset_text().set_color('#599FDC')

        # ensure scientific notation is off and don't use offset text
        # self.ax1.ticklabel_format(style='plain', axis='y', useOffset=False)

        self.ax2.set_ylabel(label2, color='#E66D5F')
        self.ax2.yaxis.get_offset_text().set_color('#E66D5F')

    def _set_yoy_axes_style(self, label1, label2):
        """Set axes style for revenue YoY chart

        Args:
            label1 (str): Label for the major y-axis
            label2 (str): Label for the second y-axis
        """
        self.style_helper.set_axes_style(self.ax3, self.ax4, label1, label2)

        # label beside axes
        self.ax3.set_ylabel(label1, color='#A94085')
        # offset text of axes
        self.ax3.yaxis.get_offset_text().set_color('#A94085')

        # ensure scientific notation is off and don't use offset text
        # self.ax3.ticklabel_format(style='plain', axis='y', useOffset=False)

        self.ax4.set_ylabel(label2, color='#E66D5F')
        self.ax4.yaxis.get_offset_text().set_color('#E66D5F')

    def _create_table(self):
        """Create table

        Returns:
            ttk.Frame: Created table
        """
        # container for widgets
        table_frame = ttk.Frame(self)

        # table: | year_month | revenue | ... | revenue ytd yoy |
        columns = (
            'year_month',
            'revenue',
            'revenue_mom',
            'revenue_ly',
            'revenue_yoy',
            'revenue_ytd',
            'revenue_ytd_yoy',
        )

        table = ttk.Treeview(table_frame, columns=columns, show='headings')

        table.heading('year_month', text='年/月')
        table.heading('revenue', text='營收')
        table.heading('revenue_mom', text='MoM%')
        table.heading('revenue_ly', text='去年同期')
        table.heading('revenue_yoy', text='YoY%')
        table.heading('revenue_ytd', text='累計營收')
        table.heading('revenue_ytd_yoy', text='YoY%')

        table.column('year_month', width=60)
        table.column('revenue', width=80, anchor='e')
        table.column('revenue_mom', width=60, anchor='e')
        table.column('revenue_ly', width=80, anchor='e')
        table.column('revenue_yoy', width=60, anchor='e')
        table.column('revenue_ytd', width=80, anchor='e')
        table.column('revenue_ytd_yoy', width=60, anchor='e')

        # scrollbar: | table ||
        scrollbar = AutoScrollbar(table_frame, orient='vertical', command=table.yview)

        table.configure(yscrollcommand=scrollbar.set)

        table.pack(side='left', fill='both', expand=True)

        self.table = table

        return table_frame

    def _set_charts_data(self, df_plot):
        """Set data to charts

        Args:
            df_plot (pd.DataFrame): Revenue plot data
        """
        # clear existing plots
        self.ax1.clear()
        self.ax2.clear()

        self.ax3.clear()
        self.ax4.clear()

        # check data
        if df_plot is None or df_plot.empty:
            self.canvas.draw_idle()
            return

        # determine scale and unit based on max revenue
        if 'revenue' in df_plot.columns:
            max_rev = df_plot['revenue'].max()
        elif 'revenue_ma3' in df_plot.columns:
            max_rev = df_plot['revenue_ma3'].max()
        elif 'revenue_ma12' in df_plot.columns:
            max_rev = df_plot['revenue_ma12'].max()
        else:
            max_rev = 0

        if max_rev > 9999999:
            scale = 1000000
            unit = 'B'
        elif max_rev > 9999:
            scale = 1000
            unit = 'M'
        else:
            scale = 1
            unit = 'K'

        # apply scale to revenue data
        # Note: df_plot is a copy from load_stock or caller, so we can modify it
        if 'revenue' in df_plot.columns:
            df_plot['revenue'] = df_plot['revenue'] / scale
        if 'revenue_ma3' in df_plot.columns:
            df_plot['revenue_ma3'] = df_plot['revenue_ma3'] / scale
        if 'revenue_ma12' in df_plot.columns:
            df_plot['revenue_ma12'] = df_plot['revenue_ma12'] / scale

        # plot revenue chart
        self._plot_revenue_chart(df_plot, unit)

        # plot revenue yoy chart
        self._plot_yoy_chart(df_plot)

        # adjust layout
        self.fig.tight_layout()

        self.canvas.draw_idle()

    def _plot_revenue_chart(self, df_plot, unit):
        """Plot revenue/price chart

        Args:
            df_plot (pd.DataFrame): Data for ploting
            unit (str): Unit for showing as part of label on y-axis
        """
        # Reapply styling that were reset by ax.clear()
        self._set_revenue_axes_style('Revenue (' + unit + ')', 'Price')

        # x-axis indices (categorical 0, 1, 2...)
        x_indices = range(len(df_plot))

        # plot revenue bars (on main y-axis)
        if 'revenue' in df_plot.columns:
            self.ax1.bar(
                x_indices,
                df_plot['revenue'],
                color='#599FDC',
                width=0.6,
                label='Revenue',
            )

        # plot revenue MA3 line (on main y-axis)
        if 'revenue_ma3' in df_plot.columns:
            self.ax1.plot(
                x_indices,
                df_plot['revenue_ma3'],
                color='#FBC470',
                alpha=0.8,
                linewidth=2,
                label='MA3',
            )

        # plot revenue MA12 line (on main y-axis)
        if 'revenue_ma12' in df_plot.columns:
            self.ax1.plot(
                x_indices,
                df_plot['revenue_ma12'],
                color='#66BB6A',
                alpha=0.8,
                linewidth=2,
                label='MA12',
            )

        # plot monthly price line (on secondary y-axis)
        if 'price' in df_plot.columns:
            self.ax2.plot(
                x_indices,
                df_plot['price'],
                color='#E66D5F',
                linewidth=2,
                label='Price',
            )

        # format x-axis ticks
        self._format_x_ticks(self.ax1, df_plot.get('year_month', []))

        # legends
        self._apply_legend(self.ax1, 'left')
        self._apply_legend(self.ax2, 'right')

    def _plot_yoy_chart(self, df_plot):
        """Plot revenue YoY/price chart

        Args:
            df_plot (pd.DataFrame): Data for ploting
        """
        # Reapply styling that were reset by ax.clear()
        self._set_yoy_axes_style('YoY (%)', 'Price')

        # x-axis indices (categorical 0, 1, 2...)
        x_indices = range(len(df_plot))

        # plot revenue YoY bars (on main y-axis)
        if 'revenue_yoy' in df_plot.columns:
            self.ax3.bar(
                x_indices,
                df_plot['revenue_yoy'],
                color='#A94085',
                width=0.6,
                label='YoY (%)',
            )

        # plot monthly price line (on secondary y-axis)
        if 'price' in df_plot.columns:
            self.ax4.plot(
                x_indices,
                df_plot['price'],
                color='#E66D5F',
                linewidth=2,
                label='Price',
            )

        # format x-axis ticks
        self._format_x_ticks(self.ax3, df_plot.get('year_month', []))

        # legends
        self._apply_legend(self.ax3, 'left')
        self._apply_legend(self.ax4, 'right')

    def _format_x_ticks(self, ax, series, num_max_ticks=6):
        """Format x-axis ticks and labels with step size

        Args:
            ax: Matplotlib axis to format
            series (pd.Series): Data containing all available x labels
            num_max_ticks (int): Maximum number of ticks to show
        """
        num_ticks = len(series)
        if num_ticks == 0:
            return

        step = max(1, num_ticks // num_max_ticks)

        tick_positions = range(0, num_ticks, step)
        tick_labels = series.iloc[::step]

        ax.set_xticks(tick_positions, labels=tick_labels)

        # remove padding on left and right
        ax.set_xlim(-0.5, num_ticks - 0.5)

    def _apply_legend(self, ax, side='left'):
        """Apply legend to specified axis and side

        Args:
           ax: Matplotlib axis to apply
           side (str): location of legend, 'left' or 'right' of chart
        """
        handles, labels = ax.get_legend_handles_labels()
        if not handles:
            return

        if side == 'left':
            loc = 'upper left'
            anchor = (0, 1.2)
        elif side == 'right':
            loc = 'upper right'
            anchor = (1, 1.2)
        else:
            loc = 'best'
            anchor = (0, 0, 1, 1)

        # TBD:
        # draw on ax2 to be on top of all lines of ax1
        # legend = ax2.legend(

        legend = ax.legend(
            handles,
            labels,
            loc=loc,
            frameon=False,
            labelcolor='#FFFFFF',
            bbox_to_anchor=anchor,
            ncol=3,
        )
        legend.get_frame().set_facecolor('#1C1C1C')
        # legend.get_frame().set_edgecolor('#363636')
        legend.get_frame().set_alpha(0.6)
        legend.set_zorder(100)

        # TBD:
        # for drawing on ax2
        # must add back as artist to show multiple legends on same ax
        # ax2.add_artist(legend)

    def _set_table_data(self, df):
        """Set data to table

        Args:
            df (pd.DataFrame): Revenue data (may have extra columns for chart)
        """
        # clear old data
        self.table.delete(*self.table.get_children())

        if df is None or df.empty:
            return

        # check if dataframe has at least the required columns
        df_cols = df.columns.tolist()
        table_cols = self.table['columns']

        if len(df_cols) < len(table_cols):
            print('Warning: Invalid revenue data')
            print(df.head(3))
            print('...')
            return

        # insert data (only use first N columns matching table columns)
        num_cols = len(table_cols)
        for _, row in df.iterrows():
            self.table.insert('', 'end', values=tuple(row.iloc[:num_cols]))

    def set_data(self, df, df_plot=None):
        """Set data to panel

        Args:
            df (pd.DataFrame): Revenue data for table
            df_plot (pd.DataFrame): Revenue plot data for charts
        """
        self._set_charts_data(df_plot)
        self._set_table_data(df)

    def clear(self):
        """Clear data on panel"""
        # clear chart
        self._set_charts_data(None)

        # clear table
        self._set_table_data(None)
