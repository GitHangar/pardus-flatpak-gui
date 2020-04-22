#!/usr/bin/env python3
#
# Pardus Flatpak GUI Application module
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

from pardusflatpakgui.mainwindow import MainWindow
from pardusflatpakgui.installwindow import InstallWindow

import gettext
import locale
import sys
import gi
gi.require_version('Gtk', '3.0')
gi.require_version('GLib', '2.0')
gi.require_version('Flatpak', '1.0')
gi.require_version('Gio', '2.0')
from gi.repository import Gtk, GLib, Flatpak, Gio

locale.setlocale(locale.LC_ALL, "")
gettext.bindtextdomain("pardus-flatpak-gui", "po/")
gettext.textdomain("pardus-flatpak-gui")
_ = gettext.gettext
gettext.install("pardus-flatpak-gui", "po/")


class FlatpakGUIApp(Gtk.Application):
    def __init__(self, application_id, flags):
        Gtk.Application.__init__(self, application_id=application_id, flags=flags)

        try:
            messages_gui_file = "ui/messagedialogs.glade"
            messages_builder = Gtk.Builder.new_from_file(messages_gui_file)
            messages_builder.connect_signals(self)
        except GLib.GError:
            print(_("Error reading message dialogs GUI file: ")
                  + messages_gui_file)
            raise

        self.MessageDialogError = messages_builder.get_object(
            "MessageDialogError")

        self.connect("activate", self.new_window)

    def new_window(self, application):
        if len(sys.argv) == 1:
            MainWindow(self)
        elif len(sys.argv) == 2:
            file_name = sys.argv[1]
            try:
                file = open(file_name, "r")
            except FileNotFoundError:
                self.MessageDialogError.set_markup(
                    _("<big><b>File Not Found Error</b></big>"))
                self.MessageDialogError.format_secondary_text(
                    _("File not found: ") + file_name)
                self.MessageDialogError.run()
                self.MessageDialogError.hide()
                return None
            else:
                file_contents = file.read(-1)
                file_contents_bytes = bytes(file_contents, "utf-8")
                file_contents_glib_bytes = GLib.Bytes.new(file_contents_bytes)

                InstallWindow(self, application, file_contents_glib_bytes)
        else:
            self.MessageDialogError.set_markup(
                _("<big><b>Argument Error</b></big>"))
            self.MessageDialogError.format_secondary_text(
                _("There are too many arguments. Argument count: ") +
                str(len(sys.argv)))
            self.MessageDialogError.run()
            self.MessageDialogError.hide()
            return None
