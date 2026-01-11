from tkinter import ttk

from panels.auto_scrollbar import AutoScrollbar


class FinancialPanel(ttk.Frame):
    """Financial panel with chart and table

    Args:
        parent: Parent widget
        style_helper: Object with set_chart_style and set_axes_style methods
    """

    def __init__(self, parent, style_helper):
        super().__init__(parent)

        # this is how to set styles
        self.style_helper = style_helper

        # create chart at top
        self._create_chart().pack(side='top', fill='x')

        # create table below chart
        self._create_table().pack(side='top', fill='both', expand=True)

    def _create_chart(self):
        """Create financial chart

        Returns:
            ttk.Frame: Created chart
        """
        # container for chart
        chart_frame = ttk.Frame(self)

        return chart_frame

    def _create_table(self):
        """Create financial table

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

    def set_data(self, df):
        """Set financial data

        Args:
            df: pd.DataFrame containing financial data
        """
        if df.empty:
            return

        # check if column count matches
        df_cols = df.columns.tolist()
        table_cols = self.table['columns']

        if len(df_cols) != len(table_cols):
            print('Warning: invalid financial data')
            print(df.head(3))
            print('...')
            return

        # update headers
        for i, col_name in enumerate(df_cols):
            self.table.heading(table_cols[i], text=col_name)

        # clear old data
        self.table.delete(*self.table.get_children())

        # insert data
        for _, row in df.iterrows():
            self.table.insert('', 'end', values=tuple(row))

    def clear(self):
        """Clear data on panel"""
        # reset headers
        table_cols = self.table['columns']

        for i in range(1, len(table_cols)):
            self.table.heading(table_cols[i], text='YYYY.Q-')

        # clear table
        self.table.delete(*self.table.get_children())
