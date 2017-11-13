from collections import defaultdict
from operator import itemgetter

from PyQt4.QtCore import Qt, QTimer
from PyQt4.QtGui import QApplication, QListView

from Orange.data import Table, Domain, ContinuousVariable
from Orange.widgets import widget, gui, settings
from Orange.widgets.utils.itemmodels import VariableListModel


class DnDListView(QListView):
    def __init__(self, callback, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._callback = callback

    def dropEvent(self, event):
        super().dropEvent(event)
        QTimer.singleShot(100, self._callback)


class OWUniqueCount(widget.OWWidget):
    name = 'UniqueCount'
    icon = 'icons/UniqueCount.svg'
    description = 'Count instances unique by specified key attribute(s).'

    inputs = [('Data', Table, 'set_data')]
    outputs = [('Unique Counts', Table)]

    want_main_area = False

    settingsHandler = settings.DomainContextHandler()

    model_attrs = settings.ContextSetting(([], []))
    autocommit = settings.Setting(True)

    def __init__(self):
        hbox = gui.hBox(self.controlArea)
        _properties = dict(alternatingRowColors=True,
                           defaultDropAction=Qt.MoveAction,
                           dragDropMode=QListView.DragDrop,
                           dragEnabled=True,
                           selectionMode=QListView.ExtendedSelection,
                           selectionBehavior=QListView.SelectRows,
                           showDropIndicator=True,
                           acceptDrops=True)
        listview_avail = DnDListView(lambda: self.commit(), self, **_properties)
        self.model_avail = model = VariableListModel(parent=self, enable_dnd=True)
        listview_avail.setModel(model)

        listview_key = DnDListView(lambda: self.commit(), self, **_properties)
        self.model_key = model = VariableListModel(parent=self, enable_dnd=True)
        listview_key.setModel(model)

        box = gui.vBox(hbox, 'Available Variables')
        box.layout().addWidget(listview_avail)
        box = gui.vBox(hbox, 'Group-By Key')
        box.layout().addWidget(listview_key)

        gui.auto_commit(self.controlArea, self, 'autocommit', 'Commit',
                        orientation=Qt.Horizontal)

    def set_data(self, data):
        self.data = data
        if data is None:
            self.model_avail.wrap([])
            self.model_key.wrap([])
            self.commit()
            return

        self.closeContext()
        self.model_attrs = (list(data.domain) + list(data.domain.metas), [])
        self.openContext(data.domain)

        self.model_avail.wrap(self.model_attrs[0])
        self.model_key.wrap(self.model_attrs[1])
        self.commit()

    def commit(self):
        if self.data is None or len(self.model_key) == 0:
            self.send('Unique Counts', None)
            return

        uniques = defaultdict(int)
        rows = zip(*[self.data.get_column_view(dom_var.name)[0]
                     for dom_var in self.model_key])
        for row in rows:
            uniques[row] += 1
        domain = Domain([dom_var for dom_var in self.model_key] + [ContinuousVariable('count')])
        table = Table.from_domain(domain)
        table.extend([list(item[0]) + [item[1]] for item in uniques.items()])
        self.send('Unique Counts', table)
        return


if __name__ == '__main__':
    app = QApplication([])
    w = OWUniqueCount()
    w.show()
    w.set_data(Table('iris'))
    app.exec()
