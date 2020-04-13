#!/usr/bin/env python3
#
# Flatpak GUI info window module
# Copyright (C) 2020 Erdem Ersoy
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import gettext
import locale
import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
gi.require_version('GLib', '2.0')
from gi.repository import Gtk, Gdk, GLib

locale.setlocale(locale.LC_ALL, "")
gettext.bindtextdomain("flatpak-gui", "po/")
gettext.textdomain("flatpak-gui")
_ = gettext.gettext
gettext.install("flatpak-gui", "po/")


class InfoWindow(object):
    def __init__(self, application, infostring, app):
        self.Application = application
        self.InfoString = infostring
        self.App = app

        try:
            InfoGUIFile = "ui/infowindow.glade"
            InfoBuilder = Gtk.Builder.new_from_file(InfoGUIFile)
            InfoBuilder.connect_signals(self)
        except GLib.GError:
            print(_("Error reading GUI file: ") + InfoGUIFile)
            raise

        InfoTextBuffer = InfoBuilder.get_object(
                                    "InfoTextBuffer")
        InfoTextBuffer.set_text(infostring)

        InfoButton = InfoBuilder.get_object("InfoButton")
        InfoButton.set_label(_("_Copy to Clipboard"))

        self.InfoWindow = InfoBuilder.get_object("InfoWindow")
        self.InfoWindow.set_application(application)
        self.InfoWindow.set_title(_("Info About ") + app.get_name())
        self.InfoWindow.show()

    def onDestroy(self, *args):
        self.InfoWindow.destroy()

    def onPressedCopyToClipboard(self, button):
        ClipboardCurrent = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
        ClipboardCurrent.set_text(self.InfoString, -1)
