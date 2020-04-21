#!/usr/bin/env python3
#
# Pardus Flatpak GUI install from entry first window module
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

from pardusflatpakgui.installfromentrywindow_2 import InstallFromEntryWindow2

import gettext
import locale
import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Flatpak', '1.0')
gi.require_version('GLib', '2.0')
gi.require_version('Gio', '2.0')
gi.require_version('Gdk', '3.0')
from gi.repository import Gtk, Flatpak, GLib, Gio, Gdk

locale.setlocale(locale.LC_ALL, "")
gettext.bindtextdomain("pardus-flatpak-gui", "po/")
gettext.textdomain("pardus-flatpak-gui")
_ = gettext.gettext
gettext.install("pardus-flatpak-gui", "po/")


class InstallFromEntryWindow(object):
    def __init__(self, application, flatpak_installation, tree_view, search_filter):
        self.Application = application
        self.FlatpakInstallation = flatpak_installation
        self.TreeViewMain = tree_view
        self.SearchFilter = search_filter

        try:
            install_input_gui_file = "ui/installfromentrywindow.glade"
            self.install_input_builder = Gtk.Builder.new_from_file(
                                           install_input_gui_file)
            self.install_input_builder.connect_signals(self)
        except GLib.GError:
            print(_("Error reading GUI file: ") + install_input_gui_file)
            raise

        try:
            messages_gui_file = "ui/messagedialogs.glade"
            messages_builder = Gtk.Builder.new_from_file(messages_gui_file)
            messages_builder.connect_signals(self)
        except GLib.GError:
            print(_("Error reading message dialogs GUI file: ") +
                  messages_gui_file)
            raise

        self.MessageDialogError = messages_builder.get_object(
            "MessageDialogError")

        self.InstallEntryLabel = self.install_input_builder.get_object(
            "InstallEntryLabel")
        self.InstallEntryLabel.set_text(
            _("Please enter an application name (Ex: org.libreoffice.LibreOffice) what you want to install from "
              "Flathub."))

        self.InstallEntryLabel2 = self.install_input_builder.get_object(
            "InstallEntryLabel2")
        self.InstallEntryLabel2.set_text(
            _("NOTE: Installing an application from third party remote repositories isn't secured as installing an "
              "application from official repositories of your distribution."))

        self.InstallEntryButton = self.install_input_builder.get_object(
            "InstallEntryButton")
        self.InstallEntryButton.set_label(_("I_nstall"))

        self.InstallEntry = self.install_input_builder.get_object(
            "InstallEntry")

        self.InstallEntryWindow = \
            self.install_input_builder.get_object("InstallEntryWindow")
        self.InstallEntryWindow.set_title(_("Enter an application name"))
        self.InstallEntryWindow.set_application(application)
        self.InstallEntryWindow.show()

    def on_install_at_install(self, button):
        real_name = self.InstallEntry.get_text()
        if len(real_name.split(".")) < 3:
            self.MessageDialogError.set_markup(
                _("<big><b>Input Error</b></big>"))
            self.MessageDialogError.format_secondary_text(
                _("Input entered is invalid."))
            self.MessageDialogError.run()
            self.MessageDialogError.hide()
            return None

        flathub_refs_list = self.FlatpakInstallation.list_remote_refs_sync("flathub", Gio.Cancellable.new())
        installed_refs_list = self.FlatpakInstallation.list_installed_refs()

        for item in flathub_refs_list:
            if item.get_name() == real_name and \
              item.get_arch() == Flatpak.get_default_arch() and \
              item not in installed_refs_list:
                ref = item

        InstallFromEntryWindow2(self.Application, ref, self.FlatpakInstallation,
                                self.TreeViewMain, self.SearchFilter)
        self.on_destroy(self.InstallEntryWindow, Gdk.Event.new(0))

    def on_destroy(self, widget, event):
        self.InstallEntry.set_text("")
        widget.destroy()
