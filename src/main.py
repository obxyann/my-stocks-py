import tkinter as tk
from tkinter import ttk

import sv_ttk


class StockApp(ttk.Frame):
    def __init__(self, master):
        super().__init__(master)

        # set ui style
        self.set_style('dark')

        # pack to root
        self.pack(fill='both', expand=True)

        # create all UI components
        self.create_toolbar()

        self.create_main_layout()

        self.create_status_bar()

    def set_style(self, theme):
        # set theme
        sv_ttk.set_theme(theme)

        dark = sv_ttk.get_theme() == 'dark'

        self.dark_var = tk.BooleanVar(value=dark)

        # configure ttk styles
        style = ttk.Style()

        style.configure('Toolbar.TFrame', pady=4)

    def toggle_theme(self):
        sv_ttk.toggle_theme()

    def create_toolbar(self):
        """Top toolbar"""
        tool_bar = ttk.Frame(self, style='Toolbar.TFrame')
        tool_bar.pack(side='top', pady=6, fill='x')

        # buttons: [Load][Export]
        ttk.Button(tool_bar, text='Load').pack(side='left', padx=6)
        ttk.Button(tool_bar, text='Export').pack(side='left')

        # toggle: [1|0] Dark
        ttk.Checkbutton(
            tool_bar,
            text='Dark',
            style='Switch.TCheckbutton',
            variable=self.dark_var,
            command=self.toggle_theme,
        ).pack(side='right', padx=6)

    def create_main_layout(self):
        """Main layout: split left and right panels"""
        paned = ttk.PanedWindow(self, orient='horizontal')
        paned.pack(fill='both', expand=True)

        # panels: [stock list | stock view]
        paned.add(self.create_stock_list(paned), weight=1)
        paned.add(self.create_stock_view(paned), weight=4)

    def create_stock_list(self, parent):
        """Panel: stock list"""
        panel = ttk.Frame(parent, width=200)

        # table: | Code | Name |
        columns = ('code', 'name')
        self.stock_list = ttk.Treeview(
            panel, columns=columns, show='headings', height=15
        )
        self.stock_list.heading('code', text='Code')
        self.stock_list.heading('name', text='Name')
        self.stock_list.column('code', width=30)  # , anchor="center")
        self.stock_list.column('name', width=120)
        self.stock_list.pack(fill='both', expand=True)

        # TBD: dummy data
        self.stock_list.insert('', 'end', values=('2330', '台積電'))
        self.stock_list.insert('', 'end', values=('2317', '鴻海'))

        return panel

    def create_stock_view(self, parent):
        """Panel: stock view"""
        panel = ttk.Frame(parent)

        # control bar
        control_bar = ttk.Frame(panel)
        control_bar.pack(side='top', pady=(0, 6), fill='x')

        # input: Stock Code [___]
        ttk.Label(control_bar, text='Stock Code').pack(side='left', padx=(6, 4))
        self.stock_code = ttk.Entry(control_bar, width=12)
        self.stock_code.pack(side='left')

        # tabs container
        tabs = ttk.Notebook(panel)
        tabs.pack(fill='both', expand=True, padx=(0, 4))

        # tab panels: _Price_Revenues_Financials_Indicators_
        tabs.add(self.create_price_panel(tabs), text='Price')
        tabs.add(self.create_revenue_panel(tabs), text='Revenues')
        tabs.add(self.create_financial_panel(tabs), text='Financials')
        tabs.add(self.create_indicator_panel(tabs), text='Indicators')

        return panel

    def create_price_panel(self, parent):
        """Tab panel: price chart"""
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
        """Tab panel: revenue"""
        panel = ttk.Frame(parent)

        # table: | year_month | revence | revence_mom | revence_ly | revence_yoy | revence_ytd | revence_ytd_yoy |
        columns = ('year_month', 'revence', 'revence_mom', 'revence_ly', 'revence_yoy', 'revence_ytd', 'revence_ytd_yoy')  # fmt: skip
        table = ttk.Treeview(panel, columns=columns, show='headings')

        table.heading('year_month', text='年/月')
        table.heading('revence', text='營收')
        table.heading('revence_mom', text='MoM')
        table.heading('revence_ly', text='去年同期')
        table.heading('revence_yoy', text='YoY')
        table.heading('revence_ytd', text='累計營收')
        table.heading('revence_ytd_yoy', text='YoY')
        table.column('year_month', width=36)
        table.column('revence', width=80, anchor='e')
        table.column('revence_mom', width=40, anchor='e')
        table.column('revence_ly', width=80, anchor='e')
        table.column('revence_yoy', width=40, anchor='e')
        table.column('revence_ytd', width=80, anchor='e')
        table.column('revence_ytd_yoy', width=40, anchor='e')
        table.pack(fill='both', expand=True)

        # TBD: dummy data
        table.insert('', 'end', values=('2025/11', '13121753', '-5.48%', '16502520', '-20.49%', '136442,298', '-1.39%'))  # fmt: skip
        table.insert('', 'end', values=('2025/10', '13882248', '4.33%', '16272067', '-14.69%', '123320,545', '1.20%'))  # fmt: skip
        table.insert('', 'end', values=('2025/09', '13306676', '8.94%', '13325249', '-0.14%', '109438,297', '3.64%'))  # fmt: skip

        return panel

    def create_financial_panel(self, parent):
        """Tab panel: financial"""
        panel = ttk.Frame(parent)

        # table: | item | period1 | ... | period8 |
        columns = ('item', 'period1', 'period2', 'period3', 'period4', 'period5', 'period6', 'period7', 'period8')  # fmt: skip
        table = ttk.Treeview(panel, columns=columns, show='headings')
        table.heading('item', text='Item')
        table.heading('period1', text='2025.Q3')
        table.heading('period2', text='2025.Q2')
        table.heading('period3', text='2025.Q1')
        table.heading('period4', text='2024.Q4')
        table.heading('period5', text='2024.Q3')
        table.heading('period6', text='2024.Q2')
        table.heading('period7', text='2024.Q1')
        table.heading('period8', text='2023.Q4')
        table.column('item', width=80)
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
        table.insert('', 'end', values=('營業收入', '39067', '35354', '34956', '49018', '41075', '38969', '25545', '28348'))  # fmt: skip
        table.insert('', 'end', values=('營業成本', '30223', '30008', '29063', '37602', '31106', '31513', '21657', '22043'))  # fmt: skip
        table.insert('', 'end', values=('營業毛利', '8844', '5347', '5894', '11416', '9969', '7456', '3887', '6305'))  # fmt: skip

        return panel

    def create_indicator_panel(self, parent):
        """Tab panel: indicator"""
        panel = ttk.Frame(parent)

        # table: | item | period1 | ... | period8 |
        columns = ('item', 'period1', 'period2', 'period3', 'period4', 'period5', 'period6', 'period7', 'period8')  # fmt: skip
        table = ttk.Treeview(panel, columns=columns, show='headings')
        table.heading('item', text='Item')
        table.heading('period1', text='2025.Q3')
        table.heading('period2', text='2025.Q2')
        table.heading('period3', text='2025.Q1')
        table.heading('period4', text='2024.Q4')
        table.heading('period5', text='2024.Q3')
        table.heading('period6', text='2024.Q2')
        table.heading('period7', text='2024.Q1')
        table.heading('period8', text='2023.Q4')
        table.column('item', width=80)
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
        table.insert('', 'end', values=('營業毛利率', '22.64', '15.12', '16.86', '23.29', '24.27', '19.13', '15.22 ', '2.24'))  # fmt: skip
        table.insert('', 'end', values=('營業利益率', '13.16', '3.15', '6.58', '10.88', '15.26', '11.1', '4.7', '12.11'))  # fmt: skip
        table.insert('', 'end', values=('稅前淨利率', '-25.9 ', '.34', '5.41', '15.32', '15.84', '14.02', '13.12', '13.46'))  # fmt: skip
        table.insert('', 'end', values=('稅後淨利率', '-30.17', '2.07', '2.2', '10.73', '11.25', '9.01', '8.77', '8.82'))  # fmt: skip

        return panel

    def create_status_bar(self):
        """Status bar"""
        status_bar = ttk.Frame(self, style='Toolbar.TFrame')
        status_bar.pack(side='bottom', pady=6, fill='x')

        # label: 'message'
        self.status = ttk.Label(status_bar, text='Ready')
        self.status.pack(side='left', padx=6)


def main():
    root = tk.Tk()
    root.title('Stock Analysis Tool')
    root.geometry('800x600')

    app = StockApp(root)

    root.mainloop()


if __name__ == '__main__':
    main()
