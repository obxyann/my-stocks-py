from tkinter import ttk


class AutoScrollbar(ttk.Scrollbar):
    """Scrollbar that hides itself if it's not needed

    Only works if you use the pack geometry manager.
    """

    def set(self, first, last):
        """Set scrollbar visible range

        Overwrite this function to update visibility.

        Args:
            first (float): top visible range between 0 and 1
            last (float): bottom visible range between 0 and 1
        """
        if float(first) <= 0.0 and float(last) >= 1.0:
            self.pack_forget()
        else:
            if not self.winfo_ismapped():
                self.pack(side='right', fill='y')

        ttk.Scrollbar.set(self, first, last)
