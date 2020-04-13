#!/usr/bin/env python3
#
# Flatpak GUI Application module
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

from flatpakgui.mainwindow import MainWindow
from flatpakgui.installwindow import InstallWindow

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
gettext.bindtextdomain("flatpak-gui", "po/")
gettext.textdomain("flatpak-gui")
_ = gettext.gettext
gettext.install("flatpak-gui", "po/")


class FlatpakGUIApp(Gtk.Application):
    def __init__(self, application_id, flags):
        Gtk.Application.__init__(self, application_id=application_id,
                                 flags=flags)

        try:
            MessagesGUIFile = "ui/messagedialogs.glade"
            MessagesBuilder = Gtk.Builder.new_from_file(MessagesGUIFile)
            MessagesBuilder.connect_signals(self)
        except GLib.GError:
            print(_("Error reading message dialogs GUI file: ")
                  + MessagesGUIFile)
            raise

        self.MessageDialogError = MessagesBuilder.get_object(
            "MessageDialogError")

        self.connect("activate", self.new_window)

    def new_window(self, *args):
        if len(sys.argv) == 1:
            MainWindow(self)
        elif len(sys.argv) == 2:
            self.FlatpakInstallation = Flatpak.Installation.new_system()

            self.FileFlatpakRefName = sys.argv[1]
            try:
                self.FileFlatpakRef = open(self.FileFlatpakRefName, "r")
            except FileNotFoundError:
                self.MessageDialogError.set_markup(
                    _("<big><b>File Not Found Error</b></big>"))
                self.MessageDialogError.format_secondary_text(
                    _("File not found: ") + self.FileFlatpakRefName)
                self.MessageDialogError.run()
                self.MessageDialogError.hide()
                return None
            else:
                self.FileFlatpakRefContents = self.FileFlatpakRef.read(-1)
                self.FileFlatpakRefContentsAsBytes = bytes(
                    self.FileFlatpakRefContents, "utf-8")
                self.FileFlatpakRefContentsAsGLibBytes = GLib.Bytes.new(
                    self.FileFlatpakRefContentsAsBytes)

                self.AppToInstall = self.FlatpakInstallation.install_ref_file(
                    self.FileFlatpakRefContentsAsGLibBytes,
                    Gio.Cancellable.new())
                if not self.AppToInstall.get_kind() == Flatpak.RefKind.APP:
                    self.MessageDialogError.set_markup(
                        _("<big><b>Installing Error</b></big>"))
                    self.MessageDialogError.format_secondary_text(
                        _("The selected file doesn't indicate a Flatpak application: ") +
                        self.FileFlatpakRefName)
                    self.MessageDialogError.run()
                    self.MessageDialogError.hide()
                    return None

                InstallWindow(self, self.AppToInstall,
                              self.FlatpakInstallation, None)
        else:
            self.MessageDialogError.set_markup(
                _("<big><b>Argument Error</b></big>"))
            self.MessageDialogError.format_secondary_text(
                _("There are too many arguments. Argument count: ") +
                str(len(sys.argv)))
            self.MessageDialogError.run()
            self.MessageDialogError.hide()
            return None
