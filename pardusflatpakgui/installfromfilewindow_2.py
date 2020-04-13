#!/usr/bin/env python3
#
# Pardus Flatpak GUI install from file second window module
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
import sys
import threading
import time
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


class InstallFromFileWindow2(object):
    def __init__(self, application, flatpakinstallation, fileflatpakrefname,
                 liststore):
        self.Application = application
        self.FlatpakInstallation = flatpakinstallation

        self.FileFlatpakRefName = fileflatpakrefname
        self.FileFlatpakRef = open(self.FileFlatpakRefName, "r")
        self.FileFlatpakRefContents = self.FileFlatpakRef.read(-1)
        self.FileFlatpakRefContentsAsBytes = bytes(
            self.FileFlatpakRefContents, "utf-8")
        self.FileFlatpakRefContentsAsGLibBytes = GLib.Bytes.new(
            self.FileFlatpakRefContentsAsBytes)

        self.FlatpakTransaction = \
            Flatpak.Transaction.new_for_installation(
                self.FlatpakInstallation,
                Gio.Cancellable.new())
        self.FlatpakTransaction.set_disable_dependencies(False)
        self.FlatpakTransaction.set_disable_prune(False)
        self.FlatpakTransaction.set_disable_related(False)
        self.FlatpakTransaction.set_disable_static_deltas(False)
        self.FlatpakTransaction.set_no_deploy(False)
        self.FlatpakTransaction.set_no_pull(False)
        self.FlatpakTransaction.add_install_flatpakref(
            self.FileFlatpakRefContentsAsGLibBytes)

        self.ListStoreMain = liststore

        try:
            InstallFromFileGUIFile = "ui/actionwindow.glade"
            InstallFromFileBuilder = Gtk.Builder.new_from_file(
                                         InstallFromFileGUIFile)
            InstallFromFileBuilder.connect_signals(self)
        except GLib.GError:
            print(_("Error reading GUI file: ") + InstallFromFileGUIFile)
            raise

        self.InstallFromFileWindow = InstallFromFileBuilder.get_object(
                                         "ActionWindow")
        self.InstallFromFileWindow.set_application(application)
        self.InstallFromFileWindow.set_title(_("Installing from file..."))
        self.InstallFromFileWindow.show()

        self.InstallFromFileProgressBar = InstallFromFileBuilder.get_object(
                                              "ActionProgressBar")
        self.ProgressBarValue = int(
            self.InstallFromFileProgressBar.get_fraction() * 100)

        self.InstallFromFileLabel = InstallFromFileBuilder.get_object(
                                        "ActionLabel")
        self.InstallFromFileTextBuffer = InstallFromFileBuilder.get_object(
                                             "ActionTextBuffer")

        self.InstallFromFileTextBuffer.set_text("\0", -1)
        self.StatusText = _("Installing from file...")
        self.InstallFromFileLabel.set_text(self.StatusText)
        self.InstallFromFileTextBuffer.set_text(self.StatusText)

        self.InstallFromFileThread = threading.Thread(
                                         target=self.InstallFromFile,
                                         args=())
        self.InstallFromFileThread.start()
        GLib.threads_init()

    def InstallFromFile(self):
        self.handler_id = self.FlatpakTransaction.connect(
                        "new-operation",
                        self.InstallProgressCallback)
        self.handler_id_2 = self.FlatpakTransaction.connect(
                        "operation-done",
                        self.InstallProgressCallbackDisconnect)
        self.handler_id_error = self.FlatpakTransaction.connect(
                        "operation-error",
                        self.InstallProgressCallbackError)
        try:
            self.FlatpakTransaction.run(Gio.Cancellable.new())
        except GLib.Error:
            statustext = _("Error at installation!")
            self.StatusText = self.StatusText + "\n" + statustext
            GLib.idle_add(self.InstallFromFileLabel.set_text,
                          statustext,
                          priority=GLib.PRIORITY_DEFAULT)
            GLib.idle_add(self.InstallFromFileTextBuffer.set_text,
                          self.StatusText,
                          priority=GLib.PRIORITY_DEFAULT)
        else:
            statustext = _("Installing completed!")
            self.StatusText = self.StatusText + "\n" + statustext
            GLib.idle_add(self.InstallFromFileLabel.set_text,
                          statustext,
                          priority=GLib.PRIORITY_DEFAULT)
            GLib.idle_add(self.InstallFromFileTextBuffer.set_text,
                          self.StatusText,
                          priority=GLib.PRIORITY_DEFAULT)
        self.FlatpakTransaction.disconnect(self.handler_id)
        self.FlatpakTransaction.disconnect(self.handler_id_2)
        self.FlatpakTransaction.disconnect(self.handler_id_error)
        time.sleep(0.5)

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

    def InstallProgressCallback(self, *args):
        self.RefToInstall = Flatpak.Ref.parse(args[1].get_ref())
        self.RefToInstallRealName = self.RefToInstall.get_name()
        self.RefToInstallArch = self.RefToInstall.get_arch()
        self.RefToInstallBranch = self.RefToInstall.get_branch()

        self.FlatpakTransaction.set_default_arch(self.RefToInstallArch)

        statustext = _("Installing: ") + self.RefToInstallRealName
        self.StatusText = self.StatusText + "\n" + statustext
        GLib.idle_add(self.InstallFromFileLabel.set_text,
                      statustext,
                      priority=GLib.PRIORITY_DEFAULT)
        GLib.idle_add(self.InstallFromFileTextBuffer.set_text,
                      self.StatusText,
                      priority=GLib.PRIORITY_DEFAULT)

        self.TransactionProgress = args[2]
        self.TransactionProgress.set_update_frequency(200)
        self.handler_id_progress = self.TransactionProgress.connect(
                                      "changed",
                                      self.ProgressBarUpdate)

    def InstallProgressCallbackDisconnect(self, *args):
        self.TransactionProgress.disconnect(self.handler_id_progress)

    def InstallProgressCallbackError(self, *args):
        self.RefToInstall = Flatpak.Ref.parse(args[1].get_ref())
        self.RefToInstallRealName = self.RefToInstall.get_name()

        statustext = _("Not installed: ") + self.RefToInstallRealName
        self.StatusText = self.StatusText + "\n" + statustext
        GLib.idle_add(self.InstallLabel.set_text,
                      statustext,
                      priority=GLib.PRIORITY_DEFAULT)
        GLib.idle_add(self.InstallTextBuffer.set_text,
                      self.StatusText,
                      priority=GLib.PRIORITY_DEFAULT)

        if self.RefToInstallRealName != self.AppToInstallRealName:
            return True
        else:
            return False

    def ProgressBarUpdate(self, transaction_progress):
        GLib.idle_add(self.InstallFromFileProgressBar.set_fraction,
                      float(transaction_progress.get_progress()) / 100.0,
                      priority=GLib.PRIORITY_DEFAULT)

    def onDestroy(self, *args):
        self.InstallFromFileWindow.destroy()
