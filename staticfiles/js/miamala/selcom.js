class SelcomManager {
  constructor() {
    this.config = {
      columnIndices: [0, 1, 2, 3, 4, 5],
      dateCache: { start: null, end: null },
      csrfToken: this.getCSRFToken(),
    };

    this.selectors = {
      newForm: "#new_selcom_transaction_form",
      editForm: "#edit_selcom_transaction_form",
      deleteForm: "#del_selcom_form",
      table: "#selcompay_table",

      // New transaction form elements
      newNames: "#sel_names",
      newAmount: "#sel_amount",
      newDescription: "#sel_description",
      newSubmitBtn: "#sel_trans_btn",

      // Edit transaction form elements
      editNames: "#sel_edit_names",
      editAmount: "#sel_edit_amount",
      editDescription: "#sel_edit_description",
      editSubmitBtn: "#sel_edit_trans_btn",
      transactionId: "#transaction_id",
      updateModal: "#update_selcom_modal",

      // Delete form elements
      deleteId: "#selcom_del_id",
      deleteSubmitBtn: "#sel_delete_btn",
      deleteModal: "#delete_selcom_modal",

      // Filter elements
      searchInput: "#search_selcom_field",
      clearFilter: "#selcom_filter_clear",
      minDate: "#min_trans_date",
      maxDate: "#max_trans_date",
      dateClear: "#date_filter_clear",
      dateFilterBtn: "#date_filter_btn",

      // Page elements
      transactionsToggle: "#transactions_toggle",
      selcomPage: "#selcom_pay_page",
      dateFilterModal: "#dateFilterModal",
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
    this.setupFormHandlers();
    this.setupTable();
    this.setupEventHandlers();
  }

  /**
   * Setup all form handlers
   */
  setupFormHandlers() {
    this.setupNewTransactionForm();
    this.setupEditTransactionForm();
    this.setupDeleteTransactionForm();
  }

  /**
   * Setup new transaction form handler
   */
  setupNewTransactionForm() {
    $(this.selectors.newForm).on("submit", (e) =>
      this.handleNewTransactionSubmit(e)
    );
  }

  /**
   * Handle new transaction form submission
   */
  handleNewTransactionSubmit(e) {
    e.preventDefault();

    const formData = new FormData();
    formData.append("names", $.trim($(this.selectors.newNames).val()));
    formData.append("amount", $(this.selectors.newAmount).val());
    formData.append("describe", $.trim($(this.selectors.newDescription).val()));

    this.submitForm({
      form: $(this.selectors.newForm),
      formData: formData,
      submitBtn: $(this.selectors.newSubmitBtn),
      submitText: "Add",
      onSuccess: (response) => {
        if (response.success) {
          $(this.selectors.newForm)[0].reset();
          this.table.draw();
        }
      },
    });
  }

  /**
   * Setup edit transaction form handler
   */
  setupEditTransactionForm() {
    $(this.selectors.editForm).on("submit", (e) =>
      this.handleEditTransactionSubmit(e)
    );
  }

  /**
   * Handle edit transaction form submission
   */
  handleEditTransactionSubmit(e) {
    e.preventDefault();

    const formData = new FormData();
    formData.append("transact_id", $(this.selectors.transactionId).val());
    formData.append("names", $.trim($(this.selectors.editNames).val()));
    formData.append("amount", $(this.selectors.editAmount).val());
    formData.append(
      "describe",
      $.trim($(this.selectors.editDescription).val())
    );

    this.submitForm({
      form: $(this.selectors.editForm),
      formData: formData,
      submitBtn: $(this.selectors.editSubmitBtn),
      submitText: "Update",
      onSuccess: (response) => {
        if (response.success) {
          this.table.draw();
        }
      },
    });
  }

  /**
   * Setup delete transaction form handler
   */
  setupDeleteTransactionForm() {
    $(this.selectors.deleteForm).on("submit", (e) =>
      this.handleDeleteTransactionSubmit(e)
    );
  }

  /**
   * Handle delete transaction form submission
   */
  handleDeleteTransactionSubmit(e) {
    e.preventDefault();

    const selcomId = $(this.selectors.deleteId).val();
    if (parseInt(selcomId) > 0) {
      const formData = new FormData();
      formData.append("delete_id", selcomId);

      this.submitForm({
        form: $(this.selectors.deleteForm),
        formData: formData,
        submitBtn: $(this.selectors.deleteSubmitBtn),
        submitText: "Yes",
        onSuccess: (response) => {
          if (response.success) {
            $(this.selectors.deleteId).val("");
            this.table.draw();
          }
        },
      });
    }
  }

  /**
   * Generic form submission handler
   */
  submitForm({ form, formData, submitBtn, submitText, onSuccess }) {
    const formSms = form.find(".formsms");

    $.ajax({
      type: "POST",
      url: form.attr("action"),
      data: formData,
      dataType: "json",
      contentType: false,
      processData: false,
      headers: { "X-CSRFToken": this.config.csrfToken },
      beforeSend: () => this.setFormLoading(submitBtn, true),
      success: (response) => {
        this.setFormLoading(submitBtn, false, submitText);
        this.handleFormResponse(formSms, response);
        if (onSuccess) onSuccess(response);
      },
      error: (xhr, status, error) => {
        console.error(error);
        this.setFormLoading(submitBtn, false, submitText);
      },
    });
  }

  /**
   * Set form loading state
   */
  setFormLoading(submitBtn, isLoading, submitText = "Submit") {
    if (isLoading) {
      submitBtn
        .html("<i class='fas fa-spinner fa-pulse'></i>")
        .attr("type", "button");
    } else {
      submitBtn.html(submitText).attr("type", "submit");
    }
  }

  /**
   * Handle form response
   */
  handleFormResponse(formSms, response) {
    const alertType = response.success ? "alert-success" : "alert-danger";
    const iconType = response.success ? "check" : "exclamation";
    const alert = `<i class="fas fa-${iconType}-circle"></i> &nbsp; ${response.sms}`;

    formSms
      .removeClass("alert-success alert-danger")
      .addClass(alertType)
      .html(alert)
      .slideDown("fast")
      .delay(5000)
      .slideUp("fast");
  }

  /**
   * Fill edit form or show delete modal
   */
  fillEditForm(rowIndex, id, action) {
    if (action === "edit") {
      const row = $(
        `${this.selectors.table} tbody tr:nth-child(${rowIndex + 1})`
      );
      const amount = $("td:nth-child(4)", row).text().replace(/,/g, "");
      let describe = $("td:nth-child(1)", row).attr("data-bs-describe");
      describe = describe === "null" ? "" : describe;

      $(this.selectors.editNames).val($("td:nth-child(3)", row).text());
      $(this.selectors.editAmount).val(parseFloat(amount));
      $(this.selectors.editDescription).val(describe);
      $(this.selectors.transactionId).val(id);
      $(this.selectors.updateModal).modal("show");
    } else {
      $(this.selectors.deleteId).val(id);
      $(this.selectors.deleteModal).modal("show");
    }
  }

  /**
   * Format dates for display
   */
  formatDates(dateStr, format) {
    const date = dateStr === "today" ? new Date() : new Date(dateStr);
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

    const day = date.getDate() < 10 ? "0" + date.getDate() : date.getDate();
    const hours =
      date.getHours() < 10 ? "0" + date.getHours() : date.getHours();
    const minutes =
      date.getMinutes() < 10 ? "0" + date.getMinutes() : date.getMinutes();

    if (format === "datetime") {
      return `${day}-${
        months[date.getMonth()]
      }-${date.getFullYear()} ${hours}:${minutes}`;
    } else {
      return `${day}-${months[date.getMonth()]}-${date.getFullYear()}`;
    }
  }

  /**
   * Get dates range from date filter modal
   */
  getDateRange() {
    const minDateStr = $(this.selectors.minDate).val();
    const maxDateStr = $(this.selectors.maxDate).val();

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
    $(`${this.selectors.table} thead tr`)
      .clone(true)
      .attr("class", "filters")
      .appendTo(`${this.selectors.table} thead`);

    this.table = $(this.selectors.table).DataTable({
      fixedHeader: true,
      processing: true,
      serverSide: true,
      ajax: this.getAjaxConfig(),
      columns: this.getColumnConfig(),
      order: [[1, "desc"]],
      paging: true,
      pageLength: 10,
      lengthChange: true,
      autoWidth: true,
      searching: true,
      bInfo: true,
      bSort: true,
      orderCellsTop: true,
      columnDefs: this.getColumnDefs(),
      dom: "lBfrtip",
      drawCallback: (response) => this.handleDrawCallback(response),
      initComplete: () => this.initTableFilters(),
    });
  }

  /**
   * Get AJAX configuration for DataTable
   */
  getAjaxConfig() {
    return {
      url: $(this.selectors.selcomPage).val(),
      type: "POST",
      data: (d) => {
        const dateRange = this.getDateRange();
        d.startdate = dateRange.start;
        d.enddate = dateRange.end;
      },
      dataType: "json",
      headers: { "X-CSRFToken": this.config.csrfToken },
    };
  }

  /**
   * Get column configuration
   */
  getColumnConfig() {
    return [
      { data: "count" },
      { data: "dates" },
      { data: "names" },
      { data: "amount" },
      { data: "profit" },
      { data: "action" },
    ];
  }

  /**
   * Get column definitions
   */
  getColumnDefs() {
    return [
      {
        targets: [0, 5],
        orderable: false,
      },
      {
        targets: 5,
        createdCell: (cell, cellData, rowData, rowIndex, colIndex) => {
          const btn = `
            <button class="btn btn-sm btn-dblue text-white me-1" 
                    onclick="selcomManager.fillEditForm(${rowIndex}, ${rowData.id}, 'edit')">
              <i class="fas fa-edit"></i>
            </button> 
            <button class="btn btn-sm btn-danger" 
                    onclick="selcomManager.fillEditForm('', ${rowData.id}, 'del')">
              <i class="fas fa-trash"></i>
            </button>
          `;
          $(cell).html(btn);
        },
      },
      {
        targets: 0,
        createdCell: (cell, cellData, rowData, rowIndex, colIndex) => {
          const info = rowData.describe === "" ? "null" : rowData.describe;
          $(cell)
            .attr("data-bs-toggle", "tooltip")
            .attr("title", "Comment: " + info)
            .attr("data-bs-describe", info);
        },
      },
      {
        targets: "_all",
        className: "align-middle text-nowrap text-center",
      },
    ];
  }

  /**
   * Handle draw callback
   */
  handleDrawCallback(response) {
    const grandTotals = response.json.grand_totals;
    const grandObj = {
      total_amount: grandTotals.total_amount,
      total_profit: grandTotals.total_profit,
    };
    this.updateFooter(grandObj);
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
        cell.addClass("bg-white");

        if (colIdx === 0 || colIdx === 5) {
          cell.html("");
        } else if (colIdx === 1) {
          const calendar = `
            <button type="button" class="btn btn-primary text-white" 
                    data-bs-toggle="modal" data-bs-target="${this.selectors.dateFilterModal}">
              <i class="fas fa-calendar-alt"></i>
            </button>
          `;
          cell.html(calendar).addClass("text-center");
        } else {
          cell.html(
            "<input type='text' class='text-charcoal' placeholder='Filter..'/>"
          );
          cell.addClass("text-center");
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
   * Setup all event handlers
   */
  setupEventHandlers() {
    this.setupSearchHandler();
    this.setupFilterHandlers();
  }

  /**
   * Setup search handler
   */
  setupSearchHandler() {
    $(this.selectors.searchInput)
      .off("keyup")
      .on("keyup", () => {
        this.table.search($(this.selectors.searchInput).val()).draw();
      });
  }

  /**
   * Setup filter handlers
   */
  setupFilterHandlers() {
    // Clear all filters
    $(this.selectors.clearFilter)
      .off("click")
      .on("click", (e) => {
        e.preventDefault();
        $(this.selectors.searchInput).val("");
        $(this.selectors.minDate).val("");
        $(this.selectors.maxDate).val("");
        $('.filters input[type="text"]').val("");
        this.table.search("").columns().search("").draw();
      });

    // Date filter handlers
    $(this.selectors.dateClear)
      .off("click")
      .on("click", () => {
        $(this.selectors.minDate).val("");
        $(this.selectors.maxDate).val("");
      });

    $(this.selectors.dateFilterBtn)
      .off("click")
      .on("click", () => this.table.draw());
  }

  /**
   * Update footer values
   */
  updateFooter(totals) {
    const footer = $(this.table.table().footer());
    let reportDates = "All time";
    const dateStart = $(this.selectors.minDate).val();
    const dateEnd = $(this.selectors.maxDate).val();

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
    tr.find("th:eq(4)").text(totals.total_profit);
  }
}

// Global functions for onclick handlers
function fill_edit_form(rowIndex, id, str) {
  if (window.selcomManager) {
    window.selcomManager.fillEditForm(rowIndex, id, str);
  }
}

// Initialize the application when DOM is ready
$(function () {
  window.selcomManager = new SelcomManager();
});
