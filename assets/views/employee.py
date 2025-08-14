from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from ..forms.employee import EmployeeForm
from ..models import Employee


@login_required
def employee_list(request):
    employees = Employee.objects.all()
    return render(request, "employee/list.html", {"employees": employees})


@login_required
def employee_create(request):
    if request.method == "POST":
        form = EmployeeForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("employee_list")
    else:
        form = EmployeeForm()
    return render(
        request, "employee/form.html", {"form": form, "title": "Add Employee"}
    )


@login_required
def employee_edit(request, pk):
    employee = get_object_or_404(Employee, pk=pk)
    if request.method == "POST":
        form = EmployeeForm(request.POST, instance=employee)
        if form.is_valid():
            form.save()
            return redirect("employee_list")
    else:
        form = EmployeeForm(instance=employee)
    return render(
        request, "employee/form.html", {"form": form, "title": "Edit Employee"}
    )


@login_required
def employee_delete(request, pk):
    employee = get_object_or_404(Employee, pk=pk)
    if request.method == "POST":
        employee.delete()
        return redirect("employee_list")
    return render(request, "employee/confirm_delete.html", {"employee": employee})
