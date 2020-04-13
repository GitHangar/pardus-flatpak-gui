#!/usr/bin/env python3
#
# Pardus Flatpak GUI update all window module
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
import threading
import time
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


class UpdateAllWindow(object):
    def __init__(self, application, flatpakinstallation, liststore):
        self.Application = application
        self.FlatpakInstallation = flatpakinstallation
        self.ListStoreMain = liststore
        self.FlatpakRefsList = self.FlatpakInstallation.list_installed_refs()
        self.FlatHubRefsList = self.FlatpakInstallation.list_remote_refs_sync(
                                   "flathub", Gio.Cancellable.new())

        for item in self.FlatpakRefsList:
            for item2 in self.FlatHubRefsList:
                if item.get_name() == item2.get_name():
                    self.FlatHubRefsList.remove(item2)
        self.FlatpakRefsList = self.FlatpakRefsList + self.FlatHubRefsList

        try:
            UpdateAllGUIFile = "ui/actionwindow.glade"
            UpdateAllBuilder = Gtk.Builder.new_from_file(UpdateAllGUIFile)
            UpdateAllBuilder.connect_signals(self)
        except GLib.GError:
            print(_("Error reading GUI file: ") + UpdateAllGUIFile)
            raise

        self.UpdateAllWindow = UpdateAllBuilder.get_object("ActionWindow")
        self.UpdateAllWindow.set_application(application)
        self.UpdateAllWindow.set_title(_("Updating All"))
        self.UpdateAllWindow.show()

        self.UpdateAllProgressBar = UpdateAllBuilder.get_object(
                                        "ActionProgressBar")
        self.ProgressBarValue = int(
            self.UpdateAllProgressBar.get_fraction() * 100)

        self.UpdateAllLabel = UpdateAllBuilder.get_object("ActionLabel")
        self.UpdateAllTextBuffer = UpdateAllBuilder.get_object(
                                       "ActionTextBuffer")

        self.UpdateAllTextBuffer.set_text("\0", -1)
        self.StatusText = _("Updating...")
        self.UpdateAllLabel.set_text(self.StatusText)
        self.UpdateAllTextBuffer.set_text(self.StatusText)

        self.UpdateAllThread = threading.Thread(
                           target=self.UpdateAll,
                           args=())
        self.UpdateAllThread.start()
        GLib.threads_init()

    def UpdateAll(self):
        for listitem in self.FlatpakRefsList:
            if listitem not in self.FlatHubRefsList:
                try:
                    self.ListItem = listitem
                    self.FlatpakInstallation.update(
                                Flatpak.UpdateFlags.NONE,
                                listitem.get_kind(),
                                listitem.get_name(),
                                listitem.get_arch(),
                                listitem.get_branch(),
                                self.UpdateAllProgressCallback(
                                    "",
                                    self.ProgressBarValue,
                                    False,
                                    listitem),
                                None,
                                Gio.Cancellable.new())
                except GLib.Error:
                    statustext = _("Not updated: ") + listitem.get_name()
                    self.StatusText = self.StatusText + "\n" + statustext
                    GLib.idle_add(self.UpdateAllLabel.set_text,
                                  statustext,
                                  priority=GLib.PRIORITY_DEFAULT)
                    GLib.idle_add(self.UpdateAllTextBuffer.set_text,
                                  self.StatusText,
                                  priority=GLib.PRIORITY_DEFAULT)
                else:
                    statustext = _("Updated: ") + listitem.get_name()
                    self.StatusText = self.StatusText + "\n" + statustext
                    GLib.idle_add(self.UpdateAllLabel.set_text,
                                  statustext,
                                  priority=GLib.PRIORITY_DEFAULT)
                    GLib.idle_add(self.UpdateAllTextBuffer.set_text,
                                  self.StatusText,
                                  priority=GLib.PRIORITY_DEFAULT)
                time.sleep(0.5)

        statustext = _("Updating completed!")
        self.StatusText = self.StatusText + "\n" + statustext
        GLib.idle_add(self.UpdateAllLabel.set_text,
                      statustext,
                      priority=GLib.PRIORITY_DEFAULT)
        GLib.idle_add(self.UpdateAllTextBuffer.set_text,
                      self.StatusText,
                      priority=GLib.PRIORITY_DEFAULT)
        GLib.idle_add(self.ListStoreMain.clear,
                      data=None,
                      priority=GLib.PRIORITY_DEFAULT)

        flatpakrefslist = \
            self.FlatpakInstallation.list_installed_refs()
        flathubrefslist = \
            self.FlatpakInstallation.list_remote_refs_sync(
                                   "flathub", Gio.Cancellable.new())

        for item in flatpakrefslist:
            for item2 in flathubrefslist:
                if item.get_name() == item2.get_name():
                    flathubrefslist.remove(item2)
        flatpakrefslist = flatpakrefslist + flathubrefslist

        for listitem in flatpakrefslist:
            if listitem.get_kind() == Flatpak.RefKind.APP and \
               listitem.get_arch() == Flatpak.get_default_arch():
                if listitem in flathubrefslist:
                    RemoteName = "flathub"
                    DownloadSize = listitem.get_download_size()
                    DownloadSizeMiB = DownloadSize / 1048576
                    DownloadSizeMiBAsString = f"{DownloadSizeMiB:.2f}" + " MiB"
                    Name = ""
                else:
                    RemoteName = ""
                    DownloadSizeMiBAsString = ""
                    Name = listitem.get_appdata_name()

                InstalledSize = listitem.get_installed_size()
                InstalledSizeMiB = InstalledSize / 1048576
                InstalledSizeMiBAsString = \
                    f"{InstalledSizeMiB:.2f}" + " MiB"

                self.ListStoreMain.append([listitem.get_name(),
                                          listitem.get_arch(),
                                          listitem.get_branch(),
                                          RemoteName,
                                          InstalledSizeMiBAsString,
                                          DownloadSizeMiBAsString,
                                          Name])
            else:
                continue

    def UpdateAllProgressCallback(self, *args, **kwargs):
        self.ProgressBarValue = self.ProgressBarValue + \
            100 / len(self.FlatpakInstallation.list_installed_refs())
        self.UpdateAllProgressBar.set_fraction(
            float(self.ProgressBarValue) / 100.0)

    def onDestroy(self, *args):
        self.UpdateAllWindow.destroy()
