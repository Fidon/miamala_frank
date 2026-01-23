from django.urls import path
from . import views as v

urlpatterns = [
    path('selcompay/', v.selcompay, name='selcompay_page'),
    path('selcompay/actions/', v.selcompay_actions, name="selcom_actions"),
    path('lipanamba/', v.lipanamba, name='lipanamba_page'),
    path('lipanamba/actions/', v.lipanamba_actions, name="lipanamba_actions"),
    path('debts/', v.debts, name='debts_page'),
    path('debts/actions/', v.debts_actions, name="debts_actions"),
    path('loans/', v.loans, name='loans_page'),
    path('loans/actions/', v.loans_actions, name="loans_actions"),
    path('expenses/', v.expenses, name='expenses_page'),
    path('expenses/actions/', v.expenses_actions, name="expenses_actions"),
    path('mauzo/', v.mauzo, name='mauzo_page'),
    path('mauzo/actions/', v.mauzo_actions, name="mauzo_actions"),
]
