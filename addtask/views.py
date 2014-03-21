# -*- coding: utf-8 -*-
# Create your views here.
from django.http import HttpResponseRedirect
from django.http import HttpResponse

#from django import forms
from django.db.models.fields import BLANK_CHOICE_DASH, BLANK_CHOICE_NONE
import models as m
#from m import Doc, Task
from django.contrib import auth
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User, Group
from django.shortcuts import render_to_response, get_object_or_404
from django.shortcuts import redirect
from django.core.context_processors import csrf
from django.template import RequestContext
from django.views.generic.list_detail import object_list, object_detail
from django.template import Context, Template
from django.contrib.admin.widgets import AdminDateWidget

# для фильтра в списке задач и даты в шапке
from vctasks.util import CurDate, FilterIndicator
from django.core.urlresolvers import reverse

from datetime import date
from django.core.files import File
from django.core.servers.basehttp import FileWrapper
from vctasks.addtask.forms import SetFilterForm, ExecuteTaskForm, AppointTaskForm, AddTaskForm, \
    AddFileForm, TaskForm, TaskFormManager, TaskFormCustomer, UserSearchForm, \
    TaskSearchForm, ChangePasswordForm, TaskFormCustomerRank 
from django.db.models import Q

import settings

from vctasks.secutil import get_task, get_task_filtered, get_filtered_tasklist, InvalidTaskId, TaskAccessDenied, TaskNotExists

# 04.12.2012 - перенос инициализации даты откр-я из models во views

@login_required
def find_task(request):
    if request.method == 'POST':
        if request.POST['id']:
            try:
                task = get_task_filtered(request.user, request.POST['id'])
            except (InvalidTaskId):
                return HttpResponse(u'Неверный ID. Заявка № ' + request.POST['id'] + u' не найдена.')
            except (TaskNotExists):
                return HttpResponse(u'Не существует Заявки. Заявка № ' + request.POST['id'] + u' не найдена.')
            except TaskAccessDenied:
                return HttpResponse(u'Недостаточно прав для открытия заявки.')
            return redirect('/taskdetail/' + request.POST['id'] + '/')
        return HttpResponse(u'Номер заявки не задан.')
    return HttpResponse(u'Номер заявки не задан.')


@login_required
def serve_base_file(request):
    """
    Выполняет download файла, имя (URL) которого передано через параметр 'fname'
    запросом GET
    
    Файл загружается, если:
    1. или текущий юзер является манагером либо заявителем либо исполнителем по
    соотв. таскам
    """
    # Выбираем имя файла
    fname = ''
    if request.method == 'GET':
        fname = request.GET.get('fname')
    else:
        return HttpResponse(u'Неверно передано имя файла.')
    if fname == '':
        return HttpResponse(u'Неверно передано имя файла.')
    docs = m.Doc.objects.filter(file=fname)
    if not docs:
        return HttpResponse(u'Указанный файл не существует.')
        # Проверка уникальности документа
    if len(docs) > 1:
        return HttpResponse(u'Переданному имени соответствует более одного файла.\n Загрузка невозможна.')
        # выбираем документ в виде документа а не в виде списка
    doc = m.Doc.objects.get(file=fname)
    # выбираем связанные задачи
    if not get_filtered_tasklist(request.user, doc):
        return HttpResponse(u'Недостаточно прав для открытия этого документа.')
        # определяем строгий mime-type файла
    import mimetypes

    ctype = mimetypes.guess_type(fname)
    f = open(settings.MEDIA_ROOT + fname, 'rb')
    data = FileWrapper(f)
    response = HttpResponse(data, content_type=ctype)
    import urllib

    response['Content-Disposition'] = 'attachment; filename=' + urllib.quote(fname.encode('utf-8'))
    return response


def start_page(request):
    return redirect('/home/')


@login_required
def execute_task_form(request, ptask_id=None):
    """
    форма отражения процесса исполнения программистом
    """
    if not request.user.groups.filter(name='developer'):
        HttpResponse(u'Недостаточно прав для данной операции.')
        # проверяем ptask_id
    if ptask_id is None:
        # если не передан POSTом, проверим в GET
        if request.method == 'GET':
            task_id = int(request.GET.get('task_id'))
            if task_id is None:
                return HttpResponse(u'Не задан task_id.')
        else:
        #return HttpResponse('ID: ' + request.POST['id'])
            task_id = int(request.POST['id'])
            if task_id is None:
                return HttpResponse(u'Не задан task_id.')
    else:
        task_id = ptask_id
    try:
        task = m.Task.objects.get(pk=task_id)
    except:
        return HttpResponse(u'Указан неверный task_id.')
    c = {}
    c1 = {}
    docs = ()
    form = {}
    c.update(csrf(request))
    if request.method == 'POST':
        form = ExecuteTaskForm(request.POST)
        if form.is_valid():
            task.id = task_id
            task.proj = form.cleaned_data['proj']
            task.exe = form.cleaned_data['exe']
            task.closing_type = form.cleaned_data['closing_type']
            task.ready_date = form.cleaned_data['ready_date']
            if not task.start_date and task.responsible:
                task.start_date = date.today()
            task.save()
        return redirect('/taskdetail/' + str(task_id) + '/?view=yes')
    else:
        form = ExecuteTaskForm({'id': task_id,
                                'ready_date': task.ready_date,
                                'decision': task.decision,
                                'proj': task.proj,
                                'exe': task.exe,
        })
        docs = m.Task.objects.get(pk=task_id).base.all()
        c1.update(form=form, docs=docs, task_id=task_id, curdate=CurDate())
        return render_to_response('edit_task.html', c1, \
                                  context_instance=RequestContext(request, c))


@login_required
def appoint_task_form(request, ptask_id=None):
    """
    форма манагера для назначения задачи исполнителю
    """
    if not request.user.groups.filter(name='manager'):
        HttpResponse(u'Недостаточно прав для данной операции.')
        # проверяем ptask_id
    if ptask_id is None:
        # если не передан POSTом, проверим в GET
        if request.method == 'GET':
            task_id = int(request.GET.get('task_id'))
            if task_id is None:
                return HttpResponse(u'Не задан task_id.')
        else:
            task_id = int(request.POST['id'])
            if task_id is None:
                return HttpResponse(u'Не задан task_id.')
    else:
        task_id = ptask_id
    try:
        task = get_task(task_id)
    except:
        return HttpResponse(u'Указан неверный task_id.')
    c = {}  # контекст запроса
    c1 = {} # доп. контекст  для шаблона
    docs = () # список прикрепл. док-тов
    form = {} # форма
    # инициализируем task
    c.update(csrf(request))
    if request.method == 'POST':
        form = AppointTaskForm(request.POST)
        if form.is_valid():
            #return HttpResponse(form.cleaned_data['is_supervised' ])
            old_responsible = task.responsible
            task.id = task_id
            task.module = form.cleaned_data['module']
            task.manager = form.cleaned_data['manager']
            task.responsible = form.cleaned_data['responsible']
            task.date_close = form.cleaned_data['date_close']
            task.closing_type = form.cleaned_data['closing_type']
            if not task.responsible:
                # если отсутствует ответственный чистим дату назначения
                # и остальные
                task.appoint_date = None
                task.start_date = None
                task.ready_date = None
                task.date_close = None
                task.closing_type = None
            elif task.responsible != old_responsible:
                # если изменен ответственный, меняется дата назначения
                task.appoint_date = date.today()
                # и чистятся вехи
                task.start_date = None
                task.ready_date = None
                task.date_close = None
                task.closing_type = None
            task.deadline = form.cleaned_data['deadline']
            if form.cleaned_data['is_supervised'] == True:
                task.is_supervised = 'Y'
            else:
                task.is_supervised = 'N'
            task.save()
            c1.update(task_id=task_id, curdate=CurDate())
            #            return render_to_response('task_registered.html', c1, \
            #                                      context_instance=RequestContext(request, c))
            # если манагер является девелопером,
            # показываем ему форму завершения заявки девелопера
            if request.user.groups.filter(name='developer'):
                return redirect('/executetask/?task_id=' + str(task_id))
            return redirect('/taskdetail/' + str(task_id) + '/?view=yes')
        else:
            return HttpResponse('Введены неверные данные.')
    else:
    # метод GET - открыта заведенная, но еще не назначенная заявка.
        # форма без заявки не может быть открыта.
        ffields = {'id': task_id, 'deadline': task.deadline, 'is_supervised': task._is_supervised(), \
                   'date_close': task.date_close, 'closing_type': task.closing_type}
        # инициализируем поля ModelChoiceField
        if task.module:
            ffields.update(module=task.module.id)
        if task.manager:
            ffields.update(manager=task.manager.id)
        else:
            from django.db.models import Count

            if Group.objects.get(name='manager').user_set.all(). \
                aggregate(Count('username'))['username__count'] == 1:
                ffields.update(manager=Group.objects.get(name='manager').user_set.all()[0])
        if task.responsible:
            ffields.update(responsible=task.responsible.id)
        form = AppointTaskForm(ffields)
        docs = m.Task.objects.get(pk=task_id).base.all()
        c1.update(form=form, docs=docs, task_id=task_id, curdate=CurDate())
        #return HttpResponse('GET:'+ str(task_id))
    return render_to_response('appointtask.html', c1, \
                              context_instance=RequestContext(request, c))


@login_required
def add_file_form(request, ptask_id=None):
    """
    форма прикрепления 0 или N файлов к таску
    """
    # проверяем ptask_id
    c = {}
    c1 = {}
    docs = ()
    form = {}
    c.update(csrf(request))
    if request.method == 'POST':
        form = AddFileForm(request.POST, request.FILES)
        if request.POST['task_id']:
            task_id = int(request.POST['task_id'])
        else:
            return HttpResponse(u'Не указан task_id.')
        if form.is_valid():
            task = m.Task.objects.get(pk=task_id)
            if request.FILES:
                # формируем контекст пркрепл. документа
                # сохраняем новый прикрепл. файл
                doc = m.Doc(file=request.FILES['attachment'])
                doc.save()
                # привязываем документ к таску
                task.base.add(doc)
            if form.cleaned_data['is_any_more'] == True:
                # формируем список уже сохраненных документов
                docs = task.base.all()
                # формируем контекст и страницу с формой для след. файла
                c1.update(form=form, docs=docs, task_id=form.cleaned_data['task_id'], \
                          curdate=CurDate())
                return render_to_response('addfile4task.html', c1, \
                                          context_instance=RequestContext(request, c))
                # если больше не требуется прикреплять,
            # манагера переводим на краткую страницу назначения исполнителя
            # методой GET
            if request.user.is_superuser or \
                    request.user.groups.filter(name="manager"):
                #return redirect('/appointtask/?task_id=' + str(task_id) )
                c1.update(task_id=form.cleaned_data['task_id'], curdate=CurDate())
                return redirect('/taskdetail/' + str(task_id) + '/?view=yes')
                # девелоперам, не являющимся манагерами,
            # показываем их форму завершения заявки
            if request.user.groups.filter(name="developer"):
                return redirect('/executetask/?task_id=' + str(task_id))
                # юзерам, которые не манагеры и не девелоперы, показываем страничку
            # подтверждения заявки
            c1.update(task_id=form.cleaned_data['task_id'], curdate=CurDate())
            return redirect('/taskdetail/' + str(task_id) + '/?view=yes')
    else:
    # метод GET - новая заявка, новая форма
        task_id = int(request.GET.get('task_id', '-1'))
        if task_id != -1:
            form = AddFileForm({'task_id': task_id})
        else:
            form = AddFileForm()
        docs = m.Task.objects.get(pk=task_id).base.all()
        c1.update(form=form, docs=docs, task_id=task_id, curdate=CurDate())
    return render_to_response('addfile4task.html', c1, \
                              context_instance=RequestContext(request, c))


@login_required
def delete_file(request, ptask_id, pdoc_id):
    """
    удаление документа из формы прикрепления и обновление формы прикрепления
    оба доп. параметра обязательны
    """
    doc = m.Doc.objects.get(pk=pdoc_id).delete()
    task = m.Task.objects.get(pk=ptask_id)
    return redirect('/addfile/?' + 'task_id=' + str(task.id))


@login_required
def delete_task(request, ptask_id):
    """
    удаление неназначенного таска заявителем
    """
    pass


@login_required
def add_task_form(request, ptask_id=None):
    """
    Вызов формы ввода заявки
    
    если задан ptask_id, то форма открывается на ред-е
    """
    # проверяем ptask_id
    if ptask_id:
        try:
            x = int(ptask_id)
        except ValueError:
            pass
    c = {}
    c.update(csrf(request))
    if request.method == "POST":
        if request.user.is_superuser: # могут смотреть и менять всё
            return edit_task(request, ptask_id)
        if request.user.groups.filter(name="manager"): # могут смотреть и менять всё
        # кроме ссылки на себя
            return edit_task(request, ptask_id, role='manager')
            # иначе - если не манагер
        if request.user.groups.filter(name="customer"):
            return edit_task(request, ptask_id, role='customer')
        form = AddTaskForm(request.POST)
        if form.is_valid():
            task = m.Task(id=form.cleaned_data['id'], \
                          name=form.cleaned_data['name'], \
                          descr=form.cleaned_data['desc'])
            task.applicant = User.objects.get(username=request.user.username)
            task.save()
            # переход на форму прикрепления файлов
            return redirect('/addfile/?' + 'task_id=' + str(task.id))
    else:
        # если новая заявка иль возврат из формы прикрепления докуметов,
        # то открываем форму на редактирование
        if ptask_id:
            task = None
            try:
                task = get_task_filtered(request.user, ptask_id)
            except (InvalidTaskId):
                return HttpResponse(u'Неверный ID. Заявка № ' + request.POST['id'] + u' не найдена.')
            except (TaskNotExists):
                return HttpResponse(u'Не существует Заявки. Заявка № ' + request.POST['id'] + u' не найдена.')
            except TaskAccessDenied:
                return HttpResponse(u'Недостаточно прав для открытия заявки.')
            if request.user.is_superuser:
                return edit_task(request, ptask_id)
            if request.user.groups.filter(name="manager"): # могут смотреть и менять всё
                return edit_task(request, ptask_id, role='manager')
            if request.user.groups.filter(name="customer"):
                return edit_task(request, ptask_id, role='customer')
            form = AddTaskForm({'id': task.id, 'name': task.name, 'descr': task.descr})
        else:
            if request.user.is_superuser:
                return edit_task(request, ptask_id)
            if request.user.groups.filter(name="manager"): # могут смотреть и менять всё
                return edit_task(request, ptask_id, role='manager')
            if request.user.groups.filter(name="customer"):
                return edit_task(request, ptask_id, role='customer')
            form = AddTaskForm()
    return render_to_response('addtask4user.html', {'form': form, 'curdate': CurDate()}, \
                              context_instance=RequestContext(request, c))


@login_required
def common_tasklist(request, page_number=None):
    """
    Список задач для всех пользователей
    p_qs - query set, передаваемый из обработчика формы фильтра
    """
    # проверяем, передан ли требуемый статус
    status = None
    p_where = None

    import urllib
    if request.method == 'GET':
        if request.GET.get('status'):
            status = request.GET.get('status')
        if request.GET.get('p_where'):
            p_where = urllib.quote(request.GET.get('p_where').encode('utf-8')) #NEW

    # ищем статус и page_number в куки
    if not status:
        if request.COOKIES.has_key('status'):
            status = request.COOKIES['status']
            if status == 'filter':
                p_where = urllib.quote(request.COOKIES['p_where'].encode('utf-8')) #NEW

    if not p_where and status == 'filter':
        status = None

    if p_where and status != 'filter':
        p_where = None

    c = {};
    all_cols = False
    template_file = "common_tasklist.html"
    #Получение номера страницы#           
    if not page_number:
        redirect_url = '/tasklist/1/'
        connector = '?'
        if request.GET.get('applicant'):
            redirect_url = redirect_url + connector + 'applicant=' + request.GET.get('applicant')
            connector = '&'
        if request.GET.get('responsible'):
            redirect_url = redirect_url + connector + 'responsible=' + request.GET.get('responsible')
            connector = '&'
        if status:
            if status != 'filter':
                redirect_url = redirect_url + connector + 'status=' + status
                connector = '&'
            if status == 'filter' and p_where:
                import urllib
                #redirect_url = redirect_url.encode('utf-8') + connector.encode('utf-8') + u'status=' + status.encode('utf-8') + u'&p_where=' + urllib.unquote(p_where).encode('utf-8')
                
                #NEW
                #return HttpResponse( redirect_url.encode('utf-8') + connector.encode('utf-8') + 'status=' + status.encode('utf-8') + '&p_where=' + urllib.unquote(p_where))
                return redirect(redirect_url.encode('utf-8') + connector.encode('utf-8') + 'status=' + status.encode('utf-8') + '&p_where=' + urllib.unquote(p_where))
        '''
        else:
            redirect_url = '/tasklist/1/'
            if request.GET.get('applicant'):
                redirect_url = redirect_url + '?applicant=' + request.GET.get('applicant')
            if request.GET.get('responsible'):
                redirect_url = redirect_url + '?responsible=' + request.GET.get('responsible')	    
        '''
        #NEW
        #return HttpResponse(redirect_url)
        return redirect(redirect_url)

        p = 1
    else:
        try:
            p = int(page_number)
        except ValueError:
            p = 1

    # применяем филтер юзера
    p_qs = None
    if status == 'filter' and p_where:
        #NEW
        p_where_qry = urllib.unquote(p_where)
        #pairs = p_where_qry.split(urllib.quote('|'.encode('utf-8')))
        pairs = p_where_qry.split('|')
        params = []
        search_string = '1=1'
        #return HttpResponse(pairs[0])
        for item, value in [cond.split('=') for cond in pairs]:
            import re

            if re.search('_like', item):
                item = item.split('_')[0]
                search_string += " and upper(" + item + ") like %s"
                upper_value = value.decode('utf-8').upper() # NEW
                params.append(upper_value)
                #return HttpResponse('ITEM=' + item + ' VALUE=' + upper_value)
            else:
                if item in ('manager', 'applicant', 'responsible', 'module'):
                    search_string += " and " + item + "_id=" + value
                if item == 'from_date_open':
                    search_string += " and date_open>=DATE %s"
                    params.append(value)
                if item == 'to_date_open':
                    search_string += " and date_open<=DATE %s"
                    params.append(value)
            for i in range(len(params)):
                if params[i][:1] != '%':
                    params[i] = '%' + params[i]
                if params[i][len(params[i]) - 1:] != '%':
                    params[i] += '%'
        p_qs = m.Task.objects.extra(where=[search_string], params=params)

        if not p_qs:
            return redirect('/task_notfound/')

    # формирование QuerySet и контекста
    c.update(all_cols=True)
    qs = [];
    status_name = u' - ВСЕ'
    if status == 'filter':
        ls = list(set(p_qs).intersection(set(get_filtered_tasklist(request.user))))
        qs = m.Task.objects.filter(pk__in=[li.id for li in ls]).order_by('-id') # lambda?
        status_name = u' - Фильтр задан пользователем'

    elif status == 'new':
        qs = get_filtered_tasklist(request.user).filter(responsible__isnull=True).exclude(closing_type='P')
        status_name = u' - НОВЫЕ'

    elif status == 'not_open':
        #return HttpResponse('>'+status+'<')
        qs = get_filtered_tasklist(request.user).filter(date_close__isnull=True, ready_date__isnull=True,
                                                        start_date__isnull=True).exclude(closing_type='P')
        status_name = u' - ВСЕ ЕЩЁ НЕ В ОБРАБОТКЕ'

    elif status == 'not_ready':
        #return HttpResponse('>'+status+'<')
        qs = get_filtered_tasklist(request.user).filter(date_close__isnull=True, ready_date__isnull=True).exclude(
            closing_type='P')
        status_name = u' - ВСЕ ЕЩЁ НЕ ГОТОВЫЕ'

    elif status == 'not_closed':
        #return HttpResponse('>'+status+'<')
        qs = get_filtered_tasklist(request.user).filter(date_close__isnull=True).exclude(closing_type='P')
        status_name = u' - ВСЕ ЕЩЁ НЕ ЗАКРЫТЫЕ'

    elif status == 'closed':
        qs = get_filtered_tasklist(request.user). \
            filter(responsible__isnull=False, date_close__isnull=False).exclude(closing_type='P')
        status_name = u' - ЗАКРЫТЫЕ'
    elif status == 'ready':
        qs = get_filtered_tasklist(request.user). \
            filter(responsible__isnull=False, date_close__isnull=True, ready_date__isnull=False).exclude(
            closing_type='P')
        status_name = u' - ГОТОВЫЕ'
    elif status == 'open':
        qs = get_filtered_tasklist(request.user). \
            filter(responsible__isnull=False, date_close__isnull=True, \
                   ready_date__isnull=True, start_date__isnull=False).exclude(closing_type='P')
        status_name = u' - В ОБРАБОТКЕ'
    elif status == 'set':
        qs = get_filtered_tasklist(request.user). \
            filter(responsible__isnull=False, date_close__isnull=True, \
                   ready_date__isnull=True, start_date__isnull=True, appoint_date__isnull=False).exclude(
            closing_type='P')
        status_name = u' - НАЗАЧЕННЫЕ'
    elif status == 'pending':
        qs = get_filtered_tasklist(request.user). \
            filter(closing_type='P')
        status_name = u' - ОТЛОЖЕННЫЕ'
    else:
        qs = get_filtered_tasklist(request.user)
        
    cd = CurDate() #; fi=FilterIndicator()

    if request.GET.get('applicant'):
        qs = qs.filter(applicant=request.GET.get('applicant')).exclude(applicant__isnull=True)
        status_name = u'-Мои заявки-' + status_name
        c.update(curdate=cd, status_name=status_name, status=status, p_where=p_where, \
                  applicant=request.GET.get('applicant') )
    elif request.GET.get('responsible'):
        qs = qs.filter(responsible=request.GET.get('responsible')).exclude(responsible__isnull=True)
        status_name = u'-К исполнению-' + status_name
        c.update(curdate=cd, status_name=status_name, status=status, p_where=p_where, \
                  responsible=request.GET.get('responsible') )
    else: 
        c.update(curdate=cd, status_name=status_name, status=status, p_where=p_where)
    
    response = HttpResponse(object_list(request, qs, paginate_by=10, page=p, \
                                        template_name=template_file, extra_context=c))

    response.set_cookie('status', value=status)
    if status == 'filter':
        #import urllib
        #response.set_cookie('p_where', value=urllib.quote(p_where.encode('utf-8')))
        response.set_cookie('p_where', value=p_where)
    return response


@login_required
def task_detail(request, ptask_id):
    """
    Детализация задачи
    """
    # проверка task_id
    if ptask_id is None:
        return HttpResponse(u'Не указан task_id.')
    task_id = ptask_id
    task = None
    try:
        task = get_task_filtered(request.user, task_id)
    except (InvalidTaskId):
        return HttpResponse(u'Неверный ID. Заявка № ' + request.POST['id'] + u' не найдена.')
    except (TaskNotExists):
        return HttpResponse(u'Не существует Заявки. Заявка № ' + request.POST['id'] + u' не найдена.')
    except (TaskAccessDenied):
        return HttpResponse(u'Недостаточно прав для открытия заявки.')
    qs = m.Task.objects.filter(pk=task_id) # Task в форме списка
    files = task.base.all()
    # если требуется только view, то view и выдаём (как подтверждение 
    # сохранения)
    st, status = task.get_status()
    if request.method == 'GET':
        if request.GET.get('view') == 'yes':
            if request.user.is_superuser or \
                    request.user.groups.filter(name="manager"): # могут смотреть и менять всё

                return HttpResponse(object_detail(request, queryset=qs, object_id=task_id, \
                                                  template_name="task_detail.html", \
                                                  extra_context={"curdate": CurDate(), \
                                                                 "header": 'Задача ' + str(task_id) + ' сохранена.', \
                                                                 "appoint_date": task.appoint_date,
                                                                 "files": files, "show_all": 'Y', "full_edit": 'Y'}))

            elif request.user.groups.filter(name="developer"): # может смотреть и менять только своё
                if task.responsible.id == User.objects.get(username=request.user.username).id or \
                                task.applicant.id == User.objects.get(username=request.user.username).id:

                    return HttpResponse(object_detail(request, queryset=qs, object_id=task_id, \
                                                      template_name="task_detail.html", \
                                                      extra_context={"curdate": CurDate(), \
                                                                     "header": 'Задача ' + str(task_id), \
                                                                     "appoint_date": task.appoint_date,
                                                                     "files": files, "show_all": 'Y',
                                                                     "full_edit": 'Y'}))
                else:
                    return render_to_response("error.html", {"curdate": CurDate(),
                                                             "message": 'Недостаточно прав.'}, \
                                              context_instance=RequestContext(request))

            else:
                # Клиент и девелопер видят только свои задачки
                if task.applicant == request.user and task.responsible != request.user:
                # Клиент не может редактировать, если у задачки есть манагер или ответственный (не он сам)
                    if (task.manager or task.responsible):
                        return HttpResponse(object_detail(request, queryset=qs, object_id=task_id, \
                                                          template_name="task_detail.html", \
                                                          extra_context={"curdate": CurDate(), \
                                                                         "header": 'Задача ' + str(
                                                                             task_id) + ' сохранена.', \
                                                                         "appoint_date": task.appoint_date,
                                                                         "files": files}))
                    else:
                        return HttpResponse(object_detail(request, queryset=qs, object_id=task_id, \
                                                          template_name="task_detail.html", \
                                                          extra_context={"curdate": CurDate(), \
                                                                         "header": 'Задача ' + str(
                                                                             task_id) + ' сохранена.', \
                                                                         "appoint_date": task.appoint_date,
                                                                         "files": files, "short_edit": 'Y'}))

                elif task.responsible == request.user:
                    #  Девелопер может смотреть и редактировать только свои ещё не закрытые задачки
                    if task.status != 'closed':
                        return HttpResponse(object_detail(request, queryset=qs, object_id=task_id, \
                                                          template_name="task_detail.html", \
                                                          extra_context={"curdate": CurDate(), \
                                                                         "header": 'Задача ' + str(
                                                                             task_id) + ' сохранена.', \
                                                                         "appoint_date": task.appoint_date,
                                                                         "files": files, "short_edit": 'Y'}))
                    else: # закрытые - только просмотр
                        return HttpResponse(object_detail(request, queryset=qs, object_id=task_id, \
                                                          template_name="task_detail.html", \
                                                          extra_context={"curdate": CurDate(), \
                                                                         "header": 'Задача ' + str(
                                                                             task_id) + ' сохранена.', \
                                                                         "appoint_date": task.appoint_date,
                                                                         "files": files}))

    # POST - часть
    # если не назначен исполнитель
    if st == 'new':
        # чужую - может посмотреть манагер через форму назначения
        if request.user.is_superuser:
            return edit_task(request, task_id)
        if request.user.groups.filter(name="manager"):
            #return redirect('/appointtask/' + str(task_id) + '/')
            return edit_task(request, task_id, role='manager') #redirect('/edittask/' + str(task_id) + '/')
            # свою заявку можно редактировать свободно
        if task.applicant.id == User.objects.get(username=request.user.username).id:
            #return HttpResponse('Почему')
            return redirect('/addtask/' + task_id + '/')
        # если назначен исполнитель, обрабатываем в зависимости от статуса
    # заявки
    # если заявка открыта или ожидает закрытия
    if st in ('set', 'open', 'ready'):
        # если манагер - то можно отредактировать назначение
        if request.user.is_superuser:
            return edit_task(request, task_id)
        if request.user.groups.filter(name="manager"):
            return edit_task(request, task_id,
                             role='manager') #            return redirect('/appointtask/' + str(task_id) +'/')
            # если открыта исполнителем - не манагером
        if task.responsible.id == User.objects.get(username=request.user.username).id:
            return redirect('/executetask/' + str(task_id) + '/')
            # Иначе - пользователь смотрит детали только своей!!! заявки
        if task.applicant.id == User.objects.get(username=request.user.username).id:
            return HttpResponse(object_detail(request, queryset=qs, object_id=task_id, \
                                              template_name="task_detail.html", \
                                              extra_context={"curdate": CurDate(), \
                                                             "header": 'Задача ' + str(task_id), \
                                                             "appoint_date": task.appoint_date,
                                                             "files": files}))
        # если заявка закрыта
    if st in ('closed', 'pending', 'discard'):
        # манагер может переназначить и изменить статус
        if request.user.is_superuser:
            return edit_task(request, task_id) #            return redirect('/appointtask/' + str(task_id) +'/')
        if request.user.groups.filter(name="manager"):
            return edit_task(request, task_id,
                             role='manager') #            return redirect('/appointtask/' + str(task_id) +'/')
            # заявитель и исполнитель могут смотреть детали заявки
        # каждый своей заявки
        if task.responsible.id == User.objects.get(username=request.user.username).id or \
                        task.applicant.id == User.objects.get(username=request.user.username).id:
            return HttpResponse(object_detail(request, queryset=qs, object_id=task_id, \
                                              template_name="task_detail.html", \
                                              extra_context={"curdate": CurDate(), \
                                                             "header": 'Задача ' + str(task_id), \
                                                             "appoint_date": task.appoint_date,
                                                             "files": files}))


@login_required
def edit_task(request, ptask_id=None, parent_task_id=None, **kwargs):
    """
    редактирование задачи для манагера и Супера
    """
    from django.core.mail import send_mail

    is_manager = False
    is_customer = False
    is_developer = False
    role = None
    try:
        role = kwargs.pop('role')
        if role == 'manager':
            is_manager = True
        if role == 'customer':
            is_customer = True
        if role == 'developer':
            is_developer = True #TODO - добавить выдачу формы и ее обработку
    except:
        None
        #if ptask_id is None:
        #return HttpResponse(u'Не указан task_id.')
    if not role:
        if request.user.groups.filter(name='manager'):
            is_manager = True
        elif request.user.groups.filter(name='customer'):
            is_customer = True
        elif not request.user.is_superuser:
            return show_error(request, u'Недостаточно прав для перехода по ссылке-1.')
    task_id = ptask_id
    task = None
    if task_id:
        try:
            task = get_task_filtered(request.user, task_id)
        except (InvalidTaskId):
            #return HttpResponse(u'Неверный ID. Заявка № ' + request.POST['id'] + u' не найдена.')
            return show_error(request, u'Неверный ID. Заявка № ' + request.POST['id'] + u' не найдена.')
        except (TaskNotExists):
            #return HttpResponse(u'Не существует Заявки. Заявка № ' + request.POST['id'] + u' не найдена.')
            return show_error(request, u'Не существует Заявки. Заявка № ' + request.POST['id'] + u' не найдена.')
        except (TaskAccessDenied):
            return show_error(request, u'Недостаточно прав для открытия заявки.')
            # прикреплённые файлы
        #files = task.base.all()
    #Вставить проверку статусов для is_customer!!!
    c1 = {}
    c = {}
    c.update(csrf(request))
    if request.method == 'GET':
        if task_id:
            if request.user.is_superuser:
                form = TaskForm({'id': task_id,
                                 'name': task.name,
                                 'descr': task.descr,
                                 'date_open': task.date_open,
                                 'start_date': task.start_date,
                                 'module': task.module,
                                 'manager': task.manager,
                                 'applicant': task.applicant,
                                 'responsible': task.responsible,
                                 'appoint_date': task.appoint_date,
                                 'deadline': task.deadline,
                                 'is_supervised': task.is_supervised,
                                 'ready_date': task.ready_date,
                                 'proj': task.proj,
                                 'exe': task.exe,
                                 'closing_type': task.closing_type,
                                 'date_close': task.date_close,
                                 'decision': task.decision,
                                 'category': task.category.all(),
                                 'urgent_important': task.urgent_important,
                                 'parent': task.parent
                                 })
            elif is_manager:
                form = TaskFormManager({'id': task_id,
                                        'name': task.name,
                                        'descr': task.descr,
                                        'date_open': task.date_open,
                                        'start_date': task.start_date,
                                        'module': task.module,
                                        #'manager':task.manager,
                                        'applicant': task.applicant,
                                        'responsible': task.responsible,
                                        'appoint_date': task.appoint_date,
                                        'deadline': task.deadline,
                                        'is_supervised': task.is_supervised,
                                        'ready_date': task.ready_date,
                                        'proj': task.proj,
                                        'exe': task.exe,
                                        'closing_type': task.closing_type,
                                        'date_close': task.date_close,
                                        'decision': task.decision,
                                        'category': task.category.all(),
                                        'urgent_important': task.urgent_important,
                                        'parent': task.parent
                })
            elif is_customer and task.get_status_short()=='new':
                form = TaskFormCustomer({'id': task_id,
                                         'name': task.name,
                                         'descr': task.descr})
            else:
                return show_error(request, u'Недостаточно прав для перехода по ссылке-2.')
        else:
            parent = None
            if parent_task_id:
                try:
                    parent = m.Task.objects.get(pk=parent_task_id)
                except m.Task.DoesNotExist:
                    pass
            if request.user.is_superuser: #20.12.2013
                if parent:
                    form = TaskForm({'date_open': date.today(), 'parent':parent})
                else:
                    form = TaskForm({'date_open': date.today()})
            elif is_manager:
                if parent:
                    form = TaskFormManager({'date_open': date.today(), 'parent':parent})
                else:
                    form = TaskFormManager({'date_open': date.today()})
            elif is_customer:
                form = TaskFormCustomer()
            else:
                return show_error(request, 'Недостаточно прав для перехода по ссылке. ')
    else: # POST
        # переменные для вычисления событий
        events = []
        if request.user.is_superuser:
            form = TaskForm(request.POST)
        elif is_manager:
            form = TaskFormManager(request.POST)
        elif is_customer:
            form = TaskFormCustomer(request.POST)
        else:
            return show_error(request, u'Недостаточно прав для ввода/корректировки данных.')
            #form = TaskForm(request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            task_temp = None
            if not task.closing_type and task.date_close and task.responsible:
                task.closing_type = 'C'
            if task_id:
                task.id = task_id
                task_temp = m.Task.objects.get(pk=task_id)
                if is_customer:
                    try:
                        if not (task_temp.responsible or task_temp.manager):
                            if task_temp.applicant:
                                task.applicant = task_temp.applicant
                            else:
                                task.applicant = request.applicant
                        else:
                            return show_error(request, u'Вы не можете изменить заявку, принятую в работу.')
                    except:
                        task.applicant = request.user
                        #task.applicant = form.cleaned_data['applicant']
            else: #
                # новая заявка
                if not task.applicant:
                    task.applicant = request.user
            if (is_manager or request.user.is_superuser) and not task.manager:
                task.manager = request.user
            if not task.date_open:
                task.date_open = date.today()
            if not task.appoint_date and task.responsible and task.manager:
                task.appoint_date = date.today()
            if not task.start_date and task.responsible:
                task.start_date = date.today()
            if task.closing_type:
                if not task.ready_date:
                    if task.date_close:
                        task.ready_date = task.date_close
                    else:
                        task.ready_date = date.today()
                if not task.date_close:
                    task.date_close = date.today()
                #20.02.2013
            if task.name and not task.descr:
                task.descr = task.name

                #if not is_customer:
                #    task.deadline = form.cleaned_data['deadline']
                #    task.is_supervised = form.cleaned_data['is_supervised' ]
                #    task.urgent_important = form.cleaned_data['urgent_important']
                #    task.save()
                #    task.category = form.cleaned_data['category']
                #    task.save()
                #task.category.through.objects.all().delete()
                #for category in m.TaskCategory.objects.filter(pk__in=request.POST.getlist('category')):
                #  task.category.add(category)
            #else:
            #    task.urgent_important = 'D'
            #    task.save()
            task.save()
            if form.cleaned_data.has_key('category'):
                task.category = form.cleaned_data['category']
                task.save()

            # подготовка рассылки
            if task_temp: # редактирование заявки
                if task.responsible != task_temp.responsible:
                    events.append('TASK_APPOINTED')
                if task.get_status()[0] == 'ready' and task_temp.get_status()[0] != 'ready':
                    events.append('TASK_READY')
                if task.get_status()[0] == 'closed' and task_temp.get_status()[0] != 'closed':
                    events.append('TASK_CLOSED')
                if task.get_status()[0] == 'pending' and task_temp.get_status()[0] != 'pending':
                    events.append('TASK_PENDING')
                if task.get_status()[0] == 'discard' and task_temp.get_status()[0] != 'discard':
                    events.append('TASK_DISCARD')
            else: # ввод новой заявки
                events.append('TASK_CREATED')
                if task.responsible: # назначен исполнитель
                    events.append('TASK_APPOINTED')
                if task.get_status()[0] == 'ready':
                    events.append('TASK_READY')
                if task.get_status()[0] == 'closed':
                    events.append('TASK_CLOSED')
                if task.get_status()[0] == 'pending':
                    events.append('TASK_PENDING')
                if task.get_status()[0] == 'discard':
                    events.append('TASK_DISCARD')

            # запуск рассылки уведомлений
            #return HttpResponse('new: ' + task.get_status()[0] + 'old: '+task_temp.get_status()[0])
            for event in events:
                m.Task.notify(event, task)
            return redirect('/addfile/?' + 'task_id=' + str(task.id))
        else:
            return HttpResponse('Форма не айс!')

    curdate = CurDate()
    return render_to_response('edit_task.html',
                              {'form': form, 'curdate': CurDate(), 'task_id': task_id, 'curdate': curdate}, \
                              context_instance=RequestContext(request, c))


@login_required
def search_form(request):
    if request.method == 'POST':
        form = TaskSearchForm(request.POST)
        search_string = 'p_where='
        params = []
        if form.is_valid():
            for item in form.cleaned_data:
                if form.cleaned_data[item]:
                    if item in ('name', 'descr', 'decision', 'proj'):
                        import urllib
                        if search_string == 'p_where=':
                            #NEW
                            
                            search_string += item + '_like=' + form.cleaned_data[item]
                        else:
                            search_string += '|' + item + '_like=' + form.cleaned_data[item]
                    if item in ('manager', 'applicant', 'responsible', 'module'):
                        if search_string == 'p_where=':
                            search_string += item + '=' + form.cleaned_data[item]
                        else:
                            search_string += '|' + item + '=' + form.cleaned_data[item]
                    if item in ('from_date_open', 'to_date_open'):
                        if search_string == 'p_where=':
                            search_string += item + '=' + form.cleaned_data[item].isoformat()
                        else:
                            search_string += '|' + item + '=' + form.cleaned_data[item].isoformat()
                    #NEW
                    #return HttpResponse(search_string)
            if search_string == 'p_where=':
                search_string = None
                #return HttpResponse(search_string)
            #qs = m.Task.objects.extra(where=[search_string], params=params)
            #if not qs:
            #  return redirect('/task_notfound/')
            return redirect('/tasklist/?status=filter&' + search_string)
            #return common_tasklist(request, None, search_string)
    else:
        form = TaskSearchForm()
        c = {}
        c.update(csrf(request))

        return render_to_response('search_task.html', {'form': form, 'curdate': CurDate()},
                                  context_instance=RequestContext(request, c))
        pass
    return HttpResponse('Данные были введены некорректно.')


@login_required
def change_password(request):
    if request.method == 'POST':
        form = ChangePasswordForm(request.POST)
        if form.is_valid():
            if request.user.check_password(form.cleaned_data['old_password']):
                request.user.set_password(form.cleaned_data['new_password'])
                request.user.save()
                return render_to_response("error.html", {"curdate": CurDate(),
                                                         "message": 'Пароль изменён.'}, \
                                          context_instance=RequestContext(request))
            else:
                return render_to_response("error.html", {"curdate": CurDate(),
                                                         "message": 'Вы указали неверный пароль.'}, \
                                          context_instance=RequestContext(request))
    form = ChangePasswordForm()
    c = {}
    c.update(csrf(request))
    return render_to_response('change_password.html', {'form': form, 'curdate': CurDate()},
                              context_instance=RequestContext(request, c))


def my_logout(request):
    from django.contrib.auth import logout

    logout(request)
    return redirect('/home/')


def home_page(request):
    """
    домашняя страничка
    """
    if request.method == 'POST':
        uname = request.POST['username']
        passw = request.POST['password']
        user = auth.authenticate(username=uname, password=passw)
        if user is not None and user.is_active:
            auth.login(request, user)
        else:
            return render_to_response("error.html", {"curdate": CurDate(),
                                                     "message": 'Указаны Неверные логин или пароль.'}, \
                                      context_instance=RequestContext(request))
    return render_to_response("hello.html", {"curdate": CurDate()}, \
                              context_instance=RequestContext(request))


def task_notfound(request):
    return render_to_response("error.html", {"curdate": CurDate(),
                                             "message": 'Данные не найдены.'}, \
                              context_instance=RequestContext(request))
                              
#20.12.2013
def show_error(request, message):                              
    return render_to_response("error.html", {"curdate": CurDate(),
                                             "message": message}, \
                              context_instance=RequestContext(request))

@login_required
def appraise_form(request, task_id):
    task = get_object_or_404(m.Task, pk=task_id)
    if request.user!=task.applicant:
        return show_error(request, u'Оценить выполнение может только заявитель.')
    try:
        task.rank = request.POST['rank']
        task.rank_date = date.today()
        task.save()
        #return HttpResponse(u'Оценка сохранена.')
        return redirect('/taskdetail/' + task_id + '/?view=yes')
    except:
        form = TaskFormCustomerRank({'id':task_id, 'rank':3})
        form_title = u'Оценка качества выполнения заявки ' + task_id
        return render_to_response('unified_form.html', {'curdate':date.today(), 'form_title':form_title, 
                'form':form}, context_instance=RequestContext(request, {}.update(csrf(request))))
        
def show_fsencoding(request):
	import sys
	return HttpResponse(sys.getfilesystemencoding())

def show_user(request):
  return HttpResponse(request.user.id)
  
@login_required
def import_users(request):
    if not request.user.is_superuser:
        return HttpResponse('Недостаочно прав!')
    
    log = ''
    import psycopg2
    pg = psycopg2.connect(database='taskdb', host='localhost', user='postgres', password='postgres')
    pgcur = pg.cursor()
    
    pgcur.execute("""
        select lower(username), first_name, last_name, middle_name, email, phone, room
          from import_users
    """)
    
    for row in pgcur.fetchall():
        # обновление уже существующего юзера
        
        pgcur.execute('select id, username from auth_user where username=%s', (row[0],))
        existing_row = pgcur.fetchone()
        user_id = None
        
        if existing_row:
            # обновляем auth_user
            try:
                pgcur.execute("""
                    update auth_user
                      set first_name = %s,
                          last_name = %s,
                          email = %s
                      where lower(username) = %s
                """, (row[1], row[2], row[4], row[0]))
                
                pg.commit()
                log += row[0] + ' updated.\n'
            except psycopg2.DatabaseError as dbe:
                pg.rollback()
                log += row[0] + u' not updated: error\n'
            except:
                pg.rollback()
                log += ' CRASH!!!\n' 
                return HttpResponse(log)
                
            user_id = existing_row[0]
            
            # обновляем addtask_person
            
            
            
            try:
                pgcur.execute("""
                    update addtask_person
                      set second_name = %s,
                          phone = %s,
                          location = %s
                      where user_id = %s
                """, (row[3], row[5], row[6], str(user_id),))
                
                pg.commit()
                log += row[0] + ' person updated.\n'
            except psycopg2.DatabaseError as dbe:
                pg.rollback()
                log += row[0] + u' person not updated: error with id = ' + str(user_id) + '\n'
            except:
                pg.rollback()
                log += ' CRASH!!!\n' 
                return HttpResponse(log)

        else: # новый юзер
            
            from django.contrib.auth.models import User
            new_user = User.objects.create_user(row[0], row[4], row[0])
            new_user.first_name = row[1]
            new_user.last_name = row[2]
            new_user.save()
            
            new_user.groups.add(Group.objects.get(name='customer'))
            
            user_id = new_user.id
            
            log += row[0] + ' created with id=' + str(user_id)
            iserror=False    
            # добавляем addtask_person
            try:
                pgcur.execute("""
                    insert into addtask_person(second_name, phone, location, login, user_id)
                    values(%s, %s, %s, %s, %s)
                """, (row[3], row[5], row[6], row[0], user_id,))
                
                pg.commit()
                log += row[0] + ' person created.\n'
            except psycopg2.DatabaseError as dbe:
                pg.rollback()
                log += row[0] + u' person not created: error with id=' + str(user_id) + '\n'
                log += ' SQL:' + 'insert into addtask_person(second_name, phone, location, login, user_id) values(%s, %s, %s, %s, %s)' \
                        % (row[3], row[5], row[6], row[0], user_id,)
                return HttpResponse(log)
            except:
                pg.rollback()
                log += ' CRASH!!!\n' 
                return HttpResponse(log)
            
    return HttpResponse(log)
            
@login_required
def admin_submenu(request):
    if request.user.is_superuser:
        return render_to_response('admin_submenu.html', {'curdate':date.today()}, context_instance=RequestContext(request))
    return render_to_response("error.html", {"curdate":date.today(),
                                             "message": 'Недостаточно прав.'}, \
                                             context_instance=RequestContext(request))
        
@login_required
def search_user_form(request):
    import vctasks.addtask.search_utils as search_utils
    if request.method == 'POST':
        form = UserSearchForm(request.POST)
        search_string = ''
        params = []
        if form.is_valid():
            for item in form.cleaned_data:
                if form.cleaned_data[item]:
                    if item=='username':
                        search_string += search_utils.add_like(search_string, item, form.cleaned_data[item])
            if search_string == 'p_where=':
                search_string = None
            return redirect('/users_found/?' + search_string) #?' + search_string)
        #return HttpResponse(search_string)
    else:
        qs = []
        found_users = False
        if request.GET.get('p_where'):
            search_string, params = search_utils.parse_query_string(request.GET.get('p_where'))
            #return HttpResponse(search_string)
            qs = User.objects.extra(where=[search_string], params=params)
        if len(qs)>0:
            found_users = True
        form = UserSearchForm()
        c = {}
        c.update(csrf(request))
        return render_to_response('search_user.html', {'form': form, 'curdate': date.today(), 'found_users':found_users, 'users':qs},
                                  context_instance=RequestContext(request, c))

    return HttpResponse(u'Некорректно введены данные.')

@login_required
def edit_user(request, user_id=None):
    from vctasks.addtask.forms import EditUserForm, CreateUserForm
    if not (request.user.groups.filter(name='manager') or request.user.is_superuser):
        return show_error(request, 'edit_user: Недостаточно полномочий для данной операции.')
    if request.method=='POST':
        if user_id:
            form = EditUserForm(request.POST)
        else:
            form = CreateUserForm(request.POST)
        if form.is_valid():
            _user = None
            if user_id:
                try:
                    _user = User.objects.get(pk=user_id)
                except User.DoesNotExist:
                    return show_error(request, u'Пользователь с id=' + str(user_id)+ u' не существует.')
                
                _user.first_name = form.cleaned_data['first_name']
                _user.last_name = form.cleaned_data['last_name']
                _user.email = form.cleaned_data['email']
                _user.save()
            else:
                import django.db
                try:
                    _user = User.objects.create_user(form.cleaned_data['username'], form.cleaned_data['email'], form.cleaned_data['password'])
                except django.db.IntegrityError:
                    return show_error(request, u'Пользователь ' + form.cleaned_data['username'] + u' уже существует.')
                _user.first_name = form.cleaned_data['first_name']
                _user.last_name = form.cleaned_data['last_name']
                _user.save()
            _user.groups = form.cleaned_data['groups'] #.add(Group.objects.get(name='customer'))
            # ищем или создаём профиль
            _person, created = m.Person.objects.get_or_create(user=_user)
            _person.second_name=form.cleaned_data['second_name']
            _person.location = form.cleaned_data['location']
            _person.phone = form.cleaned_data['phone']
            _person.save()
            return show_error(request, u'Данные пользователя ' + _user.username + u' сохранены.')
    else:
        if user_id:
            _user = None
            _person = None
            try: 
                _user = User.objects.get(pk=user_id)
                _person = m.Person.objects.get(user=_user)
                #return HttpResponse(_user.groups.all())
            except User.DoesNotExist:
                return show_error(request, u'Пользователь с user_id=' + str(user_id)+ u' не существует.')
            except m.Person.DoesNotExist:
                pass # надо будет создать в POST-части
            title = u'Редактирование пользователя'
            _second_name = ''
            _location = ''
            _phone = ''
            if _person:
                _second_name = _person.second_name
                _location = _person.location
                _phone = _person.phone
            form = EditUserForm({'user_id':user_id, 
                        'email':_user.email,
                        'first_name':_user.first_name, 
                        'second_name':_second_name, 
                        'last_name':_user.last_name, 
                        'location':_location, 
                        'phone':_phone, 
                        'groups':[group.id for group in User.objects.get(pk=user_id).groups.all()]
                        })
            if form.action:
                return render_to_response('edit_user.html', {'form':form, 'cur_date':date.today(), 'object':_user, 
                                    'action':form.action, 'title':title}, 
                                context_instance=RequestContext(request, {}.update(csrf(request))))
            return render_to_response('edit_user.html', {'form':form, 'cur_date':date.today(), 'object':_user, 'title':title}, 
                                context_instance=RequestContext(request, {}.update(csrf(request))))
        else: # новый усёр
            form = CreateUserForm()
            title = u'Создание пользователя'
            if form.action:
                return render_to_response('edit_user.html', {'form':form, 'cur_date':date.today(), 'action':form.action,
                                            'title':title}, 
                                    context_instance=RequestContext(request, {}.update(csrf(request))))
            return render_to_response('edit_user.html', {'form':form, 'cur_date':date.today(), 'title':title}, 
                    context_instance=RequestContext(request, {}.update(csrf(request))))

#    return HttpResponse(form)
    return HttpResponse(u'Некорректно введены данные в форму. ')

@login_required    
def drop_password(request, user_id):
    if request.user.is_superuser:
        #try:
            _user = User.objects.get(pk=user_id)
            _user.set_password('123456')
            _user.save()
            return show_error(request, u'Пользователю ' + _user.username + u' назначен пароль по умолчанию "123456".')
        #except:
        #    pass
        
def create_subtask(request, parent_task_id):
    return edit_task(request, None, parent_task_id)