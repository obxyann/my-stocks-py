import tkinter as tk
from tkinter import ttk

import sv_ttk


class StockApp(ttk.Frame):
    def __init__(self, master):
        super().__init__(master)

        # set theme
        sv_ttk.set_theme('dark')

        dark = sv_ttk.get_theme() == 'dark'

        self.theme_var = tk.BooleanVar(value=dark)

        self.set_style()

        self.pack(fill='both', expand=True)

        # create all UI components
        self.create_toolbar()

        self.create_main_layout()

        self.create_status_bar()

    def set_style(self):
        # configure ttk styles
        style = ttk.Style()

        style.configure('Toolbar.TFrame', pady=4)

    def create_toolbar(self):
        """Top toolbar"""
        tool_bar = ttk.Frame(self, style='Toolbar.TFrame')
        tool_bar.pack(side='top', pady=6, fill='x')

        # buttons: [Load][Export]
        ttk.Button(tool_bar, text='Load').pack(side='left', padx=6)
        ttk.Button(tool_bar, text='1Export').pack(side='left')

        # toggle: [1|0] Dark
        ttk.Checkbutton(
            tool_bar,
            text='Dark',
            style='Switch.TCheckbutton',
            variable=self.theme_var,
            command=sv_ttk.toggle_theme,
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

        # TODO:
        ttk.Label(panel, text='TODO: revenue area').pack()

        return panel

    def create_financial_panel(self, parent):
        """Tab panel: financial"""
        panel = ttk.Frame(parent)

        # table: | item | value |
        columns = ('item', 'value')
        table = ttk.Treeview(panel, columns=columns, show='headings')
        table.heading('item', text='Item')
        table.heading('value', text='Value')
        table.column('item', width=200)
        table.column('value', width=120, anchor='e')
        table.pack(fill='both', expand=True)

        # TBD: dummy data
        table.insert('', 'end', values=('Revenue', '1,234,567'))
        table.insert('', 'end', values=('Operating Income', '345,678'))
        table.insert('', 'end', values=('Net Income', '210,456'))

        return panel

    def create_indicator_panel(self, parent):
        """Tab panel: indicator"""
        panel = ttk.Frame(parent)

        # TODO:
        ttk.Label(panel, text='TODO: indicator area').pack()

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
