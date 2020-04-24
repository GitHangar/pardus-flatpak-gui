#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Pardus Flatpak GUI setup script
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

from pardusflatpakstore.version import Version

from setuptools import setup, find_packages
from os import listdir

ui_files = []
for file_ui in listdir("ui"):
    ui_files.append("ui/" + file_ui)

data_files = [
        ("/usr/share/applications", ["tr.org.pardus.pardus_flatpak_gui.desktop"]),
        ("/usr/share/locale/en/LC_MESSAGES", ["po/en/LC_MESSAGES/pardus-flatpak-gui.mo"]),
        ("/usr/share/locale/tr/LC_MESSAGES", ["po/tr/LC_MESSAGES/pardus-flatpak-gui.mo"]),
        ("/usr/share/pardus/pardus-flatpak-gui/ui", ui_files)
    ]

setup(
    name="Pardus Flatpak GUI",
    version=Version.getVersion(),
    packages=find_packages(),
    scripts=["pardus-flatpak-store"],
    install_requires=["PyGObject"],
    data_files=data_files,
    author="Erdem Ersoy",
    author_email="erdem.ersoy@pardus.org.tr",
    description="Flatpak GUI for Pardus.",
    license="GPLv3",
    keywords="store flatpak gui",
    url="https://www.pardus.org.tr",
)

