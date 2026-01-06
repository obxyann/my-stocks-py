import tkinter as tk
from tkinter import messagebox, ttk

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import sv_ttk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from database.stock import StockDatabase
from load_stock import load_stock
from screening.index import SCREENING_METHODS

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


class AutoScrollbar(ttk.Scrollbar):
    """A scrollbar that hides itself if it's not needed.
    Only works if you use the pack geometry manager.
    """

    def set(self, lo, hi):
        if float(lo) <= 0.0 and float(hi) >= 1.0:
            self.pack_forget()
        else:
            if not self.winfo_ismapped():
                self.pack(side='right', fill='y')
        ttk.Scrollbar.set(self, lo, hi)


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

        # combobox: Screening Method [v]
        methods = list(SCREENING_METHODS.keys())
        self.method_combo = ttk.Combobox(
            tool_bar, values=methods, width=12, state='readonly'
        )
        self.method_combo.pack(side='left', padx=6)
        self.method_combo.bind('<<ComboboxSelected>>', self.on_select_method)

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

        # buttons: [Load][Export]
        btn_bar = ttk.Frame(panel)
        btn_bar.pack(side='bottom', fill='x', pady=6)
        ttk.Button(btn_bar, text='Load').pack(side='left', padx=6)
        ttk.Button(btn_bar, text='Save').pack(side='left')

        # table: | Code | Name |
        columns = ('code', 'name')
        self.stock_list = ttk.Treeview(
            panel, columns=columns, show='headings', height=15
        )
        self.stock_list.heading('code', text='Code')
        self.stock_list.heading('name', text='Name')
        self.stock_list.column('code', width=40)  # , anchor="center")
        self.stock_list.column('name', width=100)

        # add scrollbar
        scrollbar = AutoScrollbar(
            panel, orient='vertical', command=self.stock_list.yview
        )
        self.stock_list.configure(yscrollcommand=scrollbar.set)

        self.stock_list.pack(side='left', fill='both', expand=True)
        self.stock_list.bind('<<TreeviewSelect>>', self.on_select_stock)

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

        # create chart at top
        self._create_revenue_chart(panel)

        # create table below chart
        self._create_revenue_table(panel)

        return panel

    def _create_revenue_chart(self, parent):
        """Create revenue chart with seaborn

        Args:
            parent: Parent widget
        """
        # create figure with dark background matching app theme
        self.revenue_fig, self.revenue_ax = plt.subplots(figsize=(8, 2.5))

        # set style
        sns.set_style('darkgrid')

        # create secondary y-axis for price
        self.revenue_ax2 = self.revenue_ax.twinx()

        # create canvas and pack
        self.revenue_canvas = FigureCanvasTkAgg(self.revenue_fig, master=parent)
        self.revenue_canvas.get_tk_widget().pack(side='top', fill='x', padx=4, pady=4)

        # set initial empty state
        self.revenue_ax.set_xlabel('')
        self.revenue_ax.set_ylabel('Revenue')
        self.revenue_ax2.set_ylabel('Price')
        self.revenue_fig.tight_layout()
        self.revenue_canvas.draw()

    def _create_revenue_table(self, parent):
        """Create revenue data table

        Args:
            parent: Parent widget
        """
        # container for table and scrollbar
        table_frame = ttk.Frame(parent)
        table_frame.pack(side='top', fill='both', expand=True)

        # table: | year_month | revence | ...
        columns = ('year_month', 'revence', 'revence_mom', 'revence_ly', 'revence_yoy', 'revence_ytd', 'revence_ytd_yoy')  # fmt: skip
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

        # add scrollbar
        scrollbar = AutoScrollbar(table_frame, orient='vertical', command=table.yview)
        table.configure(yscrollcommand=scrollbar.set)

        table.pack(side='left', fill='both', expand=True)

        self.revenue_table = table

        return table_frame


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

        # add scrollbar
        scrollbar = AutoScrollbar(panel, orient='vertical', command=table.yview)
        table.configure(yscrollcommand=scrollbar.set)

        table.pack(side='left', fill='both', expand=True)

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

        # add scrollbar
        scrollbar = AutoScrollbar(panel, orient='vertical', command=table.yview)
        table.configure(yscrollcommand=scrollbar.set)

        table.pack(side='left', fill='both', expand=True)

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

        # clear revenue chart and table
        self.set_revenue_chart_data(pd.DataFrame())
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
            self.set_revenue_chart_data(data['revenue'], data['price'])
            self.set_revenue_table_data(data['revenue'])
        if 'financial' in data:
            self.set_financial_data(data['financial'])
        if 'metrics' in data:
            self.set_metrics_data(data['metrics'])

    def set_revenue_chart_data(self, df_revenue, df_price=None):
        """Set data to revenue chart

        Args:
            df_revenue: DataFrame with columns [year_month, revence, revenue_3ma]
            df_price: DataFrame with columns [year_month, price] (optional)
        """
        # clear axes
        self.revenue_ax.clear()
        self.revenue_ax2.clear()

        if df_revenue.empty:
            self.revenue_canvas.draw()
            return

        # prepare data - reverse to chronological order (oldest first)
        df_rev = df_revenue.iloc[::-1].reset_index(drop=True)

        x_labels = df_rev['year_month'].tolist()
        x_positions = range(len(x_labels))

        # plot revenue bars
        revenue_values = pd.to_numeric(df_rev['revence'], errors='coerce')
        self.revenue_ax.bar(
            x_positions,
            revenue_values,
            color='steelblue',
            alpha=0.7,
            label='Revenue',
            zorder=2,
        )

        # plot revenue_ma3 line if available
        if 'revenue_3ma' in df_rev.columns:
            ma3_values = pd.to_numeric(df_rev['revenue_3ma'], errors='coerce')
            self.revenue_ax.plot(
                x_positions,
                ma3_values,
                color='orange',
                linewidth=2,
                marker='',
                label='MA3',
                zorder=3,
            )

        # plot price line on secondary axis if available
        if df_price is not None and not df_price.empty:
            # reverse price data to chronological order
            df_p = df_price.iloc[::-1].reset_index(drop=True)

            # merge price with revenue data by year_month
            price_dict = dict(zip(df_p['year_month'], df_p['price']))
            price_values = [price_dict.get(ym, None) for ym in x_labels]

            self.revenue_ax2.plot(
                x_positions,
                price_values,
                color='lightgreen',
                linewidth=2,
                marker='',
                label='Price',
                zorder=4,
            )
            self.revenue_ax2.set_ylabel('Price', color='lightgreen')
            self.revenue_ax2.tick_params(axis='y', labelcolor='lightgreen')

        # set x-axis labels with interval to avoid crowding
        tick_interval = max(1, len(x_labels) // 12)
        tick_positions = list(range(0, len(x_labels), tick_interval))
        tick_labels = [x_labels[i] for i in tick_positions]

        self.revenue_ax.set_xticks(tick_positions)
        self.revenue_ax.set_xticklabels(
            tick_labels, rotation=45, ha='right', fontsize=8
        )

        # set labels
        self.revenue_ax.set_ylabel('Revenue', color='steelblue')
        self.revenue_ax.tick_params(axis='y', labelcolor='steelblue')

        # add legend
        lines1, labels1 = self.revenue_ax.get_legend_handles_labels()
        lines2, labels2 = self.revenue_ax2.get_legend_handles_labels()
        self.revenue_ax.legend(
            lines1 + lines2, labels1 + labels2, loc='upper left', fontsize=8
        )

        # adjust layout
        self.revenue_fig.tight_layout()
        self.revenue_canvas.draw()

    def set_revenue_table_data(self, df):
        """Set revenue data

        Args:
            df: pd.DataFrame containing revenue data (may have extra columns for chart)
        """
        if df.empty:
            return

        # check if dataframe has at least the required columns
        df_cols = df.columns.tolist()
        table_cols = self.revenue_table['columns']

        if len(df_cols) < len(table_cols):
            print('Warning: invalid revenue data')
            print(df.head(3))
            print('...')
            return

        # MEMO: don't need to update headers

        # clear old data
        self.revenue_table.delete(*self.revenue_table.get_children())

        # insert data (only use first N columns matching table columns)
        num_cols = len(table_cols)
        for _, row in df.iterrows():
            self.revenue_table.insert('', 'end', values=tuple(row.iloc[:num_cols]))

    def set_financial_data(self, df):
        """Set financial data

        Args:
            df: pd.DataFrame containing financial data
        """
        # check if column count matches
        if df.empty:
            return

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
        if df.empty:
            return

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

    def on_select_method(self, event=None):
        """Handle screening method selection

        Args:
            event: Combobox selection event
        """
        selected = self.method_combo.get()

        if selected not in SCREENING_METHODS:
            return

        # get list function and call it
        list_func = SCREENING_METHODS[selected]

        df_stocks = list_func(self.db)

        # set data to stock list
        self.set_stock_list(df_stocks)

    def on_select_stock(self, event):
        """Handle stock list selection

        Args:
            event: Treeview selection event
        """
        selection = self.stock_list.selection()

        if not selection:
            return

        item = self.stock_list.item(selection[0])
        values = item['values']

        if values:
            code = str(values[0])
            self.on_view_stock(code)

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
    root.geometry('960x720')

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
