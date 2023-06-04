""" url приложения статистики """
from django.urls import path
from .views import ManagerWork, SumForPayment, export_sum_for_payment


urlpatterns = [
   # path('', start_login, name='login_page'),
   path('manager-work', ManagerWork.as_view(), name='manager_work_page'),
   path('sum-for-payment', SumForPayment.as_view(), name='sum-for-payment'),
   path('export-sum-for-payment', export_sum_for_payment, name='export-sum-for-payment'),
]