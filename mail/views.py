""" представления почтовых сообщений """

from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.contrib.auth.models import User


def mail_ordered_parts(record, parts):
    """ уведомление менеджера о заказе запчастей """

    # формируем список получателей
    mails = []
    main_email = record.report.service_center.staff_user.email
    if main_email:
        mails.append(main_email)
    staffs = User.objects.filter(groups__name='GeneralStaff')
    for staff in staffs:
        if staff.email:
            mails.append(staff.email)
    # если есть кому отправлять формируем письмо
    if mails:
        # рендеринг HTML шаблона
        html_content = render_to_string(
                'mail/parts_order.html',
                {'record': record, 'parts': parts,}
            )
        # подготовка сообщения
        msg = EmailMultiAlternatives(
                subject = f'RENOVA. Заказа на запчасти от {record.report.service_center}',
                body =  f'RENOVA. Заказа на запчасти от {record.report.service_center}',
                from_email = 'report_service@re-nova.com',
                #to = mails
                to = ['shagi80@mail.ru']
            )                
        # привязка HTML и отправка
        msg.attach_alternative(html_content, "text/html")
        msg.send()    
        return True
    
    return False        


def mail_send_parts(parts):
    """ уведомление СЦ об отправке запчастей """

    # формируем список получателей
    mails = [parts.first().record.report.service_center.user.email, ]
    # если есть кому отправлять формируем письмо
    if mails:
        # рендеринг HTML шаблона
        html_content = render_to_string(
                'mail/parts_send.html',
                {'parts': parts,}
            )
        # подготовка сообщения
        msg = EmailMultiAlternatives(
                subject = f'RENOVA. Ваш заказ на запчасти отправлен.',
                body =  f'RENOVA. Ваш заказ на запчасти отправлен.',
                from_email = 'report_service@re-nova.com',
                to = mails
                #to = ['shagi80@mail.ru']
            )                
        # привязка HTML и отправка
        msg.attach_alternative(html_content, "text/html")
        msg.send()    
        return True
    
    return False        

