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
from pardusflatpakgui.installfromentrywindow import InstallFromEntryWindow
from pardusflatpakgui.installfromfilewindow import InstallFromFileWindow
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
gettext.bindtextdomain("pardus-flatpak-gui", "po/")
gettext.textdomain("pardus-flatpak-gui")
_ = gettext.gettext
gettext.install("pardus-flatpak-gui", "po/")


class MainWindow(object):
    def __init__(self, application):
        self.Application = application
        self.url = "https://dl.flathub.org/repo/appstream/"
        self.urlext = "flatpakref"

        try:
            MainGUIFile = "ui/mainwindow.glade"
            MainBuilder = Gtk.Builder.new_from_file(MainGUIFile)
            MainBuilder.connect_signals(self)
        except GLib.GError:
            print(_("Error reading GUI file: ") + MainGUIFile)
            raise

        try:
            AboutGUIFile = "ui/aboutdialog.glade"
            AboutBuilder = Gtk.Builder.new_from_file(AboutGUIFile)
            AboutBuilder.connect_signals(self)
        except GLib.GError:
            print(_("Error reading About dialog GUI file: ") + AboutGUIFile)
            raise

        try:
            MessagesGUIFile = "ui/messagedialogs.glade"
            MessagesBuilder = Gtk.Builder.new_from_file(MessagesGUIFile)
            MessagesBuilder.connect_signals(self)
        except GLib.GError:
            print(_("Error reading message dialogs GUI file: ") +
                  MessagesGUIFile)
            raise

        self.MainWindow = MainBuilder.get_object("MainWindow")
        self.MainWindow.set_application(application)

        self.HeaderBarMain = MainBuilder.get_object("HeaderBarMain")
        self.HeaderBarMain.set_title(_("Pardus Flatpak GUI"))
        self.HeaderBarMain.set_subtitle(_("Manage Flatpak softwares via GUI on Pardus"))

        self.RunMenuItem = MainBuilder.get_object("RunMenuItem")
        self.RunMenuItem.set_label(_("_Run"))

        self.InfoMenuItem = MainBuilder.get_object("InfoMenuItem")
        self.InfoMenuItem.set_label(_("_Info"))

        self.UninstallMenuItem = MainBuilder.get_object("UninstallMenuItem")
        self.UninstallMenuItem.set_label(_("_Uninstall"))

        self.InstallMenuItem = MainBuilder.get_object("InstallMenuItem")
        self.InstallMenuItem.set_label(_("I_nstall"))

        self.InstallFromEntryMenuItem = MainBuilder.get_object("InstallFromEntryMenuItem")
        self.InstallFromEntryMenuItem.set_label(_("Install From _Entry"))

        self.InstallFromFileMenuItem = MainBuilder.get_object(
                                           "InstallFromFileMenuItem")
        self.InstallFromFileMenuItem.set_label(_("Install _From File"))

        self.UpdateAllMenuItem = MainBuilder.get_object("UpdateAllMenuItem")
        self.UpdateAllMenuItem.set_label(_("Up_date All"))

        self.AboutMenuItem = MainBuilder.get_object("AboutMenuItem")
        self.AboutMenuItem.set_label(_("_About"))

        self.TreeViewColumnRealName = MainBuilder.get_object(
                                          "TreeViewColumnRealName")
        self.TreeViewColumnRealName.set_title(_("Real Name"))

        self.TreeViewColumnArch = MainBuilder.get_object("TreeViewColumnArch")
        self.TreeViewColumnArch.set_title(_("Arch"))

        self.TreeViewColumnBranch = MainBuilder.get_object("TreeViewColumnBranch")
        self.TreeViewColumnBranch.set_title(_("Branch"))

        self.TreeViewColumnRemoteName = MainBuilder.get_object(
                                            "TreeViewColumnRemoteName")
        self.TreeViewColumnRemoteName.set_title(_("Remote Name"))

        self.TreeViewColumnInstalledSize = MainBuilder.get_object(
                                               "TreeViewColumnInstalledSize")
        self.TreeViewColumnInstalledSize.set_title(_("Installed Size"))

        self.TreeViewColumnDownloadSize = MainBuilder.get_object(
                                               "TreeViewColumnDownloadSize")
        self.TreeViewColumnDownloadSize.set_title(_("Download Size"))

        self.TreeViewColumnName = MainBuilder.get_object("TreeViewColumnName")
        self.TreeViewColumnName.set_title(_("Name"))

        self.SortModel = MainBuilder.get_object("SortModel")
        self.SortModel.set_sort_func(0, self.SortingCompareFunction, (self.TreeViewColumnRealName, 0))
        self.SortModel.set_sort_func(1, self.SortingCompareFunction, (self.TreeViewColumnArch, 1))
        self.SortModel.set_sort_func(2, self.SortingCompareFunction, (self.TreeViewColumnBranch, 2))
        self.SortModel.set_sort_func(3, self.SortingCompareFunction, (self.TreeViewColumnRemoteName, 3))
        self.SortModel.set_sort_func(4, self.SortingFloatCompareFunction, (self.TreeViewColumnInstalledSize, 4))
        self.SortModel.set_sort_func(5, self.SortingFloatCompareFunction, (self.TreeViewColumnDownloadSize, 5))
        self.SortModel.set_sort_func(6, self.SortingCompareFunction, (self.TreeViewColumnName, 6))

        self.FlatpakInstallation = Flatpak.Installation.new_system()
        self.FlatpakRefsList = self.FlatpakInstallation.list_installed_refs()
        self.FlatHubRefsList = self.FlatpakInstallation.list_remote_refs_sync(
                                   "flathub", Gio.Cancellable.new())

        for item in self.FlatpakRefsList:
            for item2 in self.FlatHubRefsList:
                if item.get_name() == item2.get_name():
                    self.FlatHubRefsList.remove(item2)
        self.FlatpakRefsList = self.FlatpakRefsList + self.FlatHubRefsList

        self.ListStoreMain = MainBuilder.get_object("ListStoreMain")

        for item in self.FlatpakRefsList:
            if item.get_kind() == Flatpak.RefKind.APP and \
              item.get_arch() == Flatpak.get_default_arch():
                isremoteref = isinstance(item, Flatpak.RemoteRef)
                isinstalledref = isinstance(item, Flatpak.InstalledRef)

                RealName = item.get_name()
                Arch = item.get_arch()
                Branch = item.get_branch()
                InstalledSize = item.get_installed_size()
                InstalledSizeMiB = InstalledSize / 1048576
                InstalledSizeMiBAsString = f"{InstalledSizeMiB:.2f}" + " MiB"

                if isremoteref:
                    if item in self.FlatHubRefsList:
                        RemoteName = "flathub"
                    else:
                        RemoteName = ""
                    DownloadSize = item.get_download_size()
                    DownloadSizeMiB = DownloadSize / 1048576
                    DownloadSizeMiBAsString = f"{DownloadSizeMiB:.2f}" + " MiB"
                    Name = ""
                elif isinstalledref:
                    RemoteName = item.get_origin()
                    DownloadSizeMiBAsString = ""
                    Name = item.get_appdata_name()

                self.ListStoreMain.append([RealName,
                                          Arch,
                                          Branch,
                                          RemoteName,
                                          InstalledSizeMiBAsString,
                                          DownloadSizeMiBAsString,
                                          Name])
            else:
                continue

        self.TreeViewMain = MainBuilder.get_object("TreeViewMain")

        self.SearchEntryMain = MainBuilder.get_object("SearchEntryMain")

        self.SearchFilter = MainBuilder.get_object("SearchFilter")
        self.SearchFilter.set_visible_func(self.SearchFilterFunction)

        self.HeaderBarShowButton = MainBuilder.get_object("HeaderBarShowButton")
        self.HeaderBarShowButton.set_label(_("Show Installed Apps"))

        self.AboutDialog = AboutBuilder.get_object("AboutDialog")
        self.AboutDialog.set_comments(_("Flatpak GUI for Pardus"))
        self.AboutDialog.set_copyright(_("Copyright (C) 2020 Erdem Ersoy"))
        self.AboutDialog.set_program_name(_("Pardus Flatpak GUI"))
        self.AboutDialog.set_version(Version.getVersion())
        self.AboutDialog.set_website_label(_("Pardus Flatpak GUI Web Site"))

        self.MessageDialogError = MessagesBuilder.get_object(
            "MessageDialogError")

        self.MainWindow.show()

    def SearchFilterFunction(self, model, iteration, data):
        search_entry_text = self.SearchEntryMain.get_text()
        real_name = model[iteration][0]
        name = model[iteration][6]

        if name == "":
            is_installed = False
        else:
            is_installed = True

        if len(search_entry_text) == 0 and not self.HeaderBarShowButton.get_active():
            return True
        if len(search_entry_text) == 0 and self.HeaderBarShowButton.get_active():
            return is_installed
        elif (real_name.lower().count(search_entry_text.lower()) > 0 or name.lower().count(search_entry_text.lower()) > 0) \
          and not self.HeaderBarShowButton.get_active():
            return True
        elif (real_name.lower().count(search_entry_text.lower()) > 0 or name.lower().count(search_entry_text.lower()) > 0) \
          and self.HeaderBarShowButton.get_active():
            return is_installed
        else:
            return False

    def SortingCompareFunction(self, tree_model_filter, row1, row2, data):
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

    def SortingFloatCompareFunction(self, tree_model_filter, row1, row2, data):
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

    def onDestroy(self, *args):
        self.MainWindow.destroy()

    def onSelectionChanged(self, treeselection):
        Selection = self.TreeViewMain.get_selection()
        TreeModel, TreeIter = Selection.get_selected()
        if TreeIter is None:
            return None

        # If the selected app is installed
        if TreeModel.get_value(TreeIter, 5) == "":
            self.RunMenuItem.set_sensitive(True)
            self.UninstallMenuItem.set_sensitive(True)
            self.InstallMenuItem.set_sensitive(False)

        # If the selected app is not installed
        else:
            self.RunMenuItem.set_sensitive(False)
            self.UninstallMenuItem.set_sensitive(False)
            self.InstallMenuItem.set_sensitive(True)

    def onSearchChanged(self, search_entry):
        self.SearchFilter.refilter()

    def onResorted(self, tree_sortable):
        self.SearchFilter.refilter()

    def onPressShowButton(self, toggle_button):
        self.SearchFilter.refilter()

    def onRun(self, menuitem):
        Selection = self.TreeViewMain.get_selection()
        TreeModel, TreeIter = Selection.get_selected()
        if TreeIter is None:
            self.MessageDialogError.set_markup(
                _("<big><b>Selection Error</b></big>"))
            self.MessageDialogError.format_secondary_text(
                _("None of the applications are selected."))
            self.MessageDialogError.run()
            self.MessageDialogError.hide()
            return None
        TreePath = TreeModel.get_path(TreeIter)
        SelectedRowIndex = TreePath.get_indices()[0]

        AppToRunRealName = self.ListStoreMain.get_value(TreeIter, 0)
        AppToRunArch = self.ListStoreMain.get_value(TreeIter, 1)
        AppToRunBranch = self.ListStoreMain.get_value(TreeIter, 2)

        AppToRun = Flatpak.Ref.parse("app/" + AppToRunRealName + "/" +
                                     AppToRunArch + "/" + AppToRunBranch)

        AppToRunCommit = AppToRun.get_commit()

        FlatpakActionSuccess = self.FlatpakInstallation.launch(
            AppToRunRealName,
            AppToRunArch,
            AppToRunBranch,
            AppToRunCommit,
            Gio.Cancellable.new())

        if FlatpakActionSuccess:
            pass
        else:
            self.MessageDialogError.set_markup(
                _("<big><b>Running Error</b></big>"))
            self.MessageDialogError.format_secondary_text(
                _("The selected application couldn't run."))
            self.MessageDialogError.run()
            self.MessageDialogError.hide()

    def onInfo(self, menuitem):
        Selection = self.TreeViewMain.get_selection()
        TreeModel, TreeIter = Selection.get_selected()
        if TreeIter is None:
            self.MessageDialogError.set_markup(
                _("<big><b>Selection Error</b></big>"))
            self.MessageDialogError.format_secondary_text(
                _("None of the applications are selected."))
            self.MessageDialogError.run()
            self.MessageDialogError.hide()
            return None
        TreePath = TreeModel.get_path(TreeIter)
        SelectedRowIndex = TreePath.get_indices()[0]

        self.FlatpakRefsList = self.FlatpakInstallation.list_installed_refs()
        self.FlatHubRefsList = self.FlatpakInstallation.list_remote_refs_sync(
                                   "flathub", Gio.Cancellable.new())

        for item in self.FlatpakRefsList:
            for item2 in self.FlatHubRefsList:
                if item.get_name() == item2.get_name():
                    self.FlatHubRefsList.remove(item2)
        self.FlatpakRefsList = self.FlatpakRefsList + self.FlatHubRefsList

        AppRealName = self.ListStoreMain.get_value(TreeIter, 0)
        AppArch = self.ListStoreMain.get_value(TreeIter, 1)
        AppBranch = self.ListStoreMain.get_value(TreeIter, 2)

        for item in self.FlatpakRefsList:
            if item.get_name() == AppRealName:
                App = item
                break

        AppCollectionID = App.get_collection_id()
        if AppCollectionID is None:
            AppCollectionID = _("None")
        AppCommit = App.get_commit()

        AppIsInstalledRef = isinstance(App, Flatpak.InstalledRef)
        AppIsRemoteRef = isinstance(App, Flatpak.RemoteRef)

        if AppIsInstalledRef:
            # AppContentRating = App.get_appdata_content_rating()
            # if AppContentRating is None:
                # AppContentRating = _("None")

            # AppContentRatingType = App.get_appdata_content_rating_type()
            # if AppContentRatingType is None:
                # AppContentRatingType = _("None")

            AppLicense = App.get_appdata_license()
            if AppLicense is None:
                AppLicense = _("None")

            AppName = App.get_appdata_name()
            if AppName is None:
                AppName = _("None")

            AppSummary = App.get_appdata_summary()
            if AppSummary is None:
                AppSummary = _("None")

            AppVersion = App.get_appdata_version()
            if AppVersion is None:
                AppVersion = _("None")

            AppDeployDir = App.get_deploy_dir()
            if AppDeployDir is None:
                AppDeployDir = _("None")

            AppEOLReason = App.get_eol()
            if AppEOLReason is None:
                AppEOLReason = _("None")

            AppEOLRebased = App.get_eol_rebase()
            if AppEOLRebased is None:
                AppEOLRebased = _("None")

            AppInstalledSize = App.get_installed_size()
            AppInstalledSizeMiB = AppInstalledSize / 1048576
            AppInstalledSizeMiBAsString = f"{AppInstalledSizeMiB:.2f}" + " MiB"

            AppIsCurrent = App.get_is_current()
            if AppIsCurrent:
                AppIsCurrentString = _("Yes")
            else:
                AppIsCurrentString = _("No")

            AppLatestCommit = App.get_latest_commit()
            if AppLatestCommit is None:
                AppLatestCommit = _("None")

            AppOrigin = App.get_origin()
            if AppOrigin is None:
                AppOrigin = _("None")

            AppSubpaths = App.get_subpaths()
            if AppSubpaths is None or not AppSubpaths:
                AppSubpathsAsString = _("None")
            else:
                AppSubpathsAsString = ""
                for item in AppSubpaths:
                    AppSubpathsAsString = AppSubpathsAsString + item + ", "
                    AppSubpathsAsString = AppSubpathsAsString[:-2]

            InfoString = _("Real Name: ") + AppRealName + "\n" + \
                _("Arch: ") + AppArch + "\n" + \
                _("Branch: ") + AppBranch + "\n" + \
                _("Collection ID: ") + AppCollectionID + "\n" + \
                _("Commit: ") + AppCommit + "\n" + \
                _("Is Installed: ") + _("Yes") + "\n" + \
                _("License: ") + AppLicense + "\n" + \
                _("Name: ") + AppName + "\n" + \
                _("Summary: ") + AppSummary + "\n" + \
                _("Version: ") + AppVersion + "\n" + \
                _("Deploy Dir: ") + AppDeployDir + "\n" + \
                _("EOL Reason: ") + AppEOLReason + "\n" + \
                _("EOL Rebased: ") + AppEOLRebased + "\n" + \
                _("Installed Size: ") + AppInstalledSizeMiBAsString + "\n" + \
                _("Is Current: ") + AppIsCurrentString + "\n" + \
                _("Latest Commit: ") + AppLatestCommit + "\n" + \
                _("Origin: ") + AppOrigin + "\n" + \
                _("Subpaths: ") + AppSubpathsAsString + "\n"

        elif AppIsRemoteRef:
            AppDownloadSize = App.get_download_size()
            AppDownloadSizeMiB = AppDownloadSize / 1048576
            AppDownloadSizeMiBAsString = f"{AppDownloadSizeMiB:.2f}" + " MiB"

            AppEOLReason = App.get_eol()
            if AppEOLReason is None:
                AppEOLReason = _("None")

            AppEOLRebased = App.get_eol_rebase()
            if AppEOLRebased is None:
                AppEOLRebased = _("None")

            AppInstalledSize = App.get_installed_size()
            AppInstalledSizeMiB = AppInstalledSize / 1048576
            AppInstalledSizeMiBAsString = f"{AppInstalledSizeMiB:.2f}" + " MiB"

            AppRemoteName = App.get_remote_name()
            if AppRemoteName is None:
                AppRemoteName = _("None")

            InfoString = _("Real Name: ") + AppRealName + "\n" + \
                _("Arch: ") + AppArch + "\n" + \
                _("Branch: ") + AppBranch + "\n" + \
                _("Collection ID: ") + AppCollectionID + "\n" + \
                _("Commit: ") + AppCommit + "\n" + \
                _("Is Installed: ") + _("Yes") + "\n" + \
                _("Download Size: ") + AppDownloadSizeMiBAsString + "\n" + \
                _("EOL Reason: ") + AppEOLReason + "\n" + \
                _("EOL Rebased: ") + AppEOLRebased + "\n" + \
                _("Installed Size: ") + AppInstalledSizeMiBAsString + "\n" + \
                _("Remote Name: ") + AppRemoteName + "\n"

        InfoWindow(self.Application, InfoString, App)

    def onUninstall(self, menuitem):
        Selection = self.TreeViewMain.get_selection()
        TreeModel, TreeIter = Selection.get_selected()
        if TreeIter is None:
            self.MessageDialogError.set_markup(
                _("<big><b>Selection Error</b></big>"))
            self.MessageDialogError.format_secondary_text(
                _("None of the applications are selected."))
            self.MessageDialogError.run()
            self.MessageDialogError.hide()
            return None
        TreePath = TreeModel.get_path(TreeIter)
        SelectedRowIndex = TreePath.get_indices()[0]

        AppToUninstallRealName = self.ListStoreMain.get_value(TreeIter, 0)
        AppToUninstallArch = self.ListStoreMain.get_value(TreeIter, 1)
        AppToUninstallBranch = self.ListStoreMain.get_value(TreeIter, 2)

        self.FlatHubRefsList = self.FlatpakInstallation.list_remote_refs_sync(
                                   "flathub", Gio.Cancellable.new())

        for item in self.FlatpakRefsList:
            if item.get_name() == AppToUninstallRealName and item not in self.FlatHubRefsList:
                App = item
                break

        UninstallWindow(self.Application, AppToUninstallRealName,
                        AppToUninstallArch, AppToUninstallBranch,
                        self.FlatpakInstallation, self.ListStoreMain)

    def onInstall(self, menuitem):
        Selection = self.TreeViewMain.get_selection()
        TreeModel, TreeIter = Selection.get_selected()
        if TreeIter is None:
            self.MessageDialogError.set_markup(
                _("<big><b>Selection Error</b></big>"))
            self.MessageDialogError.format_secondary_text(
                _("None of the applications are selected."))
            self.MessageDialogError.run()
            self.MessageDialogError.hide()
            return None
        TreePath = TreeModel.get_path(TreeIter)
        SelectedRowIndex = TreePath.get_indices()[0]

        AppToInstallRealName = self.ListStoreMain.get_value(TreeIter, 0)
        AppToInstallArch = self.ListStoreMain.get_value(TreeIter, 1)
        AppToInstallBranch = self.ListStoreMain.get_value(TreeIter, 2)
        AppToInstallRemote = self.ListStoreMain.get_value(TreeIter, 3)

        for item in self.FlatpakRefsList:
            if item.get_name() == AppToInstallRealName and item not in self.FlatHubRefsList:
                App = item
                break

        InstallWindow(self.Application, AppToInstallRealName,
                      AppToInstallArch, AppToInstallBranch,
                      AppToInstallRemote, self.FlatpakInstallation,
                      self.ListStoreMain)

    def onInstallFromEntry(self, menuitem):
        InstallFromEntryWindow(self.Application, self.FlatpakInstallation,
                               self.ListStoreMain)

    def onInstallFromFile(self, menuitem):
        InstallFromFileWindow(self.Application, self.FlatpakInstallation,
                               self.ListStoreMain)

    def onUpdateAll(self, menuitem):
        UpdateAllWindow(self.Application, self.FlatpakInstallation,
                        self.ListStoreMain)

    def onAbout(self, menuitem):
        self.AboutDialog.run()
        self.AboutDialog.hide()
