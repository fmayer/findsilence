# Split WAV - Split long WAV files into tracks
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
import os.path
import math

from wx.lib.wordwrap import wordwrap

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import findsilence

def _(s):
    """ Dummy gettext function """
    return s


class AdvancedSettings(wx.Dialog):
    def __init__(self, parent):
        wx.Dialog.__init__(self, parent)
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        pause_sizer = wx.BoxSizer()
        
        self.pauses = wx.SpinCtrl(self, initial=2)
        pause_sizer.Add(wx.StaticText(self, -1, _(
            "Length of Pauses (in sec): ")), 0, 
                        wx.ALIGN_CENTER_VERTICAL)
        pause_sizer.Add(self.pauses, 1, wx.EXPAND)
        main_sizer.Add(pause_sizer, 1, wx.EXPAND | wx.ALL)
        ok_sizer = wx.BoxSizer()
        ok_sizer.Add(wx.Button(self, wx.ID_OK, _("Okay")), 1, wx.EXPAND)
        ok_sizer.Add(wx.Button(self, wx.ID_CANCEL, _("Cancel")), 1, wx.EXPAND)
        main_sizer.Add(ok_sizer, 1, wx.EXPAND)
        self.SetSizer(main_sizer)
        main_sizer.Fit(self)


class MainPanel(wx.PyPanel):
    def __init__(self, parent):
        wx.PyPanel.__init__(self, parent)
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
        frames = self.Parent.pauses * 43027
        try:
            findsilence.split_phono(file_name, directory, frames)
        except findsilence.FileExists:
            wx.MessageBox(_("The directory you've selected is a file"))
        
        
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
        opts = AdvancedSettings(None)
        if opts.ShowModal() == wx.ID_OK:
            self.pauses = opts.pauses.Value
        
    def on_about(self, evt):
        license = open(os.path.join(
            os.path.abspath(os.path.dirname(__file__)), '..', "COPYING"))
        license = license.read()
        
        info = wx.AboutDialogInfo()
        info.Name = "Split WAV"
        info.Version = "0.1"
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


def create_gui():
    app = wx.PySimpleApp()

    frame = MainFrame()
    frame.Show()
    app.MainLoop()


if __name__ == '__main__':
    create_gui()