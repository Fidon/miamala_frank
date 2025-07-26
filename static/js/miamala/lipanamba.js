// fill update form
function fill_edit_form(rowIndex, id, str) {
  if (str == "edit") {
    var row = $("#lipanamba_table tbody tr:nth-child(" + (rowIndex + 1) + ")");
    var amount = $("td:nth-child(4)", row).text().replace(/,/g, "");
    var describe = $("td:nth-child(1)", row).attr("data-bs-describe");
    describe = describe == "null" ? "" : describe;
    $("#lipa_edit_names").val($("td:nth-child(3)", row).text());
    $("#lipa_edit_amount").val(parseFloat(amount));
    $("#lipa_edit_description").val(describe);
    $("#transaction_id").val(id);
    $("#update_lipa_modal").modal("show");
  } else {
    $("#lipa_del_id").val(id);
    $("#delete_lipa_modal").modal("show");
  }
}

$(function () {
  // Get the CSRF token
  const CSRF_TOKEN = document
    .querySelector('meta[name="csrf-token"]')
    .getAttribute("content");
  const dateCache = { start: null, end: null };
  $("#transactions_toggle").click();

  // New lipanamba transactions
  $("#new_lipa_transaction_form").submit(function (e) {
    e.preventDefault();
    var formSms = $("#new_lipa_transaction_form .formsms");
    var trans_names = $.trim($("#lipa_names").val());
    var trans_amount = $("#lipa_amount").val();
    var trans_describe = $.trim($("#lipa_description").val());
    var formData = new FormData();
    formData.append("names", trans_names);
    formData.append("amount", trans_amount);
    formData.append("describe", trans_describe);

    var submitBtn = $("#lipa_trans_btn");

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
          $("#new_lipa_transaction_form")[0].reset();
          table.draw();
        } else {
          alert = `<i class="fas fa-exclamation-circle"></i> &nbsp; ${response.sms}`;
          formSms.removeClass("alert-success").addClass("alert-danger");
        }
        formSms.html(alert).slideDown("fast").delay(5000).slideUp("fast");
      },
      error: function (xhr, status, error) {
        console.error(error);
      },
    });
  });

  // submit lipa transaction update form
  $("#edit_lipa_transaction_form").submit(function (e) {
    e.preventDefault();
    var formSms = $("#edit_lipa_transaction_form .formsms");
    var trans_names = $.trim($("#lipa_edit_names").val());
    var trans_amount = $("#lipa_edit_amount").val();
    var trans_describe = $.trim($("#lipa_edit_description").val());
    var formData = new FormData();
    formData.append("transact_id", $("#transaction_id").val());
    formData.append("names", trans_names);
    formData.append("amount", trans_amount);
    formData.append("describe", trans_describe);

    var submitBtn = $("#lipa_edit_trans_btn");

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
          alert = `<i class="fas fa-check-circle"></i> &nbsp; ${response.sms}`;
          formSms.removeClass("alert-danger").addClass("alert-success");
          table.draw();
        } else {
          alert = `<i class="fas fa-exclamation-circle"></i> &nbsp; ${response.sms}`;
          formSms.removeClass("alert-success").addClass("alert-danger");
        }
        formSms.html(alert).slideDown("fast").delay(5000).slideUp("fast");
      },
      error: function (xhr, status, error) {
        console.error(error);
      },
    });
  });

  // delete lipanamba transaction
  $("#del_lipa_form").submit(function (e) {
    e.preventDefault();
    var lipa_id = $("#lipa_del_id").val();
    if (parseInt(lipa_id) > 0) {
      var formData = new FormData();
      formData.append("delete_id", lipa_id);

      var submitBtn = $("#lipa_delete_btn");
      var formSms = $("#del_lipa_form .formsms");

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
            $("#lipa_del_id").val("");
            alert = `<i class="fas fa-check-circle"></i> &nbsp; ${response.sms}`;
            formSms.removeClass("alert-danger").addClass("alert-success");
            table.draw();
          } else {
            alert = `<i class="fas fa-exclamation-circle"></i> &nbsp; ${response.sms}`;
            formSms.removeClass("alert-success").addClass("alert-danger");
          }
          formSms.html(alert).slideDown("fast").delay(5000).slideUp("fast");
        },
        error: function (xhr, status, error) {
          console.error(error);
        },
      });
    }
  });

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

  // Get dates from dateFilter modal
  function get_dates_range() {
    const minDateStr = $("#min_trans_date").val();
    const maxDateStr = $("#max_trans_date").val();

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
  $("#lipanamba_table thead tr")
    .clone(true)
    .attr("class", "filters")
    .appendTo("#lipanamba_table thead");

  var table = $("#lipanamba_table").DataTable({
    fixedHeader: true,
    processing: true,
    serverSide: true,
    ajax: {
      url: $("#lipanamba_page_url").val(),
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
      { data: "profit" },
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
        targets: [0, 5],
        orderable: false,
      },
      {
        targets: 5,
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
        total_profit: grand_totals.total_profit,
      };
      updateFooter(grand_obj);
    },
    initComplete: function () {
      var api = this.api();
      api
        .columns([0, 1, 2, 3, 4, 5])
        .eq(0)
        .each(function (colIdx) {
          var cell = $(".filters th").eq(
            $(api.column(colIdx).header()).index()
          );
          $(cell).addClass("bg-white");

          if (colIdx == 0 || colIdx == 5) {
            cell.html("");
          } else if (colIdx == 1) {
            var calendar = `<button type="button" class="btn btn-primary text-white" data-bs-toggle="modal" data-bs-target="#dateFilterModal"><i class="fas fa-calendar-alt"></i></button>`;
            cell.html(calendar);
            cell.addClass("text-center");
            $("#date_filter_clear").on("click", function () {
              $("#min_trans_date").val("");
              $("#max_trans_date").val("");
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
  $("#search_lipa_field").keyup(function () {
    table.search($(this).val()).draw();
  });

  // clear all table filters
  $("#lipanamba_filter_clear").click(function (e) {
    e.preventDefault();
    $("#search_lipa_field").val("");
    $("#min_trans_date").val("");
    $("#max_trans_date").val("");
    $('.filters input[type="text"]').val("");
    table.search("").columns().search("").draw();
  });

  // update footer values
  function updateFooter(totals) {
    var footer = $(table.table().footer());
    var report_dates = "All time";
    var date_start = $("#min_trans_date").val();
    var date_end = $("#max_trans_date").val();
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
    tr.find("th:eq(4)").text(totals.total_profit);
  }
});
