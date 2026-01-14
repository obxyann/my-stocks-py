from tkinter import ttk

import pandas as pd
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

        # create chart at top
        self._create_chart().pack(fill='x')

        # create table below chart
        self._create_table().pack(fill='both', expand=True)

    def _create_chart(self):
        """Create chart

        Returns:
            ttk.Frame: Created chart
        """
        # container for chart
        chart_frame = ttk.Frame(self)

        # create matplotlib figure
        # figsize=(width, height) is in inches, inches * dpi = pixels
        self.fig = Figure(figsize=(7.5, 2.5), dpi=100)

        # create axes
        self.ax1 = self.fig.add_subplot(111)
        self.ax2 = self.ax1.twinx()

        # set style
        self._set_chart_style()

        # embed figure in tkinter
        self.canvas = FigureCanvasTkAgg(self.fig, master=chart_frame)

        self.canvas.get_tk_widget().pack(fill='both', expand=True)

        # adjust layout
        self.fig.tight_layout()

        return chart_frame

    def _set_chart_style(self):
        """Set chart style"""
        self.style_helper.set_chart_style(self.fig, self.ax1, self.ax2)

        # NOTE: below styles are reset by ax.clear() and must be reapplied in
        #       set_chart_data()
        self.style_helper.set_axes_style(self.ax1, self.ax2, 'Revenue', 'Price')

    def _create_table(self):
        """Create table

        Returns:
            ttk.Frame: Created table
        """
        # container for widgets
        table_frame = ttk.Frame(self)

        # table: | year_month | revence | ... | revence ytd yoy |
        columns = (
            'year_month',
            'revence',
            'revence_mom',
            'revence_ly',
            'revence_yoy',
            'revence_ytd',
            'revence_ytd_yoy',
        )

        table = ttk.Treeview(table_frame, columns=columns, show='headings')

        table.heading('year_month', text='年/月')
        table.heading('revence', text='營收')
        table.heading('revence_mom', text='MoM%')
        table.heading('revence_ly', text='去年同期')
        table.heading('revence_yoy', text='YoY%')
        table.heading('revence_ytd', text='累計營收')
        table.heading('revence_ytd_yoy', text='YoY%')

        table.column('year_month', width=60)
        table.column('revence', width=80, anchor='e')
        table.column('revence_mom', width=60, anchor='e')
        table.column('revence_ly', width=80, anchor='e')
        table.column('revence_yoy', width=60, anchor='e')
        table.column('revence_ytd', width=80, anchor='e')
        table.column('revence_ytd_yoy', width=60, anchor='e')

        # scrollbar: | table ||
        scrollbar = AutoScrollbar(table_frame, orient='vertical', command=table.yview)

        table.configure(yscrollcommand=scrollbar.set)

        table.pack(side='left', fill='both', expand=True)

        self.table = table

        return table_frame

    def _set_chart_data(self, df_revenue, df_price=None):
        """Set data to chart

        Args:
            df_revenue: pd.DataFrame containing revenue data
            df_price: pd.DataFrame containing price data (optional)
        """
        # clear existing plots
        self.ax1.clear()
        self.ax2.clear()

        # check data
        if df_revenue is None or df_revenue.empty:
            self.canvas.draw_idle()
            return

        # prepare data
        # 1. sort ascending for chart x-axis
        df_plot = df_revenue.copy().sort_values('year_month')

        # 2. merge price data
        if df_price is not None and not df_price.empty:
            # align price data with revenue x-axis
            df_plot = pd.merge(
                df_plot, df_price[['year_month', 'price']], on='year_month', how='left'
            )

        # 3. determine scale and unit based on max revenue
        if 'revence' in df_plot.columns and not df_plot.empty:
            max_rev = df_plot['revence'].max()
        else:
            max_rev = 0

        scale = 1
        unit = 'K'

        if max_rev > 9999999:
            scale = 1000000
            unit = 'B'
        elif max_rev > 9999:
            scale = 1000
            unit = 'M'

        # apply scale to revenue data
        if 'revence' in df_plot.columns:
            df_plot['revence'] = df_plot['revence'] / scale
        if 'revenue_ma3' in df_plot.columns:
            df_plot['revenue_ma3'] = df_plot['revenue_ma3'] / scale
        if 'revenue_ma12' in df_plot.columns:
            df_plot['revenue_ma12'] = df_plot['revenue_ma12'] / scale

        # 4. x-axis indices (categorical 0, 1, 2...)
        num_ticks = len(df_plot)
        x_indices = range(num_ticks)

        # plot revenue bars (on main y-axis)
        if 'revence' in df_plot.columns:
            self.ax1.bar(
                x_indices,
                df_plot['revence'],
                color='#599FDC',
                alpha=0.8,
                label='Revenue',
                width=0.6,
            )

        # plot revenue MA3 line (on main y-axis)
        if 'revenue_ma3' in df_plot.columns:
            self.ax1.plot(
                x_indices,
                df_plot['revenue_ma3'],
                color='#FBC470',
                alpha=0.7,
                linewidth=2,
                label='MA3',
            )

        # plot revenue MA12 line (on main y-axis)
        if 'revenue_ma12' in df_plot.columns:
            self.ax1.plot(
                x_indices,
                df_plot['revenue_ma12'],
                color='#66BB6A',
                alpha=0.7,
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
        step = max(1, num_ticks // 6)

        tick_positions = range(0, num_ticks, step)
        tick_labels = df_plot['year_month'].iloc[::step]

        self.ax1.set_xticks(tick_positions, labels=tick_labels)

        # remove padding on left and right
        self.ax1.set_xlim(-0.5, num_ticks - 0.5)

        # NOTE: Reapply styling that were reset by ax.clear()
        self.style_helper.set_axes_style(
            self.ax1, self.ax2, 'Revenue (' + unit + ')', 'Price'
        )

        # ensure scientific notation is off and don't use offset text
        self.ax1.ticklabel_format(style='plain', axis='y', useOffset=False)

        # legends
        h1, l1 = self.ax1.get_legend_handles_labels()
        h2, l2 = self.ax2.get_legend_handles_labels()

        # revenue legend on the left (draw on ax2 to be on top of all lines)
        if h1:
            leg1 = self.ax2.legend(
                h1,
                l1,
                loc='upper left',
                frameon=True,
                labelcolor='#FFFFFF',
                bbox_to_anchor=(0, 1.2),
                ncol=3,
            )
            leg1.get_frame().set_facecolor('#1C1C1C')
            leg1.get_frame().set_edgecolor('#363636')
            leg1.get_frame().set_alpha(0.6)
            leg1.set_zorder(100)

            # must add back as artist to show multiple legends on same ax
            self.ax2.add_artist(leg1)

        # price legend on the right
        if h2:
            leg2 = self.ax2.legend(
                h2,
                l2,
                loc='upper right',
                frameon=True,
                labelcolor='#FFFFFF',
                bbox_to_anchor=(1, 1.2),
            )
            leg2.get_frame().set_facecolor('#1C1C1C')
            leg2.get_frame().set_edgecolor('#363636')
            leg2.get_frame().set_alpha(0.6)
            leg2.set_zorder(100)

        # adjust layout
        self.fig.tight_layout()

        self.canvas.draw_idle()

    def _set_table_data(self, df):
        """Set data to table

        Args:
            df: pd.DataFrame containing revenue data (may have extra columns for chart)
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

    def set_data(self, df_revenue, df_price=None):
        """Set data to panel

        Args:
            df_revenue: pd.DataFrame containing revenue data
            df_price: pd.DataFrame containing price data (optional)
        """
        self._set_chart_data(df_revenue, df_price)
        self._set_table_data(df_revenue)

    def clear(self):
        """Clear data on panel"""
        # clear chart
        self._set_chart_data(None)

        # clear table
        self._set_table_data(None)
