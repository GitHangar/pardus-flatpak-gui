#!/bin/sh
#
# Pardus Flatpak GUI localization updating script
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

xgettext --default-domain=pardus-flatpak-gui \
         --lang=Python \
         --from-code=utf-8 \
         --output=pardus-flatpak-gui.pot \
         pardus-flatpak-gui pardusflatpakgui/*.py

msgmerge --lang=en \
         --update \
         po/en/LC_MESSAGES/pardus-flatpak-gui.po \
         pardus-flatpak-gui.pot
msgmerge --lang=tr \
         --update \
         po/tr/LC_MESSAGES/pardus-flatpak-gui.po \
         pardus-flatpak-gui.pot

msgfmt --check --directory=po/en/LC_MESSAGES/ \
       --output-file=po/en/LC_MESSAGES/pardus-flatpak-gui.mo \
       pardus-flatpak-gui.po \

msgfmt --check --directory=po/tr/LC_MESSAGES/ \
       --output-file=po/tr/LC_MESSAGES/pardus-flatpak-gui.mo \
       pardus-flatpak-gui.po \
