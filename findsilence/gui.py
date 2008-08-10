import wx
import sys
import os.path

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import findsilence

def _(s):
    """ Dummy gettext function """
    return s


class MainPanel(wx.PyPanel):
    def __init__(self, parent):
        wx.PyPanel.__init__(self, parent)
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        self.file_select = wx.FilePickerCtrl(self, 
                                             message=_("Select Input File"))
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
        sizer.Add(execute)
        
        execute.Bind(wx.EVT_BUTTON, self.on_execute)
        
        self.SetSizer(sizer)
        sizer.Fit(self)
    
    def on_execute(self, evt):
        file_name = os.path.abspath(self.file_select.Path)
        directory = os.path.abspath(self.dir_select.GetPath())
        try:
            findsilence.split_phono(file_name, directory)
        except findsilence.FileExists:
            wx.MessageBox(_("The directory you've selected is a file"))
        
        
class MainFrame(wx.Frame):
    def __init__(self):
        wx.Frame.__init__(self, None)
        self.panel = MainPanel(self)
        self.Fit()
        
if __name__ == '__main__':
    app = wx.PySimpleApp()
    frame = MainFrame()
    frame.Show()
    app.MainLoop()