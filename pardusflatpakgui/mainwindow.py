#!/usr/bin/env python3
#
# Pardus Flatpak GUI main window module
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

from pardusflatpakgui.infowindow import InfoWindow
from pardusflatpakgui.installwindow import InstallWindow
from pardusflatpakgui.uninstallwindow import UninstallWindow
from pardusflatpakgui.updateallwindow import UpdateAllWindow
from pardusflatpakgui.version import Version

import gettext
import locale
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


class MainWindow(object):
    def __init__(self, application):
        self.Application = application

        try:
            main_gui_file = "/usr/share/pardus/pardus-flatpak-gui/ui/mainwindow.glade"
            main_builder = Gtk.Builder.new_from_file(main_gui_file)
            main_builder.connect_signals(self)
        except GLib.GError:
            print(_("Error reading GUI file: ") + main_gui_file)
            raise

        try:
            about_gui_file = "/usr/share/pardus/pardus-flatpak-gui/ui/aboutdialog.glade"
            about_builder = Gtk.Builder.new_from_file(about_gui_file)
            about_builder.connect_signals(self)
        except GLib.GError:
            print(_("Error reading About dialog GUI file: ") + about_gui_file)
            raise

        try:
            messages_gui_file = "/usr/share/pardus/pardus-flatpak-gui/ui/messagedialogs.glade"
            messages_builder = Gtk.Builder.new_from_file(messages_gui_file)
            messages_builder.connect_signals(self)
        except GLib.GError:
            print(_("Error reading message dialogs GUI file: ") +
                  messages_gui_file)
            raise

        self.FlatpakInstallation = Flatpak.Installation.new_system()
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

        self.ListStoreMain = main_builder.get_object("ListStoreMain")

        self.MessageDialogError = messages_builder.get_object("MessageDialogError")
        self.MessageDialogError.set_title(_("Pardus Flatpak GUI Error Dialog"))

        self.MessageDialogQuestion = messages_builder.get_object("MessageDialogQuestion")
        self.MessageDialogQuestion.set_title(_("Pardus Flatpak GUI Question Dialog"))

        # Debug print()'s:
        # print("self.FlatHubRefsList:", len(self.FlatHubRefsList))
        # print("self.InstalledRefsList:", len(self.InstalledRefsList))
        # print("self.NonInstalledRefsList:", len(self.NonInstalledRefsList))
        # print("self.AllRefsList:", len(self.AllRefsList))

        for item in self.AllRefsList:
            if item.get_kind() == Flatpak.RefKind.APP and \
                    item.get_arch() == Flatpak.get_default_arch():
                if isinstance(item, Flatpak.RemoteRef):
                    item_is_installed = False
                elif isinstance(item, Flatpak.InstalledRef):
                    item_is_installed = True
                else:
                    item_is_installed = None

                real_name = item.get_name()
                arch = item.get_arch()
                branch = item.get_branch()
                installed_size = item.get_installed_size()
                installed_size_mib = installed_size / 1048576
                installed_size_mib_str = f"{installed_size_mib:.2f}" + " MiB"

                if not item_is_installed:
                    if item in self.FlatHubRefsList:
                        remote_name = "flathub"
                    else:
                        remote_name = ""
                    download_size = item.get_download_size()
                    download_size_mib = download_size / 1048576
                    download_size_mib_str = f"{download_size_mib:.2f}" + " MiB"
                    name = ""
                elif item_is_installed:
                    remote_name = item.get_origin()
                    download_size_mib_str = ""
                    name = item.get_appdata_name()
                else:
                    remote_name = ""
                    download_size_mib_str = ""
                    name = ""

                    self.MessageDialogError.set_markup(
                        _("<big><b>Invalid Flatpak Reference Error</b></big>"))
                    self.MessageDialogError.format_secondary_text(
                        _("Invalid Flatpak reference is: ") + "app/" + real_name + "/" + arch + "/" + branch)
                    self.MessageDialogError.run()
                    self.MessageDialogError.hide()

                if item_is_installed is not None:
                    self.ListStoreMain.append([real_name,
                                               arch,
                                               branch,
                                               remote_name,
                                               installed_size_mib_str,
                                               download_size_mib_str,
                                               name])
            else:
                continue

        self.HeaderBarMain = main_builder.get_object("HeaderBarMain")
        self.HeaderBarMain.set_title(_("Pardus Flatpak GUI"))
        self.HeaderBarMain.set_subtitle(_("Manage Flatpak softwares via GUI on Pardus"))

        self.RunMenuItem = main_builder.get_object("RunMenuItem")
        self.RunMenuItem.set_label(_("_Run"))

        self.InfoMenuItem = main_builder.get_object("InfoMenuItem")
        self.InfoMenuItem.set_label(_("_Info"))

        self.UninstallMenuItem = main_builder.get_object("UninstallMenuItem")
        self.UninstallMenuItem.set_label(_("_Uninstall"))

        self.InstallMenuItem = main_builder.get_object("InstallMenuItem")
        self.InstallMenuItem.set_label(_("I_nstall"))

        self.ActionsMenu = main_builder.get_object("ActionsMenu")

        self.UpdateAllMenuItem = main_builder.get_object("UpdateAllMenuItem")
        self.UpdateAllMenuItem.set_label(_("_Update All"))

        self.AboutMenuItem = main_builder.get_object("AboutMenuItem")
        self.AboutMenuItem.set_label(_("_About"))

        self.TreeViewColumnRealName = main_builder.get_object(
            "TreeViewColumnRealName")
        self.TreeViewColumnRealName.set_title(_("Real Name"))

        self.TreeViewColumnArch = main_builder.get_object("TreeViewColumnArch")
        self.TreeViewColumnArch.set_title(_("Arch"))

        self.TreeViewColumnBranch = main_builder.get_object("TreeViewColumnBranch")
        self.TreeViewColumnBranch.set_title(_("Branch"))

        self.TreeViewColumnRemoteName = main_builder.get_object(
            "TreeViewColumnRemoteName")
        self.TreeViewColumnRemoteName.set_title(_("Remote Name"))

        self.TreeViewColumnInstalledSize = main_builder.get_object(
            "TreeViewColumnInstalledSize")
        self.TreeViewColumnInstalledSize.set_title(_("Installed Size"))

        self.TreeViewColumnDownloadSize = main_builder.get_object(
            "TreeViewColumnDownloadSize")
        self.TreeViewColumnDownloadSize.set_title(_("Download Size"))

        self.TreeViewColumnName = main_builder.get_object("TreeViewColumnName")
        self.TreeViewColumnName.set_title(_("Name"))

        self.TreeViewMain = main_builder.get_object("TreeViewMain")

        self.TreeSelectionMain = main_builder.get_object("TreeSelectionMain")

        self.SearchEntryMain = main_builder.get_object("SearchEntryMain")
        self.SearchEntryMain.set_placeholder_text(_("Click here for search"))

        self.SearchFilter = main_builder.get_object("SearchFilter")
        self.SearchFilter.set_visible_func(self.search_filter_function)

        self.SortModel = main_builder.get_object("SortModel")
        self.SortModel.set_sort_func(0, self.sorting_compare_function, (self.TreeViewColumnRealName, 0))
        self.SortModel.set_sort_func(1, self.sorting_compare_function, (self.TreeViewColumnArch, 1))
        self.SortModel.set_sort_func(2, self.sorting_compare_function, (self.TreeViewColumnBranch, 2))
        self.SortModel.set_sort_func(3, self.sorting_compare_function, (self.TreeViewColumnRemoteName, 3))
        self.SortModel.set_sort_func(4, self.sorting_float_compare_function, (self.TreeViewColumnInstalledSize, 4))
        self.SortModel.set_sort_func(5, self.sorting_float_compare_function, (self.TreeViewColumnDownloadSize, 5))
        self.SortModel.set_sort_func(6, self.sorting_compare_function, (self.TreeViewColumnName, 6))

        self.HeaderBarShowButton = main_builder.get_object("HeaderBarShowButton")
        self.HeaderBarShowButton.set_label(_("Show Installed Apps"))

        self.AboutDialog = about_builder.get_object("AboutDialog")
        self.AboutDialog.set_comments(_("Flatpak GUI for Pardus"))
        self.AboutDialog.set_copyright(_("Copyright (C) 2020 Erdem Ersoy"))
        self.AboutDialog.set_program_name(_("Pardus Flatpak GUI"))
        self.AboutDialog.set_version(Version.getVersion())
        self.AboutDialog.set_website_label(_("Pardus Flatpak GUI Web Site"))

        self.MainWindow = main_builder.get_object("MainWindow")
        self.MainWindow.set_application(application)
        self.MainWindow.show()

    def search_filter_function(self, model, iteration, data):
        search_entry_text = self.SearchEntryMain.get_text()
        real_name = model[iteration][0]
        name = model[iteration][6]

        # If a reference is installed
        if model[iteration][5] == "":
            is_installed = True
        else:
            is_installed = False

        if len(search_entry_text) == 0 and not self.HeaderBarShowButton.get_active():
            return True
        if len(search_entry_text) == 0 and self.HeaderBarShowButton.get_active():
            if UpdateAllWindow.at_updating:
                return True
            else:
                return is_installed
        elif (real_name.lower().count(search_entry_text.lower()) > 0 or name.lower().count(
                search_entry_text.lower()) > 0) and not self.HeaderBarShowButton.get_active():
            return True
        elif (real_name.lower().count(search_entry_text.lower()) > 0 or name.lower().count(
                search_entry_text.lower()) > 0) and self.HeaderBarShowButton.get_active():
            if UpdateAllWindow.at_updating:
                return True
            else:
                return is_installed
        else:
            return False

    def sorting_compare_function(self, tree_model_filter, row1, row2, data):
        sorting_column, id_number = data
        value1 = tree_model_filter.get_value(row1, id_number)
        value2 = tree_model_filter.get_value(row2, id_number)

        if value1 == "" and value2 == "":
            return 0
        elif value1 == "" and value2 != "":
            return -1
        elif value1 != "" and value2 == "":
            return 1

        if value1 < value2:
            return -1
        elif value1 == value2:
            return 0
        else:
            return 1

    def sorting_float_compare_function(self, tree_model_filter, row1, row2, data):
        sorting_column, id_number = data
        value1 = tree_model_filter.get_value(row1, id_number)[:-4]
        value2 = tree_model_filter.get_value(row2, id_number)[:-4]

        if value1 == "" and value2 == "":
            return 0
        elif value1 == "" and value2 != "":
            return -1
        elif value1 != "" and value2 == "":
            return 1

        value1_float = float(value1)
        value2_float = float(value2)

        if value1_float < value2_float:
            return -1
        elif value1_float == value2_float:
            return 0
        else:
            return 1

    def on_delete_main_window(self, widget, event):
        widget.hide_on_delete()

    def on_columns_changed(self, tree_view):  # FIXME: Remove
        selection = tree_view.get_selection()
        tree_model, tree_iter = selection.get_selected()
        if tree_iter is None:
            return None

        # If the selected app is installed
        if tree_model.get_value(tree_iter, 5) == "":
            self.RunMenuItem.set_sensitive(True)
            self.UninstallMenuItem.set_sensitive(True)
            self.InstallMenuItem.set_sensitive(False)

        # If the selected app is not installed
        else:
            self.RunMenuItem.set_sensitive(False)
            self.UninstallMenuItem.set_sensitive(False)
            self.InstallMenuItem.set_sensitive(True)

    def on_selection_changed(self, tree_selection):
        tree_model, tree_iter = tree_selection.get_selected()
        if tree_iter is None:
            return None

        # If the selected app is installed
        if tree_model.get_value(tree_iter, 5) == "":
            self.RunMenuItem.set_sensitive(True)
            self.UninstallMenuItem.set_sensitive(True)
            self.InstallMenuItem.set_sensitive(False)

        # If the selected app is not installed
        else:
            self.RunMenuItem.set_sensitive(False)
            self.UninstallMenuItem.set_sensitive(False)
            self.InstallMenuItem.set_sensitive(True)

    def on_search_changed(self, search_entry):
        self.SearchFilter.refilter()

    def on_resorted(self, tree_sortable):
        self.SearchFilter.refilter()

    def on_press_show_button(self, toggle_button):
        self.SearchFilter.refilter()

    def on_show_actions_menu(self, widget, event):
        if event.button == 3:  # 3 == Right mouse button
            x = event.x
            y = event.y
            path_info = self.TreeViewMain.get_path_at_pos(x, y)
            if path_info != None:
                path = path_info[0]
                self.TreeSelectionMain.select_path(path)
                self.ActionsMenu.popup_at_pointer(None)
            else:
                pass

    def on_run(self, menu_item):
        selection = self.TreeViewMain.get_selection()
        tree_model, tree_iter = selection.get_selected()
        if tree_iter is None:
            self.MessageDialogError.set_markup(
                _("<big><b>Selection Error</b></big>"))
            self.MessageDialogError.format_secondary_text(
                _("None of the applications are selected."))
            self.MessageDialogError.run()
            self.MessageDialogError.hide()
            return None

        real_name = tree_model.get_value(tree_iter, 0)
        arch = tree_model.get_value(tree_iter, 1)
        branch = tree_model.get_value(tree_iter, 2)

        ref = Flatpak.Ref.parse("app/" + real_name + "/" +
                                arch + "/" + branch)

        commit = ref.get_commit()

        try:
            success = self.FlatpakInstallation.launch(
                real_name,
                arch,
                branch,
                commit,
                Gio.Cancellable.new())
        except GLib.Error:
            self.MessageDialogError.set_markup(
                _("<big><b>Running Error</b></big>"))
            self.MessageDialogError.format_secondary_text(
                _("The selected application couldn't run."))
            self.MessageDialogError.run()
            self.MessageDialogError.hide()
        else:
            if success:
                pass
            else:
                self.MessageDialogError.set_markup(
                    _("<big><b>Running Error</b></big>"))
                self.MessageDialogError.format_secondary_text(
                    _("The selected application couldn't run."))
                self.MessageDialogError.run()
                self.MessageDialogError.hide()

    def on_info(self, menu_item):
        selection = self.TreeViewMain.get_selection()
        tree_model, tree_iter = selection.get_selected()
        if tree_iter is None:
            self.MessageDialogError.set_markup(
                _("<big><b>Selection Error</b></big>"))
            self.MessageDialogError.format_secondary_text(
                _("None of the applications are selected."))
            self.MessageDialogError.run()
            self.MessageDialogError.hide()
            return None

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

        real_name = tree_model.get_value(tree_iter, 0)
        arch = tree_model.get_value(tree_iter, 1)
        branch = tree_model.get_value(tree_iter, 2)

        for item in self.AllRefsList:
            if item.get_name() == real_name:
                ref = item
                break

        if ref not in self.AllRefsList:
            self.MessageDialogError.set_markup(
                _("<big><b>Invalid Flatpak Reference Error</b></big>"))
            self.MessageDialogError.format_secondary_text(
                _("Invalid Flatpak reference is: ") + "app/" + real_name + "/" + arch + "/" + branch)
            self.MessageDialogError.run()
            self.MessageDialogError.hide()
            return None

        collection_id = ref.get_collection_id()
        if collection_id is None:
            collection_id = _("None")
        commit = ref.get_commit()

        if isinstance(ref, Flatpak.RemoteRef):
            is_installed = False
        elif isinstance(ref, Flatpak.InstalledRef):
            is_installed = True
        else:
            is_installed = None

        if is_installed:
            app_license = ref.get_appdata_license()
            if app_license is None:
                app_license = _("None")

            name = ref.get_appdata_name()
            if name is None:
                name = _("None")

            summary = ref.get_appdata_summary()
            if summary is None:
                summary = _("None")

            version = ref.get_appdata_version()
            if version is None:
                version = _("None")

            deploy_dir = ref.get_deploy_dir()
            if deploy_dir is None:
                deploy_dir = _("None")

            eol_reason = ref.get_eol()
            if eol_reason is None:
                eol_reason = _("None")

            eol_rebased = ref.get_eol_rebase()
            if eol_rebased is None:
                eol_rebased = _("None")

            installed_size = ref.get_installed_size()
            installed_size_mib = installed_size / 1048576
            installed_size_mib_as_string = f"{installed_size_mib:.2f}" + " MiB"

            is_current = ref.get_is_current()
            if is_current:
                is_current_str = _("Yes")
            else:
                is_current_str = _("No")

            latest_commit = ref.get_latest_commit()
            if latest_commit is None:
                latest_commit = _("None")

            origin = ref.get_origin()
            if origin is None:
                origin = _("None")

            sub_paths = ref.get_subpaths()
            if sub_paths is None or not sub_paths:
                sub_paths_str = _("None")
            else:
                sub_paths_str = ""
                for item in sub_paths:
                    sub_paths_str = sub_paths_str + item + ", "
                    sub_paths_str = sub_paths_str[:-2]

            info_str = _("Real Name: ") + real_name + "\n" + \
                       _("Arch: ") + arch + "\n" + \
                       _("Branch: ") + branch + "\n" + \
                       _("Collection ID: ") + collection_id + "\n" + \
                       _("Commit: ") + commit + "\n" + \
                       _("Is Installed: ") + _("Yes") + "\n" + \
                       _("License: ") + app_license + "\n" + \
                       _("Name: ") + name + "\n" + \
                       _("Summary: ") + summary + "\n" + \
                       _("Version: ") + version + "\n" + \
                       _("Deploy Dir: ") + deploy_dir + "\n" + \
                       _("EOL Reason: ") + eol_reason + "\n" + \
                       _("EOL Rebased: ") + eol_rebased + "\n" + \
                       _("Installed Size: ") + installed_size_mib_as_string + "\n" + \
                       _("Is Current: ") + is_current_str + "\n" + \
                       _("Latest Commit: ") + latest_commit + "\n" + \
                       _("Origin: ") + origin + "\n" + \
                       _("Subpaths: ") + sub_paths_str + "\n"

        elif not is_installed:
            download_size = ref.get_download_size()
            download_size_mib = download_size / 1048576
            download_size_mib_str = f"{download_size_mib:.2f}" + " MiB"

            eol_reason = ref.get_eol()
            if eol_reason is None:
                eol_reason = _("None")

            eol_rebased = ref.get_eol_rebase()
            if eol_rebased is None:
                eol_rebased = _("None")

            installed_size = ref.get_installed_size()
            installed_size_mib = installed_size / 1048576
            installed_size_mib_as_string = f"{installed_size_mib:.2f}" + " MiB"

            remote = ref.get_remote_name()
            if remote is None:
                remote = _("None")

            info_str = _("Real Name: ") + real_name + "\n" + \
                _("Arch: ") + arch + "\n" + \
                _("Branch: ") + branch + "\n" + \
                _("Collection ID: ") + collection_id + "\n" + \
                _("Commit: ") + commit + "\n" + \
                _("Is Installed: ") + _("Yes") + "\n" + \
                _("Download Size: ") + download_size_mib_str + "\n" + \
                _("EOL Reason: ") + eol_reason + "\n" + \
                _("EOL Rebased: ") + eol_rebased + "\n" + \
                _("Installed Size: ") + installed_size_mib_as_string + "\n" + \
                _("Remote Name: ") + remote + "\n"
        else:
            self.MessageDialogError.set_markup(
                _("<big><b>Invalid Flatpak Reference Error</b></big>"))
            self.MessageDialogError.format_secondary_text(
                _("Invalid Flatpak reference is: ") + "app/" + real_name + "/" + arch + "/" + branch)
            self.MessageDialogError.run()
            self.MessageDialogError.hide()
            return None

        InfoWindow(self.Application, info_str, ref)

    def on_uninstall(self, menu_item):
        if not self.HeaderBarShowButton.get_active():
            button_not_pressed_already = True
        elif self.HeaderBarShowButton.get_active():
            button_not_pressed_already = False
            self.HeaderBarShowButton.set_active(False)
            self.SearchFilter.refilter()

        selection = self.TreeViewMain.get_selection()
        tree_model, tree_iter = selection.get_selected()
        if tree_iter is None:
            self.MessageDialogError.set_markup(
                _("<big><b>Selection Error</b></big>"))
            self.MessageDialogError.format_secondary_text(
                _("None of the applications are selected."))
            self.MessageDialogError.run()
            self.MessageDialogError.hide()
            return None

        real_name = tree_model.get_value(tree_iter, 0)
        arch = tree_model.get_value(tree_iter, 1)
        branch = tree_model.get_value(tree_iter, 2)
        name = tree_model.get_value(tree_iter, 6)

        self.MessageDialogQuestion.set_markup(
            _("<big><b>Uninstalling ") + name + "(" + real_name + ")" + "</b></big>")
        self.MessageDialogQuestion.format_secondary_text(
            _("Are you sure to uninstall ") + name + "?")
        answer = self.MessageDialogQuestion.run()
        self.MessageDialogQuestion.hide()

        if answer == Gtk.ResponseType.YES:
            UninstallWindow(self.Application, self.FlatpakInstallation, real_name,
                            arch, branch, tree_model, tree_iter, selection, self.SearchFilter, self.HeaderBarShowButton,
                            button_not_pressed_already)
        elif answer == Gtk.ResponseType.NO:
            return None

    def on_install(self, menu_item):
        selection = self.TreeViewMain.get_selection()
        tree_model, tree_iter = selection.get_selected()
        if tree_iter is None:
            self.MessageDialogError.set_markup(
                _("<big><b>Selection Error</b></big>"))
            self.MessageDialogError.format_secondary_text(
                _("None of the applications are selected."))
            self.MessageDialogError.run()
            self.MessageDialogError.hide()
            return None

        real_name = tree_model.get_value(tree_iter, 0)
        arch = tree_model.get_value(tree_iter, 1)
        branch = tree_model.get_value(tree_iter, 2)
        remote = tree_model.get_value(tree_iter, 3)

        self.MessageDialogQuestion.set_markup(
            _("<big><b>Installing ") + real_name + "</b></big>")
        self.MessageDialogQuestion.format_secondary_text(
            _("Are you sure to install ") + real_name + "?")
        answer = self.MessageDialogQuestion.run()
        self.MessageDialogQuestion.hide()

        if answer == Gtk.ResponseType.YES:
            InstallWindow(self.Application, self.FlatpakInstallation, real_name, arch, branch,
                          remote, tree_model, tree_iter, selection, self.SearchFilter)
        elif answer == Gtk.ResponseType.NO:
            return None

    def on_update_all(self, menu_item):
        UpdateAllWindow.at_updating = True
        tree_model = self.TreeViewMain.get_model()
        UpdateAllWindow(self.Application, self.FlatpakInstallation,
                        tree_model, self.HeaderBarShowButton)

    def on_about(self, menu_item):
        self.AboutDialog.run()
        self.AboutDialog.hide()
