from tkinter import ttk


class AutoScrollbar(ttk.Scrollbar):
    """A scrollbar that hides itself if it's not needed

    Only works if you use the pack geometry manager.
    """

    def set(self, lo, hi):
        if float(lo) <= 0.0 and float(hi) >= 1.0:
            self.pack_forget()
        else:
            if not self.winfo_ismapped():
                self.pack(side='right', fill='y')

        ttk.Scrollbar.set(self, lo, hi)
