from tkinter import ttk

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from panels.auto_scrollbar import AutoScrollbar


class FinancialPanel(ttk.Frame):
    """Financial panel with chart and table

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
        self.fig = Figure(figsize=(7.5, 3.2), dpi=100)

        # create axes for each chart
        self.ax_cash_flow = self.fig.add_subplot(121)
        self.ax_eps = self.fig.add_subplot(122)

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
        self.style_helper.set_chart_style(self.fig, self.ax_cash_flow)
        self.style_helper.set_chart_style(self.fig, self.ax_eps)

        # self.ax_cash_flow.set_title('Cash Flow', color='#FFFFFF')
        # self.ax_eps.set_title('EPS', color='#FFFFFF')

        self._set_axes_style(self.ax_cash_flow, 'Cash Flow')
        self._set_axes_style(self.ax_eps, 'EPS')

    def _set_axes_style(self, ax, label):
        """Set axes style for charts

        Args:
            ax: Matplotlib axis to style
            label (str): Label for the y-axis
        """
        self.style_helper.set_axes_style(ax, label1=label)

        ax.tick_params(axis='x', rotation=0)

        # ensure scientific notation is off and don't use offset text
        # ax.ticklabel_format(style='plain', axis='y', useOffset=False)        

    def _create_table(self):
        """Create table

        Returns:
            ttk.Frame: Created table
        """
        # container for widgets
        table_frame = ttk.Frame(self)

        # table: | item | period1 | ... | period8 |
        columns = (
            'item',
            'period1',
            'period2',
            'period3',
            'period4',
            'period5',
            'period6',
            'period7',
            'period8',
        )

        table = ttk.Treeview(table_frame, columns=columns, show='headings')

        table.heading('item', text='Item')
        table.heading('period1', text='YYYY.Q-')
        table.heading('period2', text='YYYY.Q-')
        table.heading('period3', text='YYYY.Q-')
        table.heading('period4', text='YYYY.Q-')
        table.heading('period5', text='YYYY.Q-')
        table.heading('period6', text='YYYY.Q-')
        table.heading('period7', text='YYYY.Q-')
        table.heading('period8', text='YYYY.Q-')

        table.column('item', width=94)
        table.column('period1', width=80, anchor='e')
        table.column('period2', width=80, anchor='e')
        table.column('period3', width=80, anchor='e')
        table.column('period4', width=80, anchor='e')
        table.column('period5', width=80, anchor='e')
        table.column('period6', width=80, anchor='e')
        table.column('period7', width=80, anchor='e')
        table.column('period8', width=80, anchor='e')

        # scrollbar: | table ||
        scrollbar = AutoScrollbar(table_frame, orient='vertical', command=table.yview)

        table.configure(yscrollcommand=scrollbar.set)

        table.pack(side='left', fill='both', expand=True)

        self.table = table

        return table_frame

    def _set_charts_data(self, df_plot):
        """Set data to charts

        Args:
            df_plot (pd.DataFrame): Financial plot data
        """
        # clear existing plots
        self.ax_cash_flow.clear()
        self.ax_eps.clear()

        # check data
        if df_plot is None or df_plot.empty:
            self.canvas.draw_idle()
            return

        # plot charts
        self._plot_cash_flow_chart(df_plot)
        self._plot_eps_chart(df_plot)

        # adjust layout
        self.fig.tight_layout()
        
        self.canvas.draw_idle()

    def _plot_cash_flow_chart(self, df_plot):
        """Plot cash flow chart

        Args:
            df_plot (pd.DataFrame): Data for plotting
        """
        ax = self.ax_cash_flow

        # Reapply styling that were reset by ax.clear()
        self._set_axes_style(ax, 'Cash Flow')

        # x-axis indices (categorical 0, 1, 2...)
        x_indices = range(len(df_plot))

        # plot lines
        if 'net_income' in df_plot.columns:
            ax.plot(
                x_indices,
                df_plot['net_income'],
                color='#66BB6A',
                linewidth=2,
                label='Net Income',
            )

        if 'opr_cash_flow' in df_plot.columns:
            ax.plot(
                x_indices,
                df_plot['opr_cash_flow'],
                color='#599FDC',
                linewidth=2,
                label='Op Cash Flow',
            )

        # format x-axis ticks
        self._format_x_ticks(ax, df_plot.get('year_quarter', []))
        
        # legends
        self._apply_legend(ax)

        # title
        # ax.set_title('Cash Flow', color='#FFFFFF')        

    def _plot_eps_chart(self, df_plot):
        """Plot EPS chart

        Args:
            df_plot (pd.DataFrame): Data for plotting
        """
        ax = self.ax_eps

        # Reapply styling that were reset by ax.clear()
        self._set_axes_style(ax, 'EPS')

        # x-axis indices (categorical 0, 1, 2...)
        x_indices = range(len(df_plot))

        if 'eps' in df_plot.columns:
            ax.bar(
                x_indices,
                df_plot['eps'],
                color='#E66D5F',
                width=0.4,
                label='EPS',
            )

        # format x-axis ticks
        self._format_x_ticks(ax, df_plot.get('year_quarter', []))

        # legends
        self._apply_legend(ax)

        # title
        # ax.set_title('EPS', color='#FFFFFF')           

    def _format_x_ticks(self, ax, series, num_max_ticks=4):
        """Format x-axis ticks and labels with step size

        Args:
            ax: Matplotlib axis to format
            series: Data containing all available x labels
            num_max_ticks (int): Maximum number of ticks to show
        """
        num_ticks = len(series)
        if num_ticks == 0:
            return

        # format x-axis ticks
        step = max(1, num_ticks // num_max_ticks)

        tick_positions = range(0, num_ticks, step)
        tick_labels = series[::step]

        ax.set_xticks(tick_positions, labels=tick_labels)

        # remove padding on left and right
        ax.set_xlim(-0.5, num_ticks - 0.5)

    def _apply_legend(self, ax):
        """Apply legend to specified axis

        Args:
            ax: Matplotlib axis to apply
        """
        handles, labels = ax.get_legend_handles_labels()
        if not handles:
            return

        legend = ax.legend(
            handles,
            labels,
            loc='upper left',
            frameon=False,
            labelcolor='#FFFFFF',
            bbox_to_anchor=(0, 1.2),
            ncol=3,
        )
        legend.get_frame().set_facecolor('#1C1C1C')
        # legend.get_frame().set_edgecolor('#363636')
        legend.get_frame().set_alpha(0.6)
        legend.set_zorder(100)


    def _set_table_data(self, df):
        """Set data to table

        Args:
            df (pd.DataFrame): Financial data
        """
        # reset headers of table
        table_cols = self.table['columns']

        for i in range(1, len(table_cols)):
            self.table.heading(table_cols[i], text='YYYY.Q-')

        # clear old data
        self.table.delete(*self.table.get_children())

        if df is None or df.empty:
            return

        # check if column count matches
        df_cols = df.columns.tolist()
        table_cols = self.table['columns']

        if len(df_cols) != len(table_cols):
            print('Warning: Invalid financial data')
            print(df.head(3))
            print('...')
            return

        # update headers
        for i, col_name in enumerate(df_cols):
            self.table.heading(table_cols[i], text=col_name)

        # insert data
        for _, row in df.iterrows():
            self.table.insert('', 'end', values=tuple(row))

    def set_data(self, df, df_plot=None):
        """Set data to panel

        NOTE: Data has been pivoted for table from database (in load_stock.py)

        Args:
            df (pd.DataFrame): Financial data for table
            df_plot (pd.DataFrame): Financial plot data for charts
        """
        self._set_charts_data(df_plot)
        self._set_table_data(df)

    def clear(self):
        """Clear data on panel"""
        self._set_charts_data(None)
        self._set_table_data(None)
