# -+- encoding: utf-8 -+-

import Tkinter as tk

import tkMessageBox

import gettext
_ = gettext.translation('messages', 'gui', fallback=True).ugettext

from serial.tools import list_ports

from flydream.altimeter import Altimeter

class Separator(tk.Frame):

    def __init__(self, parent):
        tk.Frame.__init__(self, parent,
                background='darkgrey', height=1, relief=tk.RIDGE)


class FdaAltimeterControl(tk.Toplevel):

    PORT_SELECTION_FRAME_HEIGHT = 80
    SUB_FRAME_X_PADDING = 20

    def __init__(self):
        tk.Toplevel.__init__(self)

        self.initialize()

    def initialize(self):
        self.title(_(u'FlyDream Altimeter - Device Controller'))

        # Set minimal size
        self.minsize(640, 320)
        self.resizable(False, False)

        # Altimeter local device.
        frame = tk.Frame(self, height=self.PORT_SELECTION_FRAME_HEIGHT)
        frame.pack(fill=tk.BOTH, expand=tk.YES)

        tk.Label(frame, text=_(u'Altimeter plugged on:')).pack(side=tk.LEFT)

        detect_button = tk.Button(frame, text=_(u'Refresh'),
                command=self.refresh_serial_ports)
        detect_button.pack(side=tk.RIGHT)

        self.port = tk.StringVar(self)
        self.ports = tk.OptionMenu(frame, self.port,
                _(u'Detecting serial ports...'))
        self.ports.pack(fill=tk.BOTH, expand=1)

        # Update possible serial ports.
        self.refresh_serial_ports()

        # Upload altimeter flight data.
        frame = tk.Frame(self, padx=self.SUB_FRAME_X_PADDING)
        frame.pack(fill=tk.BOTH, expand=tk.YES)

        label = tk.Label(frame, anchor=tk.W, text=_(u'Upload'))
        label.pack(side=tk.TOP, fill=tk.X)

        Separator(frame).pack(fill=tk.X)

        label = tk.Label(frame, anchor=tk.W,
                text=_(u'Tell the altimeter to send flight '
                    'data to your computer'))
        label.pack(side=tk.LEFT)

        upload = tk.Button(frame, text=_(u'Upload data'),
                command=self.upload)
        upload.pack(side=tk.RIGHT)

        # Erase altimeter flight data.
        frame = tk.Frame(self, padx=self.SUB_FRAME_X_PADDING)
        frame.pack(fill=tk.BOTH, expand=tk.YES)

        label = tk.Label(frame, anchor=tk.W, text=_(u'Clear'))
        label.pack(side=tk.TOP, fill=tk.X)

        Separator(frame).pack(fill=tk.X)

        label = tk.Label(frame, anchor=tk.W,
                text=_(u'Delete all the flight data from your altimeter'))
        label.pack(side=tk.LEFT)

        erase = tk.Button(frame, text=_(u'Erase data'),
                command=self.erase)
        erase.pack(side=tk.RIGHT)

        # Setup altimeter sampling frequency.
        frame = tk.Frame(self, padx=self.SUB_FRAME_X_PADDING)
        frame.pack(fill=tk.BOTH, expand=tk.YES)

        label = tk.Label(frame, anchor=tk.W, text=_(u'Configure'))
        label.pack(side=tk.TOP, fill=tk.X)

        Separator(frame).pack(fill=tk.X)

        self.frequency = tk.StringVar(self)
        self.frequency.set('1')
        frequency = tk.OptionMenu(frame, self.frequency, '1', '2', '4', '8')
        frequency.pack(side=tk.LEFT)

        label = tk.Label(frame, text=_(u'records per second'))
        label.pack(side=tk.LEFT)

        setup = tk.Button(frame, text=_(u'Set sampling frequency'),
                command=self.set_frequency)
        setup.pack(side=tk.RIGHT)

    def upload(self):
        tkMessageBox.showwarning('Upload flight data', 'Not implemented yet')

    def erase(self):
        reply = tkMessageBox.askokcancel(_(u'Erase flight data'),
                _(u'Really erase all flight data in your altimeter?'))
        if reply:
            self.do_erase()

    def do_erase(self):
        tkMessageBox.showwarning('Erase flight data', 'Not implemented yet')

    def set_frequency(self):
        tkMessageBox.showwarning('Upload flight data', 'Not implemented yet')

    def refresh_serial_ports(self):
        # Build port list.
        port_list = self.detect_serial_ports()

        # Remove previous items in combobox.
        menu = self.ports['menu']
        menu.delete(0, tk.END)

        # Add new items in combobox.
        self.port.set(port_list[0])
        for pr in port_list:
            menu.add_command(label=pr, command=lambda p=pr: self.port.set(p))

    def detect_serial_ports(self):
        # Try to detect system serial devices.
        port_list = []
        try:
            # Convert to filenames.
            port_list = [info[0].replace('cu', 'tty')
                    for info in list_ports.comports()]
        except Exception as e:
            tkMessageBox.showwarning('Serial Ports Detection',
                    'Error while detecting serial ports: %s' % e.message)

        # Insert default port as first entry.
        default = Altimeter().port
        try:
            # Try to remove default one to prevent duplication.
            port_list.remove(default)
        except ValueError:
            pass
        port_list.insert(0, default)

        return port_list
