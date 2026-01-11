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

        # for setting styles
        self.style_helper = style_helper

        # create control bar at top
        self._create_control_bar().pack(fill='x', pady=(0, 6))

        # create tab panels below control bar
        self._create_tab_panels().pack(fill='both', expand=True, padx=(0, 4))

    def _create_control_bar(self):
        """Create control bar

        Returns:
            ttk.Frame: Created bar
        """
        # container for widgets
        bar = ttk.Frame(self)

        # label: Stock Code Name
        self.stock_name = ttk.Label(bar, text='---- ----')
        self.stock_name.pack(side='left', padx=6)

        return bar

    def _create_tab_panels(self):
        """Create tab panels

        Returns:
            ttk.Notebook: Created tab panels
        """
        # container for panels
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
        """Set data to stock view

        Args:
            data (dict): dictionary containing metadata
                         - 'code_name': Stock code and name, string
                         - 'ohlc_price': OHLC price data, DataFrame
                         - 'revenue': Revenue data, DataFrame
                         - 'avg_price': Average price data, DataFrame
                         - 'financial': Financial data, DataFrame
                         - 'metrics': Financial metrics data, DataFrame
        """
        self.clear()

        # set stock name
        if 'code_name' in data:
            self.stock_name['text'] = data['code_name']

        # set panels
        if 'ohlc_price' in data:
            self.price_panel.set_data(data['ohlc_price'])
        if 'revenue' in data:
            self.revenue_panel.set_data(data['revenue'], data.get('avg_price'))
        if 'financial' in data:
            self.financial_panel.set_data(data['financial'])
        if 'metrics' in data:
            self.metrics_panel.set_data(data['metrics'])

    def clear(self):
        """Clear stock view"""
        # clear stock_name
        self.stock_name['text'] = '---- ----'

        # clear panels
        self.price_panel.clear()
        self.revenue_panel.clear()
        self.financial_panel.clear()
        self.metrics_panel.clear()
