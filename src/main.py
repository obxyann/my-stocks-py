import tkinter as tk
from tkinter import messagebox, ttk

import pandas as pd
import sv_ttk

from database.stock import StockDatabase
from load_stock import load_stock

# global app
app = None


def initialize_database():
    """Initialize database"""
    try:
        # initialize database
        db = StockDatabase()

        # TODO: validate...

        return db

    except Exception as error:
        print(f'Database initialization failed: {error}')
        raise


class StockApp(ttk.Frame):
    def __init__(self, master, db):
        """Initialize the application

        Args:
            master: The root window
            db: StockDatabase instance
        """
        super().__init__(master)

        # set database
        self.db = db

        # set ui style
        self.set_style('dark')

        # pack to root, fit to window
        self.pack(fill='both', expand=True)

        # create UI components
        self.create_toolbar()

        self.create_main_layout()

        self.create_status_bar()

    def set_style(self, theme):
        """Set the UI style and theme

        Args:
            theme (str): Name of theme to apply
        """
        # set theme
        sv_ttk.set_theme(theme)

        dark = sv_ttk.get_theme() == 'dark'

        self.dark_var = tk.BooleanVar(value=dark)

        # configure ttk styles
        style = ttk.Style()

        style.configure('Toolbar.TFrame', pady=4)

    def toggle_theme(self):
        """Toggle between light and dark themes"""
        sv_ttk.toggle_theme()

    ########################
    # create UI components #
    ########################

    def create_toolbar(self):
        """Create the top toolbar"""
        tool_bar = ttk.Frame(self, style='Toolbar.TFrame')
        tool_bar.pack(side='top', pady=6, fill='x')

        # buttons: [Load][Export]
        ttk.Button(tool_bar, text='Load').pack(side='left', padx=6)
        ttk.Button(tool_bar, text='Export').pack(side='left')

        # input: Stock Code [___]
        ttk.Label(tool_bar, text='Stock Code').pack(side='left', padx=6)
        self.search_code = ttk.Entry(tool_bar, width=12)
        self.search_code.pack(side='left')
        self.search_code.bind(
            '<Return>', lambda e: self.on_view_stock(self.search_code.get())
        )

        # toggle: [1|0] Dark
        ttk.Checkbutton(
            tool_bar,
            text='Dark',
            style='Switch.TCheckbutton',
            variable=self.dark_var,
            command=self.toggle_theme,
        ).pack(side='right', padx=6)

    def create_main_layout(self):
        """Create main layout with split panels"""
        paned = ttk.PanedWindow(self, orient='horizontal')
        paned.pack(fill='both', expand=True)

        # panels: [stock list | stock view]
        paned.add(self.create_stock_list(paned), weight=1)
        paned.add(self.create_stock_view(paned), weight=4)

    def create_stock_list(self, parent):
        """Create the stock list panel

        Args:
            parent: Parent widget

        Returns:
            ttk.Frame: Created panel
        """
        panel = ttk.Frame(parent)  # , width=200)

        # table: | Code | Name |
        columns = ('code', 'name')
        self.stock_list = ttk.Treeview(
            panel, columns=columns, show='headings', height=15
        )
        self.stock_list.heading('code', text='Code')
        self.stock_list.heading('name', text='Name')
        self.stock_list.column('code', width=36)  # , anchor="center")
        self.stock_list.column('name', width=100)
        self.stock_list.pack(fill='both', expand=True)

        return panel

    def create_stock_view(self, parent):
        """Create the stock view panel

        Args:
            parent: Parent widget

        Returns:
            ttk.Frame: Created panel
        """
        panel = ttk.Frame(parent)

        # control bar
        control_bar = ttk.Frame(panel)
        control_bar.pack(side='top', pady=(0, 6), fill='x')

        # label: Stock Code Name
        self.stock_name = ttk.Label(control_bar, text='---- ----')
        self.stock_name.pack(side='left', padx=6)

        # tabs container
        tabs = ttk.Notebook(panel)
        tabs.pack(fill='both', expand=True, padx=(0, 4))

        # tab panels: _Price_Revenues_Financials_Metrics_
        tabs.add(self.create_price_panel(tabs), text='Price')
        tabs.add(self.create_revenue_panel(tabs), text='Revenues')
        tabs.add(self.create_financial_panel(tabs), text='Financials')
        tabs.add(self.create_metrics_panel(tabs), text='Metrics')

        return panel

    def create_price_panel(self, parent):
        """Create the price chart tab panel

        Args:
            parent: Parent widget

        Returns:
            ttk.Frame: Created panel
        """
        panel = ttk.Frame(parent)

        # control bar
        control_bar = ttk.Frame(panel)
        control_bar.pack(side='top', pady=4, fill='x')

        # combobox: Period [D|v]
        options = ['D', 'M', 'Y']
        ttk.Label(control_bar, text='Period').pack(side='left', padx=(6, 4))
        period = ttk.Combobox(control_bar, values=options, width=2, state='readonly')
        period.current(0)
        period.pack(side='left')

        # TODO:
        ttk.Label(panel, text='TODO: price chart area').pack()

        return panel

    def create_revenue_panel(self, parent):
        """Create the revenue data tab panel

        Args:
            parent: Parent widget

        Returns:
            ttk.Frame: Created panel
        """
        panel = ttk.Frame(parent)

        # table: | year_month | revence | revence_mom | revence_ly | revence_yoy | revence_ytd | revence_ytd_yoy |
        columns = ('year_month', 'revence', 'revence_mom', 'revence_ly', 'revence_yoy', 'revence_ytd', 'revence_ytd_yoy')  # fmt: skip
        table = ttk.Treeview(panel, columns=columns, show='headings')

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
        table.pack(fill='both', expand=True)

        # TBD: dummy data
        # table.insert('', 'end', values=('2025/11', '13121753', '-5.48%', '16502520', '-20.49%', '136442,298', '-1.39%'))  # fmt: skip
        # table.insert('', 'end', values=('2025/10', '13882248', '4.33%', '16272067', '-14.69%', '123320,545', '1.20%'))  # fmt: skip
        # table.insert('', 'end', values=('2025/09', '13306676', '8.94%', '13325249', '-0.14%', '109438,297', '3.64%'))  # fmt: skip

        self.revenue_table = table

        return panel

    def create_financial_panel(self, parent):
        """Create the financial data tab panel

        Args:
            parent: Parent widget

        Returns:
            ttk.Frame: Created panel
        """
        panel = ttk.Frame(parent)

        # table: | item | period1 | ... | period8 |
        columns = ('item', 'period1', 'period2', 'period3', 'period4', 'period5', 'period6', 'period7', 'period8')  # fmt: skip
        table = ttk.Treeview(panel, columns=columns, show='headings')
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
        table.pack(fill='both', expand=True)

        # TBD: dummy data
        # table.insert('', 'end', values=('營業收入', '39067', '35354', '34956', '49018', '41075', '38969', '25545', '28348'))  # fmt: skip
        # table.insert('', 'end', values=('營業成本', '30223', '30008', '29063', '37602', '31106', '31513', '21657', '22043'))  # fmt: skip
        # table.insert('', 'end', values=('營業毛利', '8844', '5347', '5894', '11416', '9969', '7456', '3887', '6305'))  # fmt: skip

        self.financial_table = table

        return panel

    def create_metrics_panel(self, parent):
        """Create the metrics data tab panel

        Args:
            parent: Parent widget

        Returns:
            ttk.Frame: Created panel
        """
        panel = ttk.Frame(parent)

        # table: | item | period1 | ... | period8 |
        columns = ('item', 'period1', 'period2', 'period3', 'period4', 'period5', 'period6', 'period7', 'period8')  # fmt: skip
        table = ttk.Treeview(panel, columns=columns, show='headings')
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
        table.pack(fill='both', expand=True)

        # TBD: dummy data
        # table.insert('', 'end', values=('營業毛利率', '22.64', '15.12', '16.86', '23.29', '24.27', '19.13', '15.22 ', '2.24'))  # fmt: skip
        # table.insert('', 'end', values=('營業利益率', '13.16', '3.15', '6.58', '10.88', '15.26', '11.1', '4.7', '12.11'))  # fmt: skip
        # table.insert('', 'end', values=('稅前淨利率', '-25.9 ', '.34', '5.41', '15.32', '15.84', '14.02', '13.12', '13.46'))  # fmt: skip
        # table.insert('', 'end', values=('稅後淨利率', '-30.17', '2.07', '2.2', '10.73', '11.25', '9.01', '8.77', '8.82'))  # fmt: skip

        self.metrics_table = table

        return panel

    def create_status_bar(self):
        """Create the status bar at the bottom"""
        status_bar = ttk.Frame(self, style='Toolbar.TFrame')
        status_bar.pack(side='bottom', pady=6, fill='x')

        # label: 'message'
        self.status = ttk.Label(status_bar, text='Ready')
        self.status.pack(side='left', padx=6)

    #############################
    # set data to UI components #
    #############################

    def set_stock_list(self, df):
        """Set stock list data

        Args:
            df: pd.DataFrame containing stock data
        """
        # check if column count matches
        df_cols = df.columns.tolist()
        table_cols = self.stock_list['columns']

        if len(df_cols) != len(table_cols):
            print('Warning: invalid stock list data')
            print(df.head(3))
            print('...')
            return

        # clear table
        self.stock_list.delete(*self.stock_list.get_children())

        # insert data
        for _, row in df.iterrows():
            self.stock_list.insert('', 'end', values=tuple(row))

    def clear_stock_view(self):
        """Clear stock view"""
        # clear stock_name
        self.stock_name['text'] = '---- ----'

        # clear revenue_table
        self.revenue_table.delete(*self.revenue_table.get_children())

        # clear financial_table
        table_cols = self.financial_table['columns']

        for i in range(1, len(table_cols)):
            self.financial_table.heading(table_cols[i], text='YYYY.Q-')

        self.financial_table.delete(*self.financial_table.get_children())

        # clear metrics_table
        table_cols = self.metrics_table['columns']

        for i in range(1, len(table_cols)):
            self.metrics_table.heading(table_cols[i], text='YYYY.Q-')

        self.metrics_table.delete(*self.metrics_table.get_children())

    def set_stock_view(self, data):
        """set data of stock view

        Args:
            data (dict): dictionary containing metadata and DataFrames
                       - 'code_name': Stock code and name string
                       - 'revenue': Revenue data
                       - 'financial': Financial data
                       - 'metrics': Financial metrics data
        """
        self.clear_stock_view()

        code_name = data.get('code_name')
        if code_name:
            self.stock_name['text'] = code_name

        if 'revenue' in data:
            self.set_revenue_data(data['revenue'])
        if 'financial' in data:
            self.set_financial_data(data['financial'])
        if 'metrics' in data:
            self.set_metrics_data(data['metrics'])

    def set_revenue_data(self, df):
        """Set revenue data

        Args:
            df: pd.DataFrame containing revenue data
        """
        # check if column count matches
        df_cols = df.columns.tolist()
        table_cols = self.revenue_table['columns']

        if len(df_cols) != len(table_cols):
            print('Warning: invalid revenue data')
            print(df.head(3))
            print('...')
            return

        # MEMO: don't need to update headers

        # clear old data
        self.revenue_table.delete(*self.revenue_table.get_children())

        # insert data
        for _, row in df.iterrows():
            self.revenue_table.insert('', 'end', values=tuple(row))

    def set_financial_data(self, df):
        """Set financial data

        Args:
            df: pd.DataFrame containing financial data
        """
        # check if column count matches
        df_cols = df.columns.tolist()
        table_cols = self.financial_table['columns']

        if len(df_cols) != len(table_cols):
            print('Warning: invalid financial data')
            print(df.head(3))
            print('...')
            return

        # update headers
        for i, col_name in enumerate(df_cols):
            self.financial_table.heading(table_cols[i], text=col_name)

        # clear old data
        self.financial_table.delete(*self.financial_table.get_children())

        # insert data
        for _, row in df.iterrows():
            self.financial_table.insert('', 'end', values=tuple(row))

    def set_metrics_data(self, df):
        """Set metrics data

        Args:
            df: pd.DataFrame containing metrics data
        """
        # check if column count matches
        df_cols = df.columns.tolist()
        table_cols = self.metrics_table['columns']

        if len(df_cols) != len(table_cols):
            print('Warning: invalid metrics data')
            print(df.head(3))
            print('...')
            return

        # update headers
        for i, col_name in enumerate(df_cols):
            self.metrics_table.heading(table_cols[i], text=col_name)

        # clear old data
        self.metrics_table.delete(*self.metrics_table.get_children())

        # insert data
        for _, row in df.iterrows():
            self.metrics_table.insert('', 'end', values=tuple(row))

    ###########
    # actions #
    ###########

    def on_view_stock(self, stock_code):
        """View stock data for the given code

        Args:
            stock_code (str): The stock code to view
        """
        # check if stock exists
        df = self.db.get_stock_by_code(stock_code)

        if df.empty:
            messagebox.showinfo('Message', '無此股票')
            return

        # validate security and business type
        row = df.iloc[0]
        if row['security_type'] != 'stk' or row['business_type'] != 'ci':
            code = row['code']
            name = row['name']
            messagebox.showinfo('Message', f'{code} {name} 不是一般工商業股票')

        # load and set data
        stock_data = load_stock(stock_code, self.db)

        self.set_stock_view(stock_data)


def test(app):
    """Test data panels with dummy data

    Args:
        app: StockApp instance
    """
    # stock list dummy data
    columns_stocks = ('code', 'name')
    data_stocks = [
        ('2330', '台積電'),
        ('2317', '鴻海'),
    ]
    df_stocks = pd.DataFrame(data_stocks, columns=columns_stocks)

    # set data to stock list
    app.set_stock_list(df_stocks)

    # revenue dummy data
    # fmt: off
    columns_rev = (
        'year_month', 'revence', 'revence_mom', 'revence_ly', 'revence_yoy', 'revence_ytd', 'revence_ytd_yoy'
    )
    data_rev = [
        ('2025/11', '13121753', '-5.48%', '16502520', '-20.49%', '136442,298', '-1.39%'),
        ('2025/10', '13882248', '4.33%', '16272067', '-14.69%', '123320,545', '1.20%'),
        ('2025/09', '13306676', '8.94%', '13325249', '-0.14%', '109438,297', '3.64%'),
    ]
    # fmt: on
    df_rev = pd.DataFrame(data_rev, columns=columns_rev)

    # financial dummy data
    # fmt: off
    columns_fin = (
        'Item', '2025.Q3', '2025.Q2', '2025.Q1', '2024.Q4', '2024.Q3', '2024.Q2', '2024.Q1', '2023.Q4'
    )
    data_fin = [
        ('營業收入', '39067', '35354', '34956', '49018', '41075', '38969', '25545', '28348'),
        ('營業成本', '30223', '30008', '29063', '37602', '31106', '31513', '21657', '22043'),
        ('營業毛利', '8844', '5347', '5894', '11416', '9969', '7456', '3887', '6305'),
    ]
    # fmt: on
    df_fin = pd.DataFrame(data_fin, columns=columns_fin)

    # metrics dummy data
    # fmt: off
    columns_ind = (
        'Item', '2025.Q3', '2025.Q2', '2025.Q1', '2024.Q4', '2024.Q3', '2024.Q2', '2024.Q1', '2023.Q4'
    )
    data_ind = [
        ('營業毛利率', '22.64', '15.12', '16.86', '23.29', '24.27', '19.13', '15.22 ', '2.24'),
        ('營業利益率', '13.16', '3.15', '6.58', '10.88', '15.26', '11.1', '4.7', '12.11'),
        ('稅前淨利率', '-25.9 ', '.34', '5.41', '15.32', '15.84', '14.02', '13.12', '13.46'),
        ('稅後淨利率', '-30.17', '2.07', '2.2', '10.73', '11.25', '9.01', '8.77', '8.82'),
    ]
    # fmt: on
    df_ind = pd.DataFrame(data_ind, columns=columns_ind)

    # set data to stock view
    app.set_stock_view(
        {
            'code_name': '1101 台泥',
            'revenue': df_rev,
            'financial': df_fin,
            'metrics': df_ind,
        }
    )


def main():
    """Main entry point of the application"""
    root = tk.Tk()
    root.title('Stock Analysis Tool')
    root.geometry('1024x600')

    # initialize database
    db = initialize_database()

    # initialize app
    global app
    app = StockApp(root, db)

    # test(app)

    # run app
    root.mainloop()


if __name__ == '__main__':
    main()
