from django.urls import path
from . import views as v

urlpatterns = [
    path('selcompay/', v.selcom_transactions_page, name='selcompay_page'),
    path('selcompay/actions/', v.selcom_transactions_actions, name="selcom_actions"),
    path('lipanamba/', v.lipa_transactions_page, name='lipanamba_page'),
    path('lipanamba/actions/', v.lipanamba_transactions_actions, name="lipanamba_actions"),
    path('debts/', v.debts_page, name='debts_page'),
    path('debts/actions/', v.debts_actions, name="debts_actions"),
    path('loans/', v.loans_page, name='loans_page'),
    path('loans/actions/', v.loans_actions, name="loans_actions"),
]
