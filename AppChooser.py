# Copyright (C) 2017 Tom Hartill
#
# AppChooser.py - A set of GTK+ 3 widgets for selecting installed applications.
#
# AppChooser is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation; either version 3 of the License, or (at your option) any later
# version.
#
# AppChooser is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with
# AppChooser; if not, see http://www.gnu.org/licenses/.
#
# An up to date version can be found at:
# https://github.com/Tomha/python-gtk-app-chooser

import re
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gio, GObject, Gtk, Pango


class AppChooserDialog(Gtk.Dialog):
    """GTK+ 3 Dialog to allow selection of an installed application.
    
    The Gio.AppInfo of the selected app is made available as the result of the 
    run method, or by the get_selected_app method.
    """

    def __init__(self, parent=None):
        super().__init__()

        self.set_default_size(350, 400)
        self.set_icon_name("gtk-search")
        self.set_title("Choose An Application")
        if parent:
            self.set_parent(parent)

        self._mime_types = []
        self._filter_term = ""
        self._selected_app = ""
        self._use_regex = False
        self._app_list = []

        # Widgets start here

        # Filtering
        self._filter_entry = Gtk.Entry()
        filter_label = Gtk.Label("Filter Term:")
        filter_clear_button = Gtk.Button.new_from_icon_name("gtk-clear",
                                                            Gtk.IconSize.MENU)
        filter_box = Gtk.Box()
        filter_box.set_spacing(4)
        filter_box.pack_start(filter_label, False, False, 0)
        filter_box.pack_start(self._filter_entry, True, True, 0)
        filter_box.pack_start(filter_clear_button, False, False, 0)

        # App view
        self._list_store = Gtk.ListStore(str, str, int)
        pixbuf_renderer = Gtk.CellRendererPixbuf()
        text_renderer = Gtk.CellRendererText()
        icon_column = Gtk.TreeViewColumn("icon", pixbuf_renderer, icon_name=0)
        text_column = Gtk.TreeViewColumn("text", text_renderer, text=1)

        self._app_view = Gtk.TreeView()
        self._app_view.set_model(self._list_store)
        self._app_view.set_headers_visible(False)
        self._app_view.append_column(icon_column)
        self._app_view.append_column(text_column)

        scroller = Gtk.ScrolledWindow()
        scroller.add(self._app_view)

        app_box_frame = Gtk.Frame()
        app_box_frame.add(scroller)

        # Pack widgets in dialog
        content_box = self.get_content_area()
        content_box.set_margin_left(8)
        content_box.set_margin_right(8)
        content_box.set_margin_top(8)
        content_box.set_margin_bottom(8)
        content_box.set_spacing(8)
        content_box.pack_start(filter_box, False, False, 0)
        content_box.pack_start(app_box_frame, True, True, 0)

        # Set dialog buttons
        button_box = self.get_action_area()
        button_box.set_spacing(4)
        self.add_button(Gtk.STOCK_OK, 1)
        self.add_button(Gtk.STOCK_CANCEL, 0)

        # Connect signals
        self._filter_entry.connect("changed", self._filter_apps)
        filter_clear_button.connect("clicked", lambda button:
                                    self._filter_entry.set_text(""))
        self._app_view.connect("cursor-changed", self._on_app_selected)
        self._app_view.connect("row-activated", self._on_app_activated)

    def _filter_apps(self, entry):
        """Filter apps based on filter term, used when filter term changes.

        If use_regex is True, the provided string will be used as the pattern
        for a regex match, otherwise basic case-insensitive matching is used.
        
        :param entry: Text entry containing filter text.
        :return: None
        """
        self._filter_term = entry.get_text()
        self._list_store.clear()

        if self._filter_term == "":
            for i in range(len(self._app_list)):
                app = self._app_list[i]
                if self._mime_types:
                    supported_types_specific = app.get_supported_types()
                    supported_types_general = []
                    for mime_type in supported_types_specific:
                        mime_type = mime_type.split('/')
                        if mime_type[0] not in supported_types_general:
                            supported_types_general += [mime_type[0]]
                    no_match = True
                    for mime_type in self._mime_types:
                        if mime_type in supported_types_general or \
                                        mime_type in supported_types_specific:
                            no_match = False
                            break
                    if no_match:
                        continue
                icon = self._app_list[i].get_icon()
                app_icon = icon.to_string() if icon else "gtk-missing-icon"
                app_name = self._app_list[i].get_display_name()
                self._list_store.append([app_icon, app_name, i])
        else:
            for i in range(len(self._app_list)):
                app = self._app_list[i]
                if self._filter_term:
                    if self._use_regex:
                        if not re.search(self._filter_term,
                                         app.get_display_name()):
                            continue
                    else:
                        if not self._filter_term.lower() in \
                                app.get_display_name().lower():
                            continue
                if self._mime_types:
                    supported_types_specific = app.get_supported_types()
                    supported_types_general = []
                    for mime_type in supported_types_specific:
                        mime_type = mime_type.split('/')
                        if mime_type[0] not in supported_types_general:
                            supported_types_general += [mime_type[0]]
                    no_match = True
                    for mime_type in self._mime_types:
                        if mime_type in supported_types_general or \
                                        mime_type in supported_types_specific:
                            no_match = False
                            break
                    if no_match:
                        continue
                icon = self._app_list[i].get_icon()
                app_icon = icon.to_string() if icon else "gtk-missing-icon"
                app_name = self._app_list[i].get_display_name()
                self._list_store.append([app_icon, app_name, i])

    def _on_app_activated(self, view, path, column):
        """Emulate pressing "OK" when an application is double clicked.
        
        :param view: TreeView containing the activated application row.
        :param path: TreePath to the row activated row.
        :param column: TreeViewColumn in which activation occured.
        :return: None
        """
        self.response(1)

    def _on_app_selected(self, view):
        """Set the selected app property when the selection changes.
        
        :param view: TreeView in which selection changed.
        :return: None
        """
        selection = self._app_view.get_selection()
        if not selection:
            self._selected_icon = None
        else:
            tree_model, tree_iter = selection.get_selected()
            if not tree_iter:
                self._selected_app = None
            else:
                app_index = tree_model.get_value(tree_iter, 2)
                self._selected_app = self._app_list[app_index]

    def get_mime_types(self):
        """Get the list of mime types from which to select apps.

        :return: List of mime types being filtered.
        """
        return self._mime_types

    def get_filter_term(self):
        """Get the string used for filtering apps by display name.

        :return: String used for filtering apps by display name.
        """
        return self._filter_term

    def get_selected_app(self):
        """Get the Gio.AppInfo of the app selected in the dialog.

        Will be None until the button's dialog has been closed once.

        :return: Gio.AppInfo of the selected app.
        """
        return self._selected_app

    def get_use_regex(self):
        """ Get whether the filter term should be used as a regex pattern.

        :return: Whether the filter term is used as a regex pattern.
        """
        return self._use_regex

    def run(self):
        """Run dialog to select an installed app.
        
        :return: None
        """
        self._app_list = Gio.AppInfo.get_all()
        self._app_list.sort(key=lambda app: app.get_display_name())
        self._filter_apps(self._filter_entry)
        if self._filter_term:
            self.filter_entry.set_text(self._filter_term)
        self.show_all()
        result = super().run()
        self.destroy()
        if result == 1:
            return self._selected_app
        return None

    def set_mime_types(self, mime_types):
        """ Get the list of mime types from which to select apps.

        Dialog will not update mime types once it has been shown.

        :param mime_types: List of mime types to allow selection from.
        :return: None
        """
        if not type(mime_types) == list:
            raise TypeError("must be type list, not " +
                            type(mime_types).__name__)
        self._mime_types = list(set(mime_types))

    def set_filter_term(self, filter_term):
        """Set the string used for filtering apps by display name.

        If use_regex is True, the provided string will be used as the pattern
        for a regex match, otherwise basic case-insensitive matching is used.

        Dialog will not update the filter term once it has been shown.

        :param filter_term: String used for filtering apps by display name.
        :return: None
        """
        if not type(filter_term) == str:
            raise TypeError("must be type str, not " +
                            type(filter_term).__name__)
        self._filter_term = filter_term

    def set_use_regex(self, use_regex):
        """Set whether or not regex terms are used to filter apps.

        If use_regex is True, the filter term will be used as the pattern for a
        regex match, otherwise basic case-insensitive matching is used.

        Dialog will not update this value once it has been shown.

        :param use_regex: Whether the filter term is used as a regex pattern.
        :return: None
        """
        if not type(use_regex) == bool:
            raise TypeError("must be type bool, not " +
                            type(use_regex).__name__)
        self._use_regex = use_regex


class AppChooserButton(Gtk.Button):
    """GTK + 3 Button to open a dialog to select an installed application.

    The Gio.AppInfo of the selected app is emitted via the "app_selected"
    signal once the dialog is closed. 
    """

    def __init__(self):
        super().__init__()

        self._mime_types = []
        self._filter_term = ""
        self._use_regex = False
        self._selected_app = None

        # Register a custom icon_selected signal for once dialog closes.
        GObject.type_register(AppChooserButton)
        GObject.signal_new("app-selected",
                           AppChooserButton,
                           GObject.SIGNAL_RUN_FIRST,
                           GObject.TYPE_NONE,
                           [GObject.TYPE_STRING])

        # Widgets go here
        self._icon = Gtk.Image.new_from_icon_name("gtk-search",
                                                  Gtk.IconSize.MENU)
        self._icon.set_margin_left(2)

        open_icon = Gtk.Image.new_from_icon_name("document-open-symbolic",
                                                 Gtk.IconSize.MENU)
        self._label = Gtk.Label("(Choose An App)")
        self._label.set_hexpand(True)
        self._label.set_halign(Gtk.Align.START)
        self._label.set_ellipsize(Pango.EllipsizeMode.END)

        box = Gtk.Box()
        box.set_spacing(4)
        box.pack_start(self._icon, False, False, 0)
        box.pack_start(self._label, False, True, 0)
        box.pack_start(open_icon, False, False, 2)

        self.add(box)
        self.connect("clicked", self._show_dialog)

    def _show_dialog(self, button):
        """Called when the button is clicked to show a selection dialog.

        :param button: The button used to show the dialog (self)
        :return: None
        """
        dialog = AppChooserDialog()
        dialog.set_transient_for(self.get_toplevel())
        dialog.set_mime_types(self._mime_types)
        dialog.set_filter_term(self._filter_term)
        dialog.set_use_regex(self._use_regex)
        self._selected_app = dialog.run()
        dialog.destroy()

        if self._selected_app:
            app_icon = self._selected_app.get_icon()
            icon_name = app_icon.to_string() if app_icon else \
                "gtk-missing-icon"
            self._icon.set_from_icon_name(icon_name, Gtk.IconSize.MENU)
            self._label.set_text(self._selected_app.get_display_name())
        else:
            self._icon.set_from_icon_name("gtk-search", Gtk.IconSize.MENU)
            self._label.set_text("(Choose An App)")
        self.emit("app_selected", self._selected_app)

    def get_mime_types(self):
        """Get the list of mime types from which to select apps.

        :return: List of mime types being filtered.
        """
        return self._mime_types

    def get_filter_term(self):
        """Get the string used for filtering apps by display name.

        :return: String used for filtering apps by display name.
        """
        return self._filter_term

    def get_selected_app(self):
        """Get the Gio.AppInfo of the app selected in the dialog.
        
        Will be None until the button's dialog has been closed once.
        
        :return: Gio.AppInfo of the selected app.
        """
        return self._selected_app

    def get_use_regex(self):
        """ Get whether the filter term should be used as a regex pattern.

        :return: Whether the filter term is used as a regex pattern.
        """
        return self._use_regex

    def set_mime_types(self, mime_types):
        """ Get the list of mime types from which to select apps.

        Dialog will not update mime types while it is active.

        :param mime_types: List of mime types to allow selection from.
        :return: None
        """
        if not type(mime_types) == list:
            raise TypeError("must be type list, not " +
                            type(mime_types).__name__)
        self._mime_types = list(set(mime_types))

    def set_filter_term(self, filter_term):
        """Set the string used for filtering apps by display name.

        If use_regex is True, the provided string will be used as the pattern
        for a regex match, otherwise basic case-insensitive matching is used.

        Dialog will not update the filter term once it has been shown.

        :param filter_term: String used for filtering apps by display name.
        :return: None
        """
        if not type(filter_term) == str:
            raise TypeError("must be type str, not " +
                            type(filter_term).__name__)
        self._filter_term = filter_term

    def set_use_regex(self, use_regex):
        """Set whether or not regex terms are used to filter apps.

        If use_regex is True, the filter term will be used as the pattern for a
        regex match, otherwise basic case-insensitive matching is used.

        Dialog will not update this value once it has been shown.

        :param use_regex: Whether the filter term is used as a regex pattern.
        :return: None
        """
        if not type(use_regex) == bool:
            raise TypeError("must be type bool, not " +
                            type(use_regex).__name__)
        self._use_regex = use_regex


class AppChooserComboBox(Gtk.ComboBox):
    """GTK+ 3 ComboBox allowing selection of an installed application.
    
    The Gio.AppInfo of the currently selected app is made available via the
    get_selected_app method.
    """

    def __init__(self):
        super().__init__()

        self._mime_types = []
        self._filter_term = ""
        self._use_regex = False
        self._app_list = []

        pixbuf_renderer = Gtk.CellRendererPixbuf()
        pixbuf_renderer.set_alignment(0, 0.5)
        pixbuf_renderer.set_padding(2, 0)
        text_renderer = Gtk.CellRendererText()
        text_renderer.set_alignment(0, 0.5)

        self._app_store = Gtk.ListStore(str, str)
        self.set_model(self._app_store)
        self.pack_start(pixbuf_renderer, True)
        self.add_attribute(pixbuf_renderer, "icon_name", 0)
        self.pack_start(text_renderer, True)
        self.add_attribute(text_renderer, "text", 1)

    def get_mime_types(self):
        """Get the list of mime types from which to select apps.
        
        :return: List of mime types to be displayed.
        """
        return self._mime_types

    def get_filter_term(self):
        """Get the string used for filtering apps by display name.
        
        :return: String used for filtering apps by display name.
        """
        return self._filter_term

    def get_selected_app(self):
        """Get the Gio.AppInfo of the app currently selected in the combo box.
        
        :return: Gio.AppInfo of currently selected app.
        """
        selection_index = self.get_active()
        if selection_index == 0:  # When "Choose An App)" is selected
            return None
        else:
            return self._app_list[selection_index - 1]

    def get_use_regex(self):
        """ Get whether the filter term should be used as a regex pattern.
        
        :return: Whether the filter term is used as a regex pattern.
        """
        return self._use_regex

    def populate(self):
        """Populate the combo box with installed applications.
        
        :return: None
        """
        app_list = Gio.AppInfo.get_all()
        self._app_list = []

        for app in app_list:
            if self._filter_term:
                if self._use_regex:
                    if not re.search(self._filter_term,
                                     app.get_display_name()):
                        continue
                else:
                    if not self._filter_term.lower() in \
                            app.get_display_name().lower():
                        continue

            if self._mime_types:
                supported_types_specific = app.get_supported_types()
                supported_types_general = []
                for mime_type in supported_types_specific:
                    mime_type = mime_type.split('/')
                    if mime_type[0] not in supported_types_general:
                        supported_types_general += [mime_type[0]]
                no_match = True
                for mime_type in self._mime_types:
                    if mime_type in supported_types_general or \
                                    mime_type in supported_types_specific:
                        no_match = False
                        break
                if no_match:
                    continue

            self._app_list += [app]

        self._app_list.sort(key=lambda app: app.get_display_name())

        self._app_store.clear()
        self._app_store.append(["gtk-search", "(Choose An App)"])
        for app in self._app_list:
            icon = app.get_icon()
            icon_name = icon.to_string() if icon else "gtk-missing-icon"
            self._app_store.append([icon_name, app.get_display_name()])
        self.set_active(0)
        self.show_all()

    def set_mime_types(self, mime_types):
        """ Get the list of mime types from which to select apps.
        
        Combobox will not update mime types once it has been shown.
        
        :param mime_types: List of mime types to allow selection from.
        :return: None
        """
        if not type(mime_types) == list:
            raise TypeError("must be type list, not " +
                            type(mime_types).__name__)
        self._mime_types = list(set(mime_types))

    def set_filter_term(self, filter_term):
        """Set the string used for filtering apps by display name.
        
        If use_regex is True, the provided string will be used as the pattern
        for a regex match, otherwise basic case-insensitive matching is used.
        
        Combobox will not update the filter term once it has been shown.
        
        :param filter_term: String used for filtering apps by display name.
        :return: None
        """
        if not type(filter_term) == str:
            raise TypeError("must be type str, not " +
                            type(filter_term).__name__)
        self._filter_term = filter_term

    def set_use_regex(self, use_regex):
        """Set whether or not regex terms are used to filter apps.
        
        If use_regex is True, the filter term will be used as the pattern for a
        regex match, otherwise basic case-insensitive matching is used.
        
        Combobox will not update this value once it has been shown.
        
        :param use_regex: Whether the filter term is used as a regex pattern.
        :return: None
        """
        if not type(use_regex) == bool:
            raise TypeError("must be type bool, not " +
                            type(use_regex).__name__)
        self._use_regex = use_regex
