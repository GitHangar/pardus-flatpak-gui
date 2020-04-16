#!/usr/bin/env python3
#
# Pardus Flatpak GUI uninstall from file window module
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


class UninstallWindow(object):
    def __init__(self, application, realname, arch, branch,
                 flatpakinstallation, treeview, runmenuitem,
                 installmenuitem, uninstallmenuitem):
        self.Application = application

        self.AppToUninstallRealName = realname
        self.AppToUninstallArch = arch
        self.AppToUninstallBranch = branch

        self.FlatpakInstallation = flatpakinstallation
        self.FlatpakTransaction = \
            Flatpak.Transaction.new_for_installation(
                self.FlatpakInstallation,
                Gio.Cancellable.new())
        self.FlatpakTransaction.set_default_arch(self.AppToUninstallArch)
        self.FlatpakTransaction.set_disable_dependencies(False)
        self.FlatpakTransaction.set_disable_prune(False)
        self.FlatpakTransaction.set_disable_related(False)
        self.FlatpakTransaction.set_disable_static_deltas(False)
        self.FlatpakTransaction.set_no_deploy(False)
        self.FlatpakTransaction.set_no_pull(False)
        self.FlatpakTransaction.add_uninstall(
            "app/" + self.AppToUninstallRealName + "/" +
            self.AppToUninstallArch + "/" + self.AppToUninstallBranch)

        self.TreeViewMain = treeview

        self.Selection = self.TreeViewMain.get_selection()
        self.TreeModel, self.TreeIter = self.Selection.get_selected()
        self.TreePath = self.TreeModel.get_path(self.TreeIter)
        self.SelectedRowIndex = self.TreePath.get_indices()[0]

        self.RunMenuItem = runmenuitem
        self.InstallMenuItem = installmenuitem
        self.UninstallMenuItem = uninstallmenuitem

        try:
            UninstallGUIFile = "ui/actionwindow.glade"
            UninstallBuilder = Gtk.Builder.new_from_file(UninstallGUIFile)
            UninstallBuilder.connect_signals(self)
        except GLib.GError:
            print(_("Error reading GUI file: ") + UninstallGUIFile)
            raise

        self.UninstallWindow = UninstallBuilder.get_object("ActionWindow")
        self.UninstallWindow.set_application(application)
        self.UninstallWindow.set_title(_("Uninstalling..."))
        self.UninstallWindow.show()

        self.UninstallProgressBar = UninstallBuilder.get_object(
                                        "ActionProgressBar")
        self.ProgressBarValue = int(
            self.UninstallProgressBar.get_fraction() * 100)

        self.UninstallLabel = UninstallBuilder.get_object("ActionLabel")
        self.UninstallTextBuffer = UninstallBuilder.get_object(
                                       "ActionTextBuffer")

        self.UninstallTextBuffer.set_text("\0", -1)
        self.StatusText = _("Uninstalling...")
        self.UninstallLabel.set_text(self.StatusText)
        self.UninstallTextBuffer.set_text(self.StatusText)

        self.UninstallThread = threading.Thread(
                           target=self.Uninstall,
                           args=())
        self.UninstallThread.start()
        GLib.threads_init()

    def Uninstall(self):
        self.handler_id = self.FlatpakTransaction.connect(
                        "new-operation",
                        self.UninstallProgressCallback)
        self.handler_id_2 = self.FlatpakTransaction.connect(
                        "operation-done",
                        self.UninstallProgressCallbackDisconnect)
        self.handler_id_error = self.FlatpakTransaction.connect(
                        "operation-error",
                        self.UninstallProgressCallbackError)
        try:
            self.FlatpakTransaction.run(Gio.Cancellable.new())
        except GLib.Error:
            statustext = _("Error at uninstallation!")
            self.StatusText = self.StatusText + "\n" + statustext
            GLib.idle_add(self.UninstallLabel.set_text,
                          statustext,
                          priority=GLib.PRIORITY_DEFAULT)
            GLib.idle_add(self.UninstallTextBuffer.set_text,
                          self.StatusText,
                          priority=GLib.PRIORITY_DEFAULT)
        else:
            statustext = _("Uninstalling completed!")
            self.StatusText = self.StatusText + "\n" + statustext
            GLib.idle_add(self.UninstallLabel.set_text,
                          statustext,
                          priority=GLib.PRIORITY_DEFAULT)
            GLib.idle_add(self.UninstallTextBuffer.set_text,
                          self.StatusText,
                          priority=GLib.PRIORITY_DEFAULT)
        self.FlatpakTransaction.disconnect(self.handler_id)
        self.FlatpakTransaction.disconnect(self.handler_id_2)
        self.FlatpakTransaction.disconnect(self.handler_id_error)
        time.sleep(0.5)

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
                    listitem.get_arch() == Flatpak.get_default_arch() and \
                    listitem.get_branch() == self.AppToUninstallBranch and \
                    listitem.get_name() == self.AppToUninstallRealName:
                if listitem in flathubrefslist:
                    RemoteName = "flathub"
                    DownloadSize = listitem.get_download_size()
                    DownloadSizeMiB = DownloadSize / 1048576
                    DownloadSizeMiBAsString = f"{DownloadSizeMiB:.2f}" + " MiB"
                    Name = ""

                InstalledSize = listitem.get_installed_size()
                InstalledSizeMiB = InstalledSize / 1048576
                InstalledSizeMiBAsString = \
                    f"{InstalledSizeMiB:.2f}" + " MiB"

                self.TreeModel.set_row(self.TreeIter, [listitem.get_name(),
                                                       listitem.get_arch(),
                                                       listitem.get_branch(),
                                                       RemoteName,
                                                       InstalledSizeMiBAsString,
                                                       DownloadSizeMiBAsString,
                                                       Name])

                self.RunMenuItem.set_sensitive(False)
                self.UninstallMenuItem.set_sensitive(False)
                self.InstallMenuItem.set_sensitive(True)

                GLib.idle_add(self.TreeModel.refilter,
                              data=None,
                              priority=GLib.PRIORITY_DEFAULT)
                time.sleep(0.25)
                break
            else:
                continue

    def UninstallProgressCallback(self, *args):
        self.RefToUninstall = Flatpak.Ref.parse(args[1].get_ref())
        self.RefToUninstallRealName = self.RefToUninstall.get_name()

        statustext = _("Uninstalling: ") + self.RefToUninstallRealName
        self.StatusText = self.StatusText + "\n" + statustext
        GLib.idle_add(self.UninstallLabel.set_text,
                      statustext,
                      priority=GLib.PRIORITY_DEFAULT)
        GLib.idle_add(self.UninstallTextBuffer.set_text,
                      self.StatusText,
                      priority=GLib.PRIORITY_DEFAULT)

        self.TransactionProgress = args[2]
        self.TransactionProgress.set_update_frequency(200)
        self.handler_id_progress = self.TransactionProgress.connect(
                                      "changed",
                                      self.ProgressBarUpdate)

    def UninstallProgressCallbackDisconnect(self, *args):
        self.TransactionProgress.disconnect(self.handler_id_progress)

    def UninstallProgressCallbackError(self, *args):
        self.RefToUninstall = Flatpak.Ref.parse(args[1].get_ref())
        self.RefToUninstallRealName = self.RefToUninstall.get_name()

        statustext = _("Not uninstalled: ") + self.RefToUninstallRealName
        self.StatusText = self.StatusText + "\n" + statustext
        GLib.idle_add(self.UninstallLabel.set_text,
                      statustext,
                      priority=GLib.PRIORITY_DEFAULT)
        GLib.idle_add(self.UninstallTextBuffer.set_text,
                      self.StatusText,
                      priority=GLib.PRIORITY_DEFAULT)

        if self.RefToUninstallRealName != self.AppToUninstallRealName:
            return True
        else:
            return False

    def ProgressBarUpdate(self, transaction_progress):
        GLib.idle_add(self.InstallProgressBar.set_fraction,
                      float(transaction_progress.get_progress()) / 100.0,
                      priority=GLib.PRIORITY_DEFAULT)

    def onDestroy(self, *args):
        self.UninstallWindow.destroy()
