from tkinter import ttk

from panels.auto_scrollbar import AutoScrollbar


class StockListPanel(ttk.Frame):
    """Stock list panel with treeview

    Args:
        parent: Parent widget
        on_select_callback: Callback function when stock is selected
    """

    def __init__(self, parent, on_select_callback=None):
        super().__init__(parent)

        # callback on action
        self.on_select_callback = on_select_callback

        # create button bar at bottom (must be placed first)
        self._create_button_bar().pack(side='bottom', fill='x', pady=6)

        # create table at top (so we can fill remaining space)
        self._create_table().pack(side='top', fill='both', expand=True)

    def _create_button_bar(self):
        """Create button bar

        Returns:
            ttk.Frame: Created bar
        """
        # container for widgets
        bar = ttk.Frame(self)

        # buttons: [Load][Export]
        ttk.Button(bar, text='Load').pack(side='left', padx=6)
        ttk.Button(bar, text='Save').pack(side='left')

        return bar

    def _create_table(self):
        """Create table

        Returns:
            ttk.Frame: Created table
        """
        # container for widgets
        table_frame = ttk.Frame(self)

        # table: | Code | Name |
        columns = ('code', 'name')

        table = ttk.Treeview(self, columns=columns, show='headings', height=15)

        table.heading('code', text='Code')
        table.heading('name', text='Name')

        table.column('code', width=40)
        table.column('name', width=100)

        # scrollbar: | table ||
        scrollbar = AutoScrollbar(self, orient='vertical', command=table.yview)

        table.configure(yscrollcommand=scrollbar.set)

        table.pack(side='left', fill='both', expand=True)

        table.bind('<<TreeviewSelect>>', self._on_select)

        self.table = table

        return table_frame

    def _on_select(self, event):
        """Handle stock list selection

        Args:
            event: Treeview selection event
        """
        selection = self.table.selection()

        if not selection:
            return

        item = self.table.item(selection[0])
        values = item['values']

        if values and self.on_select_callback:
            code = str(values[0])
            self.on_select_callback(code)

    def set_data(self, df):
        """Set data to stock list

        Args:
            df: pd.DataFrame containing stock data
        """
        # clear old data
        self.table.delete(*self.table.get_children())

        if df is None or df.empty:
            return

        # check if dataframe has at least the required columns
        df_cols = df.columns.tolist()
        table_cols = self.table['columns']

        if len(df_cols) < len(table_cols):
            print('Warning: invalid stock list data')
            print(df.head(3))
            print('...')
            return

        # insert data
        for _, row in df.iterrows():
            self.table.insert('', 'end', values=tuple(row))
