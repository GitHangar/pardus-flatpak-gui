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


class InstallFromFileWindow(object):
    def __init__(self, application, file_contents_glib_bytes):
        self.Application = application
        self.FileFlatpakRefContentsGLibBytes = file_contents_glib_bytes

        self.FlatpakInstallation = Flatpak.Installation.new_system(Gio.Cancellable.new())
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
            file_contents_glib_bytes)

        self.handler_id = self.FlatpakTransaction.connect(
            "new-operation",
            self.install_progress_callback)
        self.handler_id_2 = self.FlatpakTransaction.connect(
            "operation-done",
            self.install_progress_callback_disconnect)
        self.handler_id_error = self.FlatpakTransaction.connect(
            "operation-error",
            self.install_progress_callback_error)

        try:
            install_from_file_gui_file = "ui/actionwindow.glade"
            install_from_file_builder = Gtk.Builder.new_from_file(
                                         install_from_file_gui_file)
            install_from_file_builder.connect_signals(self)
        except GLib.GError:
            print(_("Error reading GUI file: ") + install_from_file_gui_file)
            raise

        self.InstallFromFileWindow = install_from_file_builder.get_object(
                                         "ActionWindow")
        self.InstallFromFileWindow.set_application(application)
        self.InstallFromFileWindow.set_title(_("Installing from file..."))
        self.InstallFromFileWindow.show()

        self.InstallFromFileProgressBar = install_from_file_builder.get_object(
                                              "ActionProgressBar")
        self.ProgressBarValue = int(
            self.InstallFromFileProgressBar.get_fraction() * 100)

        self.InstallFromFileLabel = install_from_file_builder.get_object(
                                        "ActionLabel")
        self.InstallFromFileTextBuffer = install_from_file_builder.get_object(
                                             "ActionTextBuffer")

        self.InstallFromFileTextBuffer.set_text("\0", -1)
        self.StatusText = _("Installing from file...")
        self.InstallFromFileLabel.set_text(self.StatusText)
        self.InstallFromFileTextBuffer.set_text(self.StatusText)

        self.InstallFromFileThread = threading.Thread(
                                         target=self.install_from_file,
                                         args=())
        self.InstallFromFileThread.start()
        GLib.threads_init()

    def install_from_file(self):
        try:
            self.FlatpakTransaction.run(Gio.Cancellable.new())
        except GLib.Error:
            status_text = _("Error at installation!")
            self.StatusText = self.StatusText + "\n" + status_text
            GLib.idle_add(self.InstallFromFileLabel.set_text,
                          status_text,
                          priority=GLib.PRIORITY_DEFAULT)
            GLib.idle_add(self.InstallFromFileTextBuffer.set_text,
                          self.StatusText,
                          priority=GLib.PRIORITY_DEFAULT)
        else:
            status_text = _("Installing completed!")
            self.StatusText = self.StatusText + "\n" + status_text
            GLib.idle_add(self.InstallFromFileLabel.set_text,
                          status_text,
                          priority=GLib.PRIORITY_DEFAULT)
            GLib.idle_add(self.InstallFromFileTextBuffer.set_text,
                          self.StatusText,
                          priority=GLib.PRIORITY_DEFAULT)
        self.FlatpakTransaction.disconnect(self.handler_id)
        self.FlatpakTransaction.disconnect(self.handler_id_2)
        self.FlatpakTransaction.disconnect(self.handler_id_error)
        time.sleep(0.5)

    def install_progress_callback(self, transaction, operation, progress):
        ref_to_install = Flatpak.Ref.parse(operation.get_ref())
        ref_to_install_real_name = ref_to_install.get_name()

        status_text = _("Installing: ") + ref_to_install_real_name
        self.StatusText = self.StatusText + "\n" + status_text
        GLib.idle_add(self.InstallFromFileLabel.set_text,
                      status_text,
                      priority=GLib.PRIORITY_DEFAULT)
        GLib.idle_add(self.InstallFromFileTextBuffer.set_text,
                      self.StatusText,
                      priority=GLib.PRIORITY_DEFAULT)

        self.TransactionProgress = progress  # FIXME: Fix PyCharm warning
        self.TransactionProgress.set_update_frequency(200)
        self.handler_id_progress = self.TransactionProgress.connect(
            "changed",
            self.progress_bar_update)  # FIXME: Fix PyCharm warning

    def install_progress_callback_disconnect(self, transaction, operation, commit, result):
        self.TransactionProgress.disconnect(self.handler_id_progress)

    def install_progress_callback_error(self, transaction, operation, error, details):
        ref_to_install = Flatpak.Ref.parse(operation.get_ref())
        ref_to_install_real_name = ref_to_install.get_name()

        status_text = _("Not installed: ") + ref_to_install_real_name
        self.StatusText = self.StatusText + "\n" + status_text
        GLib.idle_add(self.InstallFromFileLabel.set_text,
                      status_text,
                      priority=GLib.PRIORITY_DEFAULT)
        GLib.idle_add(self.InstallFromFileTextBuffer.set_text,
                      self.StatusText,
                      priority=GLib.PRIORITY_DEFAULT)

        return False

    def progress_bar_update(self, transaction_progress):
        GLib.idle_add(self.InstallFromFileProgressBar.set_fraction,
                      float(transaction_progress.get_progress()) / 100.0,
                      priority=GLib.PRIORITY_DEFAULT)

    def on_delete_action_window(self, widget, event):
        widget.hide_on_delete()
