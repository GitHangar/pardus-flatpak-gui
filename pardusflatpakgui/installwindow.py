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
gettext.bindtextdomain("flatpak-gui", "/usr/share/locale/")
gettext.textdomain("flatpak-gui")
_ = gettext.gettext
gettext.install("flatpak-gui", "/usr/share/locale/")


class InstallWindow(object):
    def __init__(self, application, flatpak_installation, real_name, arch,
                 branch, remote, tree_model, tree_iter, selection, search_filter):
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

        self.TreeModel = tree_model
        self.TreeIter = tree_iter
        self.Selection = selection
        self.SearchFilter = search_filter

        self.handler_id = self.FlatpakTransaction.connect(
            "new-operation",
            self.install_progress_callback)
        self.handler_id_2 = self.FlatpakTransaction.connect(
            "operation-done",
            self.install_progress_callback_done)
        self.handler_id_error = self.FlatpakTransaction.connect(
            "operation-error",
            self.install_progress_callback_error)

        try:
            install_gui_file = "/usr/share/pardus/pardus-flatpak-gui/ui/actionwindow.glade"
            install_builder = Gtk.Builder.new_from_file(install_gui_file)
            install_builder.connect_signals(self)
        except GLib.GError:
            print(_("Error reading GUI file: ") + install_gui_file)
            raise

        self.InstallCancellation = Gio.Cancellable.new()

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
        GLib.idle_add(self.Selection.unselect_all,
                      data=None,
                      priority=GLib.PRIORITY_DEFAULT)
        time.sleep(0.2)

        handler_id_cancel = self.InstallCancellation.connect(self.cancellation_callback, None)
        try:
            self.FlatpakTransaction.run(self.InstallCancellation)
        except GLib.Error:
            status_text = _("Error at installation!")
            self.StatusText = self.StatusText + "\n" + status_text
            GLib.idle_add(self.InstallLabel.set_text,
                          status_text,
                          priority=GLib.PRIORITY_DEFAULT)
            GLib.idle_add(self.InstallTextBuffer.set_text,
                          self.StatusText,
                          priority=GLib.PRIORITY_DEFAULT)
            self.disconnect_handlers(handler_id_cancel)
            return None
        else:
            status_text = _("Installing completed!")
            self.StatusText = self.StatusText + "\n" + status_text
            GLib.idle_add(self.InstallLabel.set_text,
                          status_text,
                          priority=GLib.PRIORITY_DEFAULT)
            GLib.idle_add(self.InstallTextBuffer.set_text,
                          self.StatusText,
                          priority=GLib.PRIORITY_DEFAULT)
        self.disconnect_handlers(handler_id_cancel)

    def install_progress_callback(self, transaction, operation, progress):
        ref_to_install = Flatpak.Ref.parse(operation.get_ref())
        ref_to_install_real_name = ref_to_install.get_name()

        status_text = _("Installing: ") + ref_to_install_real_name
        self.StatusText = self.StatusText + "\n" + status_text
        GLib.idle_add(self.InstallLabel.set_text,
                      status_text,
                      priority=GLib.PRIORITY_DEFAULT)
        GLib.idle_add(self.InstallTextBuffer.set_text,
                      self.StatusText,
                      priority=GLib.PRIORITY_DEFAULT)

        self.TransactionProgress = progress  # FIXME: Fix PyCharm warning
        self.TransactionProgress.set_update_frequency(200)
        self.handler_id_progress = self.TransactionProgress.connect(
                                      "changed",
                                      self.progress_bar_update)  # FIXME: Fix PyCharm warning

    def install_progress_callback_done(self, transaction, operation, commit, result):
        self.TransactionProgress.disconnect(self.handler_id_progress)

        operation_ref = Flatpak.Ref.parse(operation.get_ref())
        operation_ref_real_name = operation_ref.get_name()
        operation_ref_arch = operation_ref.get_arch()
        operation_ref_branch = operation_ref.get_branch()
        for installed_ref in self.FlatpakInstallation.list_installed_refs():
            if installed_ref.get_name() == operation_ref_real_name and \
               installed_ref.get_arch() == operation_ref_arch and \
               installed_ref.get_branch() == operation_ref_branch and \
               installed_ref.get_kind() == Flatpak.RefKind.APP:
                installed_ref_real_name = installed_ref.get_name()
                installed_ref_arch = installed_ref.get_arch()
                installed_ref_branch = installed_ref.get_branch()
                installed_ref_remote = "FlatHub"

                installed_size = installed_ref.get_installed_size()
                installed_size_mib = installed_size / 1048576
                installed_size_mib_str = \
                    f"{installed_size_mib:.2f}" + " MiB"

                download_size_mib_str = ""
                name = installed_ref.get_appdata_name()

                tree_model = self.TreeModel.get_model()
                tree_iter = tree_model.get_iter_first()
                while tree_iter:
                    real_name = tree_model.get_value(tree_iter, 0)
                    arch = tree_model.get_value(tree_iter, 1)
                    branch = tree_model.get_value(tree_iter, 2)
                    if real_name == installed_ref_real_name and \
                       arch == installed_ref_arch and \
                       branch == installed_ref_branch:
                        GLib.idle_add(tree_model.set_row,
                                      tree_iter, [installed_ref_real_name,
                                                  installed_ref_arch,
                                                  installed_ref_branch,
                                                  installed_ref_remote,
                                                  installed_size_mib_str,
                                                  download_size_mib_str,
                                                  name],
                                      priority=GLib.PRIORITY_DEFAULT)
                        time.sleep(0.2)

                        tree_model.refilter()
                        time.sleep(0.3)
                    tree_iter = tree_model.iter_next(tree_iter)

    def install_progress_callback_error(self, transaction, operation, error, details):
        ref_to_install = Flatpak.Ref.parse(operation.get_ref())
        ref_to_install_real_name = ref_to_install.get_name()

        status_text = _("Not installed: ") + ref_to_install_real_name
        self.StatusText = self.StatusText + "\n" + status_text
        GLib.idle_add(self.InstallLabel.set_text,
                      status_text,
                      priority=GLib.PRIORITY_DEFAULT)
        GLib.idle_add(self.InstallTextBuffer.set_text,
                      self.StatusText,
                      priority=GLib.PRIORITY_DEFAULT)

        if ref_to_install_real_name != self.RealName:
            return True
        else:
            return False

    def progress_bar_update(self, transaction_progress):
        GLib.idle_add(self.InstallProgressBar.set_fraction,
                      float(transaction_progress.get_progress()) / 100.0,
                      priority=GLib.PRIORITY_DEFAULT)

    def cancellation_callback(self, *data):
        status_text = _("Installing canceled!")
        self.StatusText = self.StatusText + "\n" + status_text
        GLib.idle_add(self.InstallLabel.set_text,
                      status_text,
                      priority=GLib.PRIORITY_DEFAULT)
        GLib.idle_add(self.InstallTextBuffer.set_text,
                      self.StatusText,
                      priority=GLib.PRIORITY_DEFAULT)

    def disconnect_handlers(self, handler_id_cancel):
        self.InstallCancellation.disconnect(handler_id_cancel)
        self.FlatpakTransaction.disconnect(self.handler_id)
        self.FlatpakTransaction.disconnect(self.handler_id_2)
        self.FlatpakTransaction.disconnect(self.handler_id_error)

    def on_delete_action_window(self, widget, event):
        self.InstallCancellation.cancel()
        widget.hide_on_delete()
