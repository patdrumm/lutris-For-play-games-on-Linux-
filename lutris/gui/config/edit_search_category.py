# pylint: disable=no-member
from gettext import gettext as _
from typing import Any, Dict

from gi.repository import Gtk

from lutris.database import categories as categories_db
from lutris.gui.dialogs import QuestionDialog, SavableModelessDialog
from lutris.search import GameSearch


class EditSearchCategoryDialog(SavableModelessDialog):
    """Games assigned to category dialog."""

    def __init__(self, parent, category: Dict[str, Any]) -> None:
        self.category = category.get("name") or "New Category"
        self.category_id = category.get("id")
        self.search = category.get("search") or ""
        title = _("Configure %s") % self.category

        super().__init__(title, parent=parent, border_width=10)
        self.set_default_size(500, 350)

        self.vbox.set_homogeneous(False)
        self.vbox.set_spacing(10)

        self.name_entry = self._add_entry_box(_("Name"), self.category)
        self.search_entry = self._add_entry_box(_("Search"), self.search)

        # self.vbox.pack_start(self._create_games_checkboxes(), True, True, 0)

        delete_button = self.add_styled_button(Gtk.STOCK_DELETE, Gtk.ResponseType.NONE, css_class="destructive-action")
        delete_button.connect("clicked", self.on_delete_clicked)
        delete_button.set_sensitive(bool(self.category_id))

        self.show_all()

    def _add_entry_box(self, label: str, text: str) -> Gtk.Entry:
        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        entry_label = Gtk.Label(label)
        entry = Gtk.Entry()
        entry.set_text(text)
        hbox.pack_start(entry_label, False, False, 0)
        hbox.pack_start(entry, True, True, 0)
        self.vbox.pack_start(hbox, False, False, 0)
        return entry

    def on_delete_clicked(self, _button):
        dlg = QuestionDialog(
            {
                "title": _("Do you want to delete the category '%s'?") % self.category,
                "question": _(
                    "This will permanently destroy the category, but the games themselves will not be deleted."
                ),
                "parent": self,
            }
        )
        if dlg.result == Gtk.ResponseType.YES:
            categories_db.remove_category(self.category_id)
            self.destroy()

    def on_save(self, _button: Gtk.Button) -> None:
        """Save game info and destroy widget."""
        old_name: str = self.category
        new_name: str = categories_db.strip_category_name(self.name_entry.get_text())
        old_search: str = self.search
        new_search: str = str(GameSearch(self.search_entry.get_text()))

        if not new_name:
            new_name = old_name

        if categories_db.is_reserved_category(new_name):
            raise RuntimeError(_("'%s' is a reserved category name.") % new_name)

        if old_name != new_name:
            if new_name in (c["name"] for c in categories_db.get_categories()):
                raise RuntimeError(_("'%s' is already a category, and search-based categories can't be merged."))

        if not self.category_id:
            # Creating new category!
            categories_db.add_category(category_name=new_name, search=new_search)
        elif old_name != new_name or old_search != new_search:
            # Changing an existing category.
            categories_db.redefine_category(self.category_id, new_name, new_search)

        self.destroy()