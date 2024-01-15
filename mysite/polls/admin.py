from django.contrib import admin

from .models import Question, Choice
# Register your models here.

# admin.site.register(Question)


class ChoiceInline(admin.TabularInline):
    model = Choice
    extra = 3

class QuestionAdmin(admin.ModelAdmin):
    fieldsets = [
        (None, {"fields": ["question_text"]}),
        ("Date Information", {"fields": ["pub_date"], "classes": ["collapse"]}),
    ]
    inlines = [ChoiceInline]
    list_display = ["question_text", "pub_date", "was_published_recently", "id"]
    list_filter = ["pub_date"]
    search_fields = ["question_text"]


class ChoiceAdmin(admin.ModelAdmin):
    search_fields = ["question__question_text"]
    search_help_text = "Search for the question"

admin.site.register(Choice, ChoiceAdmin)

admin.site.register(Question, QuestionAdmin)


