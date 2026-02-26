from django.shortcuts import render
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
import json
import random

from .models import (
    SentenceItem,
    StudyLog,
    UserSentenceState,
    DailyCheckin,
)

# =========================
# 工具函数
# =========================

def normalize_text(text: str):
    if not text:
        return ""
    return text.strip().lower().replace(" ", "")


def is_correct_answer(task_type, user_answer, item: SentenceItem):
    ans = normalize_text(user_answer)

    if task_type == "tell_jp_from_zh":
        return ans == normalize_text(item.text_jp)

    if task_type == "tell_en_from_zh":
        return ans == normalize_text(item.text_en)

    if task_type == "cloze_jp":
        return "締め" in user_answer or "しめ" in user_answer

    if task_type == "cloze_en":
        return "fasten" in ans

    if task_type == "ask_jp_yesno":
        return ans in ["はい", "いいえ", "はい締めました"]

    return False


# =========================
# SRS 更新
# =========================

def update_memory(user, item: SentenceItem, correct: bool):
    state, _ = UserSentenceState.objects.get_or_create(
        user=user,
        item=item,
        defaults={"memory_level": 1, "error_count": 0}
    )

    if correct:
        state.memory_level = min(state.memory_level + 1, 7)
    else:
        state.memory_level = max(state.memory_level - 1, 1)
        state.error_count += 1

    intervals = {
        1: 10,
        2: 60,
        3: 1440,
        4: 4320,
        5: 10080,
        6: 20160,
        7: 43200,
    }

    minutes = intervals.get(state.memory_level, 60)
    state.next_review = timezone.now() + timezone.timedelta(minutes=minutes)
    state.save()

    return state


# =========================
# 生成训练任务
# =========================

def generate_tasks(item: SentenceItem):
    tasks = []

    if item.text_zh and item.text_jp:
        tasks.append({
            "type": "tell_jp_from_zh",
            "prompt": item.text_zh,
            "answer": item.text_jp
        })

    if item.text_jp:
        question = item.text_jp.replace("ください", "ましたか？")
        tasks.append({
            "type": "ask_jp_yesno",
            "question": question,
            "answer": "はい"
        })

    if item.text_jp:
        tasks.append({
            "type": "cloze_jp",
            "text": item.text_jp.replace("締め", "_____"),
            "answer": "締め"
        })

    if item.text_zh and item.text_en:
        tasks.append({
            "type": "tell_en_from_zh",
            "prompt": item.text_zh,
            "answer": item.text_en
        })

    if item.text_en:
        words = item.text_en.split(" ")
        if len(words) > 2:
            words[1] = "_____"
        tasks.append({
            "type": "cloze_en",
            "text": " ".join(words),
            "answer": "fasten"
        })

    random.shuffle(tasks)
    return tasks[:3]


# =========================
# API：获取下一题
# =========================

@login_required
def get_next_training(request):
    item = SentenceItem.objects.order_by("?").first()

    if not item:
        return JsonResponse({"error": "no data"})

    tasks = generate_tasks(item)

    audio_url = item.audio.url if item.audio else None

    return JsonResponse({
        "item_id": item.id,
        "tasks": tasks,
        "audio_url": audio_url
    })


# =========================
# API：提交答案
# =========================

@csrf_exempt
@login_required
def submit_answer(request):
    data = json.loads(request.body)

    item = SentenceItem.objects.get(id=data["item_id"])
    task_type = data["task_type"]
    user_answer = data["answer"]

    correct = is_correct_answer(task_type, user_answer, item)

    # 更新SRS
    state = update_memory(request.user, item, correct)

    # 学习日志
    StudyLog.objects.create(
        user=request.user,
        item=item,
        task_type=task_type,
        correct=correct
    )

    # 打卡记录
    today = timezone.now().date()
    checkin, _ = DailyCheckin.objects.get_or_create(
        user=request.user,
        date=today
    )
    checkin.count += 1
    checkin.save()

    return JsonResponse({
        "correct": correct,
        "memory_level": state.memory_level,
        "next_review": state.next_review
    })


# =========================
# 页面
# =========================

@login_required
def train_page(request):
    return render(request, "train_engine/train.html")


@login_required
def wrong_book(request):
    states = UserSentenceState.objects.filter(
        user=request.user
    ).filter(
        Q(error_count__gte=2) |
        Q(updated_at__gte=timezone.now() - timezone.timedelta(days=7))
    ).select_related("item")

    return render(request, "train_engine/wrong_book.html", {
        "states": states
    })


@login_required
def dashboard_view(request):
    user = request.user
    today = timezone.now().date()

    # 今日训练次数
    today_count = StudyLog.objects.filter(
        user=user,
        created_at__date=today
    ).count()

    # 正确率
    total = StudyLog.objects.filter(user=user).count()
    correct = StudyLog.objects.filter(user=user, correct=True).count()
    accuracy = round((correct / total) * 100, 1) if total > 0 else 0

    # memory level 分布
    level_stats = UserSentenceState.objects.filter(user=user).values(
        "memory_level"
    ).annotate(count=Count("id")).order_by("memory_level")

    # 最近7天训练趋势
    days = []
    counts = []
    for i in range(7):
        d = today - timezone.timedelta(days=i)
        c = StudyLog.objects.filter(user=user, created_at__date=d).count()
        days.append(d.strftime("%m-%d"))
        counts.append(c)

    days.reverse()
    counts.reverse()

    # 连续打卡天数
    streak = 0
    for i in range(30):
        d = today - timezone.timedelta(days=i)
        if DailyCheckin.objects.filter(user=user, date=d).exists():
            streak += 1
        else:
            break

    context = {
        "today_count": today_count,
        "accuracy": accuracy,
        "level_stats": list(level_stats),
        "days": days,
        "counts": counts,
        "streak": streak
    }

    return render(request, "train_engine/dashboard.html", context)


def home_page(request):
    return render(request, "train_engine/home.html")