from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from train_engine.views import (
    get_next_training,
    submit_answer,
    train_page,
    dashboard_view,
    home_page, 
    wrong_book,
)

# ===== Admin 中英双语标题 =====
admin.site.site_header = "Language Engine 语言学习系统"
admin.site.site_title = "Language Engine Admin"
admin.site.index_title = "语言学习系统后台管理"

urlpatterns = [
    path("", home_page),
    path("wrong/", wrong_book),

    path("admin/", admin.site.urls),

    # Auth（登录/退出）
    path("accounts/", include("django.contrib.auth.urls")),

    # API
    path("api/train/next", get_next_training),
    path("api/train/answer", submit_answer),

    # Pages
    path("train/", train_page),
    path("dashboard/", dashboard_view),
]

# 开发环境提供媒体文件（音频上传）
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)