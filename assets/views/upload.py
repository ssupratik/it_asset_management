from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import render, redirect
import csv, io

from ..forms.bulk_upload import BulkUploadForm
from ..models import Employee, Asset, AssetType

def parse_composite_field(field_value):
    """
    Parse a composite field in the format:
      "Laptop: Working; Monitor: Good; UPS: Not Working"
    and return a mapping { 'laptop': 'Working', 'monitor': 'Good', ... }
    """
    mapping = {}
    if field_value:
        parts = field_value.split(';')
        for part in parts:
            if ':' in part:
                key, val = part.split(":", 1)
                mapping[key.strip().lower()] = val.strip()
    return mapping

def process_peripheral(row, peripheral_name, employee_obj, cond_map, rem_map):
    """
    Creates an asset record for a peripheral if its primary cell is non-empty.
    For the peripheral, the following CSV columns are expected:
      - <Peripheral Name>
      - <Peripheral Name> Serial number
      - <Peripheral Name> Year of Purchase
    """
    value = row.get(peripheral_name, "").strip()
    if not value:
        return 0
    serial = row.get(f"{peripheral_name} Serial number", "").strip()
    yop = row.get(f"{peripheral_name} Year of Purchase", "").strip()
    try:
        year = int(yop) if yop else 0
    except ValueError:
        year = 0
    # Lookup (or create) AssetType using a fixed name; you can adjust if needed.
    asset_type, _ = AssetType.objects.get_or_create(name=peripheral_name)
    condition = cond_map.get(peripheral_name.lower(), "working")
    remarks = rem_map.get(peripheral_name.lower(), "")
    Asset.objects.create(
        type=asset_type,
        make_model=value,  # using the cell value as the model info
        serial_number=serial or None,
        year_of_purchase=year,
        condition=condition,
        remarks=remarks,
        alloted_to=employee_obj,
    )
    return 1

@login_required
@permission_required('assets.add_asset', raise_exception=True)
def bulk_upload(request):
    if request.method == "POST":
        form = BulkUploadForm(request.POST, request.FILES)
        if form.is_valid():
            csv_file = form.cleaned_data["csv_file"]
            try:
                data = csv_file.read().decode("utf-8")
            except UnicodeDecodeError:
                messages.error(request, "Error decoding CSV file. Please ensure it is encoded in UTF-8.")
                return redirect("bulk_upload")

            io_string = io.StringIO(data)
            reader = csv.DictReader(io_string)
            created_count = 0
            errors = []
            with transaction.atomic():
                for row in reader:
                    # Process common employee info
                    print("Processing row:", row)
                    alloted_to_val = row.get("Alloted To", "").strip()
                    employee_obj = None
                    if alloted_to_val:
                        names = alloted_to_val.split()
                        first_name = names[0]
                        last_name = " ".join(names[1:]) if len(names) > 1 else ""
                        try:
                            employee_obj, _ = Employee.objects.get_or_create(
                                first_name=first_name,
                                last_name=last_name,
                                defaults={
                                    "designation": "Unknown",
                                    "section": "",
                                    "email": None,
                                    "phone": None,
                                }
                            )
                        except Exception as e:
                            errors.append(f"Row {reader.line_num} Employee error: {str(e)}")
                    
                    # Parse composite Condition and REMARKS fields
                    cond_map = parse_composite_field(row.get("Condition", ""))
                    rem_map = parse_composite_field(row.get("REMARKS", ""))
                    
                    # Process main asset (CPU)
                    device_val = row.get("Device", "").strip()
                    if device_val:
                        # Use "Device" to lookup AssetType
                        asset_type, _ = AssetType.objects.get_or_create(name=device_val)
                    else:
                        errors.append(f"Row {reader.line_num} missing Device")
                        continue

                    # Main asset fields
                    serial_no = row.get("Serial No.", "").strip()
                    # Although the CSV has a column "Make model", per mapping we use PROCESSOR for make_model.
                    processor = row.get("PROCESSOR", "").strip()
                    ram = row.get("RAM", "").strip()
                    hdd = row.get("HDD", "").strip()
                    ssd = row.get("SSD", "").strip()
                    os_val = row.get("OS", "").strip()
                    yop = row.get("Year of Purchase", "").strip()
                    try:
                        year = int(yop) if yop else 0
                    except ValueError:
                        year = 0

                    main_condition = cond_map.get(device_val.lower(), "working")
                    main_remarks = rem_map.get(device_val.lower(), "")
                    try:
                        Asset.objects.create(
                            type=asset_type,
                            # Here we use PROCESSOR as the make_model per mapping
                            make_model=processor,
                            serial_number=serial_no or None,
                            ram=ram,
                            hdd=hdd,
                            ssd=ssd,
                            os=os_val,
                            year_of_purchase=year,
                            condition=main_condition,
                            remarks=main_remarks,
                            alloted_to=employee_obj,
                        )
                        created_count += 1
                    except Exception as e:
                        errors.append(f"Row {reader.line_num} Main Asset error: {str(e)}")
                    
                    # Process peripherals: Monitor, Keyboard and Mouse, UPS, Printer, Speaker
                    peripheral_assets = [
                        "Monitor",
                        "Keyboard and Mouse",
                        "UPS",
                        "Printer",
                        "Speaker",
                    ]
                    for peripheral in peripheral_assets:
                        created_count += process_peripheral(row, peripheral, employee_obj, cond_map, rem_map)
            print("Finished processing. Created count:", created_count)
            print("Errors:", errors)
            if errors:
                for err in errors:
                    messages.error(request, err)
            messages.success(request, f"Successfully uploaded {created_count} asset record(s).")
            return redirect("bulk_upload")
    else:
        form = BulkUploadForm()
    return render(request, "assets/bulk_upload.html", {"form": form})


@login_required
def download_sample_csv(request):
    header = (
        "Sl.No.,Alloted To,Device,Make model,Serial No.,PROCESSOR,RAM,HDD,SSD,OS,"
        "Year of Purchase,Monitor,Monitor Serial number,Monitor Year of Purchase,"
        "Keyboard and Mouse,UPS,UPS Serial number,UPS Year of Purchase,"
        "Printer,Printer Serial number,Printer Year of Purchase,Speaker,"
        "Condition,REMARKS\n"
    )
    sample = (
        "1,John Doe,Laptop,HP ProBook,SN12345,Intel Core i7,8 GB,1 TB,256 GB,Windows 10,2023,"
        "Dell 24\",MSN456,2022,Logitech Combo,UPS Corp,UPS789,2023,HP LaserJet,PRN001,2023,Creative,"
        "Laptop: Working; Monitor: Good; Keyboard and Mouse: Working; UPS: Working; Printer: Not Working; Speaker: Working,"
        "Laptop: System is in Working Condition; Monitor: Clear display; Keyboard and Mouse: Responsive; UPS: Stable; Printer: Requires service; Speaker: Clear sound\n"
    )
    response = HttpResponse(header + sample, content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="combined_sample.csv"'
    return response