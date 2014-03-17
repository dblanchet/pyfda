import Tkinter as tk

from flydream.uploadeddata import UploadedData
from flydream.dataparser import DataParser

from gui.util import flight_description


class FdaFlightList(tk.Listbox):

    def __init__(self, parent, on_flight_selected, *args, **kwargs):
        tk.Listbox.__init__(self, parent, *args, **kwargs)
        self.on_flight_selected = on_flight_selected
        self.bind('<<ListboxSelect>>', self.on_select)

    def load_fda_file(self, path):
        # Load data.
        raw_upload = UploadedData.from_file(path)
        self._flights = DataParser().extract_flights(raw_upload.data)

        # Populate list.
        self.update_content()

        # Select last flight.
        if self._flights:
            self.selection_clear(0)
            self.selection_set(tk.END)
            self.see(tk.END)
            self.on_select(None)

    def update_content(self):
        # Clear list.
        self.delete(0, tk.END)

        # Add loaded flights.
        for flight in self._flights:
            self.insert(tk.END, flight_description(flight))

    def on_select(self, event):
        # Find out index in list.
        selection = self.curselection()
        if not selection:
            return
        index_str, = selection

        if not self._flights:
            return
        flight = self._flights[int(index_str)]

        # Tell the world about current selected flight.
        self.on_flight_selected(flight)
