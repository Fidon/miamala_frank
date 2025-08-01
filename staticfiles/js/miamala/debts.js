class DebtsManager {
  constructor() {
    this.config = {
      columnIndices: [0, 1, 2, 3, 4, 5, 6, 7, 8],
      dateCache: { start: null, end: null },
      csrfToken: this.getCSRFToken(),
    };

    this.selectors = {
      newDebtForm: "#new_debt_form",
      editDebtForm: "#edit_debt_form",
      deleteDebtForm: "#del_debt_form",
      debtsTable: "#debts_table",
      updateDebtModal: "#update_debt_modal",
      deleteDebtModal: "#delete_debt_modal",
      dateFilterModal: "#dateFilterModal",
      transactionsToggle: "#transactions_toggle",
      searchField: "#search_debt_field",
      filterClear: "#debts_filter_clear",
      dateFilterBtn: "#date_filter_btn",
      dateFilterClear: "#date_filter_clear",
      minDebtDate: "#min_debt_date",
      maxDebtDate: "#max_debt_date",
      debtsPageUrl: "#debts_page_url",

      // Form fields
      debtNames: "#debt_names",
      debtAmount: "#debt_amount",
      debtDescription: "#debt_description",
      debtEditNames: "#debt_edit_names",
      debtEditAmount: "#debt_edit_amount",
      debtEditPaid: "#debt_edit_paid",
      debtEditDescription: "#debt_edit_description",
      debtId: "#debt_id",
      debtDelId: "#debt_del_id",

      // Buttons
      newDebtBtn: "#new_debt_btn",
      debtEditBtn: "#debt_edit_btn",
      debtDeleteBtn: "#debt_delete_btn",
    };

    this.table = null;
    this.init();
  }

  /**
   * Get CSRF token from meta tag
   */
  getCSRFToken() {
    const metaTag = document.querySelector('meta[name="csrf-token"]');
    return metaTag ? metaTag.getAttribute("content") : "";
  }

  /**
   * Initialize the application
   */
  init() {
    $(this.selectors.transactionsToggle).click();
    this.setupTable();
    this.setupEventHandlers();
  }

  /**
   * Format dates for DataTable
   */
  formatDates(dateStr, str) {
    const today = dateStr === "today" ? new Date() : new Date(dateStr);
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

    if (str === "datetime") {
      return `${day}-${
        months[today.getMonth()]
      }-${today.getFullYear()} ${hours}:${minutes}`;
    } else {
      return `${day}-${months[today.getMonth()]}-${today.getFullYear()}`;
    }
  }

  /**
   * Check if debt payment is valid
   */
  checkDebt(debt, paid) {
    if (paid < 0) {
      return Math.abs(paid) <= debt;
    }
    return true;
  }

  /**
   * Fill edit form with data
   */
  fillEditForm(rowIndex, id, action) {
    if (action === "edit") {
      const row = $(
        `${this.selectors.debtsTable} tbody tr:nth-child(${rowIndex + 1})`
      );
      const names = $("td:nth-child(3)", row).text();
      const debt = $("td:nth-child(6)", row).text().replace(/,/g, "");
      let describe = $("td:nth-child(1)", row).attr("data-bs-describe");
      describe = describe === "null" ? "" : describe;

      $(this.selectors.debtEditNames).val(names);
      $(this.selectors.debtEditAmount).val(parseFloat(debt));
      $(this.selectors.debtEditDescription).val(describe);
      $(this.selectors.debtId).val(id);
      $(this.selectors.updateDebtModal).modal("show");
    } else {
      $(this.selectors.debtDelId).val(id);
      $(this.selectors.deleteDebtModal).modal("show");
    }
  }

  /**
   * Generate alert messages
   */
  generateAlert(isSuccess, message) {
    const iconClass = isSuccess
      ? "fas fa-check-circle"
      : "fas fa-exclamation-circle";
    return `<i class="${iconClass}"></i> &nbsp; ${message}`;
  }

  /**
   * Setup all event handlers
   */
  setupEventHandlers() {
    this.setupNewDebtForm();
    this.setupEditDebtForm();
    this.setupDeleteDebtForm();
    this.setupSearchAndFilters();
    this.setupDateFilters();

    // Make fillEditForm globally accessible
    window.fill_edit_form = (rowIndex, id, str) => {
      this.fillEditForm(rowIndex, id, str);
    };
  }

  /**
   * Setup new debt form
   */
  setupNewDebtForm() {
    $(this.selectors.newDebtForm).submit((e) => {
      e.preventDefault();
      const form = $(this.selectors.newDebtForm);
      const submitBtn = $(this.selectors.newDebtBtn);
      const formSms = $(`${this.selectors.newDebtForm} .formsms`);

      this.handleNewDebtSubmit(form, submitBtn, formSms);
    });
  }

  /**
   * Handle new debt form submission
   */
  handleNewDebtSubmit(form, submitBtn, formSms) {
    const formData = new FormData();
    formData.append("names", $.trim($(this.selectors.debtNames).val()));
    formData.append("amount", $(this.selectors.debtAmount).val());
    formData.append(
      "describe",
      $.trim($(this.selectors.debtDescription).val())
    );

    $.ajax({
      type: "POST",
      url: form.attr("action"),
      data: formData,
      dataType: "json",
      contentType: false,
      processData: false,
      headers: { "X-CSRFToken": this.config.csrfToken },
      beforeSend: () => {
        submitBtn
          .html("<i class='fas fa-spinner fa-pulse'></i>")
          .attr("type", "button");
      },
      success: (response) => {
        submitBtn.html("Add").attr("type", "submit");

        const alert = this.generateAlert(response.success, response.sms);
        const alertClass = response.success ? "alert-success" : "alert-danger";
        const removeAlertClass = response.success
          ? "alert-danger"
          : "alert-success";

        formSms.removeClass(removeAlertClass).addClass(alertClass);
        formSms.html(alert).slideDown("fast").delay(5000).slideUp("fast");

        if (response.success) {
          $(this.selectors.newDebtForm)[0].reset();
          this.table.draw();
        }
      },
      error: (xhr, status, error) => {
        console.error(error);
        submitBtn.html("Add").attr("type", "submit");
      },
    });
  }

  /**
   * Setup edit debt form
   */
  setupEditDebtForm() {
    $(this.selectors.editDebtForm).submit((e) => {
      e.preventDefault();
      const formSms = $(`${this.selectors.editDebtForm} .formsms`);
      const submitBtn = $(this.selectors.debtEditBtn);

      const debtNames = $.trim($(this.selectors.debtEditNames).val());
      const debtAmount = parseFloat($(this.selectors.debtEditAmount).val());
      const debtPaid = parseFloat($(this.selectors.debtEditPaid).val());
      const debtDescribe = $.trim($(this.selectors.debtEditDescription).val());

      if (this.checkDebt(debtAmount, debtPaid)) {
        this.handleEditDebtSubmit(submitBtn, formSms, debtAmount, debtPaid);
      } else {
        const alert = this.generateAlert(
          false,
          "Paid amount cannot exceed current debt!"
        );
        formSms
          .removeClass("alert-success")
          .addClass("alert-danger")
          .html(alert)
          .slideDown("fast")
          .delay(5000)
          .slideUp("fast");
      }
    });
  }

  /**
   * Handle edit debt form submission
   */
  handleEditDebtSubmit(submitBtn, formSms, debtAmount, debtPaid) {
    const form = $(this.selectors.editDebtForm);
    const formData = new FormData();
    formData.append("debt_id", $(this.selectors.debtId).val());
    formData.append("names", $.trim($(this.selectors.debtEditNames).val()));
    formData.append("paid", debtPaid);
    formData.append(
      "describe",
      $.trim($(this.selectors.debtEditDescription).val())
    );

    $.ajax({
      type: "POST",
      url: form.attr("action"),
      data: formData,
      dataType: "json",
      contentType: false,
      processData: false,
      headers: { "X-CSRFToken": this.config.csrfToken },
      beforeSend: () => {
        submitBtn
          .html("<i class='fas fa-spinner fa-pulse'></i>")
          .attr("type", "button");
      },
      success: (response) => {
        submitBtn.html("Update").attr("type", "submit");

        const alert = this.generateAlert(response.success, response.sms);
        const alertClass = response.success ? "alert-success" : "alert-danger";
        const removeAlertClass = response.success
          ? "alert-danger"
          : "alert-success";

        formSms.removeClass(removeAlertClass).addClass(alertClass);
        formSms.html(alert).slideDown("fast").delay(5000).slideUp("fast");

        if (response.success) {
          $(this.selectors.debtEditAmount).val(debtAmount + debtPaid);
          $(this.selectors.debtEditPaid).val("");
          this.table.draw();
        }
      },
      error: (xhr, status, error) => {
        console.error(error);
        submitBtn.html("Update").attr("type", "submit");
      },
    });
  }

  /**
   * Setup delete debt form
   */
  setupDeleteDebtForm() {
    $(this.selectors.deleteDebtForm).submit((e) => {
      e.preventDefault();
      const delDebtId = $(this.selectors.debtDelId).val();

      if (parseInt(delDebtId) > 0) {
        const submitBtn = $(this.selectors.debtDeleteBtn);
        const formSms = $(`${this.selectors.deleteDebtForm} .formsms`);
        this.handleDeleteDebtSubmit(submitBtn, formSms, delDebtId);
      }
    });
  }

  /**
   * Handle delete debt form submission
   */
  handleDeleteDebtSubmit(submitBtn, formSms, delDebtId) {
    const form = $(this.selectors.deleteDebtForm);
    const formData = new FormData();
    formData.append("delete_id", delDebtId);

    $.ajax({
      type: "POST",
      url: form.attr("action"),
      data: formData,
      dataType: "json",
      contentType: false,
      processData: false,
      headers: { "X-CSRFToken": this.config.csrfToken },
      beforeSend: () => {
        submitBtn
          .html("<i class='fas fa-spinner fa-pulse'></i>")
          .attr("type", "button");
      },
      success: (response) => {
        submitBtn.html("Yes").attr("type", "submit");

        const alert = this.generateAlert(response.success, response.sms);
        const alertClass = response.success ? "alert-success" : "alert-danger";
        const removeAlertClass = response.success
          ? "alert-danger"
          : "alert-success";

        formSms.removeClass(removeAlertClass).addClass(alertClass);
        formSms.html(alert).slideDown("fast").delay(5000).slideUp("fast");

        if (response.success) {
          $(this.selectors.debtDelId).val("");
          this.table.draw();
        }
      },
      error: (xhr, status, error) => {
        console.error(error);
        submitBtn.html("Yes").attr("type", "submit");
      },
    });
  }

  /**
   * Setup search and filter handlers
   */
  setupSearchAndFilters() {
    // Global search
    $(this.selectors.searchField).keyup(() => {
      this.table.search($(this.selectors.searchField).val()).draw();
    });

    // Clear all filters
    $(this.selectors.filterClear).click((e) => {
      e.preventDefault();
      $(this.selectors.searchField).val("");
      $(this.selectors.minDebtDate).val("");
      $(this.selectors.maxDebtDate).val("");
      $('.filters input[type="text"]').val("");
      this.table.search("").columns().search("").draw();
    });
  }

  /**
   * Setup date filter handlers
   */
  setupDateFilters() {
    $(this.selectors.dateFilterClear).on("click", () => {
      $(this.selectors.minDebtDate).val("");
      $(this.selectors.maxDebtDate).val("");
    });

    $(this.selectors.dateFilterBtn).on("click", () => {
      this.table.draw();
    });
  }

  /**
   * Get date range for filtering
   */
  getDateRange() {
    const minDateStr = $(this.selectors.minDebtDate).val();
    const maxDateStr = $(this.selectors.maxDebtDate).val();

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
      this.config.dateCache.start = dtStartUtc;
      this.config.dateCache.end = dtEndUtc;

      return { start: dtStartUtc, end: dtEndUtc };
    } catch (error) {
      console.error("Date processing error:", error);
      return { start: null, end: null };
    }
  }

  /**
   * Setup DataTable
   */
  setupTable() {
    // Clone header for filters
    $(`${this.selectors.debtsTable} thead tr`)
      .clone(true)
      .attr("class", "filters")
      .appendTo(`${this.selectors.debtsTable} thead`);

    this.table = $(this.selectors.debtsTable).DataTable({
      fixedHeader: true,
      processing: true,
      serverSide: true,
      ajax: {
        url: $(this.selectors.debtsPageUrl).val(),
        type: "POST",
        data: (d) => {
          const dateRange = this.getDateRange();
          d.startdate = dateRange.start;
          d.enddate = dateRange.end;
        },
        dataType: "json",
        headers: { "X-CSRFToken": this.config.csrfToken },
      },
      columns: [
        { data: "count" },
        { data: "dates" },
        { data: "names" },
        { data: "amount" },
        { data: "paid" },
        { data: "balance" },
        { data: "shop" },
        { data: "user" },
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
          targets: [0, 8],
          orderable: false,
        },
        {
          targets: 8,
          createdCell: (cell, cellData, rowData, rowIndex, colIndex) => {
            const btn = `<button class="btn btn-sm btn-dblue text-white me-1" onclick="fill_edit_form(${rowIndex}, ${rowData.id}, 'edit')"><i class="fas fa-edit"></i></button> <button class="btn btn-sm btn-danger" onclick="fill_edit_form('', ${rowData.id}, 'del')"><i class="fas fa-trash"></i></button>`;
            $(cell).html(btn);
          },
        },
        {
          targets: 0,
          createdCell: (cell, cellData, rowData, rowIndex, colIndex) => {
            const info = rowData.describe === "" ? "null" : rowData.describe;
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
      drawCallback: (response) => {
        const grandTotals = response.json.grand_totals;
        const grandObj = {
          total_amount: grandTotals.total_amount,
          total_paid: grandTotals.total_paid,
          total_balance: grandTotals.total_balance,
        };
        this.updateFooter(grandObj);
      },
      initComplete: () => this.initTableFilters(),
    });
  }

  /**
   * Initialize table filters
   */
  initTableFilters() {
    const api = this.table;

    api
      .columns(this.config.columnIndices)
      .eq(0)
      .each((colIdx) => {
        const cell = $(".filters th").eq(
          $(api.column(colIdx).header()).index()
        );
        $(cell).addClass("bg-white");

        if (colIdx === 0 || colIdx === 8) {
          cell.html("");
        } else if (colIdx === 1) {
          const calendar = `<button type="button" class="btn btn-primary text-white" data-bs-toggle="modal" data-bs-target="#dateFilterModal"><i class="fas fa-calendar-alt"></i></button>`;
          cell.html(calendar);
          cell.addClass("text-center");
        } else {
          $(cell).html(
            "<input type='text' class='text-charcoal' placeholder='Filter..'/>"
          );
          $(cell).addClass("text-center");
          this.setupColumnFilter(cell, api, colIdx);
        }
      });
  }

  /**
   * Setup individual column filter
   */
  setupColumnFilter(cell, api, colIdx) {
    const input = $("input", cell);

    input.off("keyup change").on("keyup change", function (e) {
      e.stopPropagation();
      $(this).attr("title", $(this).val());
      const regexr = "{search}";
      const cursorPosition = this.selectionStart;

      api
        .column(colIdx)
        .search(
          this.value !== "" ? regexr.replace("{search}", this.value) : "",
          this.value !== "",
          this.value === ""
        )
        .draw();

      $(this).focus()[0].setSelectionRange(cursorPosition, cursorPosition);
    });
  }

  /**
   * Update footer values
   */
  updateFooter(totals) {
    const footer = $(this.table.table().footer());
    let reportDates = "All time";
    const dateStart = $(this.selectors.minDebtDate).val();
    const dateEnd = $(this.selectors.maxDebtDate).val();

    if (dateStart && dateEnd) {
      reportDates = `${this.formatDates(
        dateStart,
        "date"
      )} - ${this.formatDates(dateEnd, "date")}`;
    } else if (dateStart) {
      reportDates = `From ${this.formatDates(dateStart, "date")}`;
    } else if (dateEnd) {
      reportDates = `Up to ${this.formatDates(dateEnd, "date")}`;
    }

    const tr = footer.find("tr:eq(0)");
    tr.find("th:eq(1)").text(reportDates);
    tr.find("th:eq(3)").text(totals.total_amount);
    tr.find("th:eq(4)").text(totals.total_paid);
    tr.find("th:eq(5)").text(totals.total_balance);
  }
}

// Initialize the application when DOM is ready
$(function () {
  new DebtsManager();
});
