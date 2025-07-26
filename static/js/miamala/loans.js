// fill update form
function fill_edit_form(rowIndex, id, str) {
  if (str == "edit") {
    var row = $("#loans_table tbody tr:nth-child(" + (rowIndex + 1) + ")");
    var names = $("td:nth-child(3)", row).text();
    var loan = $("td:nth-child(6)", row).text().replace(/,/g, "");
    var describe = $("td:nth-child(1)", row).attr("data-bs-describe");
    describe = describe == "null" ? "" : describe;
    $("#loan_edit_names").val(names);
    $("#loan_edit_amount").val(parseFloat(loan));
    $("#loan_edit_description").val(describe);
    $("#loan_id").val(id);
    $("#update_loan_modal").modal("show");
  } else {
    $("#loan_del_id").val(id);
    $("#delete_loan_modal").modal("show");
  }
}

// check loan numbers
function check_loan(loan, paid) {
  var status = false;
  if (paid < 0) {
    if (Math.abs(paid) <= loan) {
      status = true;
    }
  } else {
    status = true;
  }
  return status;
}

// format dates for DataTable
function format_dates(date_str, str) {
  if (date_str == "today") {
    var today = new Date();
  } else {
    var today = new Date(date_str);
  }
  const months = [
    "Jan",
    "Feb",
    "Mar",
    "Apr",
    "May",
    "Jun",
    "Jul",
    "Aug",
    "Sept",
    "Oct",
    "Nov",
    "Dec",
  ];
  const day = today.getDate() < 10 ? "0" + today.getDate() : today.getDate();
  const hours =
    today.getHours() < 10 ? "0" + today.getHours() : today.getHours();
  const minutes =
    today.getMinutes() < 10 ? "0" + today.getMinutes() : today.getMinutes();
  if (str == "datetime") {
    return `${day}-${
      months[today.getMonth()]
    }-${today.getFullYear()} ${hours}:${minutes}`;
  } else {
    return `${day}-${months[today.getMonth()]}-${today.getFullYear()}`;
  }
}

$(function () {
  // Get the CSRF token
  const CSRF_TOKEN = document
    .querySelector('meta[name="csrf-token"]')
    .getAttribute("content");
  const dateCache = { start: null, end: null };
  $("#transactions_toggle").click();

  // New loan
  $("#new_loan_form").submit(function (e) {
    e.preventDefault();
    var loan_amount = $("#loan_amount").val();
    var formSms = $("#new_loan_form .formsms");
    var loan_names = $.trim($("#loan_names").val());
    var loan_describe = $.trim($("#loan_description").val());
    var formData = new FormData();
    formData.append("names", loan_names);
    formData.append("amount", loan_amount);
    formData.append("describe", loan_describe);

    var submitBtn = $("#new_loan_btn");
    $.ajax({
      type: "POST",
      url: $(this).attr("action"),
      data: formData,
      dataType: "json",
      contentType: false,
      processData: false,
      headers: {
        "X-CSRFToken": CSRF_TOKEN,
      },
      beforeSend: function () {
        submitBtn
          .html("<i class='fas fa-spinner fa-pulse'></i>")
          .attr("type", "button");
      },
      success: function (response) {
        submitBtn.html("Add").attr("type", "submit");
        var alert;
        if (response.success) {
          alert = `<i class="fas fa-check-circle"></i> &nbsp; ${response.sms}`;
          formSms.removeClass("alert-danger").addClass("alert-success");
          $("#new_loan_form")[0].reset();
          table.draw();
        } else {
          alert = `<i class="fas fa-exclamation-circle"></i> &nbsp; ${response.sms}`;
          formSms.removeClass("alert-success").addClass("alert-danger");
        }
        formSms.html(alert).slideDown("fast").delay(2000).slideUp("fast");
      },
      error: function (xhr, status, error) {
        console.error(error);
      },
    });
  });

  // submit loan update form
  $("#edit_loan_form").submit(function (e) {
    e.preventDefault();
    var formSms = $("#edit_loan_form .formsms");
    var submitBtn = $("#loan_edit_btn");

    var loan_names = $.trim($("#loan_edit_names").val());
    var loan_amount = parseFloat($("#loan_edit_amount").val());
    var loan_paid = parseFloat($("#loan_edit_paid").val());
    var loan_describe = $.trim($("#loan_edit_description").val());

    if (check_loan(loan_amount, loan_paid)) {
      var formData = new FormData();
      formData.append("loan_id", $("#loan_id").val());
      formData.append("names", loan_names);
      formData.append("paid", loan_paid);
      formData.append("describe", loan_describe);

      $.ajax({
        type: "POST",
        url: $(this).attr("action"),
        data: formData,
        dataType: "json",
        contentType: false,
        processData: false,
        headers: {
          "X-CSRFToken": CSRF_TOKEN,
        },
        beforeSend: function () {
          submitBtn
            .html("<i class='fas fa-spinner fa-pulse'></i>")
            .attr("type", "button");
        },
        success: function (response) {
          submitBtn.html("Update").attr("type", "submit");
          var alert;
          if (response.success) {
            $("#loan_edit_amount").val(loan_amount + loan_paid);
            $("#loan_edit_paid").val("");
            alert = `<i class="fas fa-check-circle"></i> &nbsp; ${response.sms}`;
            formSms.removeClass("alert-danger").addClass("alert-success");
            table.draw();
          } else {
            alert = `<i class="fas fa-exclamation-circle"></i> &nbsp; ${response.sms}`;
            formSms.removeClass("alert-success").addClass("alert-danger");
          }
          formSms.html(alert).slideDown("fast").delay(2000).slideUp("fast");
        },
        error: function (xhr, status, error) {
          console.error(error);
        },
      });
    } else {
      var alert = `<i class="fas fa-exclamation-circle"></i> &nbsp; Paid amount cannot exceed current loan!`;
      formSms
        .removeClass("alert-success")
        .addClass("alert-danger")
        .html(alert)
        .slideDown("fast")
        .delay(2000)
        .slideUp("fast");
    }
  });

  // delete loan
  $("#del_loan_form").submit(function (e) {
    e.preventDefault();
    var del_loan_id = $("#loan_del_id").val();
    if (parseInt(del_loan_id) > 0) {
      var formData = new FormData();
      formData.append("delete_id", del_loan_id);

      var submitBtn = $("#loan_delete_btn");
      var formSms = $("#del_loan_form .formsms");

      $.ajax({
        type: "POST",
        url: $(this).attr("action"),
        data: formData,
        dataType: "json",
        contentType: false,
        processData: false,
        headers: {
          "X-CSRFToken": CSRF_TOKEN,
        },
        beforeSend: function () {
          submitBtn
            .html("<i class='fas fa-spinner fa-pulse'></i>")
            .attr("type", "button");
        },
        success: function (response) {
          submitBtn.html("Yes").attr("type", "submit");
          var alert;
          if (response.success) {
            $("#loan_del_id").val("");
            alert = `<i class="fas fa-check-circle"></i> &nbsp; ${response.sms}`;
            formSms.removeClass("alert-danger").addClass("alert-success");
            table.draw();
          } else {
            alert = `<i class="fas fa-exclamation-circle"></i> &nbsp; ${response.sms}`;
            formSms.removeClass("alert-success").addClass("alert-danger");
          }
          formSms.html(alert).slideDown("fast").delay(2000).slideUp("fast");
        },
        error: function (xhr, status, error) {
          console.error(error);
        },
      });
    }
  });

  // Get dates from dateFilter modal
  function get_dates_range() {
    const minDateStr = $("#min_loan_date").val();
    const maxDateStr = $("#max_loan_date").val();

    try {
      let dtStartUtc = null;
      let dtEndUtc = null;

      if (minDateStr) {
        const startDateLocal = new Date(`${minDateStr}T00:00:00.000`);
        if (isNaN(startDateLocal.getTime())) {
          throw new Error("Invalid start date format");
        }
        dtStartUtc = startDateLocal.toISOString();
      }

      if (maxDateStr) {
        const endDateLocal = new Date(`${maxDateStr}T23:59:59.999`);
        if (isNaN(endDateLocal.getTime())) {
          throw new Error("Invalid end date format");
        }
        dtEndUtc = endDateLocal.toISOString();
      }

      // Cache the results
      dateCache.start = dtStartUtc;
      dateCache.end = dtEndUtc;

      return { start: dtStartUtc, end: dtEndUtc };
    } catch (error) {
      console.error("Date processing error:", error);
      return { start: null, end: null };
    }
  }

  // DataTable configs
  $("#loans_table thead tr")
    .clone(true)
    .attr("class", "filters")
    .appendTo("#loans_table thead");

  var table = $("#loans_table").DataTable({
    fixedHeader: true,
    processing: true,
    serverSide: true,
    ajax: {
      url: $("#loans_page_url").val(),
      type: "POST",
      data: (d) => {
        const dateRange = get_dates_range();
        d.startdate = dateRange.start;
        d.enddate = dateRange.end;
      },
      dataType: "json",
      headers: { "X-CSRFToken": CSRF_TOKEN },
    },
    columns: [
      { data: "count" },
      { data: "dates" },
      { data: "names" },
      { data: "amount" },
      { data: "paid" },
      { data: "balance" },
      { data: "action" },
    ],
    order: [[1, "desc"]],
    paging: true,
    pageLength: 10,
    lengthChange: true,
    autoWidth: true,
    searching: true,
    bInfo: true,
    bSort: true,
    orderCellsTop: true,
    columnDefs: [
      {
        targets: [0, 6],
        orderable: false,
      },
      {
        targets: 6,
        createdCell: function (cell, cellData, rowData, rowIndex, colIndex) {
          var btn = `<button class="btn btn-sm btn-dblue text-white me-1" onclick="fill_edit_form(${rowIndex}, ${rowData.id}, 'edit')"><i class="fas fa-edit"></i></button> <button class="btn btn-sm btn-danger" onclick="fill_edit_form('', ${rowData.id}, 'del')"><i class="fas fa-trash"></i></button>`;
          $(cell).html(btn);
        },
      },
      {
        targets: 0,
        createdCell: function (cell, cellData, rowData, rowIndex, colIndex) {
          var info = rowData.describe == "" ? "null" : rowData.describe;
          $(cell).attr("data-bs-toggle", "tooltip");
          $(cell).attr("title", "Comment: " + info);
          $(cell).attr("data-bs-describe", info);
        },
      },
      {
        targets: "_all",
        className: "align-middle text-nowrap text-center",
      },
    ],
    dom: "lBfrtip",
    drawCallback: function (response) {
      var grand_totals = response.json.grand_totals;
      var grand_obj = {
        total_amount: grand_totals.total_amount,
        total_paid: grand_totals.total_paid,
        total_balance: grand_totals.total_balance,
      };
      updateFooter(grand_obj);
    },
    initComplete: function () {
      var api = this.api();
      api
        .columns([0, 1, 2, 3, 4, 5, 6])
        .eq(0)
        .each(function (colIdx) {
          var cell = $(".filters th").eq(
            $(api.column(colIdx).header()).index()
          );
          $(cell).addClass("bg-white");

          if (colIdx == 0 || colIdx == 6) {
            cell.html("");
          } else if (colIdx == 1) {
            var calendar = `<button type="button" class="btn btn-primary text-white" data-bs-toggle="modal" data-bs-target="#dateFilterModal"><i class="fas fa-calendar-alt"></i></button>`;
            cell.html(calendar);
            cell.addClass("text-center");
            $("#date_filter_clear").on("click", function () {
              $("#min_loan_date").val("");
              $("#max_loan_date").val("");
            });
            $("#date_filter_btn").on("click", function () {
              table.draw();
            });
          } else {
            $(cell).html(
              "<input type='text' class='text-charcoal' placeholder='Filter..'/>"
            );
            $(cell).addClass("text-center");
            $(
              "input",
              $(".filters th").eq($(api.column(colIdx).header()).index())
            )
              .off("keyup change")
              .on("keyup change", function (e) {
                e.stopPropagation();
                $(this).attr("title", $(this).val());
                var regexr = "{search}";
                var cursorPosition = this.selectionStart;
                api
                  .column(colIdx)
                  .search(
                    this.value != ""
                      ? regexr.replace("{search}", this.value)
                      : "",
                    this.value != "",
                    this.value == ""
                  )
                  .draw();
                $(this)
                  .focus()[0]
                  .setSelectionRange(cursorPosition, cursorPosition);
              });
          }
        });
    },
  });

  // table global search
  $("#search_loan_field").keyup(function () {
    table.search($(this).val()).draw();
  });

  // clear all table filters
  $("#loans_filter_clear").click(function (e) {
    e.preventDefault();
    $("#search_loan_field").val("");
    $("#min_loan_date").val("");
    $("#max_loan_date").val("");
    $('.filters input[type="text"]').val("");
    table.search("").columns().search("").draw();
  });

  // update footer values
  function updateFooter(totals) {
    var footer = $(table.table().footer());
    var report_dates = "All time";
    var date_start = $("#min_loan_date").val();
    var date_end = $("#max_loan_date").val();
    if (date_start && date_end) {
      report_dates = `${format_dates(date_start, "date")} - ${format_dates(
        date_end,
        "date"
      )}`;
    } else if (date_start) {
      report_dates = `From ${format_dates(date_start, "date")}`;
    } else if (date_end) {
      report_dates = `Up to ${format_dates(date_end, "date")}`;
    }
    var tr = footer.find("tr:eq(0)");
    tr.find("th:eq(1)").text(report_dates);
    tr.find("th:eq(3)").text(totals.total_amount);
    tr.find("th:eq(4)").text(totals.total_paid);
    tr.find("th:eq(5)").text(totals.total_balance);
  }
});
