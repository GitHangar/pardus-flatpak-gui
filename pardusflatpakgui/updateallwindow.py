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
gettext.bindtextdomain("pardus-flatpak-gui", "/usr/share/locale/")
gettext.textdomain("pardus-flatpak-gui")
_ = gettext.gettext
gettext.install("pardus-flatpak-gui", "/usr/share/locale/")


class UpdateAllWindow(object):
    at_updating = False

    def __init__(self, application, flatpak_installation, tree_model, show_button):
        self.Application = application

        self.FlatpakInstallation = flatpak_installation
        self.RefsToUpdate = flatpak_installation.list_installed_refs_for_update(Gio.Cancellable.new())
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

        self.FlatpakTransaction = \
            Flatpak.Transaction.new_for_installation(
                self.FlatpakInstallation,
                Gio.Cancellable.new())
        self.FlatpakTransaction.set_default_arch(Flatpak.get_default_arch())
        self.FlatpakTransaction.set_disable_dependencies(False)
        self.FlatpakTransaction.set_disable_prune(False)
        self.FlatpakTransaction.set_disable_related(False)
        self.FlatpakTransaction.set_disable_static_deltas(False)
        self.FlatpakTransaction.set_no_deploy(False)
        self.FlatpakTransaction.set_no_pull(False)
        for ref_to_update in self.RefsToUpdate:
            ref_str = ref_to_update.format_ref()
            self.FlatpakTransaction.add_update(ref_str, None, None)

        self.TreeModel = tree_model
        self.HeaderBarShowButton = show_button

        try:
            update_all_gui_file = "/usr/share/pardus/pardus-flatpak-gui/ui/actionwindow.glade"
            update_all_builder = Gtk.Builder.new_from_file(update_all_gui_file)
            update_all_builder.connect_signals(self)
        except GLib.GError:
            print(_("Error reading GUI file: ") + update_all_gui_file)
            raise

        self.UpdateAllCancellation = Gio.Cancellable.new()

        self.UpdateAllWindow = update_all_builder.get_object("ActionWindow")
        self.UpdateAllWindow.set_application(application)
        self.UpdateAllWindow.set_title(_("Updating All"))
        self.UpdateAllWindow.show()

        self.UpdateAllProgressBar = update_all_builder.get_object(
                                        "ActionProgressBar")
        self.ProgressBarValue = int(
            self.UpdateAllProgressBar.get_fraction() * 100)

        self.UpdateAllLabel = update_all_builder.get_object("ActionLabel")
        self.UpdateAllTextBuffer = update_all_builder.get_object(
                                       "ActionTextBuffer")

        self.UpdateAllTextBuffer.set_text("\0", -1)
        self.StatusText = _("Updating...")
        self.UpdateAllLabel.set_text(self.StatusText)
        self.UpdateAllTextBuffer.set_text(self.StatusText)

        self.handler_id = self.FlatpakTransaction.connect(
            "new-operation",
            self.update_all_progress_callback)
        self.handler_id_2 = self.FlatpakTransaction.connect(
            "operation-done",
            self.update_all_progress_callback_done)
        self.handler_id_error = self.FlatpakTransaction.connect(
            "operation-error",
            self.update_all_progress_callback_error)

        self.UpdateAllThread = threading.Thread(
                           target=self.update_all,
                           args=())
        self.UpdateAllThread.start()
        GLib.threads_init()

    def update_all(self):
        handler_id_cancel = self.UpdateAllCancellation.connect(self.cancellation_callback, None)
        try:
            self.FlatpakTransaction.run(self.UpdateAllCancellation)
        except GLib.Error:
            status_text = _("Error at updating!")
            self.StatusText = self.StatusText + "\n" + status_text
            GLib.idle_add(self.UpdateAllLabel.set_text,
                          status_text,
                          priority=GLib.PRIORITY_DEFAULT)
            GLib.idle_add(self.UpdateAllTextBuffer.set_text,
                          self.StatusText,
                          priority=GLib.PRIORITY_DEFAULT)
            self.disconnect_handlers(handler_id_cancel)
            UpdateAllWindow.at_updating = False
            return None
        else:
            status_text = _("Updating completed!")
            self.StatusText = self.StatusText + "\n" + status_text
            GLib.idle_add(self.UpdateAllLabel.set_text,
                          status_text,
                          priority=GLib.PRIORITY_DEFAULT)
            GLib.idle_add(self.UpdateAllTextBuffer.set_text,
                          self.StatusText,
                          priority=GLib.PRIORITY_DEFAULT)
        self.disconnect_handlers(handler_id_cancel)
        time.sleep(0.5)

        UpdateAllWindow.at_updating = False

        if self.HeaderBarShowButton.get_active():
            GLib.idle_add(self.HeaderBarShowButton.set_active,
                          False,
                          priority=GLib.PRIORITY_DEFAULT)
            time.sleep(0.2)

            GLib.idle_add(self.HeaderBarShowButton.set_active,
                          True,
                          priority=GLib.PRIORITY_DEFAULT)
            time.sleep(0.2)

    def update_all_progress_callback(self, transaction, operation, progress):
        ref_to_update = Flatpak.Ref.parse(operation.get_ref())
        ref_to_update_real_name = ref_to_update.get_name()
        operation_type = operation.get_operation_type()

        if operation_type == Flatpak.TransactionOperationType.UPDATE:
            status_text = _("Updating: ") + ref_to_update_real_name
            self.StatusText = self.StatusText + "\n" + status_text
            GLib.idle_add(self.UpdateAllLabel.set_text,
                          status_text,
                          priority=GLib.PRIORITY_DEFAULT)
            GLib.idle_add(self.UpdateAllTextBuffer.set_text,
                          self.StatusText,
                          priority=GLib.PRIORITY_DEFAULT)
        elif operation_type == Flatpak.TransactionOperationType.INSTALL:
            status_text = _("Installing: ") + ref_to_update_real_name
            self.StatusText = self.StatusText + "\n" + status_text
            GLib.idle_add(self.UpdateAllLabel.set_text,
                          status_text,
                          priority=GLib.PRIORITY_DEFAULT)
            GLib.idle_add(self.UpdateAllTextBuffer.set_text,
                          self.StatusText,
                          priority=GLib.PRIORITY_DEFAULT)

        self.TransactionProgress = progress  # FIXME: Fix PyCharm warning
        self.TransactionProgress.set_update_frequency(200)
        self.handler_id_progress = self.TransactionProgress.connect(
            "changed",
            self.progress_bar_update)  # FIXME: Fix PyCharm warning

    def update_all_progress_callback_done(self, transaction, operation, commit, result):  # FIXME: Test and review
        self.TransactionProgress.disconnect(self.handler_id_progress)

        operation_ref = Flatpak.Ref.parse(operation.get_ref())
        operation_ref_real_name = operation_ref.get_name()
        operation_ref_arch = operation_ref.get_arch()
        operation_ref_branch = operation_ref.get_branch()
        for updated_ref in self.RefsToUpdate:
            if updated_ref.get_name() == operation_ref_real_name and \
               updated_ref.get_arch() == operation_ref_arch and \
               updated_ref.get_branch() == operation_ref_branch and \
               updated_ref.get_kind() == Flatpak.RefKind.APP:
                updated_ref_real_name = updated_ref.get_name()
                updated_ref_arch = updated_ref.get_arch()
                updated_ref_branch = updated_ref.get_branch()
                updated_ref_remote = "flathub"

                installed_size = updated_ref.get_installed_size()
                installed_size_mib = installed_size / 1048576
                installed_size_mib_str = \
                    f"{installed_size_mib:.2f}" + " MiB"

                download_size_mib_str = ""
                name = updated_ref.get_appdata_name()

                tree_iter = self.TreeModel.get_model().get_iter_first()
                while tree_iter:
                    real_name = self.TreeModel.get_value(tree_iter, 0)
                    arch = self.TreeModel.get_value(tree_iter, 1)
                    branch = self.TreeModel.get_value(tree_iter, 2)
                    if real_name == updated_ref_real_name and \
                       arch == updated_ref_arch and \
                       branch == updated_ref_branch:
                        GLib.idle_add(self.TreeModel.set_row,
                                      tree_iter, [updated_ref_real_name,
                                                  updated_ref_arch,
                                                  updated_ref_branch,
                                                  updated_ref_remote,
                                                  installed_size_mib_str,
                                                  download_size_mib_str,
                                                  name],
                                      priority=GLib.PRIORITY_DEFAULT)
                        time.sleep(0.2)

                        self.TreeModel.refilter()
                        time.sleep(0.3)
                    tree_iter = self.TreeModel.iter_next(tree_iter)

    def update_all_progress_callback_error(self, transaction, operation, error, details):
        ref_to_update_all = Flatpak.Ref.parse(operation.get_ref())
        ref_to_update_all_real_name = ref_to_update_all.get_name()
        operation_type = operation.get_operation_type()

        if operation_type == Flatpak.TransactionOperationType.UPDATE:
            status_text = _("Not updated: ") + ref_to_update_all_real_name
            self.StatusText = self.StatusText + "\n" + status_text
            GLib.idle_add(self.UpdateAllLabel.set_text,
                          status_text,
                          priority=GLib.PRIORITY_DEFAULT)
            GLib.idle_add(self.UpdateAllTextBuffer.set_text,
                          self.StatusText,
                          priority=GLib.PRIORITY_DEFAULT)
        elif operation_type == Flatpak.TransactionOperationType.INSTALL:
            status_text = _("Not installed: ") + ref_to_update_all_real_name
            self.StatusText = self.StatusText + "\n" + status_text
            GLib.idle_add(self.UpdateAllLabel.set_text,
                          status_text,
                          priority=GLib.PRIORITY_DEFAULT)
            GLib.idle_add(self.UpdateAllTextBuffer.set_text,
                          self.StatusText,
                          priority=GLib.PRIORITY_DEFAULT)

        return True

    def progress_bar_update(self, transaction_progress):
        GLib.idle_add(self.UpdateAllProgressBar.set_fraction,
                      float(transaction_progress.get_progress()) / 100.0,
                      priority=GLib.PRIORITY_DEFAULT)

    def cancellation_callback(self, *data):
        status_text = _("Updating canceled!")
        self.StatusText = self.StatusText + "\n" + status_text
        GLib.idle_add(self.UpdateAllLabel.set_text,
                      status_text,
                      priority=GLib.PRIORITY_DEFAULT)
        GLib.idle_add(self.UpdateAllTextBuffer.set_text,
                      self.StatusText,
                      priority=GLib.PRIORITY_DEFAULT)

    def disconnect_handlers(self, handler_id_cancel):
        self.UpdateAllCancellation.disconnect(handler_id_cancel)
        self.FlatpakTransaction.disconnect(self.handler_id)
        self.FlatpakTransaction.disconnect(self.handler_id_2)
        self.FlatpakTransaction.disconnect(self.handler_id_error)

    def on_delete_action_window(self, widget, event):
        self.UpdateAllCancellation.cancel()
        widget.hide_on_delete()
