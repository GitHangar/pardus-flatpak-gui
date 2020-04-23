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
    def __init__(self, application, flatpak_installation, search_filter):
        self.Application = application

        self.FlatpakInstallation = flatpak_installation
        self.RefsToUpdate = flatpak_installation.list_installed_refs_for_update(Gio.Cancellable.new())
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
            self.FlatpakTransaction.add_update(
                ref_to_update,
                None,
                None)

        self.SearchFilter = search_filter

        try:
            update_all_gui_file = "ui/actionwindow.glade"
            update_all_builder = Gtk.Builder.new_from_file(update_all_gui_file)
            update_all_builder.connect_signals(self)
        except GLib.GError:
            print(_("Error reading GUI file: ") + update_all_gui_file)
            raise

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
            self.update_all_progress_callback_disconnect)
        self.handler_id_error = self.FlatpakTransaction.connect(
            "operation-error",
            self.update_all_progress_callback_error)

        self.UpdateAllThread = threading.Thread(
                           target=self.update_all,
                           args=())
        self.UpdateAllThread.start()
        GLib.threads_init()

    def update_all(self):
        try:
            self.FlatpakTransaction.run(Gio.Cancellable.new())
        except GLib.Error:
            status_text = _("Error at updating!")
            self.StatusText = self.StatusText + "\n" + status_text
            GLib.idle_add(self.UpdateAllLabel.set_text,
                          status_text,
                          priority=GLib.PRIORITY_DEFAULT)
            GLib.idle_add(self.UpdateAllTextBuffer.set_text,
                          self.StatusText,
                          priority=GLib.PRIORITY_DEFAULT)
        else:
            status_text = _("Installing completed!")
            self.StatusText = self.StatusText + "\n" + status_text
            GLib.idle_add(self.UpdateAllLabel.set_text,
                          status_text,
                          priority=GLib.PRIORITY_DEFAULT)
            GLib.idle_add(self.UpdateAllTextBuffer.set_text,
                          self.StatusText,
                          priority=GLib.PRIORITY_DEFAULT)
        self.FlatpakTransaction.disconnect(self.handler_id)
        self.FlatpakTransaction.disconnect(self.handler_id_2)
        self.FlatpakTransaction.disconnect(self.handler_id_error)
        time.sleep(0.5)

    def update_all_progress_callback(self, transaction, operation, progress):
        ref_to_update = Flatpak.Ref.parse(operation.get_ref())
        ref_to_update_real_name = ref_to_update.get_name()

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

    def update_all_progress_callback_disconnect(self, transaction, operation, commit, result):
        self.TransactionProgress.disconnect(self.handler_id_progress)

    def update_all_progress_callback_error(self, transaction, operation, error, details):
        ref_to_update_all = Flatpak.Ref.parse(operation.get_ref())
        ref_to_update_all_real_name = ref_to_update_all.get_name()

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

    def on_delete_action_window(self, widget, event):
        widget.hide_on_delete()
