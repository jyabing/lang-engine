from django.contrib import admin
from django.utils.html import format_html
from .models import (
    Pattern,
    SentenceItem,
    Course,
    UserPlan,
    UserSentenceState,
    StudyLog,
    Lesson,
)

# =========================
# Pattern 句型骨架（增强：预览 Cloze）
# =========================
@admin.register(Pattern)
class PatternAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "meaning_zh",
        "preview_en",
        "preview_jp",
        "preview_kr",
    )
    search_fields = ("name", "meaning_zh")

    def preview_en(self, obj):
        if obj.structure_en and obj.answer_en:
            return obj.structure_en.replace("___", f"[{obj.answer_en}]")
        return "-"
    preview_en.short_description = "EN示例"

    def preview_jp(self, obj):
        if obj.structure_jp and obj.answer_jp:
            return obj.structure_jp.replace("___", f"[{obj.answer_jp}]")
        return "-"
    preview_jp.short_description = "JP示例"

    def preview_kr(self, obj):
        if obj.structure_kr and obj.answer_kr:
            return obj.structure_kr.replace("___", f"[{obj.answer_kr}]")
        return "-"
    preview_kr.short_description = "KR示例"


# =========================
# SentenceItem 句子库（增强：显示 Cloze 预览）
# =========================
@admin.register(SentenceItem)
class SentenceItemAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "text_zh",
        "text_en",
        "text_jp",
        "text_kr",
        "pattern",
        "cloze_preview",
    )
    search_fields = (
        "text_zh",
        "text_en",
        "text_jp",
        "text_kr",
    )
    list_filter = ("pattern",)
    autocomplete_fields = ["pattern"]

    def cloze_preview(self, obj):
        if obj.pattern and obj.pattern.structure_en:
            return obj.pattern.structure_en.replace("___", "_____")
        return "-"
    cloze_preview.short_description = "Cloze预览"


# =========================
# Course 课程
# =========================
@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)
    filter_horizontal = ("items",)


# =========================
# UserPlan 学习计划
# =========================
@admin.register(UserPlan)
class UserPlanAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "course",
        "daily_goal",
        "is_active",
    )
    list_filter = (
        "is_active",
        "course",
    )
    search_fields = ("user__username",)


# =========================
# UserSentenceState 记忆状态（增强：彩色等级）
# =========================
@admin.register(UserSentenceState)
class UserSentenceStateAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "item",
        "colored_level",
        "error_count",
        "next_review",
        "updated_at",
    )
    list_filter = ("memory_level",)
    search_fields = ("user__username",)

    def colored_level(self, obj):
        level = obj.memory_level
        colors = {
            1: "red",
            2: "orange",
            3: "gold",
            4: "blue",
            5: "green",
            6: "purple",
            7: "black",
        }
        color = colors.get(level, "black")
        return format_html(
            f'<b style="color:{color}">Lv.{level}</b>'
        )
    colored_level.short_description = "记忆等级"


# =========================
# StudyLog 学习日志（增强：错误标红）
# =========================
@admin.register(StudyLog)
class StudyLogAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "item",
        "task_type",
        "result_colored",
        "created_at",
    )
    list_filter = (
        "correct",
        "task_type",
        "created_at",
    )
    search_fields = ("user__username",)

    def result_colored(self, obj):
        if obj.correct:
            return format_html('<span style="color:green">✔ 正确</span>')
        else:
            return format_html('<span style="color:red">✘ 错误</span>')
    result_colored.short_description = "结果"

@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ("name", "course", "order")
    list_filter = ("course",)
    filter_horizontal = ("items",)