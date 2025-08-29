from django.shortcuts import get_object_or_404, render

from ..models import AssetHistory as History


def history_list(request):
    histories = History.objects.select_related(
        "asset", "employee", "performed_by"
    ).order_by("-timestamp")
    return render(request, "history/list.html", {"histories": histories})


def history_detail(request, pk):
    history = get_object_or_404(
        History.objects.select_related("asset", "employee", "performed_by"), pk=pk
    )
    return render(request, "history/detail.html", {"history": history})
