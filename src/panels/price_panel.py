from tkinter import ttk

import mplfinance as mpf
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure


class PricePanel(ttk.Frame):
    """Price chart panel with K-line candlestick chart

    Args:
        parent: Parent widget
        style_helper: Object with set_chart_style and set_axes_style methods
    """

    def __init__(self, parent, style_helper):
        super().__init__(parent)

        ## for setting styles
        self.style_helper = style_helper

        # drag/zoom state
        self.drag_start = None
        self.drag_xlim = None
        self.drag_ylim = None
        self.zoom_scale = 1.1

        # create control bar at top
        self._create_control_bar().pack(fill='x', pady=4)

        # create chart below control bar
        self._create_chart().pack(fill='both', expand=True)

    def _create_control_bar(self):
        """Create control bar

        Returns:
            ttk.Frame: Created bar
        """
        # container for widgets
        bar = ttk.Frame(self)

        # combobox: Period [D|v]
        options = ['D', 'M', 'Y']

        ttk.Label(bar, text='Period').pack(side='left', padx=(6, 4))

        period = ttk.Combobox(bar, values=options, width=2, state='readonly')
        period.current(0)
        period.pack(side='left')

        return bar

    def _create_chart(self):
        """Create chart

        Returns:
            ttk.Frame: Created chart
        """
        # container for chart
        chart_frame = ttk.Frame(self)

        # create matplotlib figure
        self.fig = Figure(figsize=(7.5, 4), dpi=100)
        self.ax = self.fig.add_subplot(111)

        # set style
        self._set_chart_style()

        # embed figure in tkinter
        self.canvas = FigureCanvasTkAgg(self.fig, master=chart_frame)

        self.canvas.get_tk_widget().pack(fill='both', expand=True)

        # setup events
        self._setup_events()

        # adjust layout
        self.fig.tight_layout()

        return chart_frame

    def _set_chart_style(self):
        """Set chart style"""
        # define custom market colors
        mc = mpf.make_marketcolors(
            up='#CB4B16',
            down='#0C8F4E',
            inherit=True,  # red for up, green for down
        )

        # define custom style and store it
        self.mpf_style = mpf.make_mpf_style(
            base_mpf_style='nightclouds',
            marketcolors=mc,
            facecolor='#1C1C1C',
            edgecolor='#1C1C1C',
            figcolor='#1C1C1C',
            gridcolor='#363636',
            gridstyle=':',
            rc={'xtick.color': '#FFFFFF', 'ytick.color': '#FFFFFF'},
        )

        self.style_helper.set_chart_style(self.fig, self.ax)

        # NOTE: below styles are reset by ax.clear() and must be reapplied in
        #       set_chart_data()
        self.style_helper.set_axes_style(self.ax, label1='Price')

    def _setup_events(self):
        """Setup pan and zoom events"""
        self.canvas.mpl_connect('button_press_event', self._on_drag_start)
        self.canvas.mpl_connect('button_release_event', self._on_drag_end)
        self.canvas.mpl_connect('motion_notify_event', self._on_drag_move)
        self.canvas.mpl_connect('scroll_event', self._on_scroll)

    def _on_drag_start(self, event):
        """Handle mouse drag start (Pan)"""
        if event.inaxes != self.ax:
            return
        if event.button != 1:  # left click only
            return

        self.drag_start = (event.x, event.y)

        self.drag_xlim = self.ax.get_xlim()
        self.drag_ylim = self.ax.get_ylim()

    def _on_drag_move(self, event):
        """Handle mouse drag move (Pan)"""
        if event.inaxes != self.ax:
            return
        if self.drag_start is None:  # drag start not set
            return

        dx = event.x - self.drag_start[0]
        dy = event.y - self.drag_start[1]

        # convert pixel delta to data delta
        x_range = self.drag_xlim[1] - self.drag_xlim[0]
        y_range = self.drag_ylim[1] - self.drag_ylim[0]

        bbox = self.ax.bbox

        scale_x = x_range / bbox.width
        scale_y = y_range / bbox.height

        # calculate new limits
        # NOTE: dragging right (dx > 0) means we want to see left data -> subtract dx
        new_xlim = (
            self.drag_xlim[0] - dx * scale_x,
            self.drag_xlim[1] - dx * scale_x,
        )
        new_ylim = (
            self.drag_ylim[0] - dy * scale_y,
            self.drag_ylim[1] - dy * scale_y,
        )

        self.ax.set_xlim(new_xlim)
        self.ax.set_ylim(new_ylim)

        self.canvas.draw_idle()

    def _on_drag_end(self, event):
        """Handle mouse drag end"""
        self.drag_start = None

    def _on_scroll(self, event):
        """Handle mouse scroll (Zoom X and Y)"""
        if event.inaxes != self.ax:
            return

        if event.button == 'up':
            scale_factor = 1 / self.zoom_scale
        elif event.button == 'down':
            scale_factor = self.zoom_scale
        else:
            return

        self._zoom_axes(event.xdata, event.ydata, scale_factor)

        self.canvas.draw_idle()

    def _zoom_axes(self, cx, cy, scale):
        """Zoom axes around center point

        Args:
            cx: Center X (data coord)
            cy: Center Y (data coord)
            scale: Zoom scale factor
        """
        # zoom X
        xlim = self.ax.get_xlim()
        x_width = xlim[1] - xlim[0]
        new_x_width = x_width * scale
        rel_x = (cx - xlim[0]) / x_width
        new_xlim = [cx - new_x_width * rel_x, cx + new_x_width * (1 - rel_x)]

        self.ax.set_xlim(new_xlim)

        # zoom Y
        ylim = self.ax.get_ylim()
        y_width = ylim[1] - ylim[0]
        new_y_width = y_width * scale
        rel_y = (cy - ylim[0]) / y_width
        new_ylim = [cy - new_y_width * rel_y, cy + new_y_width * (1 - rel_y)]

        self.ax.set_ylim(new_ylim)

    def _set_chart_data(self, df):
        """Set data to chart

        Args:
            df: pd.DataFrame with DatetimeIndex and [Open, High, Low, Close, Volume]
        """
        # clear existing plot
        self.ax.clear()

        # check data
        if df is None or df.empty:
            self.canvas.draw_idle()
            return

        # plot using mpf
        # NOTE: ax=self.ax allows plotting on existing axes
        mpf.plot(
            df,
            type='candle',
            style=self.mpf_style,
            ax=self.ax,
            volume=False,  # default no volume for now, or add another ax if needed
            show_nontrading=False,
            mav=(10, 20, 60),
            warn_too_much_data=len(df) + 1, # disable waring
        )

        # set initial view to last 100 candles and auto-scale Y
        if len(df) > 100:
            # last 100 candles
            # Note: x-axis is integer index 0..len-1
            total_len = len(df)
            self.ax.set_xlim(total_len - 100 - 0.5, total_len - 0.5)

            # calculate y limits with padding based on visible data
            visible_df = df.iloc[-100:]
            min_price = visible_df['Low'].min()
            max_price = visible_df['High'].max()
            padding = (max_price - min_price) * 0.05

            self.ax.set_ylim(min_price - padding, max_price + padding)
        else:
            self.ax.set_xlim(-0.5, len(df) - 0.5)

        # NOTE: Reapply styling that were reset by ax.clear()
        self.style_helper.set_axes_style(self.ax, label1='Price')

        # adjust layout
        self.fig.tight_layout()

        self.canvas.draw_idle()

    def set_data(self, df):
        """Set data to panel

        Args:
            df: pd.DataFrame containing price (OHLC) and volume data
        """
        self._set_chart_data(df)

    def clear(self):
        """Clear data on panel"""
        # clear chart
        self._set_chart_data(None)
