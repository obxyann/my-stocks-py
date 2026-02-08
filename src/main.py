import tkinter as tk
from tkinter import messagebox, ttk

import pandas as pd
import sv_ttk

from database.stock import StockDatabase
from load_stock import load_stock
from panels import StockListPanel, StockViewPanel
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
        print(f'Error: Database initialization failed: {error}')
        raise


class StockApp(ttk.Frame):
    def __init__(self, master, db):
        """Initialize application

        Args:
            master: Root window
            db: StockDatabase instance
        """
        super().__init__(master)

        # set database
        self.db = db

        # set ui style
        self.dark_mode_var = tk.BooleanVar(value=True)

        self.set_theme()

        # pack itself to root, fit to window
        self.pack(fill='both', expand=True)

        # create UI frames
        self._create_toolbar().pack(side='top', pady=6, fill='x')

        self._create_main_layout().pack(fill='both', expand=True)

        self._create_status_bar().pack(side='bottom', pady=6, fill='x')

    ###################
    # create UI style #
    ###################

    def set_theme(self, theme=None):
        """Set and configure UI theme

        Args:
            theme (str): Name of theme to apply, 'dark', 'light'
                         None: Use current dark_mode_var value
        """
        if theme is None:
            theme = 'dark' if self.dark_mode_var.get() else 'light'
        elif theme == 'dark':
            self.dark_mode_var.set(True)
        elif theme == 'light':
            self.dark_mode_var.set(False)
        else:
            raise ValueError(f'Invalid theme: {theme}')

        # set main theme
        sv_ttk.set_theme(theme)

        # configure ttk styles
        style = ttk.Style()

        style.configure('Toolbar.TFrame', pady=4)

        # set plot theme
        # TODO: wait to implement

    def set_chart_style(self, fig, ax1, ax2=None):
        """Set chart style"""
        # background of figure
        fig.patch.set_facecolor('#1C1C1C')

        # NOTE: below axes styles will not be reset by ax.clear()
        #       so we can just set these styles once here

        # background of axes
        ax1.set_facecolor('#1C1C1C')

        # tick of axes
        ax1.tick_params(colors='#FFFFFF')
        ax1.tick_params(axis='y', labelcolor='#FFFFFF')

        # spines of axes
        ax1.spines['top'].set_color('#535353')  # .set_visible(False)
        ax1.spines['right'].set_color('#535353')  # .set_visible(False)

        ax1.spines['bottom'].set_color('#535353')
        ax1.spines['left'].set_color('#535353')

        if ax2 is not None:
            ax2.tick_params(colors='#FFFFFF')
            ax2.tick_params(axis='y', labelcolor='#FFFFFF')

            ax2.spines['top'].set_visible(False)
            ax2.spines['bottom'].set_visible(False)
            ax2.spines['left'].set_visible(False)

            ax2.spines['right'].set_color('#535353')

        self.set_axes_style(ax1, ax2)

    def set_axes_style(self, ax1, ax2=None, label1='', label2=''):
        """Set axes styles

        NOTE: Axes styles on artists will be reset by ax.clear() and must be reapplied
        """
        # below axes styles will be reset by ax.clear()

        # grid
        ax1.grid(True, axis='y', linestyle=':', alpha=0.2, color='#FFFFFF')

        # label beside axes
        ax1.set_ylabel(label1, color='#FFFFFF')

        # offset text of axes
        ax1.yaxis.get_offset_text().set_color('#FFFFFF')

        if ax2 is not None:
            # label
            ax2.set_ylabel(label2, color='#FFFFFF')

            ax2.yaxis.set_label_position('right')

            # offset text
            ax2.yaxis.get_offset_text().set_color('#FFFFFF')

    ####################
    # create UI frames #
    ####################

    def _create_toolbar(self):
        """Create toolbar

        Returns:
            ttk.Frame: Created toolbar
        """
        # container for widgets
        bar = ttk.Frame(self, style='Toolbar.TFrame')

        # combobox: Screening Method [v]
        methods = list(SCREENING_METHODS.keys())

        self.method_combo = ttk.Combobox(
            bar, values=methods, width=12, state='readonly'
        )
        self.method_combo.pack(side='left', padx=6)
        self.method_combo.bind(
            '<<ComboboxSelected>>',
            lambda e: self.on_select_method(self.method_combo.get()),
        )

        # input: Stock Code [___]
        ttk.Label(bar, text='Stock Code').pack(side='left', padx=6)

        self.search_code = ttk.Entry(bar, width=12)
        self.search_code.pack(side='left')
        # fmt: off
        self.search_code.bind(
            '<Return>',
            lambda e: self.on_view_stock(self.search_code.get())
        )
        # fmt: on

        # toggle: [1|0] Dark
        ttk.Checkbutton(
            bar,
            text='Dark',
            style='Switch.TCheckbutton',
            variable=self.dark_mode_var,
            command=self.set_theme,
        ).pack(side='right', padx=6)

        return bar

    def _create_main_layout(self):
        """Create main layout with split panels

        Returns:
            ttk.Frame: Created paned window
        """
        # container for panels
        paned = ttk.PanedWindow(self, orient='horizontal')

        # panels: [stock list | stock view]
        self.stock_list = StockListPanel(paned, on_select_callback=self.on_view_stock)
        self.stock_view = StockViewPanel(paned, style_helper=self)

        paned.add(self.stock_list, weight=2)
        paned.add(self.stock_view, weight=5)

        return paned

    def _create_status_bar(self):
        """Create status bar

        Returns:
            ttk.Frame: Created status bar
        """
        # container for widgets
        bar = ttk.Frame(self, style='Toolbar.TFrame')

        # label: 'message'
        self.status = ttk.Label(bar, text='Ready')
        self.status.pack(side='left', padx=6)

        return bar

    ###########
    # actions #
    ###########

    def on_select_method(self, method):
        """Handle screening method selection

        Args:
            method (str): Selected method
        """
        if method not in SCREENING_METHODS:
            print(f'Warning: Invalid method: {method}')
            return

        # get list function and call it
        list_func = SCREENING_METHODS[method]

        df_stocks = list_func(self.db)

        # set data to stock list
        self.stock_list.set_data(df_stocks)

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

        self.stock_view.set_data(stock_data)


def test(app):
    """Test data panels with dummy data

    Args:
        app: StockApp instance
    """
    # stock list dummy data
    columns_stocks = ('code', 'name', 'score')
    data_stocks = [
        ('2330', '台積電', 10.5),
        ('2317', '鴻海', 8.2),
    ]
    df_stocks = pd.DataFrame(data_stocks, columns=columns_stocks)

    # set data to stock list
    app.stock_list.set_data(df_stocks)

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
    df_plot = pd.DataFrame(data_rev, columns=columns_rev)

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
    app.stock_view.set_data(
        {
            'code_name': '1101 台泥',
            'revenue': df_plot,
            'financial': df_fin,
            'metrics': df_ind,
        }
    )


def main():
    """Main entry point of the application"""
    root = tk.Tk()
    root.title('Stock Analysis Tool')
    root.geometry('1024x800')

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
