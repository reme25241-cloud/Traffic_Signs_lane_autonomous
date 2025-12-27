# users/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required

from django.db.models import Q
from django.conf import settings

from django.contrib.auth import get_user_model

from .forms import *
from .models import *

def base(request):
    return render(request, 'base.html')

def signup_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('dashboard')  # Redirect to dashboard after signup
        else:
            # If form is not valid, it will pass validation errors back to the template
            return render(request, 'registration/signup.html', {'form': form})
    else:
        form = CustomUserCreationForm()
    
    # If the form is accessed via GET (for example, on initial page load)
    return render(request, 'registration/signup.html', {'form': form})


# Handle user logout
def logout_view(request):
    logout(request)
    return redirect('login')

# profile
@login_required
def profile_view(request):
    return render(request, 'account/profile.html', {'user': request.user})

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .forms import ProfileForm

@login_required
def edit_profile(request):
    user = request.user  # Get the current logged-in user

    if request.method == 'POST':
        form = ProfileForm(request.POST, instance=user)  # Pre-fill the form with user's current data
        if form.is_valid():
            form.save()  # Save the updated data to the database
            return redirect('profile')  # Redirect to profile page (or dashboard, etc.)
    else:
        form = ProfileForm(instance=user)  # Display the form with user's current data

    return render(request, 'account/edit_profile.html', {'form': form})


# dashboard

from datetime import timedelta
from django.utils import timezone
from django.db.models import Count, Avg
from django.db.models.functions import TruncDate
from django.shortcuts import render

from .models import SignUpload, SignPrediction

@login_required
def dashboard(request):
    # Filters
    days = int(request.GET.get("days", 30))
    start_date = timezone.now() - timedelta(days=days)

    qs_pred = SignPrediction.objects.filter(created_at__gte=start_date)
    qs_up = SignUpload.objects.filter(created_at__gte=start_date)

    # KPI cards
    total_uploads = qs_up.count()
    total_predictions = qs_pred.count()
    avg_conf = qs_pred.aggregate(v=Avg("confidence"))["v"] or 0.0

    # Confidence buckets
    high_conf = qs_pred.filter(confidence__gte=90).count()
    mid_conf = qs_pred.filter(confidence__gte=70, confidence__lt=90).count()
    low_conf = qs_pred.filter(confidence__lt=70).count()

    # Top predicted signs
    top_signs_qs = (
        qs_pred.values("predicted_sign")
        .annotate(count=Count("id"), avg_conf=Avg("confidence"))
        .order_by("-count")[:10]
    )
    top_signs = list(top_signs_qs)

    # Daily trend (predictions per day)
    daily_qs = (
        qs_pred.annotate(day=TruncDate("created_at"))
        .values("day")
        .annotate(count=Count("id"), avg_conf=Avg("confidence"))
        .order_by("day")
    )
    daily = list(daily_qs)

    # Recent predictions table
    recent = (
        SignPrediction.objects.select_related("upload")
        .order_by("-created_at")[:20]
    )

    context = {
        "days": days,
        "total_uploads": total_uploads,
        "total_predictions": total_predictions,
        "avg_conf": round(avg_conf, 2),
        "high_conf": high_conf,
        "mid_conf": mid_conf,
        "low_conf": low_conf,
        "top_signs": top_signs,
        "daily": daily,
        "recent": recent,
    }
    return render(request, "dashboard/dashboard.html", context)


def about(request):
    return render(request, 'about/about.html')

def lane(request):
    return render(request, 'predict/lane.html')


# chat
@login_required
def user_list_view(request):
    users = get_user_model().objects.exclude(id=request.user.id)  
    return render(request, 'users/user_list.html', {'users': users})


@login_required
def chat_view_by_id(request, user_id):
    other_user = get_object_or_404(CustomUser, id=user_id)
    messages = Message.objects.filter(
        (Q(sender=request.user) & Q(receiver=other_user)) |
        (Q(sender=other_user) & Q(receiver=request.user))
    ).order_by('timestamp')

    if request.method == 'POST':
        text = request.POST.get('text')
        image = request.FILES.get('image')
        Message.objects.create(sender=request.user, receiver=other_user, text=text, image=image)
        return redirect('chat', user_id=other_user.id)  # ✅ Corrected: use user_id instead of username

    return render(request, 'users/chat.html', {
        'messages': messages,
        'receiver': other_user
    })

# Feedback

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from .forms import FeedbackForm
from .models import Feedback

@login_required
def feedback_view(request):
    if request.method == 'POST':
        form = FeedbackForm(request.POST)
        if form.is_valid():
            feedback = form.save(commit=False)
            feedback.user = request.user
            feedback.save()
            return render(request, 'feedback/feedback_thanks.html')  # Create this template
    else:
        form = FeedbackForm()
    return render(request, 'feedback/feedback.html', {'form': form})

@login_required
def view_feedbacks(request):
    if request.user.is_superuser:
        feedbacks = Feedback.objects.all().order_by('-created_at')
        return render(request, 'feedback/view_feedbacks.html', {'feedbacks': feedbacks})
    else:
        return redirect('dashboard')

# myapp/views.py
# myapp/views.py

# views.py
# myapp/views.py
import json
import os
import cv2
import numpy as np

from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.core.files.base import ContentFile
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from .models import SignUpload, SignPrediction

@login_required
def upload_sign_image(request):
    """
    1) Upload original image to DB
    2) Render form.html with image_url + upload_id
    """
    if request.method == "POST" and request.FILES.get("image"):
        upload = SignUpload.objects.create(original_image=request.FILES["image"])
        return render(request, "predict/form.html", {"image_url": upload.original_image.url, "upload_id": upload.id})

    return render(request, "predict/upload.html")  # your upload page


def _cv2_to_contentfile(img_bgr_or_gray, filename: str) -> ContentFile:
    """
    Convert a cv2 image (numpy array) to PNG bytes -> Django ContentFile.
    """
    # Ensure correct format for imencode
    success, buf = cv2.imencode(".png", img_bgr_or_gray)
    if not success:
        raise ValueError("Failed to encode image.")
    return ContentFile(buf.tobytes(), name=filename)


@require_http_methods(["POST"])
def save_prediction(request):
    """
    Receives JSON:
      { upload_id, predicted_sign, confidence, notes }

    Loads the original image from upload_id, generates derived images, saves SignPrediction.
    """
    try:
        payload = json.loads(request.body.decode("utf-8"))
        upload_id = payload.get("upload_id")
        predicted_sign = (payload.get("predicted_sign") or "").strip()
        confidence = float(payload.get("confidence") or 0.0)
        notes = payload.get("notes") or ""

        if not upload_id:
            return JsonResponse({"ok": False, "error": "upload_id missing"}, status=400)

        upload = get_object_or_404(SignUpload, id=upload_id)

        # Read original image from disk (MEDIA_ROOT path)
        img_path = upload.original_image.path
        bgr = cv2.imread(img_path)
        if bgr is None:
            return JsonResponse({"ok": False, "error": "Could not read original image"}, status=400)

        # === Processing pipeline ===
        gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)

        # Histogram equalization works on grayscale
        equalized = cv2.equalizeHist(blurred)

        # Otsu threshold (binary)
        _, thresh = cv2.threshold(equalized, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        # ROI: largest contour bbox (simple approach)
        roi = None
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if contours:
            c = max(contours, key=cv2.contourArea)
            x, y, w, h = cv2.boundingRect(c)
            # clamp + avoid tiny detections
            if w > 20 and h > 20:
                roi = bgr[y:y+h, x:x+w]

        pred = SignPrediction.objects.create(
            upload=upload,
            predicted_sign=predicted_sign,
            confidence=confidence,
            notes=notes
        )

        # Save derived images
        pred.grayscale_image.save(f"gray_{upload_id}_{pred.id}.png", _cv2_to_contentfile(gray, f"gray_{upload_id}_{pred.id}.png"))
        pred.blurred_image.save(f"blur_{upload_id}_{pred.id}.png", _cv2_to_contentfile(blurred, f"blur_{upload_id}_{pred.id}.png"))
        pred.equalized_image.save(f"eq_{upload_id}_{pred.id}.png", _cv2_to_contentfile(equalized, f"eq_{upload_id}_{pred.id}.png"))
        pred.thresholded_image.save(f"th_{upload_id}_{pred.id}.png", _cv2_to_contentfile(thresh, f"th_{upload_id}_{pred.id}.png"))

        if roi is not None:
            pred.roi_image.save(f"roi_{upload_id}_{pred.id}.png", _cv2_to_contentfile(roi, f"roi_{upload_id}_{pred.id}.png"))

        pred.save()

        return JsonResponse({
            "ok": True,
            "prediction_id": pred.id,
            "predicted_sign": pred.predicted_sign,
            "confidence": pred.confidence
        })

    except Exception as e:
        return JsonResponse({"ok": False, "error": str(e)}, status=500)


@login_required
def predict_live_input(request):
    """Prediction form page"""
    return render(request, 'predict/form_camera.html')
