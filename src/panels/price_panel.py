import bisect
from tkinter import ttk

import matplotlib.ticker as ticker
import mplfinance as mpf
import pandas as pd
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure


class StockDateLocator(ticker.Locator):
    """Custom locator for stock dates on x axis

    Ensure Month Starts are always visible on x axis.

    Args:
        dates (pd.Index): List of datetime objects
        ax: Matplotlib axes object
        min_px_dist (int): Minimum pixel distance between ticks
    """

    def __init__(self, dates, ax, min_px_dist=60):
        self.dates = dates
        self.ax = ax
        self.min_px_dist = min_px_dist

        # calculate step for extrapolation
        if len(dates) > 1:
            # get all intervals (differences between consecutive dates)
            diffs = pd.Series(dates).diff()
            # determine the most frequent interval, default to 1 day
            self.step = (
                diffs.mode().iloc[0] if not diffs.mode().empty else pd.Timedelta(days=1)
            )
        else:
            self.step = pd.Timedelta(days=1)

    def __call__(self):
        """Return locations of ticks

        Returns:
            list: List of tick positions
        """
        dmin, dmax = self.axis.get_view_interval()

        return self.tick_values(dmin, dmax)

    def tick_values(self, vmin, vmax):
        """Calculate tick positions within range

        Args:
            vmin (float): Minimum value in view
            vmax (float): Maximum value in view

        Returns:
            list: Calculated tick positions
        """
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

            # if it is NOT a Month Start (normal day), we check if placing it would
            # crowd out a future Month Start
            idx_in_forced = bisect.bisect_right(forced_ticks, i)
            if idx_in_forced < len(forced_ticks):
                next_forced = forced_ticks[idx_in_forced]
                dist_to_next = (next_forced - i) * px_per_idx

                # if placing 'i' now makes the next Month Start impossible (too close),
                # we prefer to SKIP 'i' and wait for the Month Start
                if dist_to_next < self.min_px_dist:
                    continue

            # otherwise, place the normal day tick
            ticks.append(i)
            last_tick = i

        return ticks

    def get_date(self, idx):
        """Get date at specified index

        Args:
            idx (int): Index in date list

        Returns:
            pd.Timestamp: Date at index
        """
        if 0 <= idx < len(self.dates):
            return self.dates[idx]
        elif idx < 0:
            return self.dates[0] + (idx * self.step)
        else:
            return self.dates[-1] + ((idx - (len(self.dates) - 1)) * self.step)


class StockDateFormatter(ticker.Formatter):
    """Custom formatter for stock dates on x axis

    Args:
       dates (pd.Index): List of datetime objects
    """

    def __init__(self, dates):
        self.dates = dates

        # calculate step for extrapolation
        if len(dates) > 1:
            # get all intervals (differences between consecutive dates)
            diffs = pd.Series(dates).diff()
            # determine the most frequent interval, default to 1 day
            self.step = (
                diffs.mode().iloc[0] if not diffs.mode().empty else pd.Timedelta(days=1)
            )
        else:
            self.step = pd.Timedelta(days=1)

    def __call__(self, x, pos=None):
        """Format tick value to date string

        Args:
            x (float): Tick value
            pos (int): Position of tick on the axis

        Returns:
            str: Formatted date string for that tick label
        """
        idx = int(round(x))
        date = self.get_date(idx)

        # determine if it's a Month Start
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

    def get_date(self, idx):
        """Get date at specified index

        Args:
            idx (int): Index in date list

        Returns:
            pd.Timestamp: Date at index
        """
        if 0 <= idx < len(self.dates):
            return self.dates[idx]
        elif idx < 0:
            return self.dates[0] + (idx * self.step)
        else:
            return self.dates[-1] + ((idx - (len(self.dates) - 1)) * self.step)


class PricePanel(ttk.Frame):
    """Price chart panel with K-line candlestick chart

    Args:
        parent: Parent widget
        style_helper: Object with set_chart_style and set_axes_style methods
    """

    def __init__(self, parent, style_helper):
        super().__init__(parent)

        self.show_volume = True

        # for setting styles
        self.style_helper = style_helper

        # drag/zoom state
        self.drag_mode = None  # 'pan', 'scale_x' or 'scale_y'
        self.drag_start = None
        self.drag_xlim = None
        self.drag_ylim = None
        self.drag_ylim_vol = None
        self.zoom_scale = 1.1

        # create control bar at top
        self._create_control_bar().pack(fill='x', pady=4)

        # create chart below control bar
        self._create_chart().pack(fill='both', expand=True)

    def _create_control_bar(self):
        """Create control bar

        Returns:
            ttk.Frame: Created control bar
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
            ttk.Frame: Created frame containing chart
        """
        # container for chart
        chart_frame = ttk.Frame(self)

        # create matplotlib figure
        if self.show_volume:
            self.fig = Figure(figsize=(7.5, 4), dpi=100)  # , constrained_layout=True)
            # with gridspec for price and volume subplots
            self.gs = self.fig.add_gridspec(2, 1, height_ratios=[4, 1])
            self.ax = self.fig.add_subplot(self.gs[0])
            self.ax_vol = self.fig.add_subplot(self.gs[1], sharex=self.ax)
        else:
            self.fig = Figure(figsize=(7.5, 4), dpi=100)
            self.ax = self.fig.add_subplot(111)
            self.ax_vol = None

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
            up='#CC6666',
            down='#75AB45',
            inherit=True,  # red for up, green for down
        )

        # define custom style and store it
        self.mpf_style = mpf.make_mpf_style(
            base_mpf_style='nightclouds',
            marketcolors=mc,
            # rc={'patch.linewidth': 0},
        )

        self.style_helper.set_chart_style(self.fig, self.ax)
        self.ax_vol and self.style_helper.set_chart_style(self.fig, self.ax_vol)

        self._set_axes_style()

    def _set_axes_style(self):
        """Set axes style"""
        self.style_helper.set_axes_style(self.ax, label1='Price')
        self.ax_vol and self.style_helper.set_axes_style(self.ax_vol, label1='Volume')

        self.ax.grid(True, linestyle=':', alpha=0.2, color='#FFFFFF')
        self.ax_vol and self.ax_vol.grid(
            True, linestyle=':', alpha=0.2, color='#FFFFFF'
        )

        # hide x-axis tick labels on price chart (only show on volume chart)
        self.ax.tick_params(axis='x', rotation=0, labelbottom=False)
        self.ax_vol and self.ax_vol.tick_params(axis='x', rotation=0)

    def _setup_events(self):
        """Setup pan and zoom events"""
        self.canvas.mpl_connect('button_press_event', self._on_drag_start)
        self.canvas.mpl_connect('button_release_event', self._on_drag_end)
        self.canvas.mpl_connect('motion_notify_event', self._on_drag_move)
        self.canvas.mpl_connect('scroll_event', self._on_scroll)

    def _on_drag_start(self, event):
        """Handle mouse drag start

        Args:
            event: Matplotlib mouse event
        """
        if event.button != 1:  # left click only
            return

        # check for Pan (inside axes)
        if event.inaxes == self.ax:
            self.drag_mode = 'pan'
            self.drag_start = (event.x, event.y)
            self.drag_xlim = self.ax.get_xlim()
            self.drag_ylim = self.ax.get_ylim()
            return

        # check for Scale Y (left of axes)
        bbox = self.ax.bbox
        if (event.x < bbox.xmin) and (bbox.ymin <= event.y <= bbox.ymax):
            self.drag_mode = 'scale_y'
            self.drag_start = (event.x, event.y)
            self.drag_ylim = self.ax.get_ylim()
            return

        # check for Scale Y Vol (left of volume axes)
        if self.ax_vol:
            bbox_vol = self.ax_vol.bbox
            if (event.x < bbox_vol.xmin) and (
                bbox_vol.ymin <= event.y <= bbox_vol.ymax
            ):
                self.drag_mode = 'scale_y_vol'
                self.drag_start = (event.x, event.y)
                self.drag_ylim_vol = self.ax_vol.get_ylim()
                return

        # check for Scale X (below axes)
        if (bbox.xmin <= event.x <= bbox.xmax) and (event.y < bbox.ymin):
            self.drag_mode = 'scale_x'
            self.drag_start = (event.x, event.y)
            self.drag_xlim = self.ax.get_xlim()

    def _on_drag_move(self, event):
        """Handle mouse drag move

        Args:
            event: Matplotlib mouse event
        """
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

        elif self.drag_mode == 'scale_y_vol':
            dy = event.y - self.drag_start[1]
            bbox = self.ax_vol.bbox

            # sensitivity: 4x zoom for full height drag
            scale_factor = 4 ** (dy / bbox.height)

            y_min, y_max = self.drag_ylim_vol
            y_mid = (y_min + y_max) / 2
            y_range = y_max - y_min

            new_range = y_range / scale_factor
            new_ylim = (y_mid - new_range / 2, y_mid + new_range / 2)

            self.ax_vol.set_ylim(new_ylim)

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
        """Handle mouse drag end

        Args:
            event: Matplotlib mouse event
        """
        self.drag_mode = None
        self.drag_start = None

    def _on_scroll(self, event):
        """Handle mouse scroll (Zoom X and Y)

        Args:
            event: Matplotlib mouse event
        """
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
            cx (float): Center X (data coord)
            cy (float): Center Y (data coord)
            scale (float): Zoom scale factor
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
            df (pd.DataFrame): Price (OHLC) and volume data
        """
        # clear existing plot
        self.ax.clear()
        self.ax_vol and self.ax_vol.clear()

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
            volume=self.ax_vol or False,  # display volume on separate axes
            mav=(10, 20, 60),
            warn_too_much_data=len(df) + 1,  # disable waring
        )

        # manually adjust volume bar width and remove border
        # this is more compatible with different mplfinance versions
        if self.ax_vol:
            for patch in self.ax_vol.patches:
                # remove border
                patch.set_linewidth(0)
                patch.set_edgecolor('none')

                # adjust width (shrink to 0.5 and center it)
                current_width = patch.get_width()
                new_width = 0.6
                if current_width > new_width:
                    diff = current_width - new_width
                    patch.set_width(new_width)
                    patch.set_x(patch.get_x() + diff / 2)

        # set custom locator and formatter
        # NOTE: df.index must be DatetimeIndex used in mpf.plot
        locator = StockDateLocator(df.index, self.ax)
        formatter = StockDateFormatter(df.index)

        self.ax.xaxis.set_major_locator(locator)
        self.ax.xaxis.set_major_formatter(formatter)

        self.ax_vol and self.ax_vol.xaxis.set_major_locator(locator)
        self.ax_vol and self.ax_vol.xaxis.set_major_formatter(formatter)

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

        Data is pd.Dataframe with DatetimeIndex and [Open, High, Low, Close, Volume]

        Args:
            df (pd.DataFrame): Price (OHLC) and volume data
        """
        self._set_chart_data(df)

    def clear(self):
        """Clear data on panel"""
        # clear chart
        self._set_chart_data(None)
