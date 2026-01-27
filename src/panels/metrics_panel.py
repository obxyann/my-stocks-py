from tkinter import ttk

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from panels.auto_scrollbar import AutoScrollbar


class MetricsPanel(ttk.Frame):
    """Metrics panel with chart and table

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

        # constraints flags
        self._ax_qoq_constrained = False
        self._ax_yoy_constrained = False

    def _create_charts(self):
        """Create charts

        Returns:
            ttk.Frame: Created frame containing charts
        """
        # container for charts
        chart_frame = ttk.Frame(self)

        # create matplotlib figure
        # figsize=(width, height) is in inches, inches * dpi = pixels
        self.fig = Figure(figsize=(7.5, 5.0), dpi=100)

        # create axes for each chart
        self.ax_profit = self.fig.add_subplot(221)
        self.ax_profit_qoq = self.fig.add_subplot(222)
        self.ax_profit_yoy = self.fig.add_subplot(223)
        # self.ax_empty = self.fig.add_subplot(224)

        # self.ax_empty.axis('off')

        # set style
        self._set_charts_style()

        # embed figure in tkinter
        self.canvas = FigureCanvasTkAgg(self.fig, master=chart_frame)

        self.canvas.get_tk_widget().configure(background='#1C1C1C')
        self.canvas.get_tk_widget().pack(fill='both', expand=True)

        # handle click events
        self.canvas.mpl_connect('button_press_event', self._on_click)

        # adjust layout
        self.fig.tight_layout()

        return chart_frame

    def _set_charts_style(self):
        """Set charts style"""
        self.style_helper.set_chart_style(self.fig, self.ax_profit)
        self.style_helper.set_chart_style(self.fig, self.ax_profit_qoq)
        self.style_helper.set_chart_style(self.fig, self.ax_profit_yoy)
        # self.style_helper.set_chart_style(self.fig, self.ax_empty)

        # self.ax_profit.set_title('Profitability', color='#FFFFFF')
        # self.ax_profit_qoq.set_title('Profitability QoQ', color='#FFFFFF')
        # self.ax_profit_yoy.set_title('Profitability YoY', color='#FFFFFF')

        self._set_axes_style(self.ax_profit, 'Profitability (%)')
        self._set_axes_style(self.ax_profit_qoq, 'Profit QoQ (%)')
        self._set_axes_style(self.ax_profit_yoy, 'Profit YoY (%)')

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

        table.column('item', width=120)
        table.column('period1', width=60, anchor='e')
        table.column('period2', width=60, anchor='e')
        table.column('period3', width=60, anchor='e')
        table.column('period4', width=60, anchor='e')
        table.column('period5', width=60, anchor='e')
        table.column('period6', width=60, anchor='e')
        table.column('period7', width=60, anchor='e')
        table.column('period8', width=60, anchor='e')

        # scrollbar: | table ||
        scrollbar = AutoScrollbar(table_frame, orient='vertical', command=table.yview)

        table.configure(yscrollcommand=scrollbar.set)

        table.pack(side='left', fill='both', expand=True)

        self.table = table

        return table_frame

    def _set_charts_data(self, df_plot):
        """Set data to chart

        Args:
            df_plot (pd.DataFrame): Metrics plot data
        """
        # clear existing plots
        self.ax_profit.clear()
        self.ax_profit_qoq.clear()
        self.ax_profit_yoy.clear()
        # self.ax_empty.clear()

        # check data
        if df_plot is None or df_plot.empty:
            self.canvas.draw_idle()
            return

        # plot charts
        self._plot_profit_chart(df_plot)
        self._plot_profit_qoq_chart(df_plot)
        self._plot_profit_yoy_chart(df_plot)

        # adjust layout
        self.fig.tight_layout()

        self.canvas.draw_idle()

    def _plot_profit_chart(self, df_plot):
        """Plot profitability chart

        Args:
            df_plot (pd.DataFrame): Data for ploting
        """
        ax = self.ax_profit

        # Reapply styling that were reset by ax.clear()
        self._set_axes_style(ax, 'Profitability (%)')

        # x-axis indices (categorical 0, 1, 2...)
        x_indices = range(len(df_plot))

        # plot lines
        if 'gross_margin' in df_plot.columns:
            ax.plot(
                x_indices,
                df_plot['gross_margin'],
                color='#599FDC',
                linewidth=2,
                label='gross',
            )
        if 'opr_margin' in df_plot.columns:
            ax.plot(
                x_indices,
                df_plot['opr_margin'],
                color='#E66D5F',
                linewidth=2,
                label='opr',
            )
        if 'net_margin' in df_plot.columns:
            ax.plot(
                x_indices,
                df_plot['net_margin'],
                color='#66BB6A',
                linewidth=2,
                label='net',
            )

        # format x-axis ticks
        self._format_x_ticks(ax, df_plot.get('year_quarter', []))

        # legends
        self._apply_legend(ax)

        # title
        # ax.set_title('Profitability', color='#FFFFFF')

    def _plot_profit_qoq_chart(self, df_plot):
        """Plot profitability QoQ chart

        Args:
             df_plot (pd.DataFrame): Data for ploting
        """
        ax = self.ax_profit_qoq

        # Reapply styling that were reset by ax.clear()
        self._set_axes_style(ax, 'Profit QoQ (%)')

        # x-axis indices (categorical 0, 1, 2...)
        x_indices = range(len(df_plot))
        width = 0.25

        # plot bars
        if 'gross_margin_qoq' in df_plot.columns:
            ax.bar(
                [i - width for i in x_indices],
                df_plot['gross_margin_qoq'],
                color='#599FDC',
                width=width,
                label='gross',
            )
        if 'opr_margin_qoq' in df_plot.columns:
            ax.bar(
                x_indices,
                df_plot['opr_margin_qoq'],
                color='#E66D5F',
                width=width,
                label='opr',
            )
        if 'net_margin_qoq' in df_plot.columns:
            ax.bar(
                [i + width for i in x_indices],
                df_plot['net_margin_qoq'],
                color='#66BB6A',
                width=width,
                label='net',
            )

        # format x-axis ticks
        self._format_x_ticks(ax, df_plot.get('year_quarter', []))

        # legends
        self._apply_legend(ax)

        # apply constraints if enabled
        if getattr(self, '_ax_qoq_constrained', False):
            curr_min, curr_max = ax.get_ylim()
            ax.set_ylim(max(curr_min, -100), min(curr_max, 100))

        # title
        # ax.set_title('Profitability QoQ', color='#FFFFFF')

    def _plot_profit_yoy_chart(self, df_plot):
        """Plot profitability YoY bars on axis

        Args:
            df_plot (pd.DataFrame): Data for ploting
        """
        ax = self.ax_profit_yoy

        # Reapply styling that were reset by ax.clear()
        self._set_axes_style(ax, 'Profit YoY (%)')

        x_indices = range(len(df_plot))
        width = 0.25

        # plot bars
        if 'gross_margin_yoy' in df_plot.columns:
            ax.bar(
                [i - width for i in x_indices],
                df_plot['gross_margin_yoy'],
                color='#599FDC',
                width=width,
                label='gross',
            )
        if 'opr_margin_yoy' in df_plot.columns:
            ax.bar(
                x_indices,
                df_plot['opr_margin_yoy'],
                color='#E66D5F',
                width=width,
                label='opr',
            )
        if 'net_margin_yoy' in df_plot.columns:
            ax.bar(
                [i + width for i in x_indices],
                df_plot['net_margin_yoy'],
                color='#66BB6A',
                width=width,
                label='net',
            )

        # format x-axis ticks
        self._format_x_ticks(ax, df_plot.get('year_quarter', []))

        # legends
        self._apply_legend(ax)

        # apply constraints if enabled
        if getattr(self, '_ax_yoy_constrained', False):
            curr_min, curr_max = ax.get_ylim()
            ax.set_ylim(max(curr_min, -100), min(curr_max, 100))

        # title
        # ax.set_title('Profitability YoY', color='#FFFFFF')

    def _format_x_ticks(self, ax, series, num_max_ticks=4):
        """Format x-axis ticks and labels with step size

        Args:
            ax: Matplotlib axis to format
            series (pd.Series): Data containing all available x labels
            num_max_ticks (int): Maximum number of ticks to show
        """
        num_ticks = len(series)
        if num_ticks == 0:
            return

        # format x-axis ticks
        step = max(1, num_ticks // num_max_ticks)

        tick_positions = range(0, num_ticks, step)
        tick_labels = series.iloc[::step]

        ax.set_xticks(tick_positions, labels=tick_labels)

        # remove padding on left and right
        ax.set_xlim(-0.5, num_ticks - 0.5)

    def _on_click(self, event):
        """Handle click event on charts

        Args:
            event: Matplotlib event
        """
        if event.inaxes == self.ax_profit_qoq:
            self._ax_qoq_constrained = not getattr(self, '_ax_qoq_constrained', False)

            ax = self.ax_profit_qoq

            if self._ax_qoq_constrained:
                curr_min, curr_max = ax.get_ylim()

                ax.set_ylim(max(curr_min, -100), min(curr_max, 100))
            else:
                ax.autoscale(enable=True, axis='y')
                ax.relim()
                ax.autoscale_view(scalex=False, scaley=True)

            self.canvas.draw_idle()

        elif event.inaxes == self.ax_profit_yoy:
            self._ax_yoy_constrained = not getattr(self, '_ax_yoy_constrained', False)

            ax = self.ax_profit_yoy

            if self._ax_yoy_constrained:
                curr_min, curr_max = ax.get_ylim()

                ax.set_ylim(max(curr_min, -100), min(curr_max, 100))
            else:
                ax.autoscale(enable=True, axis='y')
                ax.relim()
                ax.autoscale_view(scalex=False, scaley=True)

            self.canvas.draw_idle()

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
            df (pd.DataFrame): Metrics data
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
            print('Warning: Invalid metrics data')
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

        Args:
            df (pd.DataFrame): Metrics data for table
            df_plot (pd.DataFrame): Metrics plot data for charts
        """
        self._set_charts_data(df_plot)
        self._set_table_data(df)

    def clear(self):
        """Clear data on panel"""
        # clear chart
        self._set_charts_data(None)
        # clear table
        self._set_table_data(None)
