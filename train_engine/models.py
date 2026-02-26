from django.db import models
from django.contrib.auth.models import User


class Pattern(models.Model):
    """
    句型骨架：structure_* 使用 ___ 作为槽位
    answer_* 是槽位正确答案（严格判定）
    """
    name = models.CharField(max_length=100)

    structure_en = models.CharField(max_length=255, blank=True)
    structure_jp = models.CharField(max_length=255, blank=True)
    structure_kr = models.CharField(max_length=255, blank=True)

    meaning_zh = models.CharField(max_length=255, blank=True)

    answer_en = models.CharField(max_length=100, blank=True)
    answer_jp = models.CharField(max_length=100, blank=True)
    answer_kr = models.CharField(max_length=100, blank=True)

    class Meta:
        verbose_name = "句型骨架 Pattern"
        verbose_name_plural = "句型骨架 Patterns"

    def __str__(self):
        return self.name


class Course(models.Model):
    """
    课程：一组句子/词汇
    """
    name = models.CharField(max_length=120, unique=True)

    class Meta:
        verbose_name = "书册 Course"
        verbose_name_plural = "书册 Courses"
    description = models.CharField(max_length=255, blank=True)
    items = models.ManyToManyField("SentenceItem", blank=True, related_name="courses")

    def __str__(self):
        return self.name
    

class Lesson(models.Model):
    course = models.ForeignKey("Course", on_delete=models.CASCADE, related_name="lessons")
    name = models.CharField(max_length=100)
    order = models.IntegerField(default=1)

    items = models.ManyToManyField("SentenceItem", blank=True)

    class Meta:
        ordering = ["order"]
        verbose_name = "章节 Lesson"
        verbose_name_plural = "章节 Lessons"


    class Meta:
        ordering = ["order"]

    def __str__(self):
        return f"{self.course.name} - {self.name}"


class UserPlan(models.Model):
    """
    学习计划：用户当前启用的课程 + 每日目标
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    daily_goal = models.IntegerField(default=20)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ("user", "course")
        verbose_name = "学习计划 Plan"
        verbose_name_plural = "学习计划 Plans"

    def __str__(self):
        return f"{self.user.username} - {self.course.name}"


class SentenceItem(models.Model):
    """
    全局内容库（共享给所有用户）
    多用户SRS不放这里，放 UserSentenceState
    """
    text_zh = models.TextField(blank=True)

    text_en = models.TextField(blank=True)
    text_jp = models.TextField(blank=True)
    text_kr = models.TextField(blank=True)

    # 真人音频上传（可空）
    audio_en_file = models.FileField(upload_to="audio/en/", blank=True, null=True)
    audio_jp_file = models.FileField(upload_to="audio/jp/", blank=True, null=True)
    audio_kr_file = models.FileField(upload_to="audio/kr/", blank=True, null=True)

    pattern = models.ForeignKey(Pattern, null=True, blank=True, on_delete=models.SET_NULL)

    class Meta:
        verbose_name = "句子 Sentence"
        verbose_name_plural = "句子 Sentences"

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"ZH:{self.text_zh[:20]} EN:{self.text_en[:20]} JP:{self.text_jp[:20]} KR:{self.text_kr[:20]}"


class UserSentenceState(models.Model):
    """
    每个用户对每个句子的独立记忆状态（核心：多用户SRS）
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    item = models.ForeignKey(SentenceItem, on_delete=models.CASCADE)

    memory_level = models.IntegerField(default=1)
    next_review = models.DateTimeField(null=True, blank=True)
    error_count = models.IntegerField(default=0)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("user", "item")
        verbose_name = "记忆状态 State"
        verbose_name_plural = "记忆状态 States"

    def __str__(self):
        return f"{self.user.username} item={self.item_id} Lv={self.memory_level}"


class StudyLog(models.Model):
    """
    训练日志（Dashboard用）：每次提交都记录
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    item = models.ForeignKey(SentenceItem, on_delete=models.CASCADE)
    task_type = models.CharField(max_length=50)
    correct = models.BooleanField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "学习记录 Log"
        verbose_name_plural = "学习记录 Logs"

    def __str__(self):
        return f"{self.user.username} item={self.item_id} {self.correct} {self.created_at}"
    

class DailyCheckin(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField()
    count = models.IntegerField(default=0)

    class Meta:
        unique_together = ("user", "date")
        verbose_name = "每日打卡 Checkin"
        verbose_name_plural = "每日打卡 Checkins"