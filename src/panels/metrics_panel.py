from tkinter import ttk

import pandas as pd
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
        self.ax_empty = self.fig.add_subplot(224)

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
        self.style_helper.set_chart_style(self.fig, self.ax_profit)
        self.style_helper.set_chart_style(self.fig, self.ax_profit_qoq)
        self.style_helper.set_chart_style(self.fig, self.ax_profit_yoy)
        self.style_helper.set_chart_style(self.fig, self.ax_empty)

        self.ax_empty.axis('off')

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

        # TBD ax.grid(True, axis='y', linestyle=':', alpha=0.2, color='#FFFFFF')

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

    def _set_charts_data(self, df):
        """Set data to chart

        Args:
            df (pd.DataFrame): Metrics data
        """
        # clear existing plots
        self.ax_profit.clear()
        self.ax_profit_qoq.clear()
        self.ax_profit_yoy.clear()
        # self.ax_empty.clear()

        # self.ax_empty.axis('off')

        # check data
        if df is None or df.empty:
            self.canvas.draw_idle()
            return

        # prepare data
        x_labels, series = self._extract_profit_series(df)
        if not x_labels:
            self.canvas.draw_idle()
            return

        # plot charts
        self._plot_profit(x_labels, series)
        self._plot_profit_qoq_chart(x_labels, series)
        self._plot_profit_yoy_chart(x_labels, series)

        # adjust layout
        self.fig.tight_layout()

        self.canvas.draw_idle()

    def _extract_profit_series(self, df):
        """Extract profitability series from data

        Args:
            df (pd.DataFrame): Metrics data

        Returns:
            tuple: (x_labels, series_dict)
        """
        if df is None or df.empty or len(df.columns) < 2:
            return [], {}

        item_col = df.columns[0]
        period_cols = df.columns[1:].tolist()

        parsed = []
        for col in period_cols:
            year, quarter = self._parse_period(col)
            if year is None or quarter is None:
                continue
            parsed.append((col, year, quarter))

        parsed.sort(key=lambda x: (x[1], x[2]))
        if not parsed:
            return [], {}

        sorted_cols = [c for c, _, _ in parsed]
        x_labels = [f'{y}.Q{q}' for _, y, q in parsed]

        row_labels = {
            'gross_margin': '營業毛利率',
            'opr_margin': '營業利益率',
            'net_margin': '稅後淨利率',
            'gross_margin_qoq': '毛利率季增率',
            'opr_margin_qoq': '營業利益率季增率',
            'net_margin_qoq': '稅後淨利率季增率',
            'gross_margin_yoy': '毛利率年增率',
            'opr_margin_yoy': '營業利益率年增率',
            'net_margin_yoy': '稅後淨利率年增率',
        }

        series = {}
        for key, label in row_labels.items():
            row = df[df[item_col] == label]
            if row.empty:
                values = [None] * len(sorted_cols)
            else:
                values = row.iloc[0][sorted_cols].tolist()

            series[key] = pd.to_numeric(pd.Series(values), errors='coerce').tolist()

        return x_labels, series

    def _parse_period(self, label):
        """Parse period string to year and quarter

        Args:
            label (str): Period string in format 'YYYY.QX'

        Returns:
            tuple: (year, quarter) or (None, None) if parsing fails
        """
        try:
            parts = str(label).split('.Q')

            if len(parts) != 2:
                return None, None

            year = int(parts[0])
            quarter = int(parts[1])

            if quarter < 1 or quarter > 4:
                return None, None
            return year, quarter

        except Exception:
            return None, None

    def _plot_profit(self, x_labels, series):
        """Plot profitability lines on axis

        Args:
            x_labels (list): List of x-axis labels
            series (dict): Dictionary containing data series
        """
        ax = self.ax_profit

        # Reapply styling that were reset by ax.clear()
        self._set_axes_style(ax, 'Profitability (%)')

        x_indices = range(len(x_labels))

        ax.plot(
            x_indices,
            series.get('gross_margin', []),
            color='#599FDC',
            linewidth=2,
            label='gross',
        )
        ax.plot(
            x_indices,
            series.get('opr_margin', []),
            color='#E66D5F',
            linewidth=2,
            label='opr',
        )
        ax.plot(
            x_indices,
            series.get('net_margin', []),
            color='#66BB6A',
            linewidth=2,
            label='net',
        )

        # format x-axis ticks
        self._format_x_ticks(ax, x_labels)

        # legends
        self._apply_legend(ax)

        # title
        # ax.set_title('Profitability', color='#FFFFFF')

    def _plot_profit_qoq_chart(self, x_labels, series):
        """Plot profitability QoQ bars on axis

        Args:
            x_labels (list): List of x-axis labels
            series (dict): Dictionary containing data series
        """
        ax = self.ax_profit_qoq

        # Reapply styling that were reset by ax.clear()
        self._set_axes_style(ax, 'Profit QoQ (%)')

        num_ticks = len(x_labels)
        x = list(range(num_ticks))
        width = 0.25

        ax.bar(
            [i - width for i in x],
            series.get('gross_margin_qoq', []),
            width=width,
            color='#599FDC',
            alpha=0.8,
            label='gross',
        )
        ax.bar(
            x,
            series.get('opr_margin_qoq', []),
            width=width,
            color='#E66D5F',
            alpha=0.8,
            label='opr',
        )
        ax.bar(
            [i + width for i in x],
            series.get('net_margin_qoq', []),
            width=width,
            color='#66BB6A',
            alpha=0.8,
            label='net',
        )

        # format x-axis ticks
        self._format_x_ticks(ax, x_labels)

        # legends
        self._apply_legend(ax)

        # title
        # ax.set_title('Profitability QoQ', color='#FFFFFF')

    def _plot_profit_yoy_chart(self, x_labels, series):
        """Plot profitability YoY bars on axis

        Args:
            x_labels (list): List of x-axis labels
            series (dict): Dictionary containing data series
        """
        ax = self.ax_profit_yoy

        # Reapply styling that were reset by ax.clear()
        self._set_axes_style(ax, 'Profit YoY (%)')

        num_ticks = len(x_labels)
        x = list(range(num_ticks))
        width = 0.25

        ax.bar(
            [i - width for i in x],
            series.get('gross_margin_yoy', []),
            width=width,
            color='#599FDC',
            alpha=0.8,
            label='gross',
        )
        ax.bar(
            x,
            series.get('opr_margin_yoy', []),
            width=width,
            color='#E66D5F',
            alpha=0.8,
            label='opr',
        )
        ax.bar(
            [i + width for i in x],
            series.get('net_margin_yoy', []),
            width=width,
            color='#66BB6A',
            alpha=0.8,
            label='net',
        )

        # format x-axis ticks
        self._format_x_ticks(ax, x_labels)

        # legends
        self._apply_legend(ax)

        # title
        # ax.set_title('Profitability YoY', color='#FFFFFF')

    def _format_x_ticks(self, ax, x_labels, num_max_ticks=4):
        """Format x-axis ticks and labels with step size

        Args:
            ax: Matplotlib axis to format
            x_labels (list): List of all available x labels
            num_max_ticks (int): Maximum number of ticks to show
        """
        num_ticks = len(x_labels)
        if num_ticks == 0:
            return

        # format x-axis ticks
        step = max(1, num_ticks // num_max_ticks)

        tick_positions = list(range(0, num_ticks, step))
        tick_labels = [x_labels[i] for i in tick_positions]

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

    def set_data(self, df):
        """Set data to panel

        NOTE: Data has been pivoted for table from database (in load_stock.py)

        Args:
            df (pd.DataFrame): Metrics data
        """
        self._set_charts_data(df)
        self._set_table_data(df)

    def clear(self):
        """Clear data on panel"""
        # clear chart
        self._set_charts_data(None)
        # clear table
        self._set_table_data(None)
