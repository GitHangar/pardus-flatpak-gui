#!/usr/bin/env python3
#
# Flatpak GUI install from file input window module
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

from .installfromfilewindow import InstallFromFileWindow

import gettext
import locale
import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Flatpak', '1.0')
gi.require_version('GLib', '2.0')
from gi.repository import Gtk, Flatpak, GLib

locale.setlocale(locale.LC_ALL, "")
gettext.bindtextdomain("flatpak-gui", "po/")
gettext.textdomain("flatpak-gui")
_ = gettext.gettext
gettext.install("flatpak-gui", "po/")


class InstallFromFileInputWindow(object):
    def __init__(self, application, flatpakinstallation, liststore):
        self.Application = application
        self.FlatpakInstallation = flatpakinstallation
        self.ListStoreMain = liststore

        try:
            InstallFromFileInputGUIFile = "ui/installfromfileinputwindow.glade"
            self.InstallFromFileInputBuilder = \
                Gtk.Builder.new_from_file(InstallFromFileInputGUIFile)
            self.InstallFromFileInputBuilder.connect_signals(self)
        except GLib.GError:
            print(_("Error reading GUI file: ") + InstallFromFileInputGUIFile)
            raise

        self.InstallFromFileInputLabel = \
            self.InstallFromFileInputBuilder.get_object(
                "InstallFromFileInputLabel")
        self.InstallFromFileInputLabel.set_text(
            _("Please choose a Flatpak reference file."))

        self.InstallFromFileInputLabel2 = \
            self.InstallFromFileInputBuilder.get_object(
                "InstallFromFileInputLabel2")
        self.InstallFromFileInputLabel2.set_text(
            _("NOTE: Installing an application from third party remote repositories isn't secured as installing an application from official repositories of your distribution."))

        self.InstallFromFileInputButton = \
            self.InstallFromFileInputBuilder.get_object(
                "InstallFromFileInputButton")
        self.InstallFromFileInputButton.set_label(_("I_nstall"))

        self.InstallFromFileInputWindow = \
            self.InstallFromFileInputBuilder.get_object(
                "InstallFromFileInputWindow")
        self.InstallFromFileInputWindow.set_title(_("Choose a file"))
        self.InstallFromFileInputWindow.set_application(application)
        self.InstallFromFileInputWindow.show()

    def onInstallAtInstallFromFile(self, button):
        self.InstallFromFileInputFileChooser = \
            self.InstallFromFileInputBuilder.get_object(
                "InstallFromFileInputFileChooser")
        self.FileFlatpakRefName = \
            self.InstallFromFileInputFileChooser.get_filename()

        InstallFromFileWindow(self.Application, self.FlatpakInstallation,
                              self.FileFlatpakRefName,
                              self.ListStoreMain)
        self.InstallFromFileInputFileChooser.unselect_filename(
            self.FileFlatpakRefName)
        self.onDestroy()

    def onDestroy(self, *args):
        self.InstallFromFileInputWindow.destroy()
