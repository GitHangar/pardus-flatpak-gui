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
    at_uninstallation = False

    def __init__(self, application, flatpak_installation, real_name, arch, branch,
                 tree_model, tree_iter, selection, search_filter, show_button):
        self.Application = application

        self.RealName = real_name
        self.Arch = arch
        self.Branch = branch
        self.RefFormat = "app/" + self.RealName + "/" + self.Arch + "/" + self.Branch

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
        self.FlatpakTransaction.add_uninstall(self.RefFormat)

        self.TreeModel = tree_model
        self.TreeIter = tree_iter
        self.Selection = selection
        self.SearchFilter = search_filter
        self.HeaderBarShowButton = show_button

        self.handler_id = self.FlatpakTransaction.connect(
            "new-operation",
            self.uninstall_progress_callback)
        self.handler_id_2 = self.FlatpakTransaction.connect(
            "operation-done",
            self.uninstall_progress_callback_disconnect)
        self.handler_id_error = self.FlatpakTransaction.connect(
            "operation-error",
            self.uninstall_progress_callback_error)

        try:
            uninstall_gui_file = "ui/actionwindow.glade"
            uninstall_builder = Gtk.Builder.new_from_file(uninstall_gui_file)
            uninstall_builder.connect_signals(self)
        except GLib.GError:
            print(_("Error reading GUI file: ") + uninstall_gui_file)
            raise

        self.UninstallWindow = uninstall_builder.get_object("ActionWindow")
        self.UninstallWindow.set_application(self.Application)
        self.UninstallWindow.set_title(_("Uninstalling..."))
        self.UninstallWindow.show()

        self.UninstallProgressBar = uninstall_builder.get_object(
                                        "ActionProgressBar")
        self.ProgressBarValue = int(
            self.UninstallProgressBar.get_fraction() * 100)

        self.UninstallLabel = uninstall_builder.get_object("ActionLabel")
        self.UninstallTextBuffer = uninstall_builder.get_object(
                                       "ActionTextBuffer")

        self.UninstallTextBuffer.set_text("\0", -1)
        self.StatusText = _("Uninstalling...")
        self.UninstallLabel.set_text(self.StatusText)
        self.UninstallTextBuffer.set_text(self.StatusText)

        self.UninstallThread = threading.Thread(
                           target=self.uninstall,
                           args=())
        self.UninstallThread.start()
        GLib.threads_init()

    def uninstall(self):
        try:
            self.FlatpakTransaction.run(Gio.Cancellable.new())
        except GLib.Error:
            status_text = _("Error at uninstalling!")
            self.StatusText = self.StatusText + "\n" + status_text
            GLib.idle_add(self.UninstallLabel.set_text,
                          status_text,
                          priority=GLib.PRIORITY_DEFAULT)
            GLib.idle_add(self.UninstallTextBuffer.set_text,
                          self.StatusText,
                          priority=GLib.PRIORITY_DEFAULT)
        else:
            status_text = _("Uninstalling completed!")
            self.StatusText = self.StatusText + "\n" + status_text
            GLib.idle_add(self.UninstallLabel.set_text,
                          status_text,
                          priority=GLib.PRIORITY_DEFAULT)
            GLib.idle_add(self.UninstallTextBuffer.set_text,
                          self.StatusText,
                          priority=GLib.PRIORITY_DEFAULT)
        self.FlatpakTransaction.disconnect(self.handler_id)
        self.FlatpakTransaction.disconnect(self.handler_id_2)
        self.FlatpakTransaction.disconnect(self.handler_id_error)
        time.sleep(0.5)

        uninstalled_ref = Flatpak.InstalledRef()
        for ref in self.FlatpakInstallation.list_remote_refs_sync("flathub", Gio.Cancellable.new()):
            if ref.get_name() == self.RealName and \
                    ref.get_arch() == self.Arch and \
                    ref.get_branch() == self.Branch:
                uninstalled_ref = ref
                break
            else:
                continue

        uninstalled_ref_real_name = uninstalled_ref.get_name()
        uninstalled_ref_arch = uninstalled_ref.get_arch()
        uninstalled_ref_branch = uninstalled_ref.get_branch()
        uninstalled_ref_remote = "flathub"
        installed_size_mib_str = ""

        download_size = uninstalled_ref.get_download_size()
        download_size_mib = download_size / 1048576
        download_size_mib_str = f"{download_size_mib:.2f}" + " MiB"

        name = ""

        # FIXME: Fix assertion 'filter_iter->stamp == filter->priv->stamp'
        GLib.idle_add(self.TreeModel.set_row,
                      self.TreeIter, [uninstalled_ref_real_name,
                                      uninstalled_ref_arch,
                                      uninstalled_ref_branch,
                                      uninstalled_ref_remote,
                                      installed_size_mib_str,
                                      download_size_mib_str,
                                      name],
                      priority=GLib.PRIORITY_DEFAULT)
        time.sleep(0.2)

        self.SearchFilter.refilter()
        time.sleep(0.3)

        UninstallWindow.at_uninstallation = False

        if self.HeaderBarShowButton.get_active():
            GLib.idle_add(self.HeaderBarShowButton.set_active,
                          False,
                          priority=GLib.PRIORITY_DEFAULT)
            time.sleep(0.2)

            GLib.idle_add(self.HeaderBarShowButton.set_active,
                          True,
                          priority=GLib.PRIORITY_DEFAULT)
            time.sleep(0.2)

    def uninstall_progress_callback(self, transaction, operation, progress):
        ref_to_uninstall = Flatpak.Ref.parse(operation.get_ref())
        ref_to_uninstall_real_name = ref_to_uninstall.get_name()

        status_text = _("Installing: ") + ref_to_uninstall_real_name
        self.StatusText = self.StatusText + "\n" + status_text
        GLib.idle_add(self.UninstallLabel.set_text,
                      status_text,
                      priority=GLib.PRIORITY_DEFAULT)
        GLib.idle_add(self.UninstallTextBuffer.set_text,
                      self.StatusText,
                      priority=GLib.PRIORITY_DEFAULT)

        self.TransactionProgress = progress  # FIXME: Fix PyCharm warning
        self.TransactionProgress.set_update_frequency(200)
        self.handler_id_progress = self.TransactionProgress.connect(
            "changed",
            self.progress_bar_update)  # FIXME: Fix PyCharm warning

    def uninstall_progress_callback_disconnect(self, transaction, operation, commit, result):
        self.TransactionProgress.disconnect(self.handler_id_progress)

    def uninstall_progress_callback_error(self, transaction, operation, error, details):
        ref_to_uninstall = Flatpak.Ref.parse(operation.get_ref())
        ref_to_uninstall_real_name = ref_to_uninstall.get_name()

        status_text = _("Not installed: ") + ref_to_uninstall_real_name
        self.StatusText = self.StatusText + "\n" + status_text
        GLib.idle_add(self.UninstallLabel.set_text,
                      status_text,
                      priority=GLib.PRIORITY_DEFAULT)
        GLib.idle_add(self.UninstallTextBuffer.set_text,
                      self.StatusText,
                      priority=GLib.PRIORITY_DEFAULT)

        if ref_to_uninstall_real_name != self.RealName:
            return True
        else:
            return False

    def progress_bar_update(self, transaction_progress):
        GLib.idle_add(self.InstallProgressBar.set_fraction,
                      float(transaction_progress.get_progress()) / 100.0,
                      priority=GLib.PRIORITY_DEFAULT)

    def on_delete_action_window(self, widget, event):
        widget.hide_on_delete()
