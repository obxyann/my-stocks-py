import bisect
from tkinter import ttk

import matplotlib.ticker as ticker
import mplfinance as mpf
import pandas as pd
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure


class StockDateLocator(ticker.Locator):
    """Custom locator to ensure month starts are always visible"""

    def __init__(self, dates, ax, min_px_dist=60):
        self.dates = dates
        self.ax = ax
        self.min_px_dist = min_px_dist

        # Calculate step for extrapolation
        if len(dates) > 1:
            diffs = pd.Series(dates).diff()
            self.step = (
                diffs.mode().iloc[0] if not diffs.mode().empty else pd.Timedelta(days=1)
            )
        else:
            self.step = pd.Timedelta(days=1)

    def get_date(self, idx):
        if 0 <= idx < len(self.dates):
            return self.dates[idx]
        elif idx < 0:
            return self.dates[0] + (idx * self.step)
        else:
            return self.dates[-1] + ((idx - (len(self.dates) - 1)) * self.step)

    def __call__(self):
        """Return the locations of the ticks"""
        dmin, dmax = self.axis.get_view_interval()

        return self.tick_values(dmin, dmax)

    def tick_values(self, vmin, vmax):
        if not len(self.dates):
            return []

        # visible range indices (allow going out of bounds)
        i_min = int(vmin)
        i_max = int(vmax)

        # screen metrics
        bbox = self.ax.get_window_extent()
        if bbox.width == 0 or (vmax - vmin) <= 0:
            return []

        px_per_idx = bbox.width / (vmax - vmin)

        # pre-calculate forced ticks (Month Starts) in the range
        forced_ticks = []
        for i in range(i_min, i_max + 1):
            is_start = False
            curr_date = self.get_date(i)
            prev_date = self.get_date(i - 1)

            if curr_date.month != prev_date.month:
                is_start = True

            if is_start:
                forced_ticks.append(i)

        ticks = []
        last_tick = -100000

        for i in range(i_min, i_max + 1):
            # 1. enforce minimum distance (first principle)
            dist = (i - last_tick) * px_per_idx
            if dist < self.min_px_dist:
                continue

            # 2. check if this is a Month Start (high priority)
            is_month_start = False
            curr_date = self.get_date(i)
            prev_date = self.get_date(i - 1)
            if curr_date.month != prev_date.month:
                is_month_start = True

            # if it is a Month Start, we place it (since we passed the distance check)
            if is_month_start:
                ticks.append(i)
                last_tick = i
                continue

            # if it is NOT a Month Start (Normal Day), we check if placing it would
            # crowd out a future Month Start
            idx_in_forced = bisect.bisect_right(forced_ticks, i)
            if idx_in_forced < len(forced_ticks):
                next_forced = forced_ticks[idx_in_forced]
                dist_to_next = (next_forced - i) * px_per_idx

                # if placing 'i' now makes the next Month Start impossible (too close),
                # we prefer to SKIP 'i' and wait for the Month Start.
                if dist_to_next < self.min_px_dist:
                    continue

            # otherwise, place the Normal Day tick
            ticks.append(i)
            last_tick = i

        return ticks


class StockDateFormatter(ticker.Formatter):
    """Custom formatter for stock dates"""

    def __init__(self, dates):
        self.dates = dates

        # Calculate step for extrapolation
        if len(dates) > 1:
            diffs = pd.Series(dates).diff()
            self.step = (
                diffs.mode().iloc[0] if not diffs.mode().empty else pd.Timedelta(days=1)
            )
        else:
            self.step = pd.Timedelta(days=1)

    def get_date(self, idx):
        if 0 <= idx < len(self.dates):
            return self.dates[idx]
        elif idx < 0:
            return self.dates[0] + (idx * self.step)
        else:
            return self.dates[-1] + ((idx - (len(self.dates) - 1)) * self.step)

    def __call__(self, x, pos=None):
        idx = int(round(x))
        date = self.get_date(idx)

        # determine if it's a month start
        is_start = False
        prev_date = self.get_date(idx - 1)
        if date.month != prev_date.month:
            is_start = True

        if is_start:
            # example: 2025-12
            return f'{date.strftime("%Y/%m")}'
        else:
            # example: 4
            return str(date.day)


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
        self.drag_mode = None  # 'pan', 'scale_x' or 'scale_y'
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

        self.canvas.get_tk_widget().configure(background='#1C1C1C')
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
        )

        self.style_helper.set_chart_style(self.fig, self.ax)

        self._set_axes_style()

    def _set_axes_style(self):
        """Set axes style"""
        self.style_helper.set_axes_style(self.ax, label1='Price')

        self.ax.grid(True, linestyle=':', alpha=0.2, color='#FFFFFF')

        self.ax.tick_params(axis='x', rotation=0)

    def _setup_events(self):
        """Setup pan and zoom events"""
        self.canvas.mpl_connect('button_press_event', self._on_drag_start)
        self.canvas.mpl_connect('button_release_event', self._on_drag_end)
        self.canvas.mpl_connect('motion_notify_event', self._on_drag_move)
        self.canvas.mpl_connect('scroll_event', self._on_scroll)

    def _on_drag_start(self, event):
        """Handle mouse drag start"""
        if event.button != 1:  # left click only
            return

        # Check for Pan (inside axes)
        if event.inaxes == self.ax:
            self.drag_mode = 'pan'
            self.drag_start = (event.x, event.y)
            self.drag_xlim = self.ax.get_xlim()
            self.drag_ylim = self.ax.get_ylim()
            return

        # Check for Scale Y (left of axes)
        bbox = self.ax.bbox
        if (event.x < bbox.xmin) and (bbox.ymin <= event.y <= bbox.ymax):
            self.drag_mode = 'scale_y'
            self.drag_start = (event.x, event.y)
            self.drag_ylim = self.ax.get_ylim()
            return

        # Check for Scale X (below axes)
        if (bbox.xmin <= event.x <= bbox.xmax) and (event.y < bbox.ymin):
            self.drag_mode = 'scale_x'
            self.drag_start = (event.x, event.y)
            self.drag_xlim = self.ax.get_xlim()

    def _on_drag_move(self, event):
        """Handle mouse drag move"""
        if self.drag_start is None:  # drag start not set
            return

        if self.drag_mode == 'pan':
            if event.inaxes != self.ax:
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

        elif self.drag_mode == 'scale_y':
            dy = event.y - self.drag_start[1]
            bbox = self.ax.bbox

            # sensitivity: 4x zoom for full height drag
            # drag up (dy > 0) -> zoom in (range shrinks)
            scale_factor = 4 ** (dy / bbox.height)

            y_min, y_max = self.drag_ylim
            y_mid = (y_min + y_max) / 2
            y_range = y_max - y_min

            new_range = y_range / scale_factor
            new_ylim = (y_mid - new_range / 2, y_mid + new_range / 2)

            self.ax.set_ylim(new_ylim)

            self.canvas.draw_idle()

        elif self.drag_mode == 'scale_x':
            dx = event.x - self.drag_start[0]
            bbox = self.ax.bbox

            # sensitivity: 4x zoom for full width drag
            # drag right (dx > 0) -> zoom in (range shrinks)
            scale_factor = 4 ** (dx / bbox.width)

            x_min, x_max = self.drag_xlim
            x_mid = (x_min + x_max) / 2
            x_range = x_max - x_min

            new_range = x_range / scale_factor
            new_xlim = (x_mid - new_range / 2, x_mid + new_range / 2)

            self.ax.set_xlim(new_xlim)

            self.canvas.draw_idle()

    def _on_drag_end(self, event):
        """Handle mouse drag end"""
        self.drag_mode = None
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
            mav=(10, 20, 60),
            warn_too_much_data=len(df) + 1,  # disable waring
        )

        # set custom locator and formatter
        # NOTE: df.index must be DatetimeIndex used in mpf.plot
        self.ax.xaxis.set_major_locator(StockDateLocator(df.index, self.ax))
        self.ax.xaxis.set_major_formatter(StockDateFormatter(df.index))

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
        self._set_axes_style()

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
