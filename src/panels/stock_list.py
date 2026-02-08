from tkinter import filedialog, messagebox, ttk

import pandas as pd

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

        # stored dataframe
        self.current_df = None

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
        ttk.Button(bar, text='Load', command=self.read_file).pack(side='left', padx=6)
        ttk.Button(bar, text='Save', command=self.save_file).pack(side='left')

        return bar

    def _create_table(self):
        """Create table for stock list

        Returns:
            ttk.Frame: Created table
        """
        # container for widgets
        table_frame = ttk.Frame(self)

        # table: | Code | Name | Score |
        columns = ('code', 'name', 'score')

        table = ttk.Treeview(table_frame, columns=columns, show='headings', height=15)

        table.heading('code', text='Code')
        table.heading('name', text='Name')
        table.heading('score', text='Score')

        table.column('code', width=40)
        table.column('name', width=80)
        table.column('score', width=50)

        # scrollbar: | table ||
        scrollbar = AutoScrollbar(table_frame, orient='vertical', command=table.yview)

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
            df (pd.DataFrame): Stock data
        """
        # save df
        self.current_df = df

        # clear old data
        self.table.delete(*self.table.get_children())

        if df is None or df.empty:
            return

        # check if dataframe has at least the required columns
        df_cols = df.columns.tolist()
        table_cols = self.table['columns']

        if len(df_cols) < len(table_cols):
            print('Warning: Invalid stock list data')
            print(df.head(3))
            print('...')
            return

        # insert data
        for _, row in df.iterrows():
            self.table.insert('', 'end', values=tuple(row))

        # reset scroll position to top
        self.table.yview_moveto(0)

        # force UI update to refresh scrollbar range
        self.update_idletasks()

    def read_file(self):
        """Browse to read csv file and load it to table"""
        file_path = filedialog.askopenfilename(
            filetypes=[('CSV files', '*.csv'), ('All files', '*.*')]
        )
        if file_path:
            try:
                # Read all columns as string to avoid type inference issues (e.g. leading zeros in stock codes)
                df = pd.read_csv(file_path, dtype=str)

                # validate columns
                required_cols = ['code', 'name']
                all_cols = list(self.table['columns'])

                if not set(required_cols).issubset(df.columns):
                    messagebox.showinfo('Message', 'CSV 格式不正確')
                    print(f'Error: CSV file must contain columns: {required_cols}')
                    return

                # handle optional columns
                if 'score' not in df.columns:
                    df['score'] = '0'

                # keep only required columns and in correct order
                df = df[all_cols]

                self.set_data(df)

            except Exception as e:
                print(f'Error: Failed to read file: {e}')

    def save_file(self):
        """Browse to save current stock list to csv file"""
        if self.current_df is None or self.current_df.empty:
            messagebox.showinfo('Message', '尚無資料')
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension='.csv',
            filetypes=[('CSV files', '*.csv'), ('All files', '*.*')],
        )
        if file_path:
            try:
                self.current_df.to_csv(file_path, index=False)

            except Exception as e:
                print(f'Error: Failed to save file: {e}')
