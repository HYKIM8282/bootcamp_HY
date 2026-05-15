from django.contrib import admin

from .models import Post


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display  = ("id", "title", "category", "author", "created_at")
    list_filter   = ("category", "created_at")
    search_fields = ("title", "content", "author__username")
    ordering      = ("-created_at",)
    readonly_fields = ("created_at", "updated_at", "like_count", "view_count")
