# findsilence - Split long WAV files into tracks
# Copyright (C) 2008 Florian Mayer

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import wx
import sys
import os
import threading

from wx.lib.wordwrap import wordwrap

# Add parent directory to PYTHONPATH. This enables the program to be run by
# just running gui.py, thus enabling the users to run the program without
# installing it.
script_path = os.path.abspath(os.path.dirname(__file__))
sys.path.append(os.path.join(script_path, os.pardir))

import findsilence

from findsilence import actions
from findsilence import defaults
from findsilence.copying import license

# Dummy gettext.
_ = lambda s: s


class Worker(threading.Thread):
    """ This is the worker Thread doing the real work to prevent the UI from
    getting unresponsive """
    def __init__(self, *args, **kwargs):
        threading.Thread.__init__(self)
        self.stopthread = threading.Event()
        self.args = args
        # Make sure self is passed as the parent_thread argument to 
        # split_phono.
        kwargs.update({"parent_thread": self})
        self.kwargs = kwargs
    
    def stop(self):
        self.stopthread.set()

    def run(self):
        try:
            findsilence.split_phono(*self.args, **self.kwargs)
        except findsilence.Cancelled:
            pass
        except findsilence.NoSilence:
            wx.CallAfter(wx.MessageBox, _("No silence could be found"))


class AdvancedSettings(wx.Dialog):
    """ Allow the user to set advanced settings """
    def __init__(self, parent):
        wx.Dialog.__init__(self, parent, -1, "Advanced Options")
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        pause_sizer = wx.BoxSizer()
        
        self.pauses = wx.SpinCtrl(self, initial=defaults.pause_seconds)
        pause_sizer.Add(wx.StaticText(self, -1, _(
            _("Length of Pauses (in sec): "))), 0, 
                        wx.ALIGN_CENTER_VERTICAL)
        pause_sizer.Add(self.pauses, 1, wx.EXPAND)
        main_sizer.Add(pause_sizer, 1, wx.EXPAND | wx.ALL)
        ok_sizer = wx.BoxSizer()
        ok_sizer.Add(wx.Button(self, wx.ID_OK, _("Okay")), 1, wx.EXPAND)
        ok_sizer.Add(wx.Button(self, wx.ID_CANCEL, _("Cancel")), 1, wx.EXPAND)
        main_sizer.Add(ok_sizer, 1, wx.EXPAND)
        self.SetSizer(main_sizer)
        main_sizer.Fit(self)


class MainPanel(wx.PyPanel, actions.ActionHandler):
    def __init__(self, parent):
        wx.PyPanel.__init__(self, parent)
        actions.ActionHandler.__init__(self)

        sizer = wx.BoxSizer(wx.VERTICAL)
        
        wildcard = 'WAV files (*.wav)|*.wav'
        
        
        self.file_select = wx.FilePickerCtrl(self, 
                                             message=_("Select Input File"),
                                             wildcard=wildcard)
        self.dir_select = wx.DirPickerCtrl(self, 
                                           message=_("Select output directory"),
                                           style=wx.DIRP_CHANGE_DIR)
        execute = wx.Button(self, -1, _("Split into Tracks"))
        file_sizer = wx.BoxSizer()
        dir_sizer = wx.BoxSizer()
        
        file_sizer.Add(wx.StaticText(self, -1, _("Input File: ")), 0, 
                       wx.ALIGN_CENTER_VERTICAL
                       )
        dir_sizer.Add(wx.StaticText(self, -1, _("Output Directory: ")), 0, 
                      wx.ALIGN_CENTER_VERTICAL
                      )
        
        file_sizer.Add(self.file_select, 1, wx.ALIGN_RIGHT | wx.EXPAND)
        dir_sizer.Add(self.dir_select, 1, wx.ALIGN_RIGHT | wx.EXPAND)
        
        sizer.Add(file_sizer, 1, wx.ALL | wx.EXPAND)
        sizer.Add(dir_sizer, 1, wx.ALL | wx.EXPAND)
        sizer.Add(execute, 1, wx.EXPAND)
        
        execute.Bind(wx.EVT_BUTTON, self.on_execute)
        
        self.SetSizer(sizer)
        sizer.Fit(self)
    
    def on_execute(self, evt):
        file_name = os.path.abspath(self.file_select.Path)
        directory = os.path.abspath(self.dir_select.GetPath())
        frames = self.Parent.pauses
        
        self.worker = Worker(file_name, directory, frames, 
                             defaults.volume_cap, defaults.min_length)
        self.worker.start()
    
    def is_file(self):
        wx.MessageBox(_("The directory you've selected is a file"))
    
    @actions.register_method('current_frame')
    def update_progessbar(self, i):
        def _update(self, i):
            (thread_continue, thread_skip) = self.progress.Update(i)
            if not thread_continue:
                self.worker.stop()
                self.progress.Destroy()
        
        wx.CallAfter(_update, self, i)
       
    @actions.register_method('frames')
    def init_progressbar(self, max_):
        def _init(self, max_):
            self.max_ = max_
            self.progress = wx.ProgressDialog(_("WAV Progress"),
                           _("Please wait while your file is being processed."),
                           maximum=max_,
                           parent=self,
                           style=wx.PD_CAN_ABORT
                            | wx.PD_APP_MODAL
                            | wx.PD_ELAPSED_TIME
                            | wx.PD_REMAINING_TIME
                            )
            
        wx.CallAfter(_init, self, max_)
    
    @actions.register_method('done')
    def done(self, state=None):
        wx.CallAfter(self.progress.Update, self.max_)
        
        
class MainFrame(wx.Frame):
    def __init__(self):
        wx.Frame.__init__(self, None, -1, "Split WAV")
        self.panel = MainPanel(self)
        self.make_menu()
        self.Fit()
        self.pauses = 2
    
    def make_menu(self):
        menu_bar = wx.MenuBar()
        
        options_menu = wx.Menu()
        adv = options_menu.Append(-1, "&Advanced Options")
        
        help_menu = wx.Menu()
        about = help_menu.Append(-1, "&About")
        
        menu_bar.Append(options_menu, "&Options")
        menu_bar.Append(help_menu, "&Help")
        self.SetMenuBar(menu_bar)
        self.Bind(wx.EVT_MENU, self.advanced, adv)
        self.Bind(wx.EVT_MENU, self.on_about, about)
    
    def advanced(self, evt):
        opts = AdvancedSettings(self)
        if opts.ShowModal() == wx.ID_OK:
            self.pauses = opts.pauses.Value
        
    def on_about(self, evt):
        info = wx.AboutDialogInfo()
        info.Name = "Split WAV"
        info.Version = "0.1rc1"
        info.Copyright = "(C) 2008 Florian Mayer"
        info.Description = wordwrap("Split WAV allows you to split your WAV "
                                    "files on pauses. \n"
                                    "This is paticulary useful for digitalizing"
                                    " old records", 
                                    350, wx.ClientDC(self))
        # info.WebSite
        info.Developers = ["Florian Mayer"]
        info.License = wordwrap(license, 500, wx.ClientDC(self))
        wx.AboutBox(info)


def create_gui(options=None, args=None, parser=None):
    app = wx.PySimpleApp()

    frame = MainFrame()
    frame.Show()
    app.MainLoop()


if __name__ == '__main__':
    create_gui()
