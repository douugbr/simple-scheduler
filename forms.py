from wtforms import Form, StringField, validators, BooleanField
from wtforms.validators import DataRequired
from wtforms.fields.html5 import DateField
from datetime import date

class AddEventForm(Form):
    name = StringField('name', [validators.Length(min=2, max=50)])
    date = DateField('date', format='%d/%m/%Y')

class RemoveEventForm(Form):
    eventid = StringField('eventid')

class AddNoteForm(Form):
    name = StringField('name', [validators.Length(min=2, max=50)])

class RemoveNoteForm(Form):
    eventid = StringField('eventid')
    notepadid = StringField('notepadid')

class UpdateNoteForm(Form):
    name = StringField('name', [validators.Length(min=2, max=50)])
    notes = StringField('notes')

class AddTodolistForm(Form):
    name = StringField('name', [validators.Length(min=2, max=50)])

class RemoveTodolistForm(Form):
    eventid = StringField('eventid')
    todolistid = StringField('todolistid')

class UpdateTodolistForm(Form):
    item = StringField('item', [validators.Length(min=2, max=50)])
    eventid = StringField('eventid')
    todolistid = StringField('todolistid')
    completed = BooleanField('completed')
