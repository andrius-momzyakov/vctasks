# coding: UTF-8
# Create your views here.

from django import forms
from django.db.models.fields import BLANK_CHOICE_DASH, BLANK_CHOICE_NONE
import models as m
from django.contrib import auth
from django.contrib.auth.models import User, Group
from django.views.generic.list_detail import object_list, object_detail
from django.template import Context, Template
from django.contrib.admin.widgets import AdminDateWidget

from datetime import date
from django.core.files import File
from django.core.servers.basehttp import FileWrapper
from django.forms import Form, ModelForm, Textarea, HiddenInput, RadioSelect

import settings


class TaskFormManager(ModelForm):
    def __init__(self, *args, **kwargs):
        super(TaskFormManager, self).__init__(*args, **kwargs)
        self.fields['responsible'].choices = [(user.id, user.username) for user in \
                                              Group.objects.get(name='developer').user_set.all()]
        self.fields['responsible'].choices.append(BLANK_CHOICE_DASH[0])

    is_supervised = forms.ChoiceField(choices=(('N', u'Нет'), ('Y', u'Да'),), required=True, initial='N')
    urgent_important = forms.ChoiceField(required=True, choices=m.Task.URGENT_IMPORTANT_MATRIX, initial='D')

    class Meta:
        model = m.Task
        fields = ( 'name', 'descr', 'urgent_important', 'parent', 'date_open', 'start_date', \
                   'applicant', 'module', \
                   'responsible', 'appoint_date', 'deadline', 'is_supervised', 'ready_date', 'decision', \
                   'proj', 'exe', 'closing_type', 'date_close', 'category', )


class TaskForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super(TaskForm, self).__init__(*args, **kwargs)
        self.fields['manager'].choices = [(user.id, user.username) for user in \
                                          Group.objects.get(name='manager').user_set.all()]
        self.fields['manager'].choices.append(BLANK_CHOICE_DASH[0])
        self.fields['responsible'].choices = [(user.id, user.username) for user in \
                                              Group.objects.get(name='developer').user_set.all()]
        self.fields['responsible'].choices.append(BLANK_CHOICE_DASH[0])

    is_supervised = forms.ChoiceField(choices=(('N', u'Нет'), ('Y', u'Да'),), required=True, initial='N')
    urgent_important = forms.ChoiceField(required=True, choices=m.Task.URGENT_IMPORTANT_MATRIX, initial='D')

    class Meta:
        model = m.Task
        fields = ('name', 'descr', 'urgent_important', 'parent', 'date_open', 'start_date', \
                  'applicant', 'module', 'manager', \
                  'responsible', 'appoint_date', 'deadline', 'is_supervised', 'ready_date', 'decision', \
                  'proj', 'exe', 'closing_type', 'date_close', 'category', )

class TaskFormCustomer(ModelForm):
#is_supervised = forms.ChoiceField(choices=(('N','Нет'),('Y','Да'),), required=True, initial='N' )
    #date_open = forms.DateField(initial=date.today())
    class Meta:
        model = m.Task
        fields = ('name', 'descr', )
        
class TaskFormCustomerRank(ModelForm):
    rank = forms.ChoiceField(label=u'Оцените результат по Вашей заявке:', choices=m.Task.MARKS, required=True, widget=RadioSelect, initial=3)
    class Meta:
        model = m.Task
        fields = ('rank', )

applicants = []


class TaskSearchForm(Form):
    def __init__(self, *args, **kwargs):
        super(TaskSearchForm, self).__init__(*args, **kwargs)
        self.fields['applicant'].choices = [(user.id, user.username) for user in User.objects.all()]
        self.fields['applicant'].choices.append(BLANK_CHOICE_DASH[0])
        self.fields['manager'].choices = [(user.id, user.username) for user in \
                                          Group.objects.get(name='manager').user_set.all()]
        self.fields['manager'].choices.append(BLANK_CHOICE_DASH[0])
        self.fields['responsible'].choices = [(user.id, user.username) for user in \
                                              Group.objects.get(name='developer').user_set.all()]
        self.fields['responsible'].choices.append(BLANK_CHOICE_DASH[0])
        self.fields['module'].choices = [(module.id, module.name) for module in \
                                              m.Module.objects.all()]
        self.fields['module'].choices.append(BLANK_CHOICE_DASH[0])

    from_date_open = forms.DateField(label='Дата открытия с:', required=False)
    to_date_open = forms.DateField(label='Дата открытия по:', required=False)
    #eq_date_open = forms.BooleanField(label='Равно', required=False) # Checkbox
    name = forms.CharField(max_length=240, label='Предмет обращения', required=False)
    descr = forms.CharField(max_length=240, label='Текст обращения', required=False)
    decision = forms.CharField(max_length=240, label='Решение', required=False)
    applicant = forms.ChoiceField(label='Заявитель', required=False)
    manager = forms.ChoiceField(label='Назначил', required=False)
    responsible = forms.ChoiceField(label='Ответственный', required=False)
    module = forms.ChoiceField(label='Модуль', required=False)
    proj = forms.CharField(label='Путь к сборке', required=False)


class ChangePasswordForm(Form):
    old_password = forms.CharField(label='Введите старый пароль', widget=forms.PasswordInput)
    new_password = forms.CharField(label='Введите новый пароль', min_length=6, widget=forms.PasswordInput)


class TaskForm_save(forms.Form):
    """
    For Superusers only!!!
    Общая форма ред-я задачи без прикрепления файлов
    """
    id = forms.IntegerField(label='', widget=forms.widgets.HiddenInput, required=False, initial=None)
    name = forms.CharField(max_length=240, label="Предмет обращения")      # Краткое наименование
    descr = forms.CharField(widget=forms.Textarea, label="Текст обращения") # Описание
    date_open = forms.DateField(label='Открыто [дд.мм.гггг]', initial=date.today())
    start_date = forms.DateField(label='Принято в работу [дд.мм.гггг]', required=False, initial=date.today())
    applicant = forms.ModelChoiceField(label='Заявитель', queryset=User.objects.filter(is_active=True), required=False)
    module = forms.ModelChoiceField(label='Модуль', queryset=m.Module.objects.all(), required=False)
    manager = forms.ModelChoiceField(label='Назначил', queryset=Group.objects.get(name='manager'). \
        user_set.filter(is_active=True), required=False)
    # исполнитель
    responsible = forms.ModelChoiceField(label='Исполнитель', queryset=Group.objects.get(name='developer'). \
        user_set.filter(is_active=True), required=False)
    appoint_date = forms.DateField(label='Дата назначения [дд.мм.гггг]', required=False)
    # планируемый срок заершения
    deadline = forms.DateField(label='Завершить к [дд.мм.гггг]', required=False, widget=AdminDateWidget)
    # контрольное?
    is_supervised = forms.ChoiceField(label='Контрольное', choices=(('N', 'Нет'), ('Y', 'Да'),), required=True,
                                      initial='N')
    ready_date = forms.DateField(label='Готово [дд.мм.гггг]', required=False)
    decision = forms.CharField(widget=forms.Textarea, label="Решение", required=False)
    proj = forms.CharField(label='Путь к сборке', required=False)
    exe = forms.CharField(label='Путь к документации', required=False)
    # тип закрытия: выполнено или пусто, дату ставит манагер
    closing_type = forms.ChoiceField(label='Тип закрытия', choices=m.Task.CLOSING_TYPE, \
                                     required=False)
    date_close = forms.DateField(label='Закрыто [дд.мм.гггг]', required=False)


class SetFilterForm(forms.Form):
    """
    Форма редактирования, а также вкл-я и выключения фильтра задач
    
    Установка фильтра действует в течение сессии
    """
    pass


class ExecuteTaskForm(forms.Form):
    """
    Класс формы таска для программиста
    """
    class Meta:
        model = m.Task
        fields = ('ready_date', 'decision', 'proj', 'exe', )

#    id = forms.IntegerField(label='', widget=forms.widgets.HiddenInput, required=False, initial=None)
#    ready_date = forms.DateField(label='Дата готовности [дд.мм.гггг]', required=False)    
#    proj = forms.CharField(label='Путь к проекту', required=False)
#    exe = forms.CharField(label='Путь к исполняемому модулю', required=False)


class AppointTaskForm(forms.Form):
    """
    Класс формы для манагера -
    назначить исполнителя и срок выполнения  
    
    приложения и прочее показываются средствами шаблона
    """
    id = forms.IntegerField(label='', widget=forms.widgets.HiddenInput, required=False, initial=None)
    # name = forms.CharField(max_length=240, label="Предмет обращения")      # Краткое наименование
    # desc = forms.CharField(widget=forms.Textarea, label="Текст обращения") # Описание
    module = forms.ModelChoiceField(label='Модуль', queryset=m.Module.objects.all(), required=False)
    manager = forms.ModelChoiceField(label='Назначил', queryset=Group.objects.get(name='manager'). \
        user_set.filter(is_active=True), required=False)
    # исполнитель
    responsible = forms.ModelChoiceField(label='Исполнитель', queryset=Group.objects.get(name='developer'). \
        user_set.filter(is_active=True), required=False)
    # планируемый срок заершения
    deadline = forms.DateField(label='Завершить к [дд.мм.гггг]', required=False, widget=AdminDateWidget)
    # контрольное?
    is_supervised = forms.BooleanField(label='Контрольное', required=False, initial=False)
    closing_type = forms.ChoiceField(label='Тип закрытия', \
                                     choices=(BLANK_CHOICE_DASH[0], ('C', 'ВЫП'),), required=False)
    date_close = forms.DateField(label='Дата закрытия [дд.мм.гггг]', required=False)


class AddTaskForm(forms.Form):
    """
    Класс формы ввода заявки пользователем  
    """
    id = forms.IntegerField(label='', widget=forms.widgets.HiddenInput, required=False, initial=None)
    name = forms.CharField(max_length=240, label="Предмет обращения")      # Краткое наименование
    descr = forms.CharField(widget=forms.Textarea, label="Текст обращения") # Описание

#   перенесено в отдельную форму дляя р-ции отношения N-N :
#    attachment = forms.FileField(label="Файл", required=False) 

class AddFileForm(forms.Form):
    """ Класс формы добавления документов. 
    Перед формой выводит список уже прикреплённых документов,
    реализуемый списком объектов и шаблоном
    """
    attachment = forms.FileField(label=u"Файл", required=False)
    is_any_more = forms.BooleanField(label=u"Добавить ещё файл", required=False, initial=False)
    #    previous = forms.CharField(max_length=240, widget=forms.widgets.HiddenInput)
    task_id = forms.IntegerField(label='', widget=forms.widgets.HiddenInput)
    
class UserSearchForm(forms.Form):
    username = forms.CharField(max_length=30, label=u'Логин', required=False)
    
class EditUserForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super(EditUserForm, self).__init__(*args, **kwargs)
        self.action = '/edit_user/' + self.data['user_id'] + '/'
    user_id = forms.CharField(label='', widget=forms.widgets.HiddenInput)
    email = forms.CharField(label='Email', max_length=75)
    last_name = forms.CharField(label=u'Фамилия', max_length=30, required=False)
    first_name = forms.CharField(label=u'Имя', max_length=30, required=False)
    second_name = forms.CharField(label=u'Отчество', max_length=30, required=False)
    location = forms.CharField(label=u'Комната', max_length=30, required=False)
    phone = forms.CharField(label=u'Телефон', max_length=30, required=False)
    groups = forms.MultipleChoiceField(label='Роли', choices=[(grp.id, grp.name) for grp in Group.objects.all()])
    
class CreateUserForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super(CreateUserForm, self).__init__(*args, **kwargs)
        self.action = '/edit_user/'
    username = forms.CharField(label='Логин', max_length=30)
    password = forms.CharField(label='Пароль', max_length=30, widget=forms.widgets.PasswordInput)
    #email = forms.EmailField(label='Email')
    email = forms.CharField(label='Email')
    last_name = forms.CharField(label=u'Фамилия', max_length=30, required=False)
    first_name = forms.CharField(label=u'Имя', max_length=30, required=False)
    second_name = forms.CharField(label=u'Отчество', max_length=30, required=False)
    location = forms.CharField(label=u'Комната', max_length=30, required=False)
    phone = forms.CharField(label=u'Телефон', max_length=30, required=False)
    groups = forms.MultipleChoiceField(label='Роли', choices=[(grp.id, grp.name) for grp in Group.objects.all()])
    
    