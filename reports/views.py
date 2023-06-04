from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.models import User
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseForbidden, HttpResponseRedirect, HttpResponse, HttpResponseNotFound, Http404
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.views.generic import CreateView, UpdateView, DetailView, ListView, TemplateView
from django.utils.http import url_has_allowed_host_and_scheme
from django.db.models import Q
from django.core.mail import send_mail
import datetime, calendar
from main.my_validators import *
from .forms import *
from .models import *
from servicecentres.models import ServiceCenters
import xlwt
from upload.forms import ReportDocumentForm, RecordDocumentForm
from mail.views import  mail_ordered_parts, mail_send_parts


# -------------------------- ОТПРАКА ПОЧТЫ -------------------------------

# отправка письма пользователю об изменении статуса отчета
def SendReportSatus(email, report, note):
    """ отправка электронного письма польхователю """
    email = report.service_center.user.email
    msg = f'Статус вашего отчета за {report.get_report_month()} изменен на "{report.get_status_display()}"\n\n'
    if note:
        msg = msg + 'Сообщение от менедежера:\n'
        msg = msg + note + '\n\n'
    msg = msg + 'Это письмо сформированно автоматическа, отвечать на него не нужно.'
    send_mail(
        'RENOVA. Статус вашего отчета изменен',
        msg,
        'report_service@re-nova.com',
        ['shagi80@mail.ru'],
        #[email],
        fail_silently=False,
    )

# отправка письма менеджеру о поступлении отчета
def SendReportToStaff(report):
    """ отправка электронного письма менеджеру """
    email = report.service_center.staff_user.email
    if email:
        msg = f'Получен отчет от {report.service_center} за {report.get_report_month()}.\n\n'
        msg = msg + 'Это письмо сформированно автоматическа, отвечать на него не нужно.'
        send_mail(
            'RENOVA. Получен новый отчет.',
            msg,
            'report_service@re-nova.com',
            ['shagi80@mail.ru'],
            #[email],
            fail_silently=False,
        )

# ------------------------- РАБОТА С ОТЧЕТОМ -----------------------------

# экспорт отчета в эксель
@user_passes_test(user_validation)
def export_report_xls(request, report_pk):
    report = get_object_or_404(Reports, pk = report_pk)
    report_date = report.get_report_month()

    response = HttpResponse(content_type='application/ms-excel')
    disp = f'attachment; filename="Report of ' + report.report_date.strftime("%b %Y") + ' .xls"'
    response['Content-Disposition'] = disp
    workBook = xlwt.Workbook(encoding='utf-8')
    workSheet = workBook.add_sheet(report_date)

    # Sheet header, first row
    boldStyle = xlwt.XFStyle()
    boldStyle.font.bold = True
    row_num = 0
    workSheet.write(row_num, 0, f'Статистическая таблица за {report_date}. {report.service_center}', boldStyle)

    # Table header, third row
    row_num = 2
    workSheet.row(row_num).height = 600
    headerStyle = xlwt.easyxf('font: bold off, color black; borders: left thin, right thin, top thin, bottom thin;\
     pattern: pattern solid, fore_color white, fore_colour gray25; align: horiz center, vert top;')
    headerStyle.alignment.wrap = 1
    columns = ['№', 'Клиент', 'Адрес', 'Телефон', 'Модель', 'Серийный номер', 'Дата продажи', 'Дата приема',
               'Дата ремонта', 'Описание датали', 'Цена детали', 'Кол-во штук', 'Номер накладной', 'Выезд',
               'За работы', 'Заявленный дефект', 'Описание работ', 'Код неисправности']
    for col_num in range(len(columns)):
        workSheet.write(row_num, col_num, columns[col_num], headerStyle)

    # Sheet body, remaining rows
    style = xlwt.XFStyle()
    records = ReportsRecords.objects.filter(report=report)
    row_num_str = 0
    for record in records:
        row_num += 1
        row_num_str += 1
        workSheet.col(0).width = 1000
        workSheet.write(row_num, 0, str(row_num_str), style)
        workSheet.col(1).width = 5000
        workSheet.write(row_num, 1, record.client, style)
        workSheet.write(row_num, 2, record.client_addr, style)
        workSheet.write(row_num, 3, record.client_phone, style)
        workSheet.col(4).width = 5000
        workSheet.write(row_num, 4, record.model_description, style)
        workSheet.col(5).width = 5000
        workSheet.write(row_num, 5, record.serial_number, style)
        if record.buy_date:
            workSheet.write(row_num, 6, record.buy_date.strftime("%d.%m.%y"), style)
        if record.start_date:
            workSheet.write(row_num, 7, record.start_date.strftime("%d.%m.%y"), style)
        if record.end_date:
            workSheet.write(row_num, 8, record.end_date.strftime("%d.%m.%y"), style)
        if record.move_cost:
            workSheet.write(row_num, 13, record.move_cost, style)
        if record.work_cost:
            workSheet.write(row_num, 14, record.work_cost, style)
        workSheet.col(15).width = 8000
        workSheet.write(row_num, 15, record.problem_description, style)
        workSheet.col(16).width = 8000
        workSheet.write(row_num, 16, record.work_description, style)
        workSheet.col(17).width = 2000
        workSheet.write(row_num, 17, record.code.code, style)
        parts = ReportsParts.objects.filter(record=record)
        for part in parts:
            workSheet.col(9).width = 8000
            workSheet.write(row_num, 9, part.title, style)
            if part.price:
                workSheet.write(row_num, 10, part.price, style)
            if part.count:
                workSheet.write(row_num, 11, part.count, style)
            workSheet.write(row_num, 12, part.document, style)
            row_num += 1
        if parts:
            row_num -= 1

    # Footer
    row_num += 1
    workSheet.write(row_num, 10, f'{report.total_part} руб',boldStyle)
    workSheet.write(row_num, 13, f'{report.total_move} руб', boldStyle)
    workSheet.write(row_num, 14, f'{report.total_work} руб', boldStyle)
    workSheet.write(row_num+1, 0, f'Всего по отчету: {report.total_cost} рублей.', boldStyle)

    workBook.save(response)
    return response

# изменение статуса отчета
@user_passes_test(staff_validation)
def ReportChangeStatus(request):
    from main.business_logic import REPORT_STATUS
    if request.method == 'POST':
        new_status = None
        report_id = None
        mail_note = ''
        if 'send_refinement' in request.POST:
            report_id = request.POST.get('send_refinement')
            new_status = 'refinement'
            mail_note = request.POST.get('message')
        else:
            for status in REPORT_STATUS:
                if status[0] in request.POST:
                    report_id = request.POST.get(status[0])
                    if status[0] == 'draft':
                        new_status = 'send'
                    elif status[0] == 'send':
                        new_status = 'received'
                    elif status[0] == 'received':
                        new_status = 'verified'
                    elif status[0] == 'refinement':
                        new_status = 'send'
                    elif status[0] == 'verified':
                        new_status = 'accepted'
                    elif status[0] == 'accepted':
                        new_status = 'payment'
                    elif status[0] == 'payment':
                        new_status = 'draft'
        if new_status and report_id:
            report = get_object_or_404(Reports, pk=int(report_id))
            if report.service_center.staff_user == request.user or request.user.is_superuser or \
                    request.user.groups.filter(name='GeneralStaff').exists():
                report.status = new_status
                report.save()
                email = report.service_center.user.email
                if email:
                    SendReportSatus(email, report, mail_note)
                if new_status == 'received':
                    return redirect('report_page', report.pk)
    next = request.META.get('HTTP_REFERER')
    if url_has_allowed_host_and_scheme(next, request.get_host()):
        return redirect(next)
    return redirect('reports_list')

# показ списка отчетов менеджеру
class ReportsForStaff(LoginRequiredMixin, StaffUserMixin, ListView):
    model = Reports
    template_name = 'reports/staff_reports_list.html'
    context_object_name = 'reports'
    extra_context = {'title': 'Все отчеты:'}
    paginate_by = 10

    def get_queryset(self):
        if self.request.user.is_superuser:
            reports = Reports.objects.all()
        elif self.request.user.groups.filter(name='GeneralStaff').exists():
            reports = Reports.objects.all().exclude(status='draft')
        else:
            reports = Reports.objects.filter(service_center__staff_user=self.request.user).exclude(status='draft')
        if self.request.GET.get("service_center", '') != '':
            reports = reports.filter(service_center=self.request.GET.get("service_center"))
        if self.request.GET.get("staff_user", '') != '':
            reports = reports.filter(service_center__staff_user=self.request.GET.get("staff_user"))
        if self.request.GET.get("use_status", '') == 'on' and self.request.GET.get("status", '') != '':
            reports = reports.filter(status=self.request.GET.get("status"))
        if self.request.GET.get("use_date", '') == 'on' and self.request.GET.get("month", '') != '' and \
                self.request.GET.get("year", '') != '':
            report_date = datetime.date(int(self.request.GET.get("year", '')), int(self.request.GET.get("month", '')),
                                        1)
            reports = reports.filter(report_date=report_date)
        return reports

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = ReportsFilterForm(self.request.GET)
        context['obj_count'] = self.object_list.count()
        return context

# добавление отчета
@user_passes_test(user_validation)
def ReportAdd(request):
    if request.method == 'POST':
        form = ReportTitleForm(request.POST)
        print('test')
        if form.is_valid():
            print(form.cleaned_data['year'])
            print(form.cleaned_data['month'])
            report_date = datetime.date(form.cleaned_data['year'], form.cleaned_data['month'], 1)
            note = form.cleaned_data['note']
            user = request.user
            try:
                center = ServiceCenters.objects.get(user=user, is_active=True)
            except():
                messages.error(request, 'Ощибка при добавлении отчета: сервисный центр не найден !')
                return redirect('user_home')
            if Reports.objects.filter(report_date=report_date, service_center=center):
                messages.error(request, 'Отчет для этого периода уже существует !')
                return redirect('user_home')
            else:
                report = Reports(service_center=center, user=user, report_date=report_date, note=note)
                report.save()
                return redirect('user_home')
    else:
        return redirect('user_home')

# изменение отчета
@user_passes_test(user_validation)
def ReportUpdate(request, report_pk):
    if request.method == 'POST':
        form = ReportTitleForm(request.POST)
        if form.is_valid():
            report = get_object_or_404(Reports, pk=report_pk)
            if report.service_center.user == request.user or request.user.is_superuser:
                report_date = datetime.date(form.cleaned_data['year'], form.cleaned_data['month'], 1)
                note = form.cleaned_data['note']
                if Reports.objects.filter(report_date=report_date, service_center=report.service_center).exclude(
                        pk=report_pk):
                    messages.error(request, 'Отчет для этого периода уже существует !')
                    return redirect('report_page', report_pk)
                else:
                    report.report_date = report_date
                    report.note = note
                    report.save()
                    return redirect('report_page', report_pk)
    else:
        return redirect('report_page', report_pk)

# отправка отчета на проверку
@user_passes_test(user_validation)
def ReportSend(request):
    if request.method == 'POST':
        if 'send' in request.POST:
            report_id = request.POST.get('send')
            if report_id:
                report = get_object_or_404(Reports, pk=int(report_id))
                if report.service_center.user == request.user or request.user.is_superuser:
                    report.status = 'send'
                    report.save()
                    SendReportToStaff(report)
    return redirect('user_home')

# показ отчета 
class ReportDetail(LoginRequiredMixin, UserMixin, DetailView):
    model = Reports
    template_name = 'reports/report_page.html'
    context_object_name = 'report'
    extra_context = {'title': 'Отчет за '}
    previos_url = None

    def dispatch(self, request, *args, **kwargs):
        if 'previos' in self.request.GET:
            self.previos_url = self.request.get_full_path().split('previos')[1][1:]
        return super().dispatch(request, *args, **kwargs)

    def test_func(self):
        report = self.get_object()
        return report.service_center.user == self.request.user or self.request.user.is_superuser or \
               (report.status != 'draft' and (report.service_center.staff_user == self.request.user or
                                              self.request.user.groups.filter(name='GeneralStaff').exists()))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        form = ReportTitleForm()
        form.initial['month'] = self.object.report_date.month
        form.initial['year'] = self.object.report_date.year
        form.initial['note'] = self.object.note
        records = ReportsRecords.objects.filter(report=self.object)
        context['records'] = records
        context['can_delete'] = (not records.filter(order_parts=True)) or (self.request.user.is_superuser) or (not records)
        context['rep_form'] = form
        context['previos_url'] = self.previos_url
        context['document_form'] = ReportDocumentForm({'report':self.object})
        return context

# ------------------- РАЬОТА С ЗАПИСЬЮ О РЕМОНТЕ -------------------------

# копирование записи о ремонте
@user_passes_test(user_validation)
def RecordCopy(request):
    """ копирование записи """
    if request.method == 'POST':
        if 'copy' in request.POST:
            record_id = request.POST.get('copy')
            if record_id:
                new_record = get_object_or_404(ReportsRecords, pk=int(record_id))
                new_record.pk = None
                new_record.serial_number = ''
                new_record.order_parts = False
                new_record.save()
                return redirect('record_update_page', new_record.pk)
    return HttpResponseNotFound()

# замечание менеджера к отчету
@user_passes_test(staff_validation)
def RecordRemarks(request):
    if request.method == 'POST':
        if 'save' in request.POST:
            record_id = request.POST.get('save')
            remarks = None
            if 'remarks' in request.POST:
                remarks = request.POST.get('remarks')
            if record_id:
                record = get_object_or_404(ReportsRecords, pk=int(record_id))
                record.remarks = remarks
                record.save()
                return redirect('record_update_page', record.pk)
    return redirect('user_home')

# установка флага "ремонт проверен"
@user_passes_test(staff_validation)
def RecordVerified(request):
    from datetime import datetime
    if request.method == 'POST':
        if 'save' in request.POST:
            record_id = request.POST.get('save')
            if record_id:
                record = get_object_or_404(ReportsRecords, pk=int(record_id))
                record.remarks = None
                record.verified = True
                record.verified_date = datetime.now().date()
                record.save()
                return redirect('record_update_page', record.pk)
    return redirect('user_home')

# перенос записи на следующий месяц
@user_passes_test(user_validation)
def RecordRemove(request):
    """ перенос записи на следующий месяц """
    if request.method == 'POST':
        if 'remove' in request.POST:
            record_id = request.POST.get('remove')
            if record_id:
                record = get_object_or_404(ReportsRecords, pk=int(record_id))
                # вычисляем дату отчета для следующего месяца
                days = calendar.monthrange(record.report.report_date.year, record.report.report_date.month)[1]
                next_month_date = record.report.report_date + datetime.timedelta(days=days)
                # пытаемся найти уже сущетвующие отчеты за следующий месяц
                reports = Reports.objects.filter(service_center=record.report.service_center,
                                                report_date=next_month_date)
                if reports:
                    # отчет должен быть один
                    if reports.count() > 1:
                        raise Http404('Целевых отчетов больше чем один !')
                    # отчет должен быть черновиком или на доработке
                    if not reports.first().status in ['draft', 'refinement']:
                        messages.error(request, 'Отчет за следующий месяц уже отправлен на проверку !')
                        return redirect('report-update', record.report.pk)
                    new_report = reports.first()
                else:
                    # если отчета не существует создаеи его
                    new_report = Reports.objects.create(
                        service_center=record.report.service_center,
                        report_date=next_month_date,
                        user=record.report.user
                    )
                # переподчиняем запись
                old_report = record.report
                record.report = new_report 
                record.save() 
                old_report.save() # мы должны пересохранить старый отчет что бы обновить итоги            
                messages.success(request, f'Запись успешно перенесена в отчет за {new_report.get_report_month()} !')
                return redirect('report-update', new_report.pk)
    return HttpResponseNotFound()

# общие процеудуры представлений добавления и обновления записи
class RecordView(View):
    success_message = 'my meesage'
    form_class = RecordForm
    error_message = 'Пожалуйста, проверьте форму !'
    template_name = 'reports/records_add.html'
    report = None

    def test_func(self):
        if self.object:
            report = self.object
        else:
            report = get_object_or_404(Reports, pk=self.kwargs['report_pk'])
        return report.service_center.user == self.request.user or self.request.user.is_superuser or (
                report.status != 'draft' and (self.request.user.groups.filter(name='GeneralStaff').exists() or
                                              report.service_center.staff_user == self.request.user))

    def form_invalid(self, form, **kwargs):
        ctx = self.get_context_data(**kwargs)
        parts_formset = PartsFormset(form.data, instance=form.instance, prefix='parts_formset')
        ctx['form'] = form
        ctx['parts_formset'] = parts_formset
        if 'errors' not in form.errors:
            # messages.error(self.request, form.errors)
            messages.error(self.request, self.error_message)
        return render(self.request, self.template_name, ctx)

    def form_valid(self, form):
        # if not form.instance.pk:
        #   form.save()
        parts_formset = PartsFormset(form.data, instance=form.instance, prefix='parts_formset')
        if parts_formset.is_valid():
            # сохраняем как есть по соответствующей кнопке или проверяем некритичные ошибки
            if form.cleaned_data['errors'] and 'save_with_warning' not in self.request.POST:
                errors_list = form.cleaned_data['errors'].split(';')
                form.add_error('errors', errors_list)
                return self.form_invalid(form)
            else:
                # только этот кусок кода выполняется если все хорошо и можно записывать
                messages.success(self.request, self.success_message)
                form.save()
                parts_formset.save()
                # проверяем список деталей на предмет заказа
                ordered_parts = []
                for part_form in parts_formset.forms:
                    if 'ORDERED' in part_form.cleaned_data and part_form.cleaned_data['ORDERED']:
                        part_form.instance.order_date = datetime.datetime.now()
                        part_form.instance.price = 0
                        part_form.instance.save()
                        part = {'title':part_form.instance.title, 'count':part_form.instance.count}
                        ordered_parts.append(part)
                if ordered_parts:
                    if  mail_ordered_parts(form.instance, ordered_parts):
                        messages.info(self.request, 'Заказ на детали отправлен !')
                    else:
                        messages.error(self.request, 'Ошибка при отравке заказа на запчасти !')
                    if not form.instance.order_parts:
                        form.instance.order_parts = True
                        form.instance.save()
                # завершение работы view
                return HttpResponseRedirect(self.get_success_url())
        else:
            form.is_valid = False
            errors = []
            for form_error in parts_formset.errors:
                if form_error:
                    for key in form_error:
                        err_string = key + ' ' + form_error[key].as_text()
                        err_string = err_string.replace('title', 'Наименование')
                        err_string = err_string.replace('count', 'Количество')
                        err_string = err_string.replace('document', 'Документ')
                        err_string = err_string.replace('price', 'Цена')
                        err_string = err_string.replace('*', '-')
                        errors.append(err_string)
            form.add_error('parts_cost', errors)
            return self.form_invalid(form)

    def get_success_url(self):
        if 'continue' in self.request.POST or 'save_with_warning' in self.request.POST:
            return  self.request.path_info
        if 'close' in self.request.POST:
            if self.object:
                return reverse('report-update', kwargs={'report_pk': self.object.report.pk})   
            return reverse('report-update', kwargs={'report_pk': self.kwargs['report_pk']})


class RecordAdd(LoginRequiredMixin, RecordView, CreateView):
    success_message = 'Ремонт успешно добавлен !'
    extra_context = {'title': 'Добавление ремонта в отчет за '}

    def setup(self, request, *args, **kwargs):
        super(RecordAdd, self).setup(request, *args, **kwargs)
        self.report = get_object_or_404(Reports, pk=self.kwargs['report_pk'])

    def get_form_kwargs(self, *args, **kwargs):
        kwargs = super().get_form_kwargs(*args, **kwargs)
        kwargs['report'] = self.report
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['report'] = get_object_or_404(Reports, pk=self.kwargs['report_pk'])
        context['can_edit'] = True
        context['parts_formset'] = PartsFormset(instance=self.object, prefix='parts_formset', user=self.request.user)
        return context


class RecordUpdate(LoginRequiredMixin, RecordView, UpdateView):
    model = ReportsRecords
    extra_context = {'title': 'Ремонт из отчета  '}
    success_message = 'Ремонт успешно изменен !'

    def get_form_kwargs(self, *args, **kwargs):
        kwargs = super().get_form_kwargs(*args, **kwargs)
        kwargs['user'] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['report'] = self.object.report
        context['record'] = self.object
        context['can_edit'] = (self.object.report.status == 'draft' or self.object.report.status == 'refinement') and \
                              (not self.request.user.is_staff or self.request.user.is_superuser) and not self.object.verified
        context['parts_formset'] = PartsFormset(instance=self.object, prefix='parts_formset', user=self.request.user)
        context['document_form'] = RecordDocumentForm({'record':self.object})
        return context

# --------------------------- AJAX -------------------------------------------

# обработка AJAX скрипта динамической формы
def load_codes_data(request):
    from django.db.models import Q
    groups = None
    codes = None
    code_id = None
    if 'product' in request.GET and request.GET.get('product'):
        product_id = request.GET.get('product')
        codes = Codes.objects.filter(Q(product_id=product_id) | Q(product_id=None), is_folder=False,
                                     is_active=True).order_by('code')
        groups = Codes.objects.filter(Q(product_id=product_id) | Q(product_id=None), is_folder=True,
                                      is_active=True).order_by('code')
        code_id = 0
        if 'code' in request.GET and request.GET.get('code'):
            code_id = int(request.GET.get('code'))
    return render(request, 'reports/codes_list_get.html', {'groups': groups, 'codes': codes, 'select_id': code_id})


# обработка AJAX скрипта динамической формы
def load_models_data(request):
    models_list = None
    if 'product' in request.GET and request.GET.get('product'):
        product_id = request.GET.get('product')
        models_list = Models.objects.filter(product_id=product_id).order_by('title')
    return render(request, 'reports/models_list_get.html', {'groups': models_list})


# обработка AJAX скрипта динамической формы
def load_work_price_data(request):
    price = 0
    if 'code' in request.GET and 'report' in request.GET and request.GET.get('code') and request.GET.get('report'):
        code_id = request.GET.get('code')
        report_id = request.GET.get('report')
        code = get_object_or_404(Codes, pk=code_id)
        report = get_object_or_404(Reports, pk=report_id)
        price_dict = GetPrices(code, report.service_center)
        if 'price' in price_dict:
            price = price_dict['price']
    return render(request, 'reports/price_get.html', {'price': price})


# удаление отета
def ReportDelete(request, report_pk):
    report = get_object_or_404(Reports, pk=report_pk)
    if request.user.is_superuser or request.user == report.user:
        report.delete()
        messages.success(request, 'Отчет успешно удален !')
        return redirect('user_home')
    else:
        return HttpResponseForbidden()


# удаление отета
def RecordDelete(request, report_pk):
    record = get_object_or_404(ReportsRecords, pk=report_pk)
    report = record.report
    if request.user.is_superuser or request.user == report.user:
        record.delete()
        messages.success(request, 'Запись успешно удалена !')
        report.save()
        return redirect(report.get_absolute_url())
    else:
        return HttpResponseForbidden()


# --------------------------- ЗАКАЗ ДЕТАЛЕЙ -------------------------------------------

class OrderedParts(LoginRequiredMixin, TemplateView):
    """ список деталей, заказаннх пользователем """
    template_name = "reports/ordered_parts.html"
    
    def get_context_data(self):
        context = super().get_context_data()
        parts = ReportsParts.objects.filter(order_date__isnull=False, 
                                            record__report__service_center__user=self.request.user,
                                            ).exclude(Q(record__report__status=STATUS_ACCEPTED)|
                                                      Q(record__report__status=STATUS_PAYMENT)
                                                      )
        if 'filter' in self.request.GET:
            parts = parts.filter(title__iregex=self.request.GET['filter'])    
        context['parts'] = parts
        records = ReportsRecords.objects.filter(pk__in=parts.values('record').distinct())
        context['records'] = records
        reports = Reports.objects.filter(pk__in=records.values('report').distinct())
        context['reports'] = reports
        context['obj_count'] = parts.count()
        context['region'] = reports.first().service_center.region
        context['form'] = UserPartForm(self.request.GET)
        return context
    

class StaffOrderedParts(LoginRequiredMixin, StaffUserMixin, TemplateView):
    """ список всех заказанных деталей """
    template_name = "reports/ordered_parts_staff.html"
    
    def get_context_data(self):
        context = super().get_context_data()
        context['title'] = 'Заказанные детали'
        if self.request.user.is_superuser or self.request.user.groups.filter(name='GeneralStaff'):
            parts = ReportsParts.objects.filter(order_date__isnull=False)          
        else:
            parts = ReportsParts.objects.filter(
                Q(order_date__isnull=False)&(
                    Q(record__report__service_center__region__staff_user = self.request.user)|
                    Q(record__report__service_center__staff_user = self.request.user)                
                    )
                )
        if parts:
            if not ('show_send' in self.request.GET and self.request.GET['show_send']):
                parts = parts.filter(send_number__isnull=True)
            if 'filter' in self.request.GET and self.request.GET['filter']:
                parts = parts.filter(title__iregex=self.request.GET['filter'])    
            if 'center' in self.request.GET and self.request.GET['center']:
                parts = parts.filter(record__report__service_center=self.request.GET['center'])
        context['parts'] = parts.order_by('order_date')
        records = ReportsRecords.objects.filter(pk__in=parts.values('record').distinct())
        context['records'] = records
        reports = Reports.objects.filter(pk__in=records.values('report').distinct())
        context['reports'] = reports
        centers = ServiceCenters.objects.filter(pk__in=reports.values('service_center').distinct())
        context['centers'] = centers
        context['obj_count'] = parts.count()
        context['form'] = UserPartForm(self.request.GET)
        return context
    

@user_passes_test(staff_validation)
def SendParts(request):
    
    if request.method == 'POST':
        # создаем список кллючей таблицы Parts из параметров запроса
        parts_pk = []
        for key in request.POST.keys():
            if key.find('part') == 0:
                parts_pk.append(int(key.replace('part','')))
        if parts_pk:
            # если список не пуст записываем параметры отправки для деталей по списку
            parts = ReportsParts.objects.filter(pk__in=parts_pk)
            for part in parts:
                part.send_date = request.POST['send_date']
                part.send_number = request.POST['number']
                part.save()
            mail_send_parts(parts)
            messages.success(request, 'Данные об отправке записаны !')
        else:
            messages.error(request, 'Ни одна деталь не выбрана !')

    return redirect('staff-ordered-parts')


# -------------------------- СПЕЦИАЛЬНЫЕ ФУНКЦИИ ---------------------------------------


@user_passes_test(superuser_validation)
def accept_all(request):
    records = ReportsRecords.objects.filter(verified=False, report__status=STATUS_RECEIVED)
    for record in records:
        record.verified = True
        record.save()
    reports = Reports.objects.filter(status=STATUS_VERIFIED)
    for report in reports:
        report.status = STATUS_ACCEPTED
        report.save()
        email = report.service_center.user.email
        mail_note = """
        Для оплаты ваших услуг нам необхоидм Акт выполненных работ и Счет на ВСЮ сумуу по отчету
        (за работы + за детали + за выезд). Если вы еще не отправляли нам эти документы почтой или по ЭДО,
        пожалуйста отправьте сканы по электронной почте на адерс sergey.shaginyan@re-nova.com.
        В теме писмьао пожалуйста укажите название своего сервисного центра и отчетный месяц.
        """
        if email:
            SendReportSatus('shagi80@mail.ru', report, mail_note)
    return redirect('reports_list')