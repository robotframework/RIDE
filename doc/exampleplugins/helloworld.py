"""A Sample Plugin


   For a module to be valid plugin it must define a function named
   init_plugin which takes a single argument which is a pointer to 
   the RobotFrame. 

   This method is responsible for creating an instance of a class
   that derives from robotide.plugins.Plugin, and returning a handle
   to that object.

"""

import cStringIO
import wx
import zlib
from robotide.application import Plugin

ID_ABOUT = wx.NewId()
ID_SHOW_HELLO = wx.NewId()
ID_SHOW_TAB = wx.NewId()
MENU_TITLE = "H&ello"
TOOLBAR_BITMAP = wx.BitmapFromImage(wx.ImageFromStream(cStringIO.StringIO(
            zlib.decompress(
                'x\xda\x01\xf5\x02\n\xfd\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x10' +
                '\x00\x00\x00\x10\x08\x06\x00\x00\x00\x1f\xf3\xffa\x00\x00\x00\x04sBIT\x08' +
                '\x08\x08\x08|\x08d\x88\x00\x00\x02\xacIDAT8\x8du\x92[H\x93a\x18\xc7\x7f\xef' +
                '\xb7\xafa\xd3\xdc\xda\x9c\x19V\xae9\x02\xb3\xb2\x03\x98\x87\xbc\x902#1:X\xe4' +
                'Ut\x82\xe8&\xa2\x82I\x18D\x11Rt\xa0n*\x02\x91\x021\xa4n:PR\x82\x91#\xc5J2m' +
                '\x98a\xda\xb22\xac\x9c\xee\xe8\xf7\xbd]\x8c,t=\xf0\\=\xff\xf7\xc7\xff\xf9' +
                '\xbf\x8f\x90R2\xb5*k\x1eY\x81+@\x05`\x9c&\x88U\x13pP\xfd\xcf\xb0vK\x81s\xd3' +
                '\xd6\xc2LT\x83\x12Wp\xbf\xad\xbf\xe4\xd6S\xef\xc3i\x80\xca\x9aGI@YE\x91\x0b' +
                '\x7f\x08\xc2\x13\x92\xa8\x06\x9a\x04M\x07M\x97\x08\xa0,\xd7\x81\xa7\xe7\x8b+' +
                '\x9e\x03kJr\x82A\x11\x82\xf1\x88D\xd3\x89\x01t\xf9\x0f$&L6\x19\x89\xe7o\xe4' +
                '\xfbhH\xd3\xa5DUb\xe2\t]2\xa13\xd9\x10\xcbm,\x14e\xd2\xc1\xfeU65\xc9\xa8T' +
                '\x17\xd8\xb5C\xddY\xc7d\xe33\'\x15E.\x14!\x00\xc1\xe0\x0f\xc9\xc8\xb8d\xaeY' +
                '\x90:K\xe1~[?\xbd\xbe\x9f\xef\xc5\x9f_p\x17\xd9\x0eg\x98\x03\x17\x02RG\x98l' +
                '\xf4e\xecc\xc4\x96\x0fB\xa1d\xc5|\xf6\x94.\x06\xe0\xe7X\x98;\xcf\xfbhz5\xd8' +
                '\x05l\x99t\x90\xa6\x06\xd6\xdb\x97\x14c\xb7\xcf\xe6E{\x07\x06\xcfyfF\r\xccMO' +
                '\xbf\xd9\xc4\xa5\x82\x8d\xb9\x8e\xcc\x07m\xfd4\xbd\x1a\x0c\x01g\xea\xdd\xa5' +
                '\xa7\x80\xbf+\xa8\xd6\xc4oy\x9bwcN\x90X\x1d\xd9\x04\xc7~a\xb4\xa4q\xeb\xb5' +
                '\x9eS\x9c3/\xf3\xf0\xb5g\xe3@u\xbd\xbb\xf4\xe2\xbf\x81M\x02Z"\xc5oJ\xfa\xdbe' +
                'J\xce\x1a\xb1t\xd9R\xc2\x9aBg\x87G\xfa\xd4\xd5\xe9\xbe\xceO\xfb\xeb\xdd\xa57' +
                '\xe2\xdd\x83\n\x90V^o\xf8:\xb4\xd6\xb5\xfd\xcb0\x86\xf0\x0345\t\x950=Cs\xb8' +
                '\xdd8\xd0`\xb5\xcf\xa8\xc5\x1d\xef9\x08\xcb\x86\x06\xe1\xf7+\xa7\x8e\xee\\YU' +
                '\\\xe9T\x9a[=DB\x82h\x10\x96\xe7\xe4\xf1\xf2a\xafv\xf5\xee\x8b\xd3&\xd3\xd8I' +
                '\x7f\xf3\x81iw\xaff\x99>\x1eYS\x98u|\xc5\xba\x85<\xfe\x00~K>\xe1\x00\x84\x04' +
                '<y+\xc9^\xe92\xec\x1a\xee:\xe1\xed\xf5\x06\x80\xb3\xd3\x1c\xf8\xceeK_\xc6' +
                '\x01\xea\xd8\xc1xb*Z@\x12\tB4\n\x13\x9a\xc08:L\x95\xb3\x11K\xd7e\x9c\xd5=b*@' +
                '\t&:Z\xbd\x1dm\x0cx\xbc(*\x18\xcd\x02S\x8a\xc0<_\x90\x9c\n?\xba\xdb\x19\xe8|' +
                'N\xd4\xba\xa8%n\x88\xba\xc5Q\x9e\x16\t\xcd\xfb\xdc\xfai\xdb\xbb\xeb\xf7\xf6&' +
                '$\x18g\x0b)\x0cR\xd3\xb4`8\x1a\xb4\x88\xe1:\xf3\xb2\x19\xb5\x8am\xc1\xe7x' +
                '\x80\xdf\xbc\xe2\x18&\xc4\xcd][\x00\x00\x00\x00IEND\xaeB`\x82\x80\xe3^\xa7' ))))


class HelloWorldPlugin(Plugin):
    """A simple RIDE plugin

       This plugin creates a notebook tab, a menu item and a toolbar
       item. The toolbar item will only be created if the main app
       has a toolbar (which it doesn't in version 0.15.1)
    """

    def __init__(self, manager=None):
        Plugin.__init__(self, manager)
        self.id = "example.hello_world"
        self.name = "Hello World Plugin"
        self.version = "0.2"
        self.active = False
        self._panel = None

    def OnPublication(self,message):
        """Handle publications from the main frame"""
        # N.B. The text widget can be destroyed if the user closes the
        # tab while the plugin is enabled, so we only log publications
        # if the window is there.
        if self.text:
            self.text.AppendText("Received a publication:\n")
            self.text.AppendText("   Topic: %s\n" % ".".join(message.topic))
            self.text.AppendText("   Data:\n")
            for key in message.data.keys():
                self.text.AppendText("      %s = %s\n" % (key, message.data[key]))
            self.text.AppendText("\n")

    def deactivate(self):
        """Deactivates this plugin."""
        self._remove_from_notebook()
        self._remove_from_menubar()
        self._remove_from_toolbar()
        self.manager.unsubscribe(self.OnPublication)
        self.active = False

    def activate(self):
        """Make the plugin available"""
        self._add_to_notebook()
        self._add_to_menubar()
        self._add_to_toolbar()
        self.manager.subscribe(self.OnPublication, ("core"))
        self.active = True

    def OnAbout(self, event):
        """Displays a dialog about this plugin"""
        info = wx.AboutDialogInfo()
        info.Name = self.name
        info.Version = self.version
        info.Description = self.__doc__
        info.Developers = ["Bryan Oakley, Orbitz Worldwide"]
        wx.AboutBox(info)

    def OnSayHello(self, event):
        """A handler for the menu and toolbar widgets"""
        dialog = wx.MessageDialog(self.manager.get_frame(), "Hello, World!", "Hello, world", style=wx.OK)
        dialog.ShowModal()

    def OnShowTab(self, event):
        """Show the notebook tab, creating it if it doesn't exist"""
        if not self._panel:
            self._add_to_notebook()
        self.manager.show_page(self._panel)

    def _add_to_notebook(self):
        """Add a tab for this plugin to the notebook"""
        notebook = self.manager.get_notebook()
        if notebook:
            self._panel = wx.Panel(notebook)
            button = wx.Button(self._panel, ID_SHOW_HELLO, "Hello, world!")
            self.text = wx.TextCtrl(self._panel, style=wx.TE_MULTILINE)
            sizer = wx.BoxSizer(wx.VERTICAL)
            sizer.Add(button,0)
            sizer.Add(self.text, 1, wx.EXPAND|wx.ALL, border=8)
            self._panel.SetSizer(sizer)
            button.Bind(wx.EVT_BUTTON, self.OnSayHello)
            notebook.AddPage(self._panel, "Hello, world!", select=False)

    def _remove_from_notebook(self):
        """Remove the tab for this plugin from the notebook"""
        notebook = self.manager.get_notebook()
        if notebook:
            notebook.DeletePage(notebook.GetPageIndex(self._panel))

    def _add_to_toolbar(self):
        """Add a button to the toolbar for this plugin"""
        toolbar = self.manager.get_tool_bar()
        if toolbar:
            toolbar.AddLabelTool(ID_SHOW_HELLO,"Say Hello",TOOLBAR_BITMAP, shortHelp="Say Hello")

    def _remove_from_toolbar(self):
        """Remove the button for this plugin from the toolbar"""
        toolbar = self.manager.get_tool_bar()
        if toolbar:
            toolbar.RemoveTool(ID_SHOW_HELLO)

    def _add_to_menubar(self):
        """Add a menu item on the menubar for this plugin

           The menu item will be added to the left of the Help menu.
        """
        menubar = self.manager.get_menu_bar()
        if menubar:
            hello_menu = wx.Menu()
            pos = menubar.FindMenu("Help")
            if pos >= 0:
                menubar.Insert(pos, hello_menu, MENU_TITLE)
            else:
                menubar.Append(hello_menu, MENU_TITLE)

            hello_menu.Append(ID_SHOW_TAB, "Show Notebook Tab", "Show and select the Hello, world notebook tab")
            hello_menu.Append(ID_SHOW_HELLO, "Say Hello", "Prints Hello World")
            hello_menu.AppendSeparator()
            hello_menu.Append(ID_ABOUT, "About this plugin", "Show information about this plugin")
            wx.EVT_MENU(self.manager.get_frame(), ID_SHOW_TAB, self.OnShowTab)
            wx.EVT_MENU(self.manager.get_frame(), ID_ABOUT, self.OnAbout)
            wx.EVT_MENU(self.manager.get_frame(), ID_SHOW_HELLO, self.OnSayHello)
                   
    def _remove_from_menubar(self):
        """Remove the menubar item from the menubar for this plugin"""
        menubar = self.manager.get_menu_bar()
        if menubar:
            pos = menubar.FindMenu(MENU_TITLE)
            if pos >= 0:
                menubar.Remove(pos)
        
