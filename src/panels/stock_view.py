from tkinter import ttk

from panels.financial_panel import FinancialPanel
from panels.metrics_panel import MetricsPanel
from panels.price_panel import PricePanel
from panels.revenue_panel import RevenuePanel


class StockViewPanel(ttk.Frame):
    """Stock view panel with tabs for different data views

    Args:
        parent: Parent widget
        style_helper: Object with set_chart_style and set_axes_style methods
    """

    def __init__(self, parent, style_helper):
        super().__init__(parent)

        # this is how to set styles
        self.style_helper = style_helper

        # create control bar at top
        self._create_control_bar().pack(side='top', pady=(0, 6), fill='x')

        # create panels
        self._create_tab_panels().pack(fill='both', expand=True, padx=(0, 4))

    def _create_control_bar(self):
        """Create control bar

        Returns:
            ttk.Frame: Created bar
        """
        # container for widgets
        control_bar = ttk.Frame(self)

        # label: Stock Code Name
        self.stock_name = ttk.Label(control_bar, text='---- ----')
        self.stock_name.pack(side='left', padx=6)

        return control_bar

    def _create_tab_panels(self):
        """Create tab panels

        Returns:
            ttk.Frame: Created tab panels frame
        """
        # tabs container
        tabs = ttk.Notebook(self)

        # create panels
        self.price_panel = PricePanel(tabs, self.style_helper)
        self.revenue_panel = RevenuePanel(tabs, self.style_helper)
        self.financial_panel = FinancialPanel(tabs, self.style_helper)
        self.metrics_panel = MetricsPanel(tabs, self.style_helper)

        # tab panels: _Price_Revenues_Financials_Metrics_
        tabs.add(self.price_panel, text='Price')
        tabs.add(self.revenue_panel, text='Revenues')
        tabs.add(self.financial_panel, text='Financials')
        tabs.add(self.metrics_panel, text='Metrics')

        return tabs

    def set_data(self, data):
        """Set data of stock view

        Args:
            data (dict): dictionary containing metadata and DataFrames
                         - 'code_name': Stock code and name string
                         - 'ohlc_price': OHLC price data
                         - 'revenue': Revenue data
                         - 'avg_price': Average price data
                         - 'financial': Financial data
                         - 'metrics': Financial metrics data
        """
        self.clear()

        code_name = data.get('code_name')
        if code_name:
            self.stock_name['text'] = code_name

        if 'ohlc_price' in data:
            self.price_panel.set_data(data['ohlc_price'])
        if 'revenue' in data:
            self.revenue_panel.set_chart_data(data['revenue'], data.get('avg_price'))
            self.revenue_panel.set_table_data(data['revenue'])
        if 'financial' in data:
            self.financial_panel.set_data(data['financial'])
        if 'metrics' in data:
            self.metrics_panel.set_data(data['metrics'])

    def clear(self):
        """Clear stock view"""
        # clear stock_name
        self.stock_name['text'] = '---- ----'

        # clear all panels
        self.price_panel.set_data(None)
        self.revenue_panel.clear()
        self.financial_panel.clear()
        self.metrics_panel.clear()
