#!/usr/bin/env python3
#
# Pardus Flatpak GUI direct install window module
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
gi.require_version('Flatpak', '1.0')
gi.require_version('GLib', '2.0')
gi.require_version('Gio', '2.0')
from gi.repository import Gtk, Flatpak, GLib, Gio

locale.setlocale(locale.LC_ALL, "")
gettext.bindtextdomain("flatpak-gui", "po/")
gettext.textdomain("flatpak-gui")
_ = gettext.gettext
gettext.install("flatpak-gui", "po/")


class InstallWindow(object):
    def __init__(self, application, flatpak_installation, real_name, arch,
                 branch, remote, list_store, search_filter):
        self.Application = application

        self.RealName = real_name
        self.Arch = arch
        self.Branch = branch
        self.Remote = remote

        self.RefFormat = "app/" + self.RealName + "/" + self.Arch + "/" + self.Branch
        self.Ref = Flatpak.Ref.parse(self.RefFormat)

        self.FlatpakInstallation = flatpak_installation
        self.FlatpakTransaction = \
            Flatpak.Transaction.new_for_installation(
                self.FlatpakInstallation,
                Gio.Cancellable.new())
        self.FlatpakTransaction.set_default_arch(self.Arch)
        self.FlatpakTransaction.set_disable_dependencies(False)
        self.FlatpakTransaction.set_disable_prune(False)
        self.FlatpakTransaction.set_disable_related(False)
        self.FlatpakTransaction.set_disable_static_deltas(False)
        self.FlatpakTransaction.set_no_deploy(False)
        self.FlatpakTransaction.set_no_pull(False)
        self.FlatpakTransaction.add_install(
            self.Remote,
            self.RefFormat,
            None)

        self.ListStoreMain = list_store
        self.SearchFilter = search_filter

        try:
            install_gui_file = "ui/actionwindow.glade"
            install_builder = Gtk.Builder.new_from_file(install_gui_file)
            install_builder.connect_signals(self)
        except GLib.GError:
            print(_("Error reading GUI file: ") + install_gui_file)
            raise

        self.InstallWindow = install_builder.get_object("ActionWindow")
        self.InstallWindow.set_application(application)
        self.InstallWindow.set_title(_("Installing..."))
        self.InstallWindow.show()

        self.InstallProgressBar = install_builder.get_object(
                                        "ActionProgressBar")
        self.ProgressBarValue = int(self.InstallProgressBar.get_fraction() * 100)

        self.InstallLabel = install_builder.get_object("ActionLabel")
        self.InstallTextBuffer = install_builder.get_object(
                                       "ActionTextBuffer")

        self.InstallTextBuffer.set_text("\0", -1)
        self.StatusText = _("Installing...")
        self.InstallLabel.set_text(self.StatusText)
        self.InstallTextBuffer.set_text(self.StatusText)

        self.InstallThread = threading.Thread(
                           target=self.install,
                           args=())
        self.InstallThread.start()
        GLib.threads_init()

    def install(self):
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
            status_text = _("Error at installation!")
            self.StatusText = self.StatusText + "\n" + status_text
            GLib.idle_add(self.InstallLabel.set_text,
                          status_text,
                          priority=GLib.PRIORITY_DEFAULT)
            GLib.idle_add(self.InstallTextBuffer.set_text,
                          self.StatusText,
                          priority=GLib.PRIORITY_DEFAULT)
        else:
            status_text = _("Installing completed!")
            self.StatusText = self.StatusText + "\n" + status_text
            GLib.idle_add(self.InstallLabel.set_text,
                          status_text,
                          priority=GLib.PRIORITY_DEFAULT)
            GLib.idle_add(self.InstallTextBuffer.set_text,
                          self.StatusText,
                          priority=GLib.PRIORITY_DEFAULT)
        self.FlatpakTransaction.disconnect(self.handler_id)
        self.FlatpakTransaction.disconnect(self.handler_id_2)
        self.FlatpakTransaction.disconnect(self.handler_id_error)
        time.sleep(0.5)

        GLib.idle_add(self.ListStoreMain.clear,
                      data=None,
                      priority=GLib.PRIORITY_DEFAULT)

        self.InstalledRefsList = self.FlatpakInstallation.list_installed_refs()
        self.FlatHubRefsList = self.FlatpakInstallation.list_remote_refs_sync(
            "flathub", Gio.Cancellable.new())
        self.NonInstalledRefsList = []

        for item in self.FlatHubRefsList:
            self.NonInstalledRefsList.append(item)
            for item_2 in self.InstalledRefsList:
                if item.get_name() == item_2.get_name() and \
                        item.get_arch() == item_2.get_arch() and \
                        item.get_branch() == item_2.get_branch():
                    if len(self.NonInstalledRefsList) != 0:
                        self.NonInstalledRefsList.pop(len(self.NonInstalledRefsList) - 1)
                    else:
                        self.NonInstalledRefsList = []

        self.AllRefsList = self.InstalledRefsList + self.NonInstalledRefsList

        for list_item in self.AllRefsList:
            if list_item.get_kind() == Flatpak.RefKind.APP and \
               list_item.get_arch() == Flatpak.get_default_arch():
                if list_item not in self.NonInstalledRefsList:
                    remote_name = "flathub"
                    download_size_mib_str = ""
                    name = list_item.get_appdata_name()
                elif list_item not in self.InstalledRefsList:
                    remote_name = self.Remote
                    download_size_mib = list_item.get_download_size()
                    download_size_mib_str = f"{download_size_mib:.2f}" + " MiB"
                    name = ""
                else:
                    continue

                installed_size = list_item.get_installed_size()
                installed_size_mib = installed_size / 1048576
                installed_size_mib_str = \
                    f"{installed_size_mib:.2f}" + " MiB"

                self.ListStoreMain.append([list_item.get_name(),
                                           list_item.get_arch(),
                                           list_item.get_branch(),
                                           remote_name,
                                           installed_size_mib_str,
                                           download_size_mib_str,
                                           name])

                self.SearchFilter.refilter()
                time.sleep(0.01)

            else:
                continue

    def InstallProgressCallback(self, *args):
        self.RefToInstall = Flatpak.Ref.parse(args[1].get_ref())
        self.RefToInstallRealName = self.RefToInstall.get_name()

        status_text = _("Installing: ") + self.RefToInstallRealName
        self.StatusText = self.StatusText + "\n" + status_text
        GLib.idle_add(self.InstallLabel.set_text,
                      status_text,
                      priority=GLib.PRIORITY_DEFAULT)
        GLib.idle_add(self.InstallTextBuffer.set_text,
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

        status_text = _("Not installed: ") + self.RefToInstallRealName
        self.StatusText = self.StatusText + "\n" + status_text
        GLib.idle_add(self.InstallLabel.set_text,
                      status_text,
                      priority=GLib.PRIORITY_DEFAULT)
        GLib.idle_add(self.InstallTextBuffer.set_text,
                      self.StatusText,
                      priority=GLib.PRIORITY_DEFAULT)

        if self.RefToInstallRealName != self.RealName:
            return True
        else:
            return False

    def ProgressBarUpdate(self, transaction_progress):
        GLib.idle_add(self.InstallProgressBar.set_fraction,
                      float(transaction_progress.get_progress()) / 100.0,
                      priority=GLib.PRIORITY_DEFAULT)

    def on_delete_action_window(self, widget, event):
        widget.hide_on_delete()
