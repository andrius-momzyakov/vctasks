# coding: UTF-8

from django.db import models
from django.contrib.auth.models import User, Group
from datetime import date
from django.db.models.fields import BLANK_CHOICE_DASH, BLANK_CHOICE_NONE
import settings
#from django.utils.translation import ugettext, ugettext_lazy as _

# Create your models here.

# 04.12.2012 
# - init of date_open fileld transferred to views.py 
# - added verbose_names for models' fields in english 
#

class IncorrectUserError(Exception):
    pass

class Person(models.Model):
    '''
    user's profile
    '''
    user = models.OneToOneField(User, verbose_name=u'Пользователь')
    second_name = models.CharField(verbose_name=u'Отчество' ,max_length=30, null=True, blank=True ) # отчество
    position = models.CharField(verbose_name=u'Должность',  max_length=50, null=True, blank=True) # должность
    #login = models.CharField(verbose_name=u'Логин', max_length=30, unique=True)  # = dbuser !!!
    location = models.CharField(verbose_name=u'Комната', max_length=30, null=True, blank=True) # адрес-комната
    phone = models.CharField(verbose_name=u'Телефон', max_length=30, null=True, blank=True) # телефон   

    def __unicode__(self):
        #u = User.objects.get(username=self.login)
        return u'<%s> %s %s %s - %s' % (self.user.username, self.user.first_name, \
                self.second_name, self.user.last_name, self.position)
    
    #class Meta:
      #unique_together = ('name', 'second_name', 'surname') # Если повторяются, 
      # использовать цифровой индекс с фамилией
      
class NotificationEvent(models.Model):
    '''
    '''
    YN_CHOICES = (('Y', u'ДА'), ('N',u'НЕТ'),)

    event_name = models.CharField(max_length=100, verbose_name=u'Имя события', unique=True)
# 20.12.2013    notify_initiator = models.CharField(max_length=1, verbose_name=u'Уведомить инициатора', choices=YN_CHOICES)
    notify_manager = models.CharField(max_length=1, verbose_name=u'Уведомить менеджера', choices=YN_CHOICES)
    notify_applicant = models.CharField(max_length=1, verbose_name=u'Уведомить заявителя', choices=YN_CHOICES)
    notify_developer = models.CharField(max_length=1, verbose_name=u'Уведомить ответственного', choices=YN_CHOICES)
    
    def __unicode__(self):
        return self.event_name
        
    
class GroupNotification(models.Model):
    '''
    '''
    event = models.ForeignKey(NotificationEvent, verbose_name=u'Событие')
    group = models.ForeignKey(Group, verbose_name=u'Группа')
    group_users = models.ManyToManyField(User, verbose_name=u'Пользователи группы') # члены группы, которых надо уведомить 
    
    def __unicode__(self):
        return self.group.name + ' on ' + self.event.event_name
        
class NotificationTemplate(models.Model):
    event = models.ForeignKey(NotificationEvent, verbose_name=u'Событие', null=True, blank=True)
#20.12.2013    initiator_subj = models.TextField(verbose_name=u'Предмет уведомления инициатора', null=True, blank=True)
#20.12.2013    initiator_body = models.TextField(verbose_name=u'Тело уведомления инициатора', null=True, blank=True)
    manager_subj = models.TextField(verbose_name=u'Предмет уведомления менеджера', null=True, blank=True)
    manager_body = models.TextField(verbose_name=u'Тело уведомления менеджера', null=True, blank=True)
    manager_body_html = models.TextField(verbose_name=u'Тело уведомления менеджера (html)', null=True, blank=True)
    developer_subj = models.TextField(verbose_name=u'Предмет уведомления исполнителя', null=True, blank=True)
    developer_body = models.TextField(verbose_name=u'Тело уведомления исполнителя', null=True, blank=True)
    developer_body_html = models.TextField(verbose_name=u'Тело уведомления исполнителя (html)', null=True, blank=True)
    customer_subj = models.TextField(verbose_name=u'Предмет уведомления заявителя', null=True, blank=True)
    customer_body = models.TextField(verbose_name=u'Тело уведомления заявителя', null=True, blank=True)
    customer_body_html = models.TextField(verbose_name=u'Тело уведомления заявителя (html)', null=True, blank=True)

    def __unicode__(self):
        return self.event.event_name

class GroupNotificationTemplate(models.Model):
    event = models.ForeignKey(NotificationEvent, verbose_name=u'Событие')
    group = models.ForeignKey(Group, verbose_name=u'Группа')
    group_subj = models.TextField(verbose_name=u'Предмет уведомления группы', null=True, blank=True)
    group_body = models.TextField(verbose_name=u'Тело уведомления группы', null=True, blank=True)
    group_body_html = models.TextField(verbose_name=u'Тело уведомления группы (html)', null=True, blank=True)

    def __unicode__(self):
        return self.group.name + ' on ' + self.event.event_name
      
class TaskCategory(models.Model):
    '''
    категории задач
    '''
    name = models.CharField(verbose_name='Имя категории', max_length=80)
    
    def __unicode__(self):
        return self.name

class Task(models.Model):
    '''
    
    '''
    YN_CHOICES = (('Y', u'ДА'), ('N',u'НЕТ'),)
    CLOSING_TYPE = (BLANK_CHOICE_DASH[0], ('C', u'ВЫП'),('D',u'ОТМЕНА'), ('P', u'ОТЛОЖ'), ) #
    # 03.02.2012
    URGENT_IMPORTANT_MATRIX = (('A', u'Важно и срочно'),('B',u'Важно'),('C',u'Срочно'),('D',u'Неважно и несрочно'),)
    MARKS = ((2, u'Неуд.'),(3, u'Удовл.'),(4, u'Хор.'),(5, u'Отл.'))
    
    name = models.CharField(verbose_name=u'Предмет', max_length=240)           # Краткое наименование
    # 20/02.2013 descr = models.TextField(verbose_name=u'Сообщение')                         # Описание
    descr = models.TextField(verbose_name=u'Сообщение', blank=True)                         # Описание
    date_open = models.DateField(verbose_name=u'Дата открытия [дд.мм.гггг]')   # Дата начала
    deadline = models.DateField(verbose_name=u'Срок [дд.мм.гггг]', blank=True, null=True)   # Срок
    is_supervised = models.CharField(verbose_name=u'Контрольное', max_length=1, default='N', choices=YN_CHOICES)  # Контрольное? 'Y' или 'N'
    date_close = models.DateField(verbose_name=u'Дата закрытия [дд.мм.гггг]', blank=True, null=True)   # дата закрытия
    appoint_date = models.DateField(verbose_name=u'Дата назначения [дд.мм.гггг]', blank=True, null=True) #дата назначения
    manager = models.ForeignKey(User, verbose_name=u'Менеджер', related_name='manager', blank=True, null=True) # , on_delete=models.PROTECT) 
    start_date = models.DateField(verbose_name=u'Принято в работу [дд.мм.гггг]', blank=True, null=True) # дата приёма девелопером в работу    
    responsible = models.ForeignKey(User, verbose_name=u'Ответственный разработчик', related_name='responsible', blank=True, null=True) # , on_delete=models.PROTECT)
    applicant = models.ForeignKey(User, verbose_name=u'Заявитель', related_name='applicant', blank=True, null=True) # Заявитель
    base = models.ManyToManyField('Doc', verbose_name=u'Прикреплённые документы', related_name='base', null=True)  # Основание (входящий док.)
    closing_type = models.CharField(verbose_name=u'Тип закрытия', max_length=1, choices=CLOSING_TYPE, blank=True, null=True) # "C"-выполнено "D"-прекращено "T"-перепоручено
    ready_date = models.DateField(verbose_name=u'Дата готовности [дд.мм.гггг]', blank=True, null=True) # дата готовности заявки, устанавливаемая девелопером
    module = models.ForeignKey('Module', verbose_name=u'Модуль', null=True, blank=True) # ссылка на модуль или тип заявки
    proj = models.CharField(max_length=100, verbose_name=u'Путь к сборке', null=True, blank=True) # путь к проекту - для разовых
    exe = models.CharField(max_length=100, verbose_name=u'Путь к документации', null=True, blank=True) # путь к exe - для разовых
    decision = models.TextField(verbose_name=u'Решение', blank=True, null=True) #опциональное поле для описания решения проблемы или ответа на вопрос
    #message_counter = models.IntegerField(default=0)  # Счётчик сообщений - в формах не отражается
    # 03.02.2013 Eisenhower's matrix
    urgent_important = models.CharField(verbose_name=u'Важно-срочно', max_length=1, default='D', choices=URGENT_IMPORTANT_MATRIX)
    # 03.02.2013
    category = models.ManyToManyField('TaskCategory', verbose_name='Категории', null=True, blank=True)
    # 11.02.2013 Род. задача
    parent = models.ForeignKey('self', verbose_name='Головная задача', blank=True, null=True)
    # Закрывать при закрытии всех дочерних задач
    # Добавлять дочерние задачи можно только для незакрытых и не отменённых задач
    # AMOMZYAKOV 23.12.2013 
    #auto_close = models.CharField(verbose_name=u'Автозакрытие', max_length=1, choices=YN_CHOICES, blank=True, null=True)
    rank = models.IntegerField(max_length=1, verbose_name=u'Оценка', null=True) #, choices=MARKS)
    rank_date = models.DateField(null=True, blank=True)
    #end 23.12.2013
    rank_comment = models.TextField(verbose_name=u'Особые отметки', null=True, blank=True)
    
    def _is_supervised(self):
        if self.is_supervised=='Y':
            return True
        return False
    def is_supervised_name(self):
        if self.is_supervised=='Y':
            return u'ДА'
        return u'НЕТ'     
    def get_status_name(self):
        return self.get_status()[1]
    def get_status_short(self):
        return self.get_status()[0]
    def get_status(self):
        """
        возвращает:
        new - новая
        set - назначено
        open - в обработке
        ready - ожидает закрытия - тип закр есть, даты -нет
        closed - закрыта
        pending - отложена
        """
        close_type = dict(self.CLOSING_TYPE)
        if self.closing_type=='P':
            return ('pending', u'ОТЛОЖЕНА')
        if self.closing_type=='D':
            return ('discard', u'ОТМЕНА')
        if self.responsible is None:
            return ('new', u'НОВАЯ',) # независимо от дат
        # иначе - если исполнитель назначен
        if self.date_close or self.closing_type=='C':
            #close_type_name = ''
            #try:
            #    close_type_name = close_type[self.closing_type] 
            #except KeyError:
            #    pass
            #return ('closed', u'ЗАКРЫТА: ' + close_type_name.decode('utf-8'))
            #return ('closed', u'ЗАКРЫТА: ' + close_type_name)
            return ('closed', u'ЗАКРЫТА')
        # иначе - если не указана дата закрытия
        if self.ready_date:
            # и девелопером указана дата готовности задачи
            return ('ready', u'ПРОВЕРКА')  
        # иначе - если не указана дата готовности
        if self.start_date:
            # и указана дата приёма девелопером в работу
            return ('open', u'В ОБРАБОТКЕ')
        # иначе - если не указана дата приёма девелопером в работу
        if self.appoint_date:
            # и указана дата назначения задачи
            return ('set', u'НАЗНАЧЕНО')
        # если указан исполнитель и не указаны даты
        return ('set', u'НАЗНАЧЕНО')
    def is_new(self):
        st, status = self.get_status()
        if st=='new':
            return True
        return False
    def __unicode__(self):
        return '<ID:' + str(self.id) + '>' + self.name
    def get_user_name(self, user_type):
        """
        user_type одно из 'applicant', 'manager', 'developer'
        """
        d = self.get_user_details(user_type)
        if d[0]:
            return d[2] + ' [' + d[1] + ']' 
        return d[2]
    def get_applicant_name(self):
        return self.get_user_name('applicant')
    def get_manager_name(self):
        return self.get_user_name('manager')
    def get_developer_name(self):
        return self.get_user_name('developer')
    def get_user_details(self, user_type):
        """
        user_type одно из 'applicant', 'manager', 'developer'
        """
        if user_type=='applicant':
            if self.applicant: #обязательное
                return self.prepare_user_details(self.applicant)
        if user_type=='manager':
            if self.manager:
                return self.prepare_user_details(self.manager)
            return [None, '', u'НЕ ВЫБРАН']
        if user_type=='developer':
            if self.responsible:
                return self.prepare_user_details(self.responsible)
            return [None, '', u'НЕ НАЗНАЧЕН']
        #raise IncorrectUserError()
    def prepare_user_details(self, puser):
        """
        puser - экземпляр классу User!
        """
        if puser is None:
            return [None, '', u'НЕ НАЗНАЧЕН']
        #if Person.objects.filter(login=puser.username):
        if Person.objects.filter(user=puser):
            return [puser.id, \
                    puser.username, \
                    puser.first_name + ' ' +\
                    Person.objects.get(user=puser).second_name[0] + '. ' + \
                    puser.last_name]
        else:
            return [puser.id, \
                    puser.username, \
                    puser.first_name + ' ' +\
                    puser.last_name]
    @staticmethod   
    def dmy_date(date):
        if date:
            return date.strftime("%d.%m.%Y")
        return u'н.д.'
    def dmy_date_open(self):
        return Task.dmy_date(self.date_open)
    def dmy_deadline(self):
        return Task.dmy_date(self.deadline)
    def dmy_date_close(self):
        return Task.dmy_date(self.date_close)    
    def dmy_appoint_date(self):
        return Task.dmy_date(self.appoint_date)
    def dmy_start_date(self):
        return Task.dmy_date(self.start_date)
    def dmy_ready_date(self):
        return Task.dmy_date(self.ready_date)
    def get_urgent_important(self):
        return [val for key, val in dict(self.URGENT_IMPORTANT_MATRIX).iteritems() if key==self.urgent_important][0]
    def get_children(self):
        return Task.objects.filter(parent=self)
        
    @staticmethod    
    def notify(event, event_object, group=None):
        # процедура рассылки уведомлений
        try:
            event = NotificationEvent.objects.get(event_name=event)
        except:
            return
        
        #obj_as_dict = event_object.__dict__
        # prepare notifications to roles in a task
        notifications = [] # элемент - список: список адресов, предмет, тело
        from django.contrib.sites.models import Site
        ctx = {'object':event_object.__dict__, 'manager':event_object.get_manager_name(),\
               'responsible':event_object.get_developer_name(), 'applicant':event_object.get_applicant_name(),\
               'site':Site.objects.get(pk=settings.SITE_ID)}
        
        from django.template import Template, Context
        ''' 20.12.2013
        if event.notify_initiator=='Y':
            try:
                notifications.append([[event_object.applicant.email],\
                                   Template(NotificationTemplate.objects.get(event=event).initiator_subj).\
                                      render(Context(ctx)),\
                                   Template(NotificationTemplate.objects.get(event=event).initiator_body).\
                                      render(Context(ctx))])
            except:
                pass
        '''
        if event.notify_manager=='Y':
            try:
                notifications.append([[event_object.manager.email],\
                                   Template(NotificationTemplate.objects.get(event=event).manager_subj).\
                                      render(Context(ctx)),\
                                   Template(NotificationTemplate.objects.get(event=event).manager_body).\
                                      render(Context(ctx))])
                if len(NotificationTemplate.objects.get(event=event).manager_body_html)!=0:
                    notifications[ len(notifications) - 1 ].append(Template(NotificationTemplate.objects.get(event=event).manager_body_html).\
                                      render(Context(ctx)))
                else:
                    notifications[ len(notifications) - 1 ].append(None)
            except NotificationTemplate.DoesNotExist:
                pass
        if event.notify_applicant=='Y':
            try:
                notifications.append([[event_object.applicant.email],\
                                   Template(NotificationTemplate.objects.get(event=event).customer_subj).\
                                      render(Context(ctx)),\
                                   Template(NotificationTemplate.objects.get(event=event).customer_body).\
                                      render(Context(ctx))])
                if len(NotificationTemplate.objects.get(event=event).customer_body_html)!=0: # НЕ РАБОТАЕТ is None с полями модели!!!
                    notifications[ len(notifications) - 1 ].append(Template(NotificationTemplate.objects.get(event=event).customer_body_html).\
                                      render(Context(ctx)))
                else:
                    notifications[ len(notifications) - 1 ].append(None)
            except NotificationTemplate.DoesNotExist:
                pass
        if event.notify_developer=='Y':
            try:
                notifications.append([[event_object.responsible.email],\
                                   Template(NotificationTemplate.objects.get(event=event).developer_subj).\
                                      render(Context(ctx)),\
                                   Template(NotificationTemplate.objects.get(event=event).developer_body).\
                                      render(Context(ctx))])
                if len(NotificationTemplate.objects.get(event=event).developer_body_html)!=0:
                    notifications[ len(notifications) - 1 ].append(Template(NotificationTemplate.objects.get(event=event).developer_body_html).\
                                      render(Context(ctx)))
                else:
                    notifications[ len(notifications) - 1 ].append(None)
            except NotificationTemplate.DoesNotExist:
                pass
        
        # prepare notifications to groups

        for group in GroupNotification.objects.filter(event=event):
            recipients = []
            if group.group_users:
                # в список рассылки включаем только указанных в списке
                for user in group.group_users.all():
                    recipients.append(user.email)
            else:
                # если список получателей не задан явно, то рассылаем всей группе
                for user in group.user_set.all():
                    recipients.append(user.email)
            try:
                notifications.append([recipients,\
                                 Template(GroupNotificationTemplate.objects.get(event=event).group_subj).\
                                     render(Context(ctx)),\
                                 Template(GroupNotificationTemplate.objects.get(event=event).group_body).\
                                     render(Context(ctx))]) # TODO - prep fields for html templates for groups
                if len(GroupNotificationTemplate.objects.get(event=event).group_body_html)!=0:
                    notifications[ len(notifications) - 1 ].append(Template(GroupNotificationTemplate.objects.get(event=event).group_body_html).\
                                      render(Context(ctx)))
                else:
                    notifications[ len(notifications) - 1 ].append(None)
            except GroupNotificationTemplate.DoesNotExist:
                pass
        # групповая рассылка
        # sending notifications to task roles & groups
        from django.core.mail import send_mail
        for notification in notifications:
            try:
                '''
                send_mail(notification[1],\
                          notification[2],\
                          settings.DEFAULT_FROM_EMAIL,\
                          notification[0], fail_silently=False)
                '''

                from django.core.mail import EmailMultiAlternatives

                msg=EmailMultiAlternatives(notification[1], notification[2], settings.DEFAULT_FROM_EMAIL, notification[0])
                if not notification[3] is None:
                    msg.attach_alternative(notification[3], "text/html")
                msg.send()
            except:
                pass

    def get_mark_name(self):
        if self.rank:
            return self.MARKS[self.rank-2][ 1]
                    
        
class Doc(models.Model):
    DOC_DIRECT = (('I', 'ВХ'), ('O', 'ИСХ'), )
    
    direction = models.CharField(max_length=1, default="I", choices=DOC_DIRECT) # Входящий или исходящий
    reg_tag = models.CharField(max_length=30, default='', null=True, blank=True) # рег номер и дата ВЦ, дата - обязательна
    reg_date = models.DateField(default=date.today())
    ext_reg_tag = models.CharField(max_length=30, null=True, blank=True) # рег номер и дата канцелярии, необязательны
    ext_reg_date = models.DateField(blank=True, null=True) 
    file = models.FileField(upload_to=settings.UPLOAD_TO) # Прикреплённый файл

    def __unicode__(self):
        if self.reg_tag!=None: 
            tmp = self.reg_tag + ' от ' + self.reg_date.strftime("%d/%m/%Y")
        else:
            tmp = 'от ' + self.reg_date.strftime("%d/%m/%Y")  
        if (self.ext_reg_date==None):
            return u'%s' % tmp
        else:
            return u'%s' % (tmp + ' (' + 
                self.ext_reg_tag + ' от ' +  
                self.ext_reg_date.strftime("%d/%m/%Y") + ')')
    def quote_file(self):
        """
        переводит имя файла в предст-е ascii
        """
        from urllib import quote
        #return unicode(str(self.file))
        return quote(unicode(self.file).encode('utf-8')) 
        #urllib.quote(unicode(d.file).encode('utf-8'))
        

class Module(models.Model):
    """
    Прог. модуль или тип заявки
    """
    MODULE_STATUS = (('C', 'ТЕК'), ('A', 'АРХИВ'), )
    
    name = models.CharField(max_length=100) # название модуля
    code = models.CharField(max_length=30) # код модуля
    status =  models.CharField(max_length=1, default='C', choices=MODULE_STATUS) # статус модуля
    comment = models.TextField(null=True, blank=True) # комментарий к статусу
    parent = models.ForeignKey('self', null=True, blank=True) # головной модуль
    dev = models.ManyToManyField('Person', related_name='dev')
#    proj = models.FilePathField(path=u"\\\\vc-host\\voda\\ISHVFP6", \
#                                recursive=True, null=True, blank=True) # путь к проекту
    proj = models.CharField(max_length=100, null=True, blank=True) # путь к проекту
#    exe = models.FilePathField(path=u"\\\\vc-host\\VFP_EXE", \
#                               recursive=True, null=True, blank=True) # путь к exe
    exe = models.CharField(max_length=100, null=True, blank=True) # путь к exe
    
    def __unicode__(self):
      return self.code + '_' + self.name
      
class Message(models.Model):
    IS_QUERY_YN = (('Y', 'Запрос'), ('N', 'Ответ'), )
    
    ordnum = models.IntegerField() # порядковый номер сообщения
    body = models.CharField(max_length=4000) # тело сообщения
    dbuser = models.CharField(max_length=30) # логин пользователя БД
    task = models.ForeignKey(Task)
    type = models.CharField(max_length=1, default='Y', choices=IS_QUERY_YN)
    
    def __init__(self, ptask):
      self.task = ptask
      if ptask.message_counter == 0:
        self.type = 'Y'
      else:
        if Message.objects.get(pk=ptask.id, ordnum=ptask.message_counter) == 'Y':
          self.type = 'N'
        else: 
          self.type = 'Y'
      ptask.message_counter += 1
      self.ordnum = ptask.message_counter
       
    class Meta:
      unique_together=("task","ordnum",)
      
    


          