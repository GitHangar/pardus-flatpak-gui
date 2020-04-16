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
from gi.repository import Gtk, Flatpak, GLib, Gio

locale.setlocale(locale.LC_ALL, "")
gettext.bindtextdomain("pardus-flatpak-gui", "po/")
gettext.textdomain("pardus-flatpak-gui")
_ = gettext.gettext
gettext.install("pardus-flatpak-gui", "po/")


class InstallFromEntryWindow(object):
    def __init__(self, application, flatpakinstallation, treeview,
                 runmenuitem, installmenuitem, uninstallmenuitem):
        self.Application = application
        self.FlatpakInstallation = flatpakinstallation
        self.TreeViewMain = treeview
        self.RunMenuItem = runmenuitem
        self.InstallMenuItem = installmenuitem
        self.UninstallMenuItem = uninstallmenuitem

        try:
            InstallInputGUIFile = "ui/installinputwindow.glade"
            self.InstallInputBuilder = Gtk.Builder.new_from_file(
                                           InstallInputGUIFile)
            self.InstallInputBuilder.connect_signals(self)
        except GLib.GError:
            print(_("Error reading GUI file: ") + InstallInputGUIFile)
            raise

        try:
            MessagesGUIFile = "ui/messagedialogs.glade"
            MessagesBuilder = Gtk.Builder.new_from_file(MessagesGUIFile)
            MessagesBuilder.connect_signals(self)
        except GLib.GError:
            print(_("Error reading message dialogs GUI file: ") +
                  MessagesGUIFile)
            raise

        self.MessageDialogError = MessagesBuilder.get_object(
            "MessageDialogError")

        self.InstallInputLabel = self.InstallInputBuilder.get_object(
            "InstallInputLabel")
        self.InstallInputLabel.set_text(
            _("Please enter an application name (Ex: org.libreoffice.LibreOffice) what you want to install from Flathub."))

        self.InstallInputLabel2 = self.InstallInputBuilder.get_object(
            "InstallInputLabel2")
        self.InstallInputLabel2.set_text(
            _("NOTE: Installing an application from third party remote repositories isn't secured as installing an application from official repositories of your distribution."))

        self.InstallInputButton = self.InstallInputBuilder.get_object(
            "InstallInputButton")
        self.InstallInputButton.set_label(_("I_nstall"))

        self.InstallInputWindow = \
            self.InstallInputBuilder.get_object("InstallInputWindow")
        self.InstallInputWindow.set_title(_("Enter an application name"))
        self.InstallInputWindow.set_application(application)
        self.InstallInputWindow.show()

    def onInstallAtInstall(self, button):
        self.InstallInputEntry = self.InstallInputBuilder.get_object(
                                     "InstallInputEntry")
        self.AppToInstallRealName = self.InstallInputEntry.get_text()
        if len(self.AppToInstallRealName.split(".")) < 3:
            self.MessageDialogError.set_markup(
                _("<big><b>Input Error</b></big>"))
            self.MessageDialogError.format_secondary_text(
                _("Input entered is invalid."))
            self.MessageDialogError.run()
            self.MessageDialogError.hide()
            return None

        self.FlatpakRefsList = \
            self.FlatpakInstallation.list_installed_refs()
        self.FlatHubRefsList = \
            self.FlatpakInstallation.list_remote_refs_sync(
                                   "flathub", Gio.Cancellable.new())

        for item in self.FlatpakRefsList:
            for item2 in self.FlatHubRefsList:
                if item.get_name() == item2.get_name():
                    self.FlatHubRefsList.remove(item2)

        self.FlatpakRefsList = self.FlatpakRefsList + self.FlatHubRefsList

        for listitem in self.FlatpakRefsList:
            if listitem.get_name() == self.AppToInstallRealName and \
              listitem.get_arch() == Flatpak.get_default_arch():
                self.AppToInstall = listitem

        self.InstallInputEntry.set_text("")
        InstallFromEntryWindow2(self.Application, self.AppToInstall,
                                self.FlatpakInstallation, self.TreeViewMain,
                                self.RunMenuItem, self.InstallMenuItem,
                                self.UninstallMenuItem)
        self.onDestroy()

    def onDestroy(self, *args):
        self.InstallInputWindow.destroy()
