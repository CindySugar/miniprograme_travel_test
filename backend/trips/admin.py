from django.contrib import admin

from .models import Expense, ExpenseShare, Settlement, Travel, TravelMember, User

admin.site.register(User)
admin.site.register(Travel)
admin.site.register(TravelMember)
admin.site.register(Expense)
admin.site.register(ExpenseShare)
admin.site.register(Settlement)
