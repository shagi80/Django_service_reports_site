from django.urls import path, re_path
from .views import *

urlpatterns = [
    path('report-export/<int:report_pk>', export_report_xls, name='report_export'),
    path('reports-list/', ReportsForStaff.as_view(), name='reports_list'),
    path('report-change-status/', ReportChangeStatus, name='report-change-status'),
    path('record-remarks/', RecordRemarks, name='record-remarks'),
    path('record-verified/', RecordVerified, name='record-verified'),
    path('report-add/', ReportAdd, name='report-add'),
    path('report-update/<int:report_pk>', ReportUpdate, name='report-update'),
    path('report-send/', ReportSend, name='report-send'),
    path('report-change-status/', ReportChangeStatus, name='report-change-status'),
    path('report/<int:pk>', ReportDetail.as_view(), name='report_page'),
    path('report-delete/<int:report_pk>', ReportDelete, name='report_delete'),

    path('record-add/<int:report_pk>', RecordAdd.as_view(), name='record_add_page'),
    path('record-update/<int:pk>', RecordUpdate.as_view(), name='record_update_page'),
    path('record-delete/<int:report_pk>', RecordDelete, name='record_delete'),
    path('record-copy/', RecordCopy, name='record-copy'),
    path('record-remove/', RecordRemove, name='record-remove'),

    path('ajax/codes-load/', load_codes_data, name='ajax_load_codes'),
    path('ajax/models-load/', load_models_data, name='ajax_load_models'),
    path('ajax/work-price-load/', load_work_price_data, name='ajax_load_work-price'),

    path('user-ordered-parts/', OrderedParts.as_view(), name='ordered-parts'),
    path('staff-ordered-parts/', StaffOrderedParts.as_view(), name='staff-ordered-parts'),
    path('send-parts/', SendParts, name='send-parts'),
    path('accept-all/', accept_all, name='accept-all'),

]
