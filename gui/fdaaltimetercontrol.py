# -+- encoding: utf-8 -+-

import Tkinter as tk

import time
import os

import tkMessageBox
import tkFileDialog
from ttk import Progressbar

import gettext
_ = gettext.translation('messages', 'gui', fallback=True).ugettext

from serial.tools import list_ports

from flydream.altimeter import Altimeter

from flydream.exception import FlyDreamAltimeterSerialPortError
from flydream.exception import FlyDreamAltimeterReadError
from flydream.exception import FlyDreamAltimeterWriteError
from flydream.exception import FlyDreamAltimeterProtocolError

RAW_FILE_EXTENSION = '.fda'


class Separator(tk.Frame):

    def __init__(self, parent):
        tk.Frame.__init__(self, parent,
                background='darkgrey', height=1, relief=tk.RIDGE)


class FdaAltimeterControl(tk.Toplevel):

    PORT_SELECTION_FRAME_HEIGHT = 80
    SUB_FRAME_X_PADDING = 20

    def __init__(self):
        tk.Toplevel.__init__(self)

        # Do not let user to close this window
        # is a communication with the Altimeter
        # is taking place.
        self.communicating = False
        self.protocol("WM_DELETE_WINDOW", self.close_asked)

        # Setup window content.
        self.initialize()

    def initialize(self):
        self.title(_(u'FlyDream Altimeter - Device Controller'))

        # Set fixed size.
        self.minsize(640, 320)
        self.resizable(False, False)

        # Altimeter local device.
        frame = tk.Frame(self, height=self.PORT_SELECTION_FRAME_HEIGHT)
        frame.pack(fill=tk.BOTH, expand=tk.YES)

        tk.Label(frame, text=_(u'Altimeter plugged on:')).pack(side=tk.LEFT)

        self.detect = tk.Button(frame, text=_(u'Refresh'),
                command=self.refresh_serial_ports)
        self.detect.pack(side=tk.RIGHT)

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

        self.progressbar = Progressbar(frame, orient='horizontal',
                mode='determinate')
        self.progressbar.pack(side=tk.BOTTOM, fill=tk.X)

        # Do not show progressbar
        # unless data is uploaded.
        self.hide_progressbar()

        self.upload_info = tk.StringVar()
        self.upload_info.set('/')
        self.info_label = tk.Label(frame, anchor=tk.NE, fg='darkgrey',
                textvariable=self.upload_info)
        self.info_label.pack(side=tk.BOTTOM, fill=tk.BOTH)

        self.label = tk.Label(frame, anchor=tk.W,
                text=_(u'Tell the altimeter to send flight '
                    'data to your computer'))
        self.label.pack(side=tk.LEFT)

        self.upload = tk.Button(frame, text=_(u'Upload data'),
                command=self.upload)
        self.upload.pack(side=tk.RIGHT)

        # Erase altimeter flight data.
        frame = tk.Frame(self, padx=self.SUB_FRAME_X_PADDING)
        frame.pack(fill=tk.BOTH, expand=tk.YES)

        label = tk.Label(frame, anchor=tk.W, text=_(u'Clear'))
        label.pack(side=tk.TOP, fill=tk.X)

        Separator(frame).pack(fill=tk.X)

        label = tk.Label(frame, anchor=tk.W,
                text=_(u'Delete all the flight data from your altimeter'))
        label.pack(side=tk.LEFT)

        self.erase = tk.Button(frame, text=_(u'Erase data'),
                command=self.erase)
        self.erase.pack(side=tk.RIGHT)

        # Setup altimeter sampling frequency.
        frame = tk.Frame(self, padx=self.SUB_FRAME_X_PADDING)
        frame.pack(fill=tk.BOTH, expand=tk.YES)

        label = tk.Label(frame, anchor=tk.W, text=_(u'Configure'))
        label.pack(side=tk.TOP, fill=tk.X)

        Separator(frame).pack(fill=tk.X)

        self.frequency = tk.StringVar(self)
        self.frequency.set('1')
        self.frequencies = tk.OptionMenu(frame, self.frequency,
                '1', '2', '4', '8')
        self.frequencies.pack(side=tk.LEFT)

        label = tk.Label(frame, text=_(u'records per second'))
        label.pack(side=tk.LEFT)

        self.setup = tk.Button(frame, text=_(u'Set sampling frequency'),
                command=self.set_frequency)
        self.setup.pack(side=tk.RIGHT)

    def allow_user_interactions(self, allow=True):
        state = tk.NORMAL if allow else tk.DISABLED
        self.ports.configure(state=state)
        self.detect.configure(state=state)
        self.upload.configure(state=state)
        self.erase.configure(state=state)
        self.frequencies.configure(state=state)
        self.setup.configure(state=state)

    def close_asked(self):
        if not self.communicating:
            self.destroy()
            return
        else:
            tkMessageBox.showwarning(_(u'Warning'),
                    _(u"""The application is communicating with the altimeter.

Please wait until communication is finished before closing this window."""))

    def hide_progressbar(self):
        self.progressbar.prev_pack = self.progressbar.pack_info()
        self.progressbar.pack_forget()

        self.update()

        # Reset progressbar for next upload.
        self.progressbar['value'] = 0

    def show_progressbar(self):
        # Well, Tkinter pack does not seem to
        # make it easy to simply hide a widget...
        #
        # I may be missing something.
        prev_info_label_packinfo = self.info_label.pack_info()
        prev_label_packinfo = self.label.pack_info()
        prev_upload_packinfo = self.upload.pack_info()

        self.info_label.pack_forget()
        self.label.pack_forget()
        self.upload.pack_forget()

        self.progressbar.pack(self.progressbar.prev_pack)

        self.info_label.pack(prev_info_label_packinfo)
        self.label.pack(prev_label_packinfo)
        self.upload.pack(prev_upload_packinfo)

        self.update()

    def upload_progressed(self, read, total):
        self.progressbar['maximum'] = total
        self.progressbar['value'] = read

        info = _(u'Please wait, %d bytes read out of %d') % (read, total)
        self.upload_info.set(info)

        self.update()

    def default_filename(self):
        return time.strftime('%Y-%m-%d %H-%M-%S', time.localtime()) \
                + '_flight'

    def upload(self):
        # TODO Add please wait message.

        # Update window state.
        self.show_progressbar()
        self.allow_user_interactions(False)
        self.communicating = True

        # Get flight data.
        port = self.port.get()
        altimeter = Altimeter(port)
        try:
            raw_data = altimeter.upload(self.upload_progressed)
        except FlyDreamAltimeterSerialPortError:
            self.show_unfound_altimeter(port)
        except (FlyDreamAltimeterReadError, FlyDreamAltimeterWriteError) as e:
            self.show_readwrite_error(port, e.message)
        except FlyDreamAltimeterProtocolError as e:
            self.show_protocol_error(port, e.message)
        else:
            # Check received data.
            if len(raw_data.data) == 0:
                tkMessageBox.showinfo(_(u'Upload Data'),
                        _(u'Altimeter contains no data.'))
            else:
                self.write_flight_data(raw_data)
        finally:
            # Restore window state.
            self.communicating = False
            self.allow_user_interactions()
            self.hide_progressbar()

        # TODO Update altimeter information.
        self.upload_info.set('Done')

    def write_flight_data(self, raw_data):
        fname = tkFileDialog.asksaveasfilename(
                    filetypes=((_(u'Flydream Altimeter Data'), '*.fda'),
                               (_(u'All files'), '*.*')),
                    title=_(u'Save flight data...'),
                    initialdir='~',
                    initialfile=self.default_filename(),
                    defaultextension=RAW_FILE_EXTENSION)
        if fname:
            raw_data.to_file(fname)

    def erase(self):
        reply = tkMessageBox.askokcancel(_(u'Erase flight data'),
                _(u'Really erase all flight data in your altimeter?'))
        if reply:
            self.do_erase()

    def do_erase(self):
        tkMessageBox.showwarning('Erase flight data', 'Not implemented yet')

    def set_frequency(self):
        tkMessageBox.showwarning('Upload flight data', 'Not implemented yet')

    def show_unfound_altimeter(self, port):
        tkMessageBox.showwarning(_(u'Sampling Frequency'),
                    _(u"""Can not open port: %s

Please ensure that:
 - your altimeter is plugged to the USB adapter.
 - the USB adapter is plugged to your computer.
 - the choosen port is correct.
 - the USB adapter driver is properly installed on your computer, see
   http://www.silabs.com/products/mcu/pages/usbtouartbridgevcpdrivers.aspx""")
                    % port)

    def show_readwrite_error(self, port, message):
        tkMessageBox.showwarning(_(u'Read/Write error'),
                    _(u"""With device on: %s

Internal error message: %s

Please ensure that:
 - the choosen port is correct.
 - your altimeter is plugged to the USB adapter.
 - the USB adapter is plugged to your computer.
 - you did not unplugged the altimeter while it was communicating.""")
                    % (port, message))

    def show_protocol_error(self, port, message):
        tkMessageBox.showwarning(_(u'Protocol error'),
                    _(u"""With device on: %s

Internal error message: %s

Please ensure that:
 - your altimeter is plugged to the USB adapter.
 - you did not unplugged the altimeter while it was communicating.""")
                    % (port, message))

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
