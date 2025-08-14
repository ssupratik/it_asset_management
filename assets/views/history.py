from django.contrib import messages
from django.shortcuts import redirect, render

from ..forms.history import HistoryForm
from ..models import History


def history_list(request):
    histories = History.objects.select_related(
        "asset", "from_employee", "to_employee"
    ).order_by("-transfer_date")
    return render(request, "history/list.html", {"histories": histories})


def history_create(request):
    if request.method == "POST":
        form = HistoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "History record added successfully.")
            return redirect("history_list")
    else:
        form = HistoryForm()
    return render(request, "history/form.html", {"form": form})
